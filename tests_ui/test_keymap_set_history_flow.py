"""履歴 UI の永続化境界とモーダル作法。実 config への書き込みは禁止。"""
import copy
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from tkinter import ttk
from unittest.mock import Mock, patch
from tests_ui.escape_delivery import send_escape
from tests_ui.hook_resume_wait import wait_for_hook_pause_count

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module, keymap_set_history_text as text
from keyseq.presentation.controllers.config_io import keymap_set_history_io as history_io
from keyseq.presentation.dialogs import keymap_set_history_dialog as dialogs
from keyseq.presentation.views.menu_bar import build_menu_bar


class KeymapSetHistoryFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        # App の生成・破棄・遅延コールバックも含め、実ファイルの保存を遮断する。
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(ConfigService, "load_keymap_set_history",
                                        return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK)))
        stack.enter_context(patch.object(ConfigService, "save_keymap_set_history",
                                        side_effect=AssertionError("unpatched history save")))
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self.app.update()
        self.store = {"recent": [{"path": "shared.json"}], "categories": [
            {"name": "z", "entries": [{"path": "shared.json"}]},
            {"name": "a", "entries": []}, {"name": "A", "entries": []},
        ]}
        self.status = contracts.HISTORY_OK
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = temporary.name
        self._patch(self.app, "config_root", root)
        self.existing = Path(root) / "shared.json"
        self.existing.write_text("{}", encoding="utf-8")
        self.read = self._patch(self.app.config_service, "load_keymap_set_history",
                                side_effect=lambda **kw: (copy.deepcopy(self.store), self.status))
        self.save = self._patch(self.app.config_service, "save_keymap_set_history", side_effect=self._save)
        self.info = self._patch(dialogs.messagebox, "showinfo")
        self.confirm = self._patch(dialogs.messagebox, "askyesno", return_value=True)
        self._patch(self.app.hook, "start_hook")
        self.callback_error = self._patch(self.app, "report_callback_exception")
        self.addCleanup(self.callback_error.assert_not_called)
        self.controller = self.app.keymap_set_history_io

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def _save(self, history, **kwargs):
        self.assertEqual(kwargs["config_root"], self.app.config_root)
        self.store = copy.deepcopy(history)
        return True, ""

    def _close(self, window):
        if window.winfo_exists():
            window.destroy()
        self.app.update()

    def _dialog(self):
        dialog = dialogs.KeymapSetHistoryDialog(self.app, controller=self.controller)
        self.addCleanup(self._close, dialog)
        dialog.update_idletasks()
        return dialog

    def _select(self, dialog, kind, name="", index=0):
        iid = next(i for i, node in dialog._nodes.items()
                   if node[0] == kind and node[1] == name and (node[2] == index or node[2] == -1))
        dialog.tree.selection_set(iid)
        dialog._update_buttons()
        return iid

    def _snapshot(self, dialog):
        return [(node, dialog.tree.item(iid, "text"), dialog.tree.item(iid, "values"))
                for iid, node in dialog._nodes.items()]

    def _choose(self, name="a"):
        return self._patch(dialogs, "CategoryChooserDialog", return_value=Mock(result=name))

    def test_menu_position_and_command(self):
        self.addCleanup(build_menu_bar, self.app)
        with patch.object(self.controller, "open_history_dialog") as open_dialog:
            build_menu_bar(self.app)
            bar = self.app.menubar
            index = next(i for i in range(bar.index("end") + 1)
                         if bar.type(i) == "cascade" and bar.entrycget(i, "label") == "ファイル")
            menu = self.app.nametowidget(bar.entrycget(index, "menu"))
            labels = [(i, menu.entrycget(i, "label")) for i in range(menu.index("end") + 1)
                      if menu.type(i) != "separator"]
            position = next(n for n, (_, label) in enumerate(labels) if label == "読込（構成セット）…")
            self.assertEqual(labels[position + 1][1], "履歴から読み込む…")
            menu.invoke(labels[position + 1][0])
            open_dialog.assert_called_once_with()
        with patch.object(history_io, "KeymapSetHistoryDialog") as constructor:
            self.controller.open_history_dialog()
            constructor.assert_called_once_with(self.app, controller=self.controller)
            constructor.return_value.wait_window.assert_called_once_with()

    def test_tree_order_missing_paths_expansion_and_font(self):
        self.store["recent"].append({"path": "user/missing.set.json"})
        dialog = self._dialog()
        roots = dialog.tree.get_children()
        self.assertEqual([dialog.tree.item(i, "text") for i in roots], [text.RECENT_NODE_LABEL, "a", "A", "z"])
        self.assertEqual([bool(dialog.tree.item(i, "open")) for i in roots], [True, False, False, False])
        entries = dialog.tree.get_children(roots[0])
        self.assertEqual(dialog.tree.item(entries[0], "text"), "shared")
        self.assertEqual(dialog.tree.item(entries[1], "text"), "missing.set" + text.MISSING_SUFFIX)
        self.assertEqual(dialog.tree.item(entries[1], "values"), ("user/missing.set.json",))
        dialog.tree.item(roots[-1], open=True)
        self._select(dialog, "category_entry", "z")
        dialog._redraw()
        self.assertEqual(dialog._selected(), ("category_entry", "z", 0, "shared.json"))
        self.assertTrue(dialog.tree.item(dialog.tree.get_children()[-1], "open"))
        self.assertEqual(len(self.store["recent"]), 2)
        self.save.assert_not_called()
        style = ttk.Style(dialog)
        for name in ("Treeview", "Treeview.Heading"):
            self.assertEqual(str(style.lookup(name, "font")), "TkDefaultFont")
        self.assertGreater(int(style.lookup("Treeview", "rowheight")), 0)

    def test_keyboard_focus_moves_into_dialog_and_only_path_column_stretches(self):
        """実機目視の指摘 2 件（Escape が親へ届く / 枠の拡縮が名前列にも及ぶ）の再発防止。"""
        dialog = self._dialog()
        self.app.update()
        # focus_force を使わずに、ダイアログ内へフォーカスが入っていること。
        self.assertTrue(str(dialog.focus_get()).startswith(str(dialog)))
        self.assertFalse(dialog.tree.column("#0", "stretch"))
        self.assertTrue(dialog.tree.column("path", "stretch"))
        chooser = dialogs.CategoryChooserDialog(dialog, names=("a",))
        self.addCleanup(self._close, chooser)
        self.app.update()
        self.assertTrue(str(chooser.focus_get()).startswith(str(chooser)))

    def test_load_failure_cancel_and_updated_disk(self):
        confirm = self._patch(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True)
        load = self._patch(self.app.keymap_set_io, "load_keymap_set_path", return_value="failed")
        dialog = self._dialog()
        self._select(dialog, "recent_entry")
        before = self._snapshot(dialog)
        dialog._load()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self._snapshot(dialog), before)
        load.assert_called_once_with(str(self.existing))
        load.reset_mock()
        confirm.return_value = False
        dialog._load()
        load.assert_not_called()
        self.assertEqual(self._snapshot(dialog), before)
        def save_during_confirm(_action):
            self.store["recent"].insert(0, {"path": "new.json"})
            return False
        confirm.side_effect = save_during_confirm
        dialog._load()
        self.assertEqual(dialog.tree.item(dialog.tree.get_children(dialog.tree.get_children()[0])[0], "values"),
                         ("new.json",))
        load.assert_not_called()

    def test_remove_only_selected_side_and_never_delete_file(self):
        for kind in ("recent_entry", "category_entry"):
            with self.subTest(kind=kind):
                self.store["recent"] = [{"path": "shared.json"}]
                self.store["categories"][0]["entries"] = [{"path": "shared.json"}]
                dialog = self._dialog()
                self._select(dialog, kind, "z" if kind == "category_entry" else "")
                with patch("os.remove") as remove, patch("os.unlink") as unlink:
                    dialog._remove_entry()
                    remove.assert_not_called()
                    unlink.assert_not_called()
                self.assertEqual(len(self.store["recent"]), int(kind != "recent_entry"))
                self.assertEqual(len(self.store["categories"][0]["entries"]), int(kind != "category_entry"))
                self.assertEqual(self.existing.read_text(encoding="utf-8"), "{}")
                self._close(dialog)

    def test_save_failure_preserves_tree_for_four_operations(self):
        self.save.side_effect = lambda *a, **kw: (False, "保存不可")
        self._choose()
        dialog = self._dialog()
        operations = (("category", "z", dialog._remove_category),
                      ("recent_entry", "", dialog._copy_entry),
                      ("recent_entry", "", dialog._remove_entry),
                      ("recent_root", "", dialog._add_category))
        for kind, name, action in operations:
            with self.subTest(action=action.__name__):
                self._select(dialog, kind, name)
                dialog.category_name.set("new")
                before = self._snapshot(dialog)
                disk = copy.deepcopy(self.store)
                with patch.object(dialog, "_redraw", wraps=dialog._redraw) as redraw:
                    action()
                    redraw.assert_called_once_with()
                self.assertEqual(self._snapshot(dialog), before)
                self.assertEqual(self.store, disk)
                self.info.assert_called_with(text.TITLE, "保存不可", parent=dialog)
        self.assertEqual(self.save.call_count, 4)

    def test_failed_edit_redraws_updated_disk_before_showing_reason(self):
        dialog = self._dialog()
        before = self._snapshot(dialog)
        self.store = {"recent": [], "categories": []}
        self.save.side_effect = lambda *a, **kw: (False, "保存不可")
        dialog.category_name.set("new")
        expected = [(("recent_root", "", -1, ""), text.RECENT_NODE_LABEL, ("",))]
        self.assertEqual(self._snapshot(dialog), before)
        self.assertNotEqual(before, expected)
        self.info.side_effect = lambda *a, **kw: self.assertEqual(self._snapshot(dialog), expected)

        dialog._add_category()

        self.assertEqual(self._snapshot(dialog), expected)
        self.assertEqual(self.store, {"recent": [], "categories": []})
        self.save.assert_called_once()
        self.info.assert_called_once_with(text.TITLE, "保存不可", parent=dialog)

    def test_category_edits_validation_and_fresh_read(self):
        dialog = self._dialog()
        for name in ("", "  ", "a"):
            dialog.category_name.set(name)
            dialog._add_category()
        self.save.assert_not_called()
        self.store["categories"].append({"name": "external", "entries": []})
        dialog.category_name.set(" new ")
        dialog._add_category()
        self.assertIn("external", [c["name"] for c in self.store["categories"]])
        self._select(dialog, "category", "new")
        for name in ("", "a", "new"):
            dialog.category_name.set(name)
            dialog._rename_category()
        self.assertEqual(self.save.call_count, 1)
        dialog.category_name.set("renamed")
        dialog._rename_category()
        self._select(dialog, "category", "z")
        dialog._remove_category()
        self.assertEqual([c["name"] for c in self.store["categories"]], ["a", "A", "external", "renamed"])

    def test_copy_duplicate_and_no_categories(self):
        chooser = self._choose()
        dialog = self._dialog()
        self._select(dialog, "recent_entry")
        dialog._copy_entry()
        self.assertEqual(self.store["categories"][1]["entries"], self.store["recent"])
        dialog._copy_entry()
        self.assertEqual(self.save.call_count, 1)
        self.info.assert_called_with(text.TITLE, text.COPY_REJECTED, parent=dialog)
        self.store["categories"] = []
        chooser.reset_mock()
        dialog._copy_entry()
        chooser.assert_not_called()
        self.info.assert_called_with(text.TITLE, text.NO_CATEGORIES, parent=dialog)

    def test_button_states_and_read_only(self):
        dialog = self._dialog()
        for kind, name, allowed in (
            ("", "", ()), ("recent_root", "", ()),
            ("recent_entry", "", (text.LOAD, text.REMOVE_ENTRY, text.COPY_ENTRY)),
            ("category_entry", "z", (text.LOAD, text.REMOVE_ENTRY)),
            ("category", "z", (text.RENAME_CATEGORY, text.REMOVE_CATEGORY)),
        ):
            if kind:
                self._select(dialog, kind, name)
            for label, button in dialog.buttons.items():
                self.assertEqual(button.instate(["!disabled"]), label in (*allowed, text.ADD_CATEGORY, text.CLOSE))
        self.status = contracts.HISTORY_READ_ONLY
        dialog._redraw()
        self._select(dialog, "recent_entry")
        self.assertTrue(dialog.notice.winfo_manager())
        self.assertTrue(dialog.category_entry.instate(["disabled"]))
        for label, button in dialog.buttons.items():
            self.assertEqual(button.instate(["!disabled"]), label in (text.LOAD, text.CLOSE))
        for edit in (lambda: self.controller.add_category("new"),
                     lambda: self.controller.rename_category("a", "b"),
                     lambda: self.controller.remove_category("z"),
                     lambda: self.controller.copy_to_category("a", "shared.json"),
                     lambda: self.controller.remove_recent(0),
                     lambda: self.controller.remove_category_entry("z", 0)):
            self.assertEqual(edit(), (False, text.READ_ONLY_NOTICE))
        self.save.assert_not_called()

    def test_close_routes_restore_hook_and_parent_grab(self):
        self.addCleanup(self.app.grab_release)
        self._patch(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True)
        load = self._patch(self.app.keymap_set_io, "load_keymap_set_path", return_value="ok")
        wait_for_hook_pause_count(self, self.app, 0)
        before = self.app.hook.get_hook_pause_count()
        for route in ("escape", "wm", "load"):
            self.app.grab_set()
            dialog = self._dialog()
            self.assertEqual(self.app.hook.get_hook_pause_count(), before + 1)
            if route == "escape":
                send_escape(self, self.app, dialog)
            elif route == "wm":
                dialog.tk.call(dialog.protocol("WM_DELETE_WINDOW"))
            else:
                self._select(dialog, "recent_entry")
                dialog.buttons[text.LOAD].invoke()
            wait_for_hook_pause_count(self, self.app, before)
            self.assertFalse(dialog.winfo_exists())
            self.assertIs(self.app.grab_current(), self.app)
        load.assert_called_once()
        self.app.grab_release()

    def test_chooser_returns_result_and_restores_history_grab(self):
        dialog = self._dialog()
        for accept in (False, True):
            chooser = dialogs.CategoryChooserDialog(dialog, names=("a", "z"))
            self.addCleanup(self._close, chooser)
            chooser.update_idletasks()
            wait_for_hook_pause_count(self, self.app, 1)
            self.assertIs(self.app.grab_current(), chooser)
            if accept:
                chooser.listbox.selection_set(1)
                chooser._ok()
            else:
                chooser.tk.call(chooser.protocol("WM_DELETE_WINDOW"))
            self.app.update()
            self.assertEqual(chooser.result, "z" if accept else "")
            self.assertIs(self.app.grab_current(), dialog)

    def test_controller_converts_exceptions_without_saving(self):
        self.read.side_effect = OSError("read failed")
        self.assertFalse(self.controller.add_category("new")[0])
        self.assertEqual(self.controller.load_history()[1], contracts.HISTORY_READ_ONLY)
        self.save.assert_not_called()
        self._patch(self.app.config_service, "resolve_config_path", side_effect=OSError("resolve failed"))
        self._patch(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True)
        load = self._patch(self.app.keymap_set_io, "load_keymap_set_path")
        flash = self._patch(self.app, "_set_flash_message")
        self.assertFalse(self.controller.entry_exists("x.json"))
        self.assertFalse(self.controller.open_keymap_set("x.json"))
        flash.assert_called_once()
        load.assert_not_called()
