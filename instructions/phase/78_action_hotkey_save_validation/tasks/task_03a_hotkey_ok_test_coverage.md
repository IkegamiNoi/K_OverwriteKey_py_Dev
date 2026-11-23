# task_03a_hotkey_ok_test_coverage

## 目的

phase 78 の完了判定前レビュー（deep-reviewer 指摘 2・3・4・ユーザー採用 2026-11-23）を受け、`ActionDialog.on_ok` の hotkey の保存のテストを補う。正本 `key_input.md` §7.7 L232・§7.9 L346 の挙動をテストで固定する。
**テストのみ（`tests_ui/test_action_dialog_key_hold.py`）。プロダクトコード・言語ファイルは変えない。**

## 対象範囲（`tests_ui/test_action_dialog_key_hold.py` のみ）

新規テストはクラスの末尾に足す。既存テストの途中に差し込まない。既存テストの書き換えは、下の ① だけとする。

1. **他方の OS の修飾キーの検査が先に走る**（指摘 2）: 既存の `test_hotkey_rejects_other_os_modifier_and_unknown_normal_name` の `left command+a` の確認を、次のとおり強める。
   - メッセージを `assertIn("不明なキー名です", ...)` で確かめる。phase 75 の文言（`capture.error.unknown_key`）で、`validate_hotkey` の文言「不明なキー名があります」とは区別できる。
   - `validate_key_name` が呼ばれていないことを確かめる（`FakeInputGateway.validated` が空）。
2. **既存の行を編集して OK すると正規化される**（指摘 3）: `make_dialog` 相当で `initial={"type": "hotkey", "value": "Ctrl+ A"}`・`mode="edit"` のダイアログを作り、OK で `_dialog_result["value"] == "ctrl+a"` になる。`make_dialog` が initial / mode を受けない場合は、このテストの中で `ActionDialog(self.root, "Action", initial=..., mode="edit")` を作り、`self.dialogs` に足す。
3. **エラー時にメッセージを出す**（指摘 4）: 文法エラー（`ctrl++a`）と不明なキー名（`invalid_names` に入れた名前）のそれぞれで、`self.showerror` が呼ばれ、第 2 引数が `self.root.validate_hotkey(<同じ値>)[0]` と一致する。

## 読むファイル

- `tests_ui/test_action_dialog_key_hold.py`（編集対象。L14-65・L300-335・L430 以降）
- `keyseq/presentation/dialogs/action_dialog.py:253-272`
- `keyseq/presentation/dialogs/action_dialog.py` の `__init__` のシグネチャ（`initial`・`mode` の受け方）

## 含まない

- プロダクトコード・言語ファイル・他のテストファイルの変更
- 記録から OK までの通しの確認（task_03 の実機目視 ③ で代える・指摘 5）
- features.md の追記（指摘 7・保留）

## 確認（verifier が実行）

- `..\..\..\.venv\Scripts\python.exe -m compileall -q tests_ui`
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_action_dialog_key_hold tests_ui.test_action_dialog_labels` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施する。
