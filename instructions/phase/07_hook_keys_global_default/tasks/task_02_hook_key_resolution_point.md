# task_02_hook_key_resolution_point

## 目的

hook キーの**解決点を 1 箇所に確定させる**。個別指定 OFF（`hook_keys_individual` が偽）なら
`config/config.json` の全体デフォルトを runtime の `hook_stop_key` / `hook_toggle_key` へ注入し、
ON なら keymap_set の個別値をそのまま使う。
これにより**フック層（`input_router` / `app.data` 直読み）は変更不要**になり、常に解決済みの値を見る。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §3（データモデルと解決順序）/
  §7 受入条件 **1**（全体デフォルトが読込時に解決されフック動作へ反映）と **2**（新規作成は再設定不要）。
- **レイヤ制約**: 解決ロジックは **application 限定**（`keyseq/application/config_service/`）。
  presentation の変更は**新規データ生成時に解決 API を呼ぶ 1 行 × 3 箇所のみ**に限定する。
  domain（`config.py`）は task_01 で完了済みのため**変更しない**。
- **フック層・UI 層に解決ロジックを分散させない**（分散すると「古いキーを使い続ける」不具合の温床。
  phase.md レビュー方針 2）。

## 対象範囲

### 1. `keyseq/application/config_service/split_loading.py`

**全体デフォルトの読み出し関数を新設**する（`build_runtime_data_from_split` より前に置く）:

```python
def load_global_hook_keys(service, *, config_root: str) -> tuple[str, str]:
    """config/config.json（起動エントリ）の hook キー全体デフォルトを (stop, toggle) で返す。

    読めない / 未設定なら ("", "")。
    """
```

- `config_root` が空なら `("", "")` を返す。
- 読み出しは **`service._load_optional_json(service._startup_entry_path(config_root))`** を使う
  （このモジュールの既存パターン。存在しない / 壊れている場合に None が返り、**keymap_set の
  読込全体を巻き込んで失敗させない**）。`dict` でなければ `("", "")`。
- 値は `normalize_key_name(str(value or ""))` で正規化して返す。

**`build_runtime_data_from_split` へ解決を組み込む**。現在の hook キーのコピーループ
（`for key in ("hook_stop_key", "hook_toggle_key", ...)`）の**直後**に置く:

```python
runtime["hook_keys_individual"] = resolve_hook_keys_individual(keymap_set)
if not runtime["hook_keys_individual"]:
    runtime["hook_stop_key"], runtime["hook_toggle_key"] = load_global_hook_keys(
        service, config_root=config_root
    )
```

- `resolve_hook_keys_individual` は `keyseq.domain.config` から import する（task_01 で新設済み）。
- **判定に渡すのは生の `keymap_set` dict**であって `runtime` ではない
  （`runtime` は `new_default_data()` 由来でフラグを常に持つため、移行判定が発火しない。task_01 の申し送り）。
- コピーループの `for key in (...)` タプルへ `"hook_keys_individual"` を**追加しない**
  （明示代入で一本化する。二重経路を作らない）。

### 2. `keyseq/application/config_service/__init__.py`

新規データにも全体デフォルトを届けるための**公開メソッド**を追加する
（`ensure_split_config_dirs` の近く、公開面の並びに合わせて配置）:

```python
def apply_global_hook_key_defaults(self, runtime: dict[str, Any], *, config_root: str) -> dict[str, Any]:
    """個別指定 OFF の runtime へ config.json の hook キー全体デフォルトを注入する（ON なら何もしない）。"""
```

- `runtime` を**その場で更新**して返す（呼び出し側が `data = ...` と書いても書かなくても成立させる）。
- `runtime.get("hook_keys_individual")` が真なら**何もしない**。
- 偽なら `split_loading.load_global_hook_keys(self, config_root=config_root)` の結果を代入する。
- **冪等**であること（複数回呼んでも結果が変わらない）。

### 3. presentation の呼び出し（**1 行 × 3 箇所のみ**）

新しい runtime を生成した**直後**に上記メソッドを呼ぶ。受入条件 2（新規作成で再設定が不要）を満たすため。

| ファイル | 箇所 |
|---|---|
| `keyseq/presentation/controllers/config_io/keymap_set_io.py` | `new_config`（新規作成・現 `:53` 付近） |
| `keyseq/presentation/controllers/config_io/keymap_set_io.py` | `restore_default`（既定に戻す・現 `:595` 付近） |
| `keyseq/presentation/controllers/config_io/startup_io.py` | `load_startup_and_config` の**空データフォールバック**（現 `:34`） |

