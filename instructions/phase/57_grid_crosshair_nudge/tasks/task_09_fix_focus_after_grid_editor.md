# task_09_fix_focus_after_grid_editor

## 目的

phase 57 完了後にユーザーが報告した不具合の修正（2026-10-14・ユーザー判断で phase 57 に追記）。
キーマップ変更のダイアログで「枠を編集…」の窓を閉じた後、**Esc でダイアログを閉じられないことがある**（欄をクリックした後なら閉じる）。
正本 `features.md` §4.6「モーダルダイアログは Escape でも閉じられる」に反する。**presentation 限定**（`keymap_edit_dialog.py`）。正本は変えない（記述どおりに動かす修正）。

### 原因（メインの probe で確定・`.venv`・実機）

編集の窓（`GridEditorWindow`）の破棄で `grab_modal` が grab をダイアログへ戻すが、**入力フォーカスは戻さない**。
OS の前面の窓はダイアログ（`GetForegroundWindow` のタイトル = 「キーマップ変更」）なのに、Tk の `focus_get()` は `None` になり、
ダイアログの `<Escape>`（`escape_close.bind_escape_close`）に Esc が届かない。phase 56 からの既存の不具合。

## 対象範囲（presentation 限定・`keyseq/presentation/dialogs/keymap_edit_dialog.py`）

* `_edit_grid`: `editor.wait_window()` の後（OK・キャンセル・Esc のどれで閉じても）、ダイアログがまだあれば（`self.winfo_exists()`）**「枠を編集…」ボタン（`self.grid_editor_btn`）へフォーカスを戻す**（`focus_force()`。`focus_set()` ではダイアログが OS 上でまだ有効になっておらず効かない＝メインの probe で確認）
* モニタを列挙できず開かなかった場合（`messagebox.showerror` の経路）は変えない

### テスト（`tests_ui/test_task06_keymap_management_ui.py`・既存の `_edit_grid` のテスト〔:415 付近・`GridEditorWindow` を差し替える形〕を手本）

* 編集の窓が結果ありで閉じた場合・キャンセル（結果なし）で閉じた場合の両方で、`_edit_grid` の後に「枠を編集…」ボタンへ `focus_force` が呼ばれる（`patch.object` で確認してよい）
* ダイアログが先に破棄されていた場合は `focus_force` を呼ばず例外にならない

## 読むファイル

* `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体・128 行程度）
* `tests_ui/test_task06_keymap_management_ui.py`（:389-575 の KeymapEditDialog と枠の編集のテスト）

## 含まない

* `grab_modal`（`presentation/modal.py`）の一般的なフォーカスの戻し方の変更（他のダイアログへ影響するため。必要なら別途）
* 他のダイアログ・編集の窓自体の変更

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_task06_keymap_management_ui tests_ui.test_dialog_escape_binding` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `discover -s tests_ui` が全 pass・`-m tests.smoke_app` OK
* メインの probe（実機）: 編集の窓を閉じた後の `focus_get()` が「枠を編集…」ボタンになる

## 完了条件

* 上記確認 pass・**reviewer 採用**
* **ユーザーの実機目視**: 「枠を編集…」を開いて閉じた直後（OK / キャンセル / Esc）に、Esc でキーマップ変更のダイアログが閉じる
