# task_04b_unknown_key_hint_on_switch_capture

## 目的

切替キーの取得で名前が `??`（Tk が判別できないキー。JIS の Caps 単独・IME ON のときのすべてのキー）のとき、何も起きず理由が分からないので、取得中の案内の欄に理由を出す（暫定 43 v0.6 §3.5・ユーザー判断 2026-10-16）。
**presentation 限定（切替キーの 2 つのダイアログ）・他の取得のダイアログは変えない。**

## 対象範囲

- `keyseq/presentation/dialogs/keymap_edit_dialog.py`・`keyseq/presentation/dialogs/keymap_switch_batch_dialog.py` の `_on_capture_keypress`:
  取得名が `"??"` のときは、`self.hint` の文言を
  「このキーは取得できません。IME が ON の場合は OFF にしてから押してください。（Escでキャンセル）」に変えて `"break"`（取得は続ける・値は入れない・messagebox は出さない）
- 修飾キー単独・禁止のキーのときの扱い（黙って無視）は変えない
- 取得を止めたとき（`_stop_capture`）の文言の戻し（従来の「例) 切替キー: 1 …」）は今のまま。取得を始めたとき（`_start_capture`）の「取得中：…」の文言も今のまま（`??` の案内は次に `??` 以外のキーで取得できるか、取得を止めるまで残ってよい）
- 文言は 2 つのダイアログで同じにする（同じ定数を使う・置き場は既存の文言の定数があればそこ、無ければ各ダイアログの近く）

### テスト（`tests_ui/test_prohibited_assign_keys_ui.py` の `??` のテストに追加）

- 両ダイアログで、取得中に `??` を送ると `hint` の文言が上の案内になり、値は空のまま・取得が続く
- その後 Esc（または取得の終了）で `hint` が従来の文言に戻る
- Caps Lock（keysym `Caps_Lock`）・修飾キー単独では `hint` が変わらない（「取得中：…」のまま）

## 読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md` §3.5（取得）
2. `keyseq/presentation/dialogs/keymap_edit_dialog.py:140-185`・`keymap_switch_batch_dialog.py:205-260`
3. `tests_ui/test_prohibited_assign_keys_ui.py`（`??` のテスト）

## 含まない

- 取得中に IME を OFF にする対策（別 idea）/ 他の取得のダイアログ / 正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `tests_ui/test_prohibited_assign_keys_ui.py` pass・`unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- **ユーザーの実機目視**: キーマップの編集ダイアログの取得中に Caps キー単独 / IME ON で文字キーを押すと、案内の欄に理由が出て、取得が続く