- いずれも `config_root=self._app.config_root` を渡す。
- **`app.py:76` の `new_default_data()` は対象外**。直後に `load_startup_and_config` が
  `self.data` を必ず上書きするため（この時点の初期化値はフックへ届かない）。理由をコメントに残さない
  （タスク定義の記録で足りる）。

### 設計メモ / 制約

- **`ensure_config_compatibility` は解決結果を壊さない**。`build_runtime_data_from_split` 末尾の
  正規化呼び出し時点で `hook_keys_individual` は既に存在するため、task_01 の
  `resolve_hook_keys_individual` はその値を維持する（＝注入した全体デフォルトが
  「個別値が非空だから ON」と誤判定されない）。**この不変条件をテストで固定すること**。
- **OFF のとき keymap_set の個別値は runtime へ持ち込まない**。読込時点では「ON→OFF 切替直前の
  値」という文脈が存在しないため、暫定仕様 §2 の「内部保持・再 ON で復活」は**同一セッション内の
  UI 操作に限る**（task_06 の担当）。
- 全体デフォルトの読み出しに失敗しても**例外を投げない**（`("", "")` へ縮退）。
  keymap_set の読込は独立して成立させる。ただし**握りつぶしの範囲は
  `_load_optional_json` が既に持つ範囲に限る**（新たな広い try/except を足さない）。

## 含まない

- **`config/config.json` への全体デフォルトの書き込みと成否付き更新 API**（task_04）。
  本タスクは**読み出し専用**。`startup_io.write_startup` は変更しない。
- **保存時の空文字クリアと `hook_keys_individual` の keymap_set への書き出し**（task_03）。
  `split_payloads.py` は触らない。
- **UI チェックボックス**（task_05）/ **capture の所有者切替・dirty 保全・ON⇄OFF の表示切替**（task_06）。
- `input_router` / `hook_controller` / `keyboard_window` など**フック層の変更**（本タスクの目的は
  「変更不要にすること」であり、触ったら設計違反）。
- 正本 `spec_detail/` への反映（task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規単体テスト**（`tests/test_config_service.py` へ追加。一時ディレクトリに
   `config/config.json` と `config/user/keymap_sets/*.json` を作って実 IO で検証する）:
   - **OFF（フラグ無し・両キー空）の keymap_set** を読むと、runtime の hook キーが
     **config.json の全体デフォルト値**になる（受入条件 1）
   - **ON（フラグ無し・stop のみ非空 = 移行で ON）の keymap_set** を読むと、
     runtime の hook キーが**個別値のまま**で、全体デフォルトに**上書きされない**（受入条件 6）
   - **明示 `hook_keys_individual: false` + 個別値あり**の keymap_set を読むと、
     全体デフォルトが優先される（明示フラグが勝つ）
   - **config.json が存在しない / 壊れている**場合でも keymap_set の読込が成功し、
     OFF の runtime の hook キーが `""` になる（例外を投げない）
   - 全体デフォルトが大文字（`"F1"`）で保存されていても**正規化されて `"f1"`** になる
   - **`hook_keys_individual` が読込後も維持される**（末尾の `ensure_config_compatibility` で
     反転しない）: OFF で全体デフォルト注入後もフラグが `False` のままであること
3. **新規単体テスト（`apply_global_hook_key_defaults`）**:
   - OFF の runtime に全体デフォルトが注入される / **ON の runtime は変化しない**
   - 2 回呼んでも結果が変わらない（冪等）
   - `config_root=""` でも例外を投げず、OFF の runtime は `""` になる
4. `-m unittest discover -s tests` が全 pass（現在 155 件 + 追加分。**件数を報告**）。
5. `-m unittest discover -s tests_ui` が全 pass（159 件）。**新規作成 / 既定に戻す**の
   既存テストが落ちていないこと。
6. `-m tests.smoke_app` が pass。
7. **保存 JSON のバイト列比較テストが無修正で pass**（本タスクは保存経路を触らないため、
   落ちたら実装が範囲外へ及んでいる）。

## 完了条件

- 「確認」1〜7 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **2「キー解決点が 1 箇所か」**と **6「層の分離」**）。
- **実機目視は本タスクでは実施しない**（UI 変更が無く、全体デフォルトを書く手段がまだ無いため
  = task_04 まで実機では確認できない）。Phase γ の実機目視は **task_07** でまとめて実施する。
