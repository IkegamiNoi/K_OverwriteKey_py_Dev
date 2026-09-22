"""群 C の Escape 結線と直接呼び出しによる後始末を固定する。"""

import copy
import tkinter as tk
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import hotkey_presets_io
from keyseq.presentation.dialogs.layout_delete_dialog import LayoutDeleteDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog


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
        dialog = LayoutDeleteDialog(self.app, title="削除", items=[("id", "name")])
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        self._close_with_escape_handler(dialog)
        self.assertIsNone(dialog.result)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_preset_manager_escape_discards_edits_and_resumes_hook(self):
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        original_data = copy.deepcopy(self.app.data)
        dialog = PresetManagerDialog(self.app)
        dialog._temp.append({"label": "unsaved", "keys": []})
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        self._close_with_escape_handler(dialog)
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


if __name__ == "__main__":
    unittest.main()
