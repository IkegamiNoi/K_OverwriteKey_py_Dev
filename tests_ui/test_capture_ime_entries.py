import unittest
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation import app as app_module
from keyseq.presentation import key_capture_ime
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs.keymap_edit_dialog import KeymapEditDialog
from keyseq.presentation.dialogs.keymap_switch_batch_dialog import KeymapSwitchBatchDialog
from keyseq.presentation.dialogs.trigger_dialog import TriggerDialog
from keyseq.presentation.hook_button_texts import UNKNOWN_CAPTURE_KEY_HINT_TEXT
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


if __name__ == "__main__":
    unittest.main()
