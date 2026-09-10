"""実ダイアログのネスト経路で、子の閉鎖後の grab 復元を固定する。"""
import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io import hotkey_presets_io
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.preset_dialog import PresetDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog


def _unexpected_showerror(_title, message, *_args, **_kwargs):
    raise AssertionError(f"unexpected messagebox.showerror: {message}")


def _unexpected_askyesno(*_args, **_kwargs):
    raise AssertionError("unexpected messagebox.askyesno")


class NestedModalGrabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self._patch(hotkey_presets_io.messagebox, "showerror", side_effect=_unexpected_showerror)
        self._patch(hotkey_presets_io.messagebox, "askyesno", side_effect=_unexpected_askyesno)
        self._patch(self.app.hook, "suspend_hook_for_dialog")
        self._patch(self.app.hook, "resume_hook_after_dialog")
        self.callback_error = self._patch(self.app, "report_callback_exception")
        # cleanup 中の Destroy コールバック例外も失敗として検出する。
        self.addCleanup(self.callback_error.assert_not_called)
        data = self.app.config_service.new_default_data()
        data["hotkey_presets"] = [{"label": "Copy", "value": "ctrl+c"}]
        data["hotkey_presets_individual"] = True
        data["hotkey_presets_path"] = "user/hotkey_presets/nested_modal.json"
        self._patch(self.app, "data", data)
        self._patch(self.app, "keymap_set_path", "user/keymap_sets/nested_modal.json")
        self.write_presets = self._patch(
            self.app.hotkey_presets_io, "write_presets",
            side_effect=AssertionError("unexpected preset write"),
        )

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    @staticmethod
    def cleanup_window(window):
        if window.winfo_exists():
            window.grab_release()
            window.destroy()

    def _preset_manager(self):
        dialog = PresetManagerDialog(self.app)
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        return dialog

    def test_preset_add_restores_manager_grab(self):
        dialog = self._preset_manager()
        original_init = PresetDialog.__init__
        children = []

        def init_and_schedule_close(child, *args, **kwargs):
            original_init(child, *args, **kwargs)
            child.after(0, child.destroy)
            self.addCleanup(self.cleanup_window, child)
            children.append(child)
            self.assertIs(self.app.grab_current(), child)

        with patch.object(PresetDialog, "__init__", init_and_schedule_close):
            dialog.add()

        self.assertEqual(len(children), 1)
        self.assertFalse(children[0].winfo_exists())
        self.assertTrue(dialog.winfo_exists())
        self.assertIs(self.app.grab_current(), dialog)

    def test_action_preset_manager_restores_action_grab(self):
        dialog = ActionDialog(self.app, title="アクション編集")
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        original_init = PresetManagerDialog.__init__
        children = []

        def init_and_schedule_close(child, *args, **kwargs):
            original_init(child, *args, **kwargs)
            child.after(0, child.destroy)
            self.addCleanup(self.cleanup_window, child)
            children.append(child)
            self.assertIs(self.app.grab_current(), child)

        with patch.object(PresetManagerDialog, "__init__", init_and_schedule_close), patch.object(
            dialog, "_rebuild_preset_buttons", wraps=dialog._rebuild_preset_buttons,
        ) as rebuild:
            dialog._open_preset_manager()

        rebuild.assert_called_once_with()
        self.assertEqual(len(children), 1)
        self.assertFalse(children[0].winfo_exists())
        self.assertTrue(dialog.winfo_exists())
        self.assertIs(self.app.grab_current(), dialog)

    def _overwrite_conflict(self):
        stored_path = "user/hotkey_presets/nested_modal.json"
        existing = [{"label": "Paste", "value": "ctrl+v"}]
        self._patch(
            self.app.config_service, "resolve_hotkey_presets_save_path", return_value=stored_path,
        )
        self._patch(
            self.app.config_service, "individual_hotkey_presets_save_rejection_reason",
            return_value="",
        )
        self._patch(
            self.app.config_service, "describe_individual_hotkey_presets_overwrite",
            return_value={"conflict": True, "existing": existing},
        )
        return stored_path, existing

    def _close_overwrite(self, manager, *, window_close=False, destroy_parent=False):
        before = set(self.app.winfo_children())
        confirmations = []

        def close_confirmation():
            windows = [window for window in self.app.winfo_children()
                       if window not in before and isinstance(window, tk.Toplevel)]
            try:
                self.assertEqual(len(windows), 1)
                child = windows[0]
                self.addCleanup(self.cleanup_window, child)
                confirmations.append(child)
                self.assertEqual(child.title(), "専用プリセットの上書き確認")
                self.assertIs(self.app.grab_current(), child)
                if destroy_parent:
                    manager.destroy()
                    self.assertFalse(manager.winfo_exists())
                    self.assertTrue(child.winfo_exists())
                if window_close:
                    handler = child.protocol("WM_DELETE_WINDOW")
                    self.assertTrue(handler)
                    child.tk.call(handler)
                    self.assertFalse(child.winfo_exists())
                else:
                    child.destroy()
            finally:
                # コールバック内のアサート失敗でも実 wait_window を解放する。
                for window in windows:
                    if window.winfo_exists():
                        window.destroy()

        after_id = self.app.after(0, close_confirmation)
        self.addCleanup(self.app.after_cancel, after_id)
        manager.on_ok()
        self.callback_error.assert_not_called()
        self.assertEqual(len(confirmations), 1)
        self.assertFalse(confirmations[0].winfo_exists())

    def test_declined_overwrite_restores_live_manager_grab(self):
        dialog = self._preset_manager()
        dialog.individual_var.set(True)
        stored_path, existing = self._overwrite_conflict()
        with patch.object(
            self.app.hotkey_presets_io, "confirm_overwrite",
            wraps=self.app.hotkey_presets_io.confirm_overwrite,
        ) as confirm:
            self._close_overwrite(dialog)

        confirm.assert_called_once_with(stored_path=stored_path, existing=existing)
        self.write_presets.assert_not_called()
        self.assertTrue(dialog.winfo_exists())
        self.assertIs(self.app.grab_current(), dialog)

    def test_window_close_restores_grab_and_tolerates_destroyed_parent(self):
        self._overwrite_conflict()
        for destroy_parent in (False, True):
            with self.subTest(destroy_parent=destroy_parent):
                dialog = self._preset_manager()
                dialog.individual_var.set(True)
                self._close_overwrite(dialog, window_close=True, destroy_parent=destroy_parent)
                # TclError は直接送出ならテスト失敗、Tk callback 経由ならここで検出する。
                self.callback_error.assert_not_called()
                if destroy_parent:
                    self.assertFalse(dialog.winfo_exists())
                    self.assertIsNone(self.app.grab_current())
                else:
                    self.assertTrue(dialog.winfo_exists())
                    self.assertIs(self.app.grab_current(), dialog)
                    dialog.destroy()
        self.write_presets.assert_not_called()
