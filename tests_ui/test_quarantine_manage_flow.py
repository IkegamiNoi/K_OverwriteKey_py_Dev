import copy
import tempfile
import tkinter as tk
import unittest
from tkinter import ttk
from pathlib import Path
from unittest.mock import Mock, patch

from keyseq.application.config_service.quarantine_manage import QuarantineDeleteResult, QuarantineRestoreResult, QuarantineUnit
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import quarantine_manage_io as manage_io
from keyseq.presentation.dialogs.quarantine_manage_dialog import QuarantineManageDialog
from keyseq.presentation.quarantine_manage_text import (
    format_delete_plan, format_delete_result,
    format_restore_plan, format_restore_result, format_unit_list,
)
from keyseq.presentation.views.menu_bar import build_menu_bar


UNIT = QuarantineUnit("20260906_101500", "2026-09-06T10:15:00", 2, 1, True)


class QuarantineManageFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.listing = self._patch(self.app.config_service, "list_quarantine_units", return_value=(UNIT,))
        self.result = QuarantineRestoreResult(UNIT.unit_id, (("keymap", "user/keymaps/a.json"),), (), True, "")
        self.restore = self._patch(self.app.config_service, "restore_quarantine_unit", return_value=self.result)
        self.dialog = Mock(action="restore", selected_unit_id=UNIT.unit_id)
        self.open_dialog = self._patch(manage_io, "QuarantineManageDialog", return_value=self.dialog)
        self.confirm = Mock(result=False)
        self.open_confirm = self._patch(manage_io, "ReferenceCleanupDialog", return_value=self.confirm)
        self.info = self._patch(manage_io.messagebox, "showinfo")

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_zero_units_notifies_without_opening_dialog(self):
        self.listing.return_value = ()
        self.app.quarantine_manage_io.manage_quarantine()
        self.assertTrue(self.app.config_root)
        self.listing.assert_called_once_with(config_root=self.app.config_root)
        self.info.assert_called_once_with("隔離の管理", "隔離された実行単位はありません。")
        self.open_dialog.assert_not_called()
        self.open_confirm.assert_not_called()
        self.restore.assert_not_called()

    def test_list_lines_and_ids_have_the_same_order(self):
        units = (UNIT, QuarantineUnit(UNIT.unit_id + "_2", "", 0, 0, False))
        self.listing.return_value = units
        self.dialog.action = ""
        self.app.quarantine_manage_io.manage_quarantine()
        self.open_dialog.assert_called_once_with(
            self.app, lines=format_unit_list(units), unit_ids=tuple(unit.unit_id for unit in units),
        )
        self.dialog.wait_window.assert_called_once_with()

    def test_close_unselected_and_unknown_selection_do_not_restore(self):
        for action, selected in (("", UNIT.unit_id), ("restore", ""), ("restore", "unknown")):
            with self.subTest(action=action, selected=selected):
                self.dialog.action, self.dialog.selected_unit_id = action, selected
                self.app.quarantine_manage_io.manage_quarantine()
        self.open_confirm.assert_not_called()
        self.restore.assert_not_called()
        self.info.assert_not_called()

    def test_confirmation_has_restore_labels_and_cancel_does_nothing(self):
        self.app.quarantine_manage_io.manage_quarantine()
        self.open_confirm.assert_called_once_with(
            self.app, title="隔離の管理", lines=format_restore_plan(UNIT),
            header="復元する内容を確認してください。", run_label="復元する",
        )
        self.confirm.wait_window.assert_called_once_with()
        self.restore.assert_not_called()
        self.info.assert_not_called()

    def test_confirmed_restore_passes_config_root_and_notifies_formatted_result(self):
        self.confirm.result = True
        self.app.quarantine_manage_io.manage_quarantine()
        self.assertTrue(self.app.config_root)
        self.restore.assert_called_once_with(UNIT.unit_id, config_root=self.app.config_root)
        self.info.assert_called_once_with("隔離の管理", "\n".join(format_restore_result(self.result)))

    def test_invalid_manifest_only_notifies_without_confirmation_or_restore(self):
        self.listing.return_value = (QuarantineUnit(UNIT.unit_id, "", 0, 0, False),)
        self.confirm.result = True
        self.app.quarantine_manage_io.manage_quarantine()
        self.info.assert_called_once_with("隔離の管理", "マニフェストが読めないため復元できません")
        self.open_confirm.assert_not_called()
        self.restore.assert_not_called()

    def test_runtime_and_dirty_state_are_unchanged_and_not_reloaded(self):
        self.confirm.result = True
        before = copy.deepcopy(self.app.data)
        dirty = copy.deepcopy(self.app.dirty_tracker.capture_dirty_snapshot())
        with patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty, patch.object(
            self.app.keymap_set_io, "apply_loaded_data_to_ui",
        ) as reload_data, patch.object(self.app.config_service.repository, "save_json") as save:
            self.app.quarantine_manage_io.manage_quarantine()
        self.assertEqual(self.app.data, before)
        self.assertEqual(self.app.dirty_tracker.capture_dirty_snapshot(), dirty)
        self.restore.assert_called_once()
        set_dirty.assert_not_called()
        reload_data.assert_not_called()
        save.assert_not_called()

    def test_settings_menu_invokes_manage_after_sweep_by_label(self):
        self.addCleanup(build_menu_bar, self.app)
        with patch.object(self.app.quarantine_manage_io, "manage_quarantine") as manage:
            build_menu_bar(self.app)
            menu = self._settings_menu()
            labels = [menu.entrycget(index, "label") for index in range(menu.index("end") + 1)
                      if menu.type(index) != "separator"]
            self.assertEqual(labels[labels.index("孤児ファイルの棚卸し…") + 1], "隔離の管理…")
            for index in range(menu.index("end") + 1):
                if menu.type(index) == "command" and menu.entrycget(index, "label") == "隔離の管理…":
                    menu.invoke(index)
                    break
        manage.assert_called_once_with()

    def _settings_menu(self):
        menubar = self.app.menubar
        for index in range(menubar.index("end") + 1):
            if menubar.type(index) == "cascade" and menubar.entrycget(index, "label") == "設定":
                return self.app.nametowidget(menubar.entrycget(index, "menu"))
        self.fail("設定メニューが見つかりません")

    def _prepare_delete(self, unit=UNIT, paths=None):
        self.dialog.action = "delete"
        self.dialog.selected_unit_id = unit.unit_id
        self.listing.return_value = (unit,)
        if paths is None:
            paths = (f"quarantine/{unit.unit_id}/manifest.json", f"quarantine/{unit.unit_id}/MixedCase.json")
        collect = self._patch(self.app.config_service, "collect_unit_paths", return_value=paths)
        result = QuarantineDeleteResult(unit.unit_id, True, "")
        delete = self._patch(self.app.config_service, "delete_quarantine_unit", return_value=result)
        return collect, delete, paths, result

    def test_delete_confirmation_cancel_does_not_delete(self):
        # 確認 19・24
        collect, delete, paths, _ = self._prepare_delete()
        self.app.quarantine_manage_io.manage_quarantine()
        collect.assert_called_once_with(UNIT.unit_id, config_root=self.app.config_root)
        self.open_confirm.assert_called_once_with(
            self.app, title="隔離の管理", lines=format_delete_plan(UNIT, paths, manifest_valid=True),
            header="削除する内容を確認してください。", run_label="削除する",
        )
        self.confirm.wait_window.assert_called_once_with()
        delete.assert_not_called()
        self.restore.assert_not_called()
        self.info.assert_not_called()

    def test_confirmed_delete_forwards_false_for_valid_manifest_and_notifies(self):
        # 確認 19・20・24
        collect, delete, paths, result = self._prepare_delete()
        self.confirm.result = True
        self.app.quarantine_manage_io.manage_quarantine()
        collect.assert_called_once_with(UNIT.unit_id, config_root=self.app.config_root)
        self.open_confirm.assert_called_once_with(
            self.app, title="隔離の管理", lines=format_delete_plan(UNIT, paths, manifest_valid=True),
            header="削除する内容を確認してください。", run_label="削除する",
        )
        delete.assert_called_once_with(UNIT.unit_id, config_root=self.app.config_root, allow_invalid_manifest=False)
        self.info.assert_called_once_with("隔離の管理", "\n".join(format_delete_result(result)))
        self.restore.assert_not_called()

    def test_invalid_manifest_delete_warns_and_forwards_true_with_empty_paths(self):
        # 確認 19・20・24: 空ディレクトリでも強い確認を経て続行する。
        unit = QuarantineUnit(UNIT.unit_id, "", 0, 0, False)
        _, delete, paths, result = self._prepare_delete(unit, paths=())
        self.confirm.result = True
        self.app.quarantine_manage_io.manage_quarantine()
        self.open_confirm.assert_called_once_with(
            self.app, title="隔離の管理", lines=format_delete_plan(unit, paths, manifest_valid=False),
            header="削除する内容を確認してください。", run_label="削除する",
        )
        lines = self.open_confirm.call_args.kwargs["lines"]
        self.assertIn("マニフェストが読めないため、中身を確認できません。", lines)
        self.assertIn("ディレクトリごと削除します。", lines)
        delete.assert_called_once_with(unit.unit_id, config_root=self.app.config_root, allow_invalid_manifest=True)
        self.info.assert_called_once_with("隔離の管理", "\n".join(format_delete_result(result)))
        self.restore.assert_not_called()

    def test_unselected_or_unknown_delete_does_not_collect_confirm_or_delete(self):
        # 確認 21・24
        collect, delete, _, _ = self._prepare_delete()
        self.confirm.result = True
        for selected in ("", "unknown"):
            with self.subTest(selected=selected):
                self.dialog.selected_unit_id = selected
                self.app.quarantine_manage_io.manage_quarantine()
        collect.assert_not_called()
        delete.assert_not_called()
        self.open_confirm.assert_not_called()
        self.info.assert_not_called()

    def test_restore_route_still_restores_without_collecting_or_deleting(self):
        # 確認 22・24
        collect, delete, _, _ = self._prepare_delete()
        self.dialog.action = "restore"
        self.confirm.result = True
        self.app.quarantine_manage_io.manage_quarantine()
        self.open_confirm.assert_called_once_with(
            self.app, title="隔離の管理", lines=format_restore_plan(UNIT),
            header="復元する内容を確認してください。", run_label="復元する",
        )
        self.restore.assert_called_once_with(UNIT.unit_id, config_root=self.app.config_root)
        self.info.assert_called_once_with("隔離の管理", "\n".join(format_restore_result(self.result)))
        collect.assert_not_called()
        delete.assert_not_called()

    def test_delete_keeps_data_dirty_state_and_real_files_unchanged(self):
        # 確認 23・24: 削除 API を patch.object し、実体も残ることを確認する。
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name) / "config"
        unit_dir = root / "quarantine" / UNIT.unit_id
        unit_dir.mkdir(parents=True)
        manifest = unit_dir / "manifest.json"
        manifest.write_text('{"entries": []}', encoding="utf-8")
        child = unit_dir / "keep.txt"
        child.write_text("keep", encoding="utf-8")
        _, delete, _, _ = self._prepare_delete()
        self.confirm.result = True
        data_before = copy.deepcopy(self.app.data)
        dirty_before = copy.deepcopy(self.app.dirty_tracker.capture_dirty_snapshot())
        with patch.object(self.app, "config_root", str(root)), patch.object(
            self.app.dirty_tracker, "set_dirty",
        ) as set_dirty, patch.object(self.app.keymap_set_io, "apply_loaded_data_to_ui") as reload_data:
            self.app.quarantine_manage_io.manage_quarantine()
        delete.assert_called_once_with(UNIT.unit_id, config_root=str(root), allow_invalid_manifest=False)
        self.assertEqual(self.app.data, data_before)
        self.assertEqual(self.app.dirty_tracker.capture_dirty_snapshot(), dirty_before)
        set_dirty.assert_not_called()
        reload_data.assert_not_called()
        self.assertEqual(manifest.read_text(encoding="utf-8"), '{"entries": []}')
        self.assertEqual(child.read_text(encoding="utf-8"), "keep")


class QuarantineManageDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def _dialog(self):
        dialog = QuarantineManageDialog(self.app, lines=("first", "second"), unit_ids=("id1", "id2"))
        self.addCleanup(lambda: dialog.destroy() if dialog.winfo_exists() else None)
        return dialog

    @staticmethod
    def _buttons(widget):
        buttons = []
        for child in widget.winfo_children():
            if isinstance(child, ttk.Button):
                buttons.append(child)
            buttons.extend(QuarantineManageDialogTest._buttons(child))
        return buttons

    def test_list_buttons_modal_and_no_selection(self):
        dialog = self._dialog()
        self.assertEqual(dialog.listbox.get(0, tk.END), ("first", "second"))
        self.assertEqual([button.cget("text") for button in self._buttons(dialog)], ["復元する…", "削除する…", "閉じる"])
        self.assertEqual(dialog.grab_current(), dialog)
        self.assertEqual(str(dialog.transient()), str(self.app))
        dialog._restore()
        self.assertEqual((dialog.action, dialog.selected_unit_id), ("", ""))
        self.assertTrue(dialog.winfo_exists())
        self._buttons(dialog)[2].invoke()
        self.assertFalse(dialog.winfo_exists())
        self.assertEqual(dialog.action, "")

    def test_selection_returns_matching_id_and_resumes_hook(self):
        with patch.object(self.app.hook, "suspend_hook_for_dialog") as suspend, patch.object(
            self.app.hook, "resume_hook_after_dialog",
        ) as resume:
            dialog = self._dialog()
            dialog.listbox.selection_set(1)
            self._buttons(dialog)[0].invoke()
        self.assertEqual((dialog.action, dialog.selected_unit_id), ("restore", "id2"))
        self.assertFalse(dialog.winfo_exists())
        suspend.assert_called_once_with()
        resume.assert_called_once_with()

    def test_escape_and_window_close_keep_action_empty(self):
        for close in ("escape", "window"):
            with self.subTest(close=close), patch.object(self.app.hook, "resume_hook_after_dialog") as resume:
                dialog = self._dialog()
                if close == "escape":
                    self.assertTrue(dialog.bind("<Escape>"))
                    dialog.deiconify()
                    dialog.update_idletasks()
                    dialog.focus_force()
                    dialog.event_generate("<Escape>")
                else:
                    dialog.tk.call(dialog.protocol("WM_DELETE_WINDOW"))
                self.assertFalse(dialog.winfo_exists())
                self.assertEqual((dialog.action, dialog.selected_unit_id), ("", ""))
                resume.assert_called_once_with()

    def test_delete_button_returns_selected_id_and_resumes_hook(self):
        # 確認 19・24
        with patch.object(self.app.config_service, "delete_quarantine_unit") as delete, patch.object(
            self.app.hook, "resume_hook_after_dialog",
        ) as resume:
            dialog = self._dialog()
            dialog.listbox.selection_set(1)
            button = next(button for button in self._buttons(dialog) if button.cget("text") == "削除する…")
            button.invoke()
        self.assertEqual((dialog.action, dialog.selected_unit_id), ("delete", "id2"))
        self.assertFalse(dialog.winfo_exists())
        resume.assert_called_once_with()
        delete.assert_not_called()

    def test_delete_button_without_selection_leaves_dialog_open(self):
        # 確認 21・24
        with patch.object(self.app.config_service, "delete_quarantine_unit") as delete:
            dialog = self._dialog()
            button = next(button for button in self._buttons(dialog) if button.cget("text") == "削除する…")
            button.invoke()
        self.assertEqual((dialog.action, dialog.selected_unit_id), ("", ""))
        self.assertTrue(dialog.winfo_exists())
        delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
