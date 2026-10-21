import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.presentation import app as app_module
from keyseq.presentation import key_capture_ime
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.grid_editor_window import GridEditorWindow
from keyseq.presentation.dialogs.keymap_edit_dialog import KeymapEditDialog
from keyseq.presentation.dialogs.keymap_switch_batch_dialog import KeymapSwitchBatchDialog
from keyseq.presentation.dialogs.trigger_dialog import TriggerDialog
from keyseq.presentation.keyboard_window import KeyboardWindow


class CaptureHookEntriesUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._io_patchers = [
            patch.object(StartupIo, "load_startup_and_config"),
            patch.object(StartupIo, "write_startup"),
            patch.object(KeymapSetIo, "save_keymap_set"),
            patch.object(KeymapSetIo, "save_keymap_set_to"),
        ]
        for patcher in cls._io_patchers:
            patcher.start()

    @classmethod
    def tearDownClass(cls):
        for patcher in reversed(cls._io_patchers):
            patcher.stop()

    def setUp(self):
        self.tracker = key_capture_ime.KeyCaptureImeTracker(
            get_open=lambda _hwnd: False,
            set_open=lambda _hwnd, _value: True,
        )
        self._tracker_patcher = patch.object(
            key_capture_ime, "_default_tracker", self.tracker
        )
        self._tracker_patcher.start()
        self.app = app_module.App()
        self.tracker.set_capture_hook(None)

    def tearDown(self):
        try:
            app_exists = self.app.winfo_exists()
        except tk.TclError:
            app_exists = False
        if app_exists:
            self.app.destroy()
        self._tracker_patcher.stop()

    @staticmethod
    def _key():
        return SimpleNamespace(keysym="Muhenkan", keycode=0, state=0)

    def _callback(self, owner):
        callback = self.tracker._owners[owner].on_hook_key
        self.assertTrue(callable(callback))
        return callback

    def test_stop_and_toggle_capture_match_tk_and_ignore_inactive_callback(self):
        for controller in (self.app.stop_key_capture, self.app.toggle_key_capture):
            with self.subTest(controller=controller._data_key):
                with patch.object(self.app.input_gateway, "validate_key_name"):
                    controller.start()
                    with patch(
                        "keyseq.presentation.controllers.key_capture.normalize_tk_key_event",
                        return_value="muhenkan",
                    ):
                        self.assertEqual(controller.on_keypress(self._key()), "break")
                    self.assertEqual(controller._var.get(), "muhenkan")
                    self.assertFalse(controller.capturing)
                    controller._var.set("")
                    controller.start()
                    callback = self._callback(controller)
                    callback("muhenkan")
                    self.assertEqual(controller._var.get(), "muhenkan")
                    self.assertEqual(self.app.data[controller._data_key], "muhenkan")
                    self.assertFalse(controller.capturing)
                    self.assertFalse(self.tracker.is_capturing(controller))
                    callback("a")
                    self.assertEqual(controller._var.get(), "muhenkan")
                # 次の owner の重複検査に影響させない。
                self.app.data[controller._data_key] = ""

    def test_single_key_dialogs_match_tk_and_ignore_inactive_callback(self):
        for dialog_class, module_name in (
            (TriggerDialog, "trigger_dialog"),
            (KeymapEditDialog, "keymap_edit_dialog"),
        ):
            with self.subTest(dialog=module_name):
                dialog = dialog_class(self.app, "Capture")
                dialog._start_capture()
                with patch(
                    f"keyseq.presentation.dialogs.{module_name}.normalize_tk_key_event",
                    return_value="muhenkan",
                ):
                    self.assertEqual(dialog._on_capture_keypress(self._key()), "break")
                self.assertEqual(dialog.key_var.get(), "muhenkan")
                self.assertFalse(dialog._capturing)
                dialog.key_var.set("")
                dialog._start_capture()
                callback = self._callback(dialog)
                callback("muhenkan")
                self.assertEqual(dialog.key_var.get(), "muhenkan")
                self.assertFalse(dialog._capturing)
                self.assertFalse(self.tracker.is_capturing(dialog))
                callback("a")
                self.assertEqual(dialog.key_var.get(), "muhenkan")
                dialog.destroy()

    def test_batch_capture_records_current_row_and_ignores_inactive_callback(self):
        dialog = KeymapSwitchBatchDialog(
            self.app, "Batch", [("新規", "One", "", ""), ("新規", "Two", "", "")],
            lambda _values: None,
        )
        dialog._start_capture(0)
        with patch(
            "keyseq.presentation.dialogs.keymap_switch_batch_dialog.normalize_tk_key_event",
            return_value="muhenkan",
        ):
            self.assertEqual(dialog._on_capture_keypress(self._key()), "break")
        self.assertEqual(dialog.key_vars[0].get(), "muhenkan")
        self.assertFalse(dialog._capturing)
        dialog._start_capture(0)
        generation = self.tracker.generation
        dialog._stop_capture()
        dialog._start_capture(1)
        self.assertGreater(self.tracker.generation, generation)
        callback = self._callback(dialog)
        callback("muhenkan")
        self.assertEqual(dialog.key_vars[1].get(), "muhenkan")
        self.assertFalse(dialog._capturing)
        self.assertIsNone(dialog._capture_index)
        self.assertFalse(self.tracker.is_capturing(dialog))
        callback("a")
        self.assertEqual([var.get() for var in dialog.key_vars], ["muhenkan"] * 2)
        dialog.destroy()

    def test_hotkey_capture_combines_held_modifiers_and_ignores_inactive_callback(self):
        dialog = ActionDialog(self.app, "Action")
        for delivery in ("tk", "hook"):
            with self.subTest(delivery=delivery):
                dialog.value_var.set("")
                dialog._start_recording()
                dialog._mods_down.add("ctrl")
                callback = self._callback(dialog)
                if delivery == "tk":
                    with patch(
                        "keyseq.presentation.dialogs.action_dialog.normalize_tk_key_event",
                        return_value="muhenkan",
                    ):
                        self.assertEqual(dialog._on_key_press(self._key()), "break")
                else:
                    callback("muhenkan")
                self.assertEqual(dialog.value_var.get(), "ctrl+muhenkan")
                self.assertFalse(dialog._recording)
                self.assertFalse(self.tracker.is_capturing(dialog))
                callback("a")
                self.assertEqual(dialog.value_var.get(), "ctrl+muhenkan")
        dialog.destroy()

    def test_key_hold_capture_matches_tk_and_ignores_inactive_callback(self):
        dialog = ActionDialog(self.app, "Action")
        dialog.type_var.set("key_hold")
        fields = dialog.key_hold_fields
        for delivery in ("tk", "hook"):
            with self.subTest(delivery=delivery):
                fields.key_var.set("")
                fields.start_recording()
                callback = self._callback(fields)
                if delivery == "tk":
                    with patch(
                        "keyseq.presentation.dialogs.action_key_hold_fields.normalize_key_hold_tk_key_event",
                        return_value="muhenkan",
                    ):
                        self.assertEqual(fields._on_key_press(self._key()), "break")
                else:
                    callback("muhenkan")
                self.assertEqual(fields.key_var.get(), "muhenkan")
                self.assertFalse(fields.recording)
                self.assertFalse(self.tracker.is_capturing(fields))
                callback("a")
                self.assertEqual(fields.key_var.get(), "muhenkan")
        dialog.destroy()

    def test_keyboard_capture_matches_tk_and_source_click_advances_generation(self):
        assign = Mock(return_value=True)
        window = KeyboardWindow(self.app, on_assign_keymap=assign)
        window._begin_edit("a")
        with patch.object(window, "_normalize_tk_key", return_value="muhenkan"):
            self.assertEqual(window._on_key_press(self._key()), "break")
        assign.assert_called_once_with("a", "muhenkan")
        self.assertIsNone(window._editing_source_key)
        assign.reset_mock()
        with patch.object(self.app.hook, "suspend_hook_for_dialog") as suspend:
            window._begin_edit("a")
            generation = self.tracker.generation
            window._begin_edit("b")
            self.assertGreater(self.tracker.generation, generation)
            suspend.assert_called_once_with()
        callback = self._callback(window)
        callback("muhenkan")
        assign.assert_called_once_with("b", "muhenkan")
        self.assertIsNone(window._editing_source_key)
        self.assertFalse(self.tracker.is_capturing(window))
        callback("a")
        assign.assert_called_once()
        window.destroy()

    def test_grid_capture_matches_tk_for_cells_operations_and_subcells(self):
        for target in ("cell", "op", "sub"):
            with self.subTest(target=target):
                window = self._new_grid()
                operation = next(iter(window.ops))
                if target == "op":
                    window.panel.select_op_key(operation)
                elif target == "sub":
                    window.panel.select_sub_key(0)
                callback = self._callback(window)
                window.on_key(self._key())
                expected = (window.layout, dict(window.ops), window.panel.sub_key_rows())
                callback("a")
                self.assertNotEqual(
                    (window.layout, window.ops, window.panel.sub_key_rows()), expected
                )
                callback("muhenkan")
                self.assertEqual(
                    (window.layout, window.ops, window.panel.sub_key_rows()), expected
                )
                if target == "cell":
                    self.assertEqual(window.layout.rows[0].cells[0].key, "muhenkan")
                elif target == "op":
                    self.assertEqual(window.ops[operation], "muhenkan")
                else:
                    self.assertEqual(window.panel.sub_key_rows()[0][0], "muhenkan")
                self.assertTrue(self.tracker.is_capturing(window))
                window.destroy()
                self.assertFalse(self.tracker.is_capturing(window))
                callback("a")
                self.assertEqual(window.layout, expected[0])
                self.assertEqual(window.ops, expected[1])
                self.assertEqual(window.panel.sub_key_rows(), expected[2])

    def _new_grid(self):
        return GridEditorWindow(
            self.app, grid=None,
            monitors=[MonitorInfo("primary", (0, 0, 600, 600), True)],
            start_monitor_id="primary", reserved=set(),
            key_name_from_event=lambda _event: "muhenkan",
        )

    def test_grid_selection_changes_advance_generation(self):
        window = self._new_grid()
        operation = next(iter(window.ops))
        for change in (
            lambda: window.panel.select_op_key(operation),
            window.panel.clear_op_selection,
            lambda: window.panel.select_sub_key(0),
            window.panel.clear_sub_selection,
            lambda: window.switch_monitor("primary"),
            window.on_escape,
            window.reset_monitor,
        ):
            generation = self.tracker.generation
            change()
            self.assertGreater(self.tracker.generation, generation)
            self.assertTrue(self.tracker.is_capturing(window))
        rect, _key = window.cell_rects()[-1][-1]
        generation = self.tracker.generation
        window.on_press(SimpleNamespace(x=(rect[0] + rect[2]) / 2,
                                        y=(rect[1] + rect[3]) / 2))
        self.assertGreater(self.tracker.generation, generation)
        window.destroy()


if __name__ == "__main__":
    unittest.main()
