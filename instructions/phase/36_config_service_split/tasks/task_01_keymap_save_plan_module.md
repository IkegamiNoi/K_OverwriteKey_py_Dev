# task_01: 個別キーマップの保存計画一式を `keymap_save_plan.py` へ切り出す

## 目的

`config_service/__init__.py:265-461`（`_save_keymap_with_plan` 〜 `_apply_saved_keymap_state` の 12 メソッド・約 197 行）を、
同パッケージの新モジュール `keyseq/application/config_service/keymap_save_plan.py` へ**挙動を変えずに**移す。

## 読むファイル

1. `keyseq/application/config_service/__init__.py:1-62`（import・クラス定数）/ `:195-461`（呼び出し元 `save_keymap_file` と移動対象）
2. `keyseq/application/config_service/save_plan_execution.py:1-40`（切り出し先の書き方の手本 = `service` を第 1 引数に取る module 関数）
3. `tests/test_config_service_contracts.py:1-20`（`INTERNAL_MODULE_NAMES`）

## 実装対象

- 新モジュール `keymap_save_plan.py` に、移動対象 12 メソッドを **`service` を第 1 引数に取る module 関数**として移す。
  - 入口は `save_keymap_with_plan(service, ...)`（公開名・先頭 `_` なし）。他はモジュール内 private（`_` 付き）でよい。
  - 本体の処理・順序・例外・戻り値は**そのまま**。`self.X` は `service.X` に置き換えるだけ。
  - `os.path` は `import os` + `os.path.xxx` のドット記法を保つ（`from os.path import ...` をしない。テストの `config_service.os.path` 差し替えが `os` モジュール経由で効くため）。
  - 定数・ドメイン関数の import は移動対象が使うものだけ。**`keymap_save_plan.py` から `config_service/__init__.py` を import しない**（循環防止。クラス定数は `service.INTERNAL_...` で参照する）。
- `__init__.py`: 移動した 12 メソッドを削除し、呼び出し元（`save_keymap_file` 内・現 206 行付近）を `keymap_save_plan.save_keymap_with_plan(self, ...)` に置き換える。
  `from . import ...` の行に `keymap_save_plan` を追加。不要になった import があれば削除（ほかで使っていないことを確認のうえ）。
  - 移動対象の 12 メソッドは外部（`keyseq/`・`tests/`・`tests_ui/`）から参照されていない（2026-09-26 実測）ため、委譲メソッドは残さない。
- `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` に `"keymap_save_plan"` を追加（アルファベット順の位置）。

## 対象外

- 他のメソッド・他ファイルの変更 / 改名・整形・ロジック変更 / `codebase_map.md`（task_08）。
- **テストの実行**（実測は verifier）。

## 完了条件

- `__init__.py` が約 200 行減り、compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・循環なし・patch 対象の維持）を通過。
