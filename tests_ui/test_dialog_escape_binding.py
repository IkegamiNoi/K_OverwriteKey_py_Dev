"""群 C の Escape 結線と実配送・直接呼び出しによる後始末を固定する。"""

import copy
import tkinter as tk
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import hotkey_presets_io
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.keymap_edit_dialog import KeymapEditDialog
from keyseq.presentation.dialogs.layout_delete_dialog import LayoutDeleteDialog
from keyseq.presentation.dialogs.preset_dialog import PresetDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog
from keyseq.presentation.dialogs.trigger_dialog import TriggerDialog
from tests_ui.escape_delivery import send_escape


class DialogEscapeBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        # 生成から破棄まで実 config への保存を遮断する。
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(
            ConfigService, "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        stack.enter_context(patch.object(
            ConfigService, "save_keymap_set_history",
            side_effect=AssertionError("unpatched history save"),
        ))
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self.app.update()
        self.handlers = {}
        original_bind = tk.Misc.bind

        def capture_bind(widget, sequence=None, func=None, add=None):
            if sequence == "<Escape>" and func is not None:
                self.handlers[widget] = func
            return original_bind(widget, sequence, func, add)

        patcher = patch.object(tk.Misc, "bind", capture_bind)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._destroy_dialogs)

    def _destroy_dialogs(self):
        for dialog in self.handlers:
            if dialog.winfo_exists():
                dialog.destroy()

    def _close_with_escape_handler(self, dialog):
        self.assertTrue(dialog.bind("<Escape>"))
        with patch.object(dialog, "destroy", wraps=dialog.destroy) as destroy:
            self.handlers[dialog](None)
        destroy.assert_called_once_with()
        self.assertFalse(dialog.winfo_exists())
        # フック再開は <Destroy> から after(0) で予約されるため、数える前に流す
        # （`hook_controller.py:57`）。
        self.app.update()

    def test_layout_delete_escape_destroys_and_resumes_hook(self):
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        with patch.object(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        ) as resume:
            dialog = LayoutDeleteDialog(self.app, title="削除", items=[("id", "name")])
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            self.assertTrue(dialog.bind("<Escape>"))
            send_escape(self, self.app, dialog)
            self.assertFalse(dialog.winfo_exists())
            # <Destroy> から after(0) で予約されたフック再開を流してから数える。
            self.app.update()
            resume.assert_called_once_with()
        self.assertIsNone(dialog.result)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_preset_manager_escape_discards_edits_and_resumes_hook(self):
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        original_data = copy.deepcopy(self.app.data)
        with patch.object(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        ) as resume:
            dialog = PresetManagerDialog(self.app)
            dialog._temp.append({"label": "unsaved", "keys": []})
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            self.assertTrue(dialog.bind("<Escape>"))
            send_escape(self, self.app, dialog)
            self.assertFalse(dialog.winfo_exists())
            # <Destroy> から after(0) で予約されたフック再開を流してから数える。
            self.app.update()
            resume.assert_called_once_with()
        self.assertEqual(self.app.data, original_data)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_hotkey_overwrite_escape_returns_cancel(self):
        errors = []

        def close(dialog):
            try:
                self._close_with_escape_handler(dialog)
            except Exception as error:
                errors.append(error)
            finally:
                if dialog.winfo_exists():
                    dialog.destroy()

        def on_grab(dialog, parent):
            self.assertIs(parent, self.app)
            self.assertTrue(dialog.bind("<Escape>"))
            # wait_window 開始後に直接呼ぶ。開始前の破棄は TclError になる。
            dialog.after_idle(lambda: close(dialog))

        with patch.object(hotkey_presets_io, "grab_modal", side_effect=on_grab) as grab:
            result = hotkey_presets_io.HotkeyPresetsIo(self.app).confirm_overwrite(
                stored_path="unused.json", existing=[], transient_parent=self.app,
            )
        grab.assert_called_once()
        if errors:
            raise errors[0]
        self.assertEqual(result, "cancel")


    def _assert_group_a_cancelled(self, dialog):
        if isinstance(dialog, ActionDialog):
            self.assertIsNone(self.app._dialog_result)
        else:
            self.assertIsNone(dialog.result)

    def test_group_a_normal_escape_cancels_and_resumes_hook(self):
        for dialog_class in (ActionDialog, TriggerDialog, KeymapEditDialog):
            with self.subTest(dialog=dialog_class.__name__):
                self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
                with patch.object(self.app, "_dialog_result", None, create=True), patch.object(
                    self.app.hook, "resume_hook_after_dialog",
                    wraps=self.app.hook.resume_hook_after_dialog,
                ) as resume:
                    dialog = dialog_class(self.app, title="Escape 検査")
                    self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                    self.assertTrue(dialog.bind("<Escape>"))
                    send_escape(self, self.app, dialog)
                    self.assertFalse(dialog.winfo_exists())
                    self.app.update()
                    self._assert_group_a_cancelled(dialog)
                    resume.assert_called_once_with()
                    self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def _assert_escape_stops_without_closing(self, dialog, state_name, resume):
        self.assertTrue(getattr(dialog, state_name))
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        dialog.focus_force()
        self.app.update()
        focused = self.app.focus_get()
        self.assertTrue(
            focused is not None and (
                focused is dialog or str(focused).startswith(f"{dialog}.")
            ),
            f"Escape 送信前のフォーカスがダイアログ外: {focused}",
        )
        dialog.event_generate("<Escape>")
        self.app.update()
        self.assertFalse(getattr(dialog, state_name))
        self.assertTrue(dialog.winfo_exists())
        self._assert_group_a_cancelled(dialog)
        resume.assert_not_called()
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)

    def test_group_a_active_escape_stops_then_second_escape_closes(self):
        cases = (
            (ActionDialog, "_start_recording", "_recording"),
            (TriggerDialog, "_start_capture", "_capturing"),
            (KeymapEditDialog, "_start_capture", "_capturing"),
        )
        for dialog_class, start_name, state_name in cases:
            with self.subTest(dialog=dialog_class.__name__):
                self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
                with patch.object(self.app, "_dialog_result", None, create=True), patch.object(
                    self.app.hook, "resume_hook_after_dialog",
                    wraps=self.app.hook.resume_hook_after_dialog,
                ) as resume:
                    dialog = dialog_class(self.app, title="Escape 停止検査")
                    getattr(dialog, start_name)()
                    self._assert_escape_stops_without_closing(dialog, state_name, resume)
                    send_escape(self, self.app, dialog)
                    self.assertFalse(dialog.winfo_exists())
                    self.app.update()
                    self._assert_group_a_cancelled(dialog)
                    resume.assert_called_once_with()
                    self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_group_a_preset_escape_cancels_and_keeps_parent_hook_paused(self):
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        with patch.object(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        ) as resume:
            # PresetDialog 自体は停止せず、呼び出し元の管理画面が停止を保持する。
            manager = PresetManagerDialog(self.app)
            dialog = PresetDialog(manager, title="Escape 検査")
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            self.assertTrue(dialog.bind("<Escape>"))
            send_escape(self, self.app, dialog)
            self.assertFalse(dialog.winfo_exists())
            self.assertIsNone(dialog.result)
            self.app.update()
            self.assertTrue(manager.winfo_exists())
            resume.assert_not_called()
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            send_escape(self, self.app, manager)
            self.app.update()
            resume.assert_called_once_with()
            self.assertEqual(self.app.hook.get_hook_pause_count(), 0)


if __name__ == "__main__":
    unittest.main()
