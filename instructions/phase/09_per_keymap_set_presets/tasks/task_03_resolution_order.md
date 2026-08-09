# task_03_resolution_order

## 目的

プリセットの**解決順序**を実装する（暫定仕様 08 **§3-2**・受入条件 **1 / 2 / 8 / 15**）。
task_02 で keymap_set から runtime へ運ばれるようになった 2 キーを使い、
**個別指定 ON なら個別ファイル / 読めなければグローバル / どちらも読めなければ置き換えない**とする。
あわせて **config 外を指す個別パスを無効**として扱う。

**レイヤ制約**: **application 限定**（`config_service/split_loading.py`）。
**domain / presentation は不変**。**保存側（`split_payloads`）も不変**（task_02 の到達点を維持）。
**`apply_global_defaults` は変更しない**（E1〜E4 は常にグローバル）。

## 対象範囲

### 1. `keyseq/application/config_service/split_loading.py` — 任意パス読み出しの切り出し

現在の `load_global_hotkey_presets`（`:65-79`）から、**「保存表記のパスを受け取って `list | None` を返す」
汎用の読み出し**を切り出す:

```python
def load_hotkey_presets_file(service, stored_path: Any, *, config_root: str) -> list[Any] | None:
    """プリセットファイルを読み、読めた場合だけ正規化済みの list を返す。"""
```

- 中身は現行 `load_global_hotkey_presets` の本体と同じ規則
  （`_resolve_config_relative_path` → `_load_optional_json` → dict か / 根キーが list か →
  `normalize_hotkey_presets`。**例外は捕捉して `None`**）。
- **`load_global_hotkey_presets` はこれを使う薄いラッパ**にする
  （`load_global_hotkey_presets_path` の結果を渡すだけ）。**公開名と戻り値の規約は変えない**。
- **空文字・非文字列の `stored_path` は `None`**（読めない扱い）。

### 2. 同ファイル — 個別パスの有効判定

```python
def resolve_individual_hotkey_presets_path(service, runtime, *, config_root: str) -> str
```
（名前は実装者判断でよい。**判定ロジックを 1 箇所に閉じる**ことが要件）

- `runtime.get("hotkey_presets_individual")` が **`True`（真偽値）でなければ無効**（空文字を返す）。
- パスが**空文字・非文字列なら無効**。
- **解決後のパスが config 配下でなければ無効**（`service.is_path_within(...)` を使う。
  **`canonical_path` / `is_path_within` は比較専用**なので、**戻り値や保存値に使わない**）。
  `config_root` が空のときは判定できないため**無効**とする。
- **キーの値は書き換えない**（無効でも `runtime["hotkey_presets_path"]` はそのまま）。

### 3. 同ファイル — `build_runtime_data_from_split` の供給を解決順序へ

現在（`:120-123` 付近）:

```python
hotkey_presets = load_global_hotkey_presets(service, config_root=config_root)
if hotkey_presets is not None:
    runtime["hotkey_presets"] = hotkey_presets
```

これを次の順序へ置き換える:

1. **個別パスが有効なら**個別ファイルを読む（`load_hotkey_presets_file`）
   - **読めた（`list`・空を含む）→ 採用**
   - **読めない（`None`）→ 2 へフォールバック**
2. **グローバルを読む**（`load_global_hotkey_presets`）
   - 読めた → 採用
   - **読めない → 置き換えない**（runtime の既定 = 組込 8 件を維持）

- **2 キーのコピーより後**に実行されること（`hotkey_presets_individual` / `hotkey_presets_path` が
  runtime に載っている必要がある）。現在の並び（キーコピー → … → プリセット供給）を保てばよい。
- **`apply_global_defaults` からは呼ばない**（E1〜E4 は keymap_set を持たないため常にグローバル）。

### 設計メモ / 制約

- **パス表記の罠**: `runtime["hotkey_presets_path"]` は**保存表記のまま**（config 配下なら相対）。
  **解決なしで `os.path` 系へ渡さない**。解決は `_resolve_config_relative_path` /
  `resolve_config_path` を通す。
- **正規化は読み出し側 1 箇所**（正本 §5.10.2）。個別・グローバルとも
  `normalize_hotkey_presets` を通った値になること。**注入 API 側・保存側には置かない**。
- **フォールバックの通知（UI 表示）は task_05 の担当**。本タスクでは
  「どちらを採用したか」を runtime へ持たせる必要はない
  （**内部キーを増やさない**。表示は task_05 で presentation 側が再判定する）。
- **受入条件 8 の「その旨が UI に出る」は task_05**。本タスクは**解決結果だけ**を満たす。

## 含まない

- **個別ファイルの既定パス算出・保存先の切替** → **task_04**
- **切替 UI・フォールバック中の表示** → **task_05**
- **Import の強制 OFF・別名保存の複製** → **task_06**
- `apply_global_defaults` の変更（E1〜E4 は常にグローバル）
- 保存側（`split_payloads`）の変更 / 正本の更新（**task_08**）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **209** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **186**）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **受入条件 2**: 個別指定 ON + 個別ファイルあり → **個別の内容**が runtime に載る
   （グローバルにも別内容を置き、**個別が勝つ**ことを値で確認）。
2. **受入条件 1**: 個別指定 OFF（フラグ無しを含む）→ **グローバル**が使われる
   （個別パスに別内容のファイルがあっても**読まれない**）。
3. **フォールバック**: 個別指定 ON + **個別ファイルが不存在 / 壊れている / 根キーが list でない**
   → **グローバルの内容**が使われる。
4. **両方読めない** → **置き換えない**（組込 8 件が残る）。
5. **空リストの扱い**: 個別ファイルが**読めて空**なら**空が採用**される
   （グローバルへフォールバック**しない**）。受入条件 9 の規則を個別側でも維持する。
6. **受入条件 15**: 個別パスが **config 外**（絶対パスで config_root の外）→ **無効**として
   グローバルが使われる。**`runtime["hotkey_presets_path"]` の値は書き換わらない**ことも確認する。
7. **正規化**: 個別ファイルに非 dict 要素・非文字列 `label`/`value` が混ざっていても
   **除去された正規化済みの値**が載る（読み出し側 1 箇所の規則が個別側にも効く）。
8. `load_global_hotkey_presets` の**既存の戻り値規約が変わっていない**
   （切り出しによる退行が無いこと。既存テストで担保されていれば追加不要）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 解決順序が §3-2 のとおりか /
  **空リストでフォールバックしていない**か〔読めた空は採用〕/ config 外の判定が
  比較専用 API で行われ**保存値を書き換えていない**か / `apply_global_defaults` に手が入っていないか /
  `load_global_hotkey_presets` の公開規約が保たれているか / パス解決の罠を踏んでいないか /
  正規化が読み出し側 1 箇所のままか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
