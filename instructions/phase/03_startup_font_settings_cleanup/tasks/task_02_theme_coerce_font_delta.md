# task_02_theme_coerce_font_delta

## 目的

負債②（逆参照）の解消。フォント差分の正規化を `theme.py` のモジュール純関数
`coerce_font_delta` に一本化し、`App._coerce_font_delta`（App private）を削除する。
これにより `ConfigIoController` → App private の逆参照が消える（暫定仕様
[§4](../../../history/02_startup_font_settings_cleanup.md)・受け入れ条件 §8-1・§8-2）。

- **挙動不変**（クランプ範囲 `-3..+3`・失敗時 0 を保つ）。**presentation 限定**・domain/application/infrastructure 不変・スキーマ不変。

## 対象範囲（presentation 限定・ロジック不変移設）

### 1. `keyseq/presentation/theme.py`（純関数を新規追加）

現行 `App._coerce_font_delta`（`app.py:357-366`）の本体を**ロジック不変**でモジュール純関数として追加する:

```python
def coerce_font_delta(value) -> int:
    """int 化し -3..+3 にクランプ。失敗時 0。フォント差分の唯一の正規化点。"""
```

- 実装は現行と等価: `try: v = int(value) except Exception: v = 0` → `-3` 未満は `-3`、`3` 超は `3`。
- 配置は既存フォントロジック（`apply_global_theme` 等）と同じ `theme.py`。追加位置はモジュール関数群の自然な箇所（例: `apply_global_theme` の近辺 or ファイル冒頭のヘルパ群付近）。

### 2. 呼び出し元 4 箇所の差し替え（`self(._app)._coerce_font_delta` → `theme.coerce_font_delta`）

| ファイル:行 | 現行 | 変更後 |
|---|---|---|
| `keyseq/presentation/app.py:58` | `self._coerce_font_delta(self._startup_settings.get("ui_font_delta_pt", 0))` | `coerce_font_delta(self._startup_settings.get("ui_font_delta_pt", 0))` |
| `keyseq/presentation/app.py:228` | `self._coerce_font_delta(delta)` | `coerce_font_delta(delta)` |
| `keyseq/presentation/app.py:390` | `self._coerce_font_delta(startup.get("ui_font_delta_pt", 0))` | `coerce_font_delta(startup.get("ui_font_delta_pt", 0))` |
| `keyseq/presentation/controllers/config_io_controller.py:278` | `self._app._coerce_font_delta(base.get("ui_font_delta_pt", 0))` | `coerce_font_delta(base.get("ui_font_delta_pt", 0))` |

- import: `app.py` は既に `theme` から `apply_global_theme` を import 済み。同じ import 元に `coerce_font_delta` を追加する
  （または `from keyseq.presentation import theme` にして `theme.coerce_font_delta` 呼び出し。既存の import 様式に合わせる）。
- `config_io_controller.py` は theme を import していない可能性が高い。`from keyseq.presentation.theme import coerce_font_delta`
  （または既存 import 様式に合わせる）を追加する。**`self._app` 経由の呼び出しを完全に除去する**こと。

### 3. `App._coerce_font_delta` の削除

`app.py:357-366` のメソッド定義を削除する（呼び出し元が 0 になった後）。周囲のコメント区切り（`# ---------------- Startup config ----------------`）は他メソッドが残るため保持してよい。

### 4. 特性テストの呼び出し先差し替え（task_01 の安全網を green に保つ）

`tests_ui/test_startup_font_characterization.py:50` の `self.app._coerce_font_delta(value)` を
`theme.coerce_font_delta(value)` へ差し替える（`theme` を import）。**アサーション（値テーブル・期待値）は一切変更しない**。
これは削除されるメソッドへの参照を移設先へ付け替える機械的更新であり、挙動契約（値・境界・失敗時0）は不変。

### 5. tk 不要の coerce 単体テストを新規追加（暫定仕様 §9 の前進ユニットテスト）

`tests/` に新規テスト（例: `tests/test_theme_coerce.py`）を追加し、`theme.coerce_font_delta` を
**tk 不要**で直接検証する（unittest 形式・既存 `tests/test_*.py` に準拠）:

- 非数値（`"x"` / `None` / `object()`）→ `0`
- 範囲内（`-3,-1,0,2,3`）→ 同値 / 範囲外（`-4,-100`→`-3` / `4,100`→`3`）/ 数値文字列（`"2"`→`2`, `"-3"`→`-3`）/ 境界（`-3`,`+3`）

## 設計メモ / 制約

- **実行環境**: python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree 相対）。
- **ロジック等価**: `coerce_font_delta` は現行本体と 1:1（順序・失敗時0・クランプ境界を変えない）。型注釈は現行 `value: any` に倣い簡潔で可。
- **依存方向**: `theme.py` は presentation 内の純ロジック。application/infrastructure を参照しない。`config_io_controller.py`（presentation）→ `theme`（presentation）は横方向で可。
- **やってはいけない**: application/domain の変更、`set_ui_font_delta` の分割（task_04）、`_load_startup_settings` の切り出し（task_03）、フォント範囲/既定値の変更、`test_startup_font_characterization.py` のアサーション値の改変。

## 含まない

- 起動設定ローダの切り出し `presentation/startup_settings.py`（task_03）。
- `set_ui_font_delta` の案 A 分割・`UiVars` 引数化（task_04）。
- 正本反映・記録（task_05）。
- フォント範囲・既定値・startup.json スキーマ・メニュー構成の変更（スコープ外）。

## 確認

`.venv` python で以下を実行し、いずれも pass すること:

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py`（clean）
- 新規単体テスト: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（従来 77 + coerce 単体分が pass）
- 安全網（差し替え後）: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui`（20 pass 維持・破綻なし）
- smoke: `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app`（pass）
- 逆参照/残存の除去確認（受け入れ条件 §8-1・§8-2）:
  - `git grep "_coerce_font_delta" -- keyseq/` が **0 件**（App メソッドが消え `theme.coerce_font_delta` に一本化）
  - `git grep "_app._coerce_font_delta"` が **0 件**（controller の逆参照消滅）
  - ※ `git grep` は追跡ファイルのみ検索。新規テストファイルが未追跡の場合は直接 `grep` でも確認する。

## 完了条件

- 上記「確認」全 pass・**reviewer 採用**（CLAUDE.md レビュー必須。観点: 仕様適合性/依存方向/責務分離/不要変更/チェック漏れ）。
- 実機目視: 本タスクでは不要（挙動不変・純関数移設）。実機目視は task_04 完了後にまとめて実施する。
