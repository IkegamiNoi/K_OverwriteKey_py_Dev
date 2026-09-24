# task_01c_nested_child_by_file_and_class

## 目的

完了判定前レビュー 2 回目の codex-adversarial 指摘（medium）への対応（ユーザー判断 2026-09-24）。
`tests_ui/test_dialog_teardown_flows.py` の `NESTED_CHILD_DIALOGS` がクラス名だけで子を判定しているため、
`dialogs/` の別ファイルに同名のトップレベルのダイアログを足すと、フックを止めなくても static_1 を素通りする。
除外を **(ファイル名, クラス名) の組**で持つ。**tests_ui 限定・production 不変・検査は弱めない**。

## 対象範囲（tests_ui 限定・`test_dialog_teardown_flows.py` のみ）

### `tests_ui/test_dialog_teardown_flows.py`

- `NESTED_CHILD_DIALOGS` を `frozenset({("preset_dialog.py", "PresetDialog"), ("keymap_set_history_dialog.py", "CategoryChooserDialog")})` に変える。
- 直前に 1 行コメントで基準を書く: 「常に親がフックを止めている間にだけ開かれ、自分では止めない子（App 直下からも開く `PresetManagerDialog` は含めない）」。
- `test_static_1_dialog_suspend_passes_self_once` の子の判定・陳腐化検出（除外リストの組がすべて発見されること）・トップレベルの抽出を
  `(path.name, node.name)` の組で行う。失敗メッセージは現行の形式のまま（陳腐化検出のメッセージには発見した組の一覧を含める）。
- それ以外（下限 9・suspend の引数条件・総数検査・static_2・static_3・`T2_DIALOG_FILES`）は**変更しない**。

## 読むファイル

- `tests_ui/test_dialog_teardown_flows.py:1-30, 227-265`（編集対象）
- `tests_ui/dialog_discovery.py`（`dialog_classes` の戻り値の形・変更しない）

## 含まない

- production コード（`keyseq/`）/ `tests_ui/dialog_discovery.py` / `test_nested_modal_grab.py` の変更。
- 文書の更新（task_02）/ テストの実行（実測は verifier）。

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q tests_ui` が clean。
- `-m unittest tests_ui.test_dialog_teardown_flows` が OK。
- **検出力の確認（一時改変・確認後に必ず `git checkout -- <keyseq のファイル>` で戻す・1 パターンずつ）**:
  1. `dialogs/layout_delete_dialog.py` の末尾に、同名のトップレベルのダイアログを想定したクラス
     `class CategoryChooserDialog(tk.Toplevel):` + `__init__(self, parent)` の本体 `super().__init__(parent)` / `grab_modal(self, parent)` を追加
     → static_1 が FAIL（トップレベル扱いで suspend 0 回）
  2. task_01b の 5)（`OrphanSweepDialog` の suspend 削除）と 6)（`PresetDialog` に suspend 追加）の再確認 → static_1 が FAIL
  確認後 `git diff --stat -- keyseq` が空。
- 回帰: `-m unittest discover -s tests_ui` が OK（537 件）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は不要。
