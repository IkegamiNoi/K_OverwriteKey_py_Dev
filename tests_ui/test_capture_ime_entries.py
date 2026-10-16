import unittest
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import patch

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
from keyseq.presentation.hook_button_texts import UNKNOWN_CAPTURE_KEY_HINT_TEXT
from keyseq.presentation.keyboard_window import KeyboardWindow
from tests_ui.escape_delivery import acquire_focus


class CaptureImeEntriesUiTest(unittest.TestCase):
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
        self.ime_open = True
        self.tracker = key_capture_ime.KeyCaptureImeTracker(
            get_open=lambda _hwnd: self.ime_open,
            set_open=self._set_ime_open,
        )
        self._tracker_patcher = patch.object(
            key_capture_ime, "_default_tracker", self.tracker
        )
        self._tracker_patcher.start()
        self.app = app_module.App()

    def tearDown(self):
        try:
            app_exists = self.app.winfo_exists()
        except tk.TclError:
            app_exists = False
        if app_exists:
            self.app.destroy()
        self._tracker_patcher.stop()

    def _set_ime_open(self, _hwnd, value):
        self.ime_open = value
        return True

    @staticmethod
    def _key(keysym):
        return SimpleNamespace(keysym=keysym, keycode=0, state=0)

    def _new_dialog(self, kind):
        if kind == "trigger":
            return TriggerDialog(self.app, "Trigger")
        if kind == "edit":
            return KeymapEditDialog(self.app, "Edit")
        return KeymapSwitchBatchDialog(
            self.app, "Batch", [("新規", "Map", "", "")], lambda _values: None
        )

    def _capture_dialog_key(self, dialog, keysym):
        return dialog._on_capture_keypress(self._key(keysym))

    def test_single_key_capture_restores_ime_on_success_escape_and_destroy(self):
        controller = self.app.stop_key_capture
        controller._apply_key = lambda _key, **_kwargs: True

        controller.start()
        self.assertFalse(self.ime_open)
        self.assertEqual(controller.on_keypress(self._key("a")), "break")
        self.assertTrue(self.ime_open)

        controller.start()
        self.assertFalse(self.ime_open)
        controller.on_keypress(self._key("Escape"))
        self.assertTrue(self.ime_open)

        controller.start()
        controller.stop(cancel=True)
        self.assertTrue(self.ime_open)

        controller.start()
        self.app.destroy()
        self.assertTrue(self.ime_open)

    def test_single_key_capture_ignores_unresolved_key_without_error(self):
        controller = self.app.stop_key_capture
        with patch("keyseq.presentation.controllers.key_capture.messagebox.showerror") as showerror:
            original_key = controller._var.get()
            controller.start()
            self.assertEqual(
                controller.on_keypress(self._key("??")), "break"
            )
            self.assertTrue(controller.capturing)
            self.assertEqual(controller._var.get(), original_key)
            showerror.assert_not_called()
            controller.stop(cancel=True)
        self.assertTrue(self.ime_open)

    def test_single_key_capture_switches_exclusive_owner_and_restores_ime(self):
        self.app.start_stop_key_capture()
        self.assertFalse(self.ime_open)
        self.app.start_toggle_key_capture()
        self.assertFalse(self.ime_open)
        self.assertFalse(self.app.stop_key_capture.capturing)
        self.assertTrue(self.app.toggle_key_capture.capturing)
        self.app.toggle_key_capture.stop(cancel=True)
        self.assertTrue(self.ime_open)

    def test_trigger_dialog_restores_ime_on_success_escape_button_and_destroy(self):
        dialog = self._new_dialog("trigger")
        dialog._start_capture()
        self.assertFalse(self.ime_open)
        self._capture_dialog_key(dialog, "a")
        self.assertTrue(self.ime_open)

        dialog._start_capture()
        self.assertFalse(self.ime_open)
        acquire_focus(self.app, dialog)  # Escape はフォーカスのある窓へ届くため
        dialog.event_generate("<Escape>")
        dialog.update()
        self.assertTrue(self.ime_open)
        self.assertTrue(dialog.winfo_exists())

        dialog._start_capture()
        dialog._toggle_capture()
        self.assertTrue(self.ime_open)
        dialog._start_capture()
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_trigger_dialog_ignores_unresolved_key_and_shows_hint(self):
        dialog = self._new_dialog("trigger")
        dialog._start_capture()
        self.assertEqual(
            dialog._on_capture_keypress(self._key("??")), "break"
        )
        self.assertTrue(dialog._capturing)
        self.assertEqual(dialog.key_var.get(), "")
        self.assertEqual(dialog.hint.cget("text"), UNKNOWN_CAPTURE_KEY_HINT_TEXT)
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_keymap_edit_dialog_restores_ime_on_success_escape_button_and_destroy(self):
        dialog = self._new_dialog("edit")
        dialog._start_capture()
        self.assertFalse(self.ime_open)
        self._capture_dialog_key(dialog, "a")
        self.assertTrue(self.ime_open)

        dialog._start_capture()
        acquire_focus(self.app, dialog)  # Escape はフォーカスのある窓へ届くため
        dialog.event_generate("<Escape>")
        dialog.update()
        self.assertTrue(self.ime_open)
        self.assertTrue(dialog.winfo_exists())

        dialog._start_capture()
        dialog._toggle_capture()
        self.assertTrue(self.ime_open)
        dialog._start_capture()
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_keymap_edit_dialog_does_not_record_unresolved_key(self):
        dialog = self._new_dialog("edit")
        dialog._start_capture()
        self.assertEqual(
            dialog._on_capture_keypress(self._key("??")), "break"
        )
        self.assertTrue(dialog._capturing)
        self.assertEqual(dialog.key_var.get(), "")
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_batch_dialog_restores_ime_on_success_escape_button_and_destroy(self):
        dialog = self._new_dialog("batch")
        dialog._start_capture(0)
        self.assertFalse(self.ime_open)
        self._capture_dialog_key(dialog, "a")
        self.assertTrue(self.ime_open)

        dialog._start_capture(0)
        dialog._on_escape()
        self.assertTrue(self.ime_open)
        self.assertTrue(dialog.winfo_exists())

        dialog._start_capture(0)
        dialog._toggle_capture(0)
        self.assertTrue(self.ime_open)
        dialog._start_capture(0)
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_batch_dialog_does_not_record_unresolved_key(self):
        dialog = self._new_dialog("batch")
        dialog._start_capture(0)
        self.assertEqual(
            dialog._on_capture_keypress(self._key("??")), "break"
        )
        self.assertTrue(dialog._capturing)
        self.assertEqual(dialog.key_vars[0].get(), "")
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_action_dialog_capture_restores_ime_and_ignores_unresolved_key(self):
        dialog = ActionDialog(self.app, "Action")
        dialog._start_recording()
        self.assertFalse(self.ime_open)
        self.assertEqual(dialog._on_key_press(self._key("??")), "break")
        self.assertTrue(dialog._recording)
        self.assertEqual(dialog.value_var.get(), "")
        self.assertEqual(dialog._on_key_press(self._key("a")), "break")
        self.assertEqual(dialog.value_var.get(), "a")
        self.assertFalse(dialog._recording)
        self.assertTrue(self.ime_open)

        dialog._start_recording()
        acquire_focus(self.app, dialog)
        dialog.event_generate("<Escape>")
        dialog.update()
        self.assertFalse(dialog._recording)
        self.assertTrue(self.ime_open)

        dialog._start_recording()
        dialog._sync_hotkey_controls(False)
        self.assertTrue(self.ime_open)
        dialog._start_recording()
        dialog._stop_recording()
        self.assertTrue(self.ime_open)
        dialog._start_recording()
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_key_hold_capture_restores_ime_and_shows_unresolved_hint(self):
        dialog = ActionDialog(self.app, "Action")
        fields = dialog.key_hold_fields
        dialog.type_var.set("key_hold")
        fields.start_recording()
        self.assertFalse(self.ime_open)
        self.assertEqual(fields._on_key_press(self._key("??")), "break")
        self.assertTrue(fields.recording)
        self.assertEqual(fields.key_var.get(), "")
        self.assertEqual(fields.key_hint.cget("text"), UNKNOWN_CAPTURE_KEY_HINT_TEXT)
        self.assertEqual(fields._on_key_press(self._key("a")), "break")
        self.assertEqual(fields.key_var.get(), "a")
        self.assertFalse(fields.recording)
        self.assertTrue(self.ime_open)

        fields.start_recording()
        acquire_focus(self.app, dialog)
        dialog.event_generate("<Escape>")
        dialog.update()
        self.assertFalse(fields.recording)
        self.assertTrue(self.ime_open)

        fields.start_recording()
        fields.sync_target()
        self.assertTrue(self.ime_open)
        fields.start_recording()
        dialog.destroy()
        self.assertTrue(self.ime_open)

    def test_action_and_key_hold_recording_overlap_restores_ime(self):
        dialog = ActionDialog(self.app, "Action")
        dialog._start_recording()
        dialog.key_hold_fields.start_recording()
        self.assertFalse(self.ime_open)
        dialog._stop_recording()
        self.assertFalse(dialog.key_hold_fields.recording)
        self.assertTrue(self.ime_open)
        dialog.destroy()

    def test_keyboard_window_capture_is_idempotent_and_restores_ime(self):
        window = KeyboardWindow(self.app)
        get_open = self.tracker._get_open
        with patch.object(self.tracker, "_get_open", wraps=get_open) as get_status:
            window._begin_edit("a")
            self.assertFalse(self.ime_open)
            first_call_count = get_status.call_count
            window._begin_edit("b")
            self.assertEqual(get_status.call_count, first_call_count)
            self.assertEqual(window._editing_source_key, "b")

        with patch.object(window, "_normalize_tk_key", return_value="??"):
            self.assertEqual(window._on_key_press(self._key("a")), "break")
        self.assertEqual(window._editing_source_key, "b")
        acquire_focus(self.app, window)
        window.event_generate("<Escape>")
        window.update()
        self.assertIsNone(window._editing_source_key)
        self.assertTrue(self.ime_open)

        window._begin_edit("a")
        window._key_bounds = [("b", 0, 0, 20, 20)]
        window._on_canvas_right_click(SimpleNamespace(x=5, y=5))
        self.assertTrue(self.ime_open)
        window._begin_edit("a")
        window._handle_close()
        self.assertTrue(self.ime_open)

        window = KeyboardWindow(self.app)
        window._begin_edit("a")
        window.destroy()
        self.assertTrue(self.ime_open)

    def test_grid_editor_capture_restores_ime_and_ignores_unresolved_key(self):
        monitor = MonitorInfo("primary", (0, 0, 100, 100), True)
        window = GridEditorWindow(
            self.app, grid=None, monitors=[monitor], start_monitor_id="primary",
            reserved=set(), key_name_from_event=lambda _event: "??",
        )
        self.assertFalse(self.ime_open)
        original_layout = window.layout
        original_ops = dict(window.ops)
        original_sub_keys = window.panel.sub_key_rows()
        self.assertEqual(window.on_key(self._key("a")), "break")
        self.assertEqual(window.layout, original_layout)
        self.assertEqual(window.ops, original_ops)
        self.assertEqual(window.panel.sub_key_rows(), original_sub_keys)
        window.destroy()
        self.assertTrue(self.ime_open)

        window = GridEditorWindow(
            self.app, grid=None, monitors=[monitor], start_monitor_id="primary",
            reserved=set(),
        )
        self.assertFalse(self.ime_open)
        # Esc は選択の解除が先で、何も選んでいなければ閉じる（段階式）
        for _ in range(4):
            if not window.winfo_exists():
                break
            window.on_escape()
        self.assertFalse(window.winfo_exists())
        self.assertTrue(self.ime_open)


if __name__ == "__main__":
    unittest.main()
