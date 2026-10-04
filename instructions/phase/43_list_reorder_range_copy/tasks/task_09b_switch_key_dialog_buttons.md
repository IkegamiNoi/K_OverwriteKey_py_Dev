# task_09b_switch_key_dialog_buttons

## 目的

切替キーの入力ダイアログのボタンを整える（暫定 30 v0.11 §6.4・正本 `features.md` §4.3・ユーザー判断 2026-10-04）。**presentation 限定・挙動の変更はボタンの有無と幅だけ。**

- まとめて設定のダイアログ（`KeymapSwitchBatchDialog`）から「クリア」ボタンを外す（切替キーは必須で空は必ずエラー）
- まとめて設定・通常の編集（`KeymapEditDialog`）の両ダイアログの「キー入力で取得」ボタンの幅を、「取得中…（Escで停止）」との長い方の文言の幅で固定する

## 対象範囲

### `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py`

- 行の「クリア」ボタン（`clear_buttons`・`_clear_key`）を削除する。行の列配置は詰める
- 取得ボタンの文言は `presentation/hook_button_texts.py` の `CAPTURE_IDLE_TEXT` / `CAPTURE_ACTIVE_TEXT` を使い（直値をやめる）、
  各取得ボタンを作った直後に `controllers/button_width.py` の `apply_fixed_button_width(btn, CAPTURE_TEXTS)` で幅を固定する

### `keyseq/presentation/dialogs/keymap_edit_dialog.py`

- 「クリア」は残す。取得ボタンの文言を同じ定数に替え、作った直後に `apply_fixed_button_width(self.capture_btn, CAPTURE_TEXTS)` で幅を固定する

### `instructions/common/codebase_map.md`

- `keymap_switch_batch_dialog.py` / `keymap_edit_dialog.py` の行に「取得ボタンは最大文言幅で固定（`apply_fixed_button_width`）」を足し、まとめて設定のダイアログにクリアが無いことを書く

### テスト（追加・修正まで）

- `tests_ui/test_keymap_switch_batch_dialog.py`: クリアボタンが無い / 取得ボタンの `width` が `fixed_button_width_chars` で求めた値と同じで、取得の開始・停止で変わらない。既存のクリアのテスト（`_clear_key`）は削除
- `KeymapEditDialog` の取得ボタンの幅が固定されることのテストを、既存の同ダイアログのテスト（`tests_ui/test_dialog_escape_binding.py` 等のどれか）の近くに 1 件足す

### 設計メモ / 制約

- `dialogs/` から `controllers/button_width.py` を import してよい（presentation 内）。循環が生じるなら報告して止める

## 読むファイル

- `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py`（全体）
- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体）
- `keyseq/presentation/controllers/button_width.py`・`keyseq/presentation/hook_button_texts.py`・`keyseq/presentation/button_width_rules.py`
- 手本: `keyseq/presentation/controllers/key_capture.py:40-50`（取得ボタンの幅の固定）
- `tests_ui/test_keymap_switch_batch_dialog.py`

## 含まない

- task_09 の残り（凍結・decisions_archive・current.md）/ ダイアログの他の見た目の変更 / フォント変更時の当て直し（ダイアログは開くたびに作るため不要）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: まとめて設定のダイアログにクリアが無い / 両ダイアログで取得の開始・停止でボタンの幅が変わらない。
