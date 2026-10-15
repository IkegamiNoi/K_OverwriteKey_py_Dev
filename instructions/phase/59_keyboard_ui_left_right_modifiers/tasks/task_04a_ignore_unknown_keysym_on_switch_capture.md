# task_04a_ignore_unknown_keysym_on_switch_capture

## 目的

task_04 の実機目視（2026-10-16）で、キーマップの編集ダイアログの「キー入力で取得」で JIS の Caps キーを単独で押すと切替キーに `??` が入ると分かった（Tk が「英数」の仮想キーの名前を判別できない）。
切替キーの取得で、名前が `??`（判別できないキー）のときも取得せずに無視する（暫定 43 v0.5 §3.5・§5-9 の取り決め）。**presentation 限定（切替キーの 2 つのダイアログ）・他の取得のダイアログは変えない。**

## 対象範囲

- `keyseq/presentation/dialogs/keymap_edit_dialog.py` の `_on_capture_keypress`・`keyseq/presentation/dialogs/keymap_switch_batch_dialog.py` の `_on_capture_keypress`:
  取得したキー名が `"??"` のときも、修飾キー単独・禁止のキーと同じく `"break"` で無視して取得を続ける（値を入れない）
- `??` は禁止の判定の集合（`domain/key_identifiers.PROHIBITED_ASSIGN_KEY_NAMES`）には入れない
- テスト（`tests_ui/test_prohibited_assign_keys_ui.py` の取得のテストに追加）: 両ダイアログの取得中に keysym `??` のキーイベント（`normalize_tk_key_event` が `??` を返す形。既存の Caps のテストの作法）を送ると値が入らず取得が続く

## 読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md` §3.5（取得）
2. `keyseq/presentation/dialogs/keymap_edit_dialog.py:160-180`・`keymap_switch_batch_dialog.py:235-255`
3. `keyseq/presentation/tk_keys.py:60-80`（`normalize_tk_key_event`）
4. `tests_ui/test_prohibited_assign_keys_ui.py`（取得のテストの作法）

## 含まない

- トリガー・停止 / トグルキー等の他の取得のダイアログ / `tk_keys` の対応表の変更 / 正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `tests_ui/test_prohibited_assign_keys_ui.py` pass・`unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- **ユーザーの実機目視**: キーマップの編集ダイアログの「キー入力で取得」で JIS の Caps キー単独を押しても何も入らず、取得が続く
