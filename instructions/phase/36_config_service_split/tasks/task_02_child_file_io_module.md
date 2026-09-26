# task_02: シーケンス / トリガー一覧ファイルの読み書きを `child_file_io.py` へ切り出す

## 目的

`ConfigService` の `load_sequence_file` / `save_sequence_file` / `load_trigger_set_file` / `save_trigger_set_file`
（task_01 前の `__init__.py:463-591`・約 129 行）の本体を、同パッケージの新モジュール
`keyseq/application/config_service/child_file_io.py` へ**挙動を変えずに**移す。

## 読むファイル

1. `keyseq/application/config_service/__init__.py` の import 部と上記 4 メソッド（task_01 後の位置は `grep -n "def load_sequence_file"` で特定）
2. `keyseq/application/config_service/keymap_save_plan.py:1-25`（task_01 で作った切り出し先の書き方）
3. `tests/test_config_service_contracts.py:1-20`（`INTERNAL_MODULE_NAMES`）

## 実装対象

- 新モジュール `child_file_io.py` に 4 メソッドの本体を **`service` を第 1 引数に取る module 関数**（公開名 `load_sequence_file` 等・同名）として移す。
  本体の処理・順序・例外・戻り値はそのまま。`self.X` → `service.X` のみ。
  `os.path` を使う場合は `import os` + ドット記法（事前束縛しない）。`__init__.py` を import しない。
- `ConfigService` の 4 メソッドは**シグネチャ（引数名・既定値・キーワード専用の区別・戻り値注釈）をそのまま残し**、本体を
  `return child_file_io.<同名>(self, <引数をそのまま渡す>)` の 1 行委譲にする
  （presentation から呼ばれ、テストが `patch.object` で差し替えるため）。docstring があれば残す。
- `from . import ...` に `child_file_io` を追加。不要になった import は、ほかで使っていないことを確認のうえ削除。
- `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` に `"child_file_io"` を追加（アルファベット順）。

## 対象外

- 他のメソッド・他ファイルの変更 / 改名・整形・ロジック変更 / `codebase_map.md`（task_08）。
- **テストの実行**（実測は verifier）。

## 完了条件

- `__init__.py` が約 100 行減り、compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・委譲のシグネチャ一致・循環なし）を通過。
