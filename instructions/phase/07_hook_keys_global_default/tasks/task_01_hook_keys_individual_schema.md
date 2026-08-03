# task_01_hook_keys_individual_schema

## 目的

hook キーの「個別指定あり」フラグ `hook_keys_individual` を runtime データのスキーマへ追加し、
**フラグが無い既存データの移行判定**（暫定仕様 06 §2「移行規則」）を domain の純関数として定義する。
以降のタスク（解決点 = task_02 / 保存 = task_03）はこの 1 本を呼ぶだけにするため、
**判定ロジックの置き場をここで 1 箇所に固定する**のが本タスクの主眼。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §2（確定事項・移行規則）/ §3（データモデル）/
  §7 受入条件 **6**（既存 keymap_set の移行）と **2**（新規は OFF）。
- **レイヤ制約: domain 限定**。`keyseq/domain/config.py` のみ変更する。
  application / presentation / infrastructure は**一切変更しない**。tkinter 依存を持ち込まない。
- **後方互換必須**（正本 `spec_detail/data_schema.md`）: 既存キーを削除しない・意味を変えない。

## 対象範囲（domain 限定・`keyseq/domain/config.py` のみ）

### 1. `DEFAULT_CONFIG` へ既定値を追加

`"hook_toggle_key": ""` の**直後**に `"hook_keys_individual": False` を追加する。
（= 新規作成した runtime は個別指定 OFF。受入条件 2 の土台）

### 2. 移行判定の純関数を新設

`normalize_key_name` の定義より後、`ensure_config_compatibility` より前に置く。

```python
def resolve_hook_keys_individual(source: Any) -> bool:
    """hook キーを個別指定するかを決める（暫定仕様 06 §2 の移行規則）。

    明示フラグ hook_keys_individual があればそれに従う。
    無ければ「正規化後に stop / toggle の少なくとも一方が非空」なら個別指定 ON とみなす。
    """
```

- 引数はキーマップセット相当の生 dict（`keymap_set.json` の payload / 単一 JSON の payload / runtime）。
- `dict` でなければ `False` を返す。
- **フラグが存在する場合はキーの中身を見ない**（明示フラグが優先）。値は `bool()` で真偽化する
  （既存の `keyboard_show_physical_key_labels` と同じ扱い）。
- フラグが無い場合のみ、`normalize_key_name(str(source.get("hook_stop_key", "") or ""))` と
  `hook_toggle_key` の同等式を評価し、**どちらか非空なら True**。
  `str(...)` で包むのは非文字列値（数値等）が来ても落ちないようにするため。

### 3. `ensure_config_compatibility` へ組み込む

既存の

```python
config["hook_stop_key"] = normalize_key_name(config.get("hook_stop_key", ""))
config["hook_toggle_key"] = normalize_key_name(config.get("hook_toggle_key", ""))
```

の**直後**に次を追加する（正規化後の値で判定させるため、この位置であること）。

```python
config["hook_keys_individual"] = resolve_hook_keys_individual(config)
```

- 既存行の順序・内容は変えない。`config.pop("hook_keymap_toggle_key", None)` の位置も変えない。
- **冪等であること**: 2 回目以降の呼び出しではフラグが既に存在するため、その値がそのまま維持される。

### 設計メモ / 制約

- **split 構成の読込経路ではこの移行は発火しない**。`split_loading.build_runtime_data_from_split` は
  `new_default_data()`（＝ `DEFAULT_CONFIG` 由来でフラグを**含む**）を土台にするため、
  最後の `ensure_config_compatibility` 時点ではフラグが常に存在するからである。
  **split 経路で生の `keymap_set` dict に対して `resolve_hook_keys_individual` を呼ぶのは task_02 の仕事**。
  本タスクでは「純関数と単一 JSON 経路（`ConfigService.load` → `ensure_config_compatibility`）」までを担う。
- **既存の保存 JSON バイト列比較テストへの影響**: `hook_keys_individual` は
  `_sanitize_runtime_for_storage`（runtime 全体をダンプする経路 = `export_runtime_data` と
  レガシー単一 JSON 保存）を通ると**出力 JSON に現れる**。
  該当する期待値ファイル / 比較テストが落ちた場合は、**差分が `hook_keys_individual` の追加 1 キーのみ**で
  あることを確認したうえで期待値を更新してよい。**それ以外のキーに差分が出た場合は実装を疑い、
  期待値を書き換えずに報告する**（`.claude/rules/spec_change_workflow.md` D「危険な誘惑」）。
  なお **keymap_set.json への書き出しは明示キー列挙**（`split_payloads.py`）のため、本タスクでは変化しない。
- 名前を `resolve_*` にするのは「解決（決定）する」意味を持たせるため。
  `migrate_*` にしないのは、フラグがある場合も含めて常にこの 1 本で決めるため。

## 含まない

- **split 経路での全体デフォルト注入・キー解決**（task_02）。`config/config.json` からの読み出しも含めない。
- **保存時の空文字クリアと `hook_keys_individual` の書き出し**（task_03）。
  `split_payloads.py` は本タスクでは触らない。
- **config.json への全体デフォルト 2 キーの追加と更新 API**（task_04）。
- **UI チェックボックス**（task_05）/ **capture の所有者切替・dirty 保全**（task_06）。
- 正本 `spec_detail/data_schema.md` への反映（task_08 の正本反映で行う。
  フェーズ中は暫定仕様 06 が正）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規単体テスト**（`tests/test_domain_config.py` へ追加。既存の
   `ensure_config_compatibility` テスト群と同じ書式に合わせる）:
   - フラグ無し + `hook_stop_key="f1"` / `hook_toggle_key=""` → **True**
   - フラグ無し + `hook_stop_key=""` / `hook_toggle_key="f2"` → **True**
   - フラグ無し + 両方 `""` → **False**
   - フラグ無し + 両方が**空白のみ**（`"  "`）→ **False**（正規化後で判定していること）
   - `hook_keys_individual=False` + `hook_stop_key="f1"` → **False**（明示フラグが優先）
   - `hook_keys_individual=True` + 両方 `""` → **True**
   - dict でない入力（`None` / `[]` / `"x"`）→ **False**
3. `ensure_config_compatibility` の確認:
   - 空 dict `{}` を通すと `hook_keys_individual` が **False** で入る
   - `{"hook_stop_key": "F1"}` を通すと `hook_stop_key == "f1"` かつ `hook_keys_individual is True`
   - **冪等性**: 一度通した結果をもう一度通してもフラグが変わらない
     （特に「ON のまま両キーが空になったケース」で False へ落ちないこと）
4. `-m unittest discover -s tests` が全 pass（既存 145 件 + 追加分）。
5. `-m unittest discover -s tests_ui` が全 pass（159 件）。
6. `-m tests.smoke_app` が pass。
7. 上記 4〜6 で**バイト列比較テストが落ちた場合**は、設計メモの判断基準に従い
   「差分が `hook_keys_individual` 1 キーのみか」を確認し、結果を報告に含める。

## 完了条件

- 「確認」1〜7 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点。特に **domain 限定を守れているか**と
  **後方互換〔既存キー削除・意味変更なし〕**）。
- **実機目視は本タスクでは実施しない**（UI 変更が無いため）。
  Phase γ の実機目視は **task_07（統合確認）**でまとめて実施する。
