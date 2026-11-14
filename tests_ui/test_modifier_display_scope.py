"""macOS modifier names are confined to display values."""

import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.domain.config import HOOK_STOP_KEY
from keyseq.domain.key_symbols import set_modifier_display_names
from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs import KeymapEditDialog, KeymapSwitchBatchDialog
from keyseq.presentation.keyboard_window import KeyboardWindow
from keyseq.presentation.ui_vars import UiVars
from keyseq.shared.i18n import fix_language

fix_language("ja")


class ModifierDisplayScopeUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = App()

    def setUp(self):
        self._data_snapshot = copy.deepcopy(self.app.data)
        self._stop_capture_state = (
            self.app.stop_key_capture.capturing,
            self.app.stop_key_capture._conflict_checks,
        )
        self._saved_stop_key = self.app.ui_vars.stop_key_var.get()
        self._saved_toggle_key = self.app.ui_vars.toggle_key_var.get()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def tearDown(self):
        set_modifier_display_names({})
        self.app.data = self._data_snapshot
        self.app.stop_key_capture.capturing, self.app.stop_key_capture._conflict_checks = (
            self._stop_capture_state
        )
        self.app.ui_vars.stop_key_var.set(self._saved_stop_key)
        self.app.ui_vars.toggle_key_var.set(self._saved_toggle_key)

    def test_keymap_list_formats_switch_key_but_keeps_empty_marker(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        self.app.data["keymaps"] = [{"id": "km1", "label": "Main", "mappings": {}, "triggers": []}]
        self.app.data["active_keymap_id"] = "km1"
        self.app.data["keymap_switch_keys"] = {"windows+c": "km1"}
        overlap = SimpleNamespace(keymap_switch_conflict=Mock(return_value=None))

        entry = self.app.keymap_panel.format_keymap_list_entry(
            0, {"id": "km1", "label": "Main"}, overlap,
        )
        self.assertIn("Command+c", entry)
        overlap.keymap_switch_conflict.assert_called_once_with("km1", "windows+c")

        self.app.data["keymap_switch_keys"] = {}
        empty_entry = self.app.keymap_panel.format_keymap_list_entry(
            0, {"id": "km1", "label": "Main"}, overlap,
        )
        self.assertIn("-", empty_entry)

        set_modifier_display_names({})
        self.app.data["keymap_switch_keys"] = {"windows+c": "km1"}
        unchanged_entry = self.app.keymap_panel.format_keymap_list_entry(
            0, {"id": "km1", "label": "Main"}, overlap,
        )
        self.assertIn("windows+c", unchanged_entry)

    def test_hook_capture_updates_display_var_without_changing_saved_key(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        self.app.data["hook_keys_individual"] = True
        self.app.data[HOOK_STOP_KEY] = "left windows"
        self.app.data["hook_toggle_key"] = "right alt"
        initial_vars = UiVars(self.app, 0)
        self.assertEqual(initial_vars.stop_key_var.get(), "left windows")
        self.assertEqual(initial_vars.stop_key_display_var.get(), "left Command")
        self.assertEqual(initial_vars.toggle_key_var.get(), "right alt")
        self.assertEqual(initial_vars.toggle_key_display_var.get(), "right Option")

        self.app.data[HOOK_STOP_KEY] = "f12"
        self.app.ui_vars.stop_key_var.set("f12")
        self.app.ui_vars.toggle_key_var.set("right alt")

        self.assertEqual(self.app.ui_vars.stop_key_display_var.get(), "f12")
        self.assertEqual(self.app.ui_vars.toggle_key_display_var.get(), "right Option")
        for view in (self.app.full_view, self.app.compact_view):
            self.assertEqual(
                str(view.hook_frame.stop_key_entry.cget("textvariable")),
                str(self.app.ui_vars.stop_key_display_var),
            )
            self.assertEqual(
                str(view.hook_frame.toggle_key_entry.cget("textvariable")),
                str(self.app.ui_vars.toggle_key_display_var),
            )

        self.assertTrue(self.app.stop_key_capture._apply_key("left windows"))

        self.assertEqual(self.app.data[HOOK_STOP_KEY], "left windows")
        self.assertEqual(self.app.ui_vars.stop_key_var.get(), "left windows")
        self.assertEqual(self.app.ui_vars.stop_key_display_var.get(), "left Command")

        set_modifier_display_names({})
        self.app.ui_vars.stop_key_var.set("left windows")
        self.app.ui_vars.toggle_key_var.set("right alt")
        self.assertEqual(self.app.ui_vars.stop_key_display_var.get(), "left windows")
        self.assertEqual(self.app.ui_vars.toggle_key_display_var.get(), "right alt")

    def test_capture_duplicate_message_displays_modifier_name_in_japanese(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        capture = self.app.stop_key_capture
        capture.capturing = True
        capture._conflict_checks = [(lambda _app, _key: True, "停止キー")]

        with patch("keyseq.presentation.controllers.key_capture.messagebox.showerror") as showerror:
            capture._record_key("left windows")

        self.assertIn("left Command", showerror.call_args.args[1])
        self.assertNotIn("left windows", showerror.call_args.args[1])

    def test_prohibited_switch_key_message_displays_modifier_name_in_japanese(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror"
        ) as showerror:
            accepted = self.app.keymap_panel.validate_keymap_switch_assignment(
                "windows", target_id="km1",
            )

        self.assertFalse(accepted)
        self.assertIn("Command", showerror.call_args.args[1])
        self.assertNotIn("windows", showerror.call_args.args[1])

    def test_keyboard_window_title_displays_modifier_name_without_changing_edit_key(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        keyboard = SimpleNamespace(
            _layout=SimpleNamespace(display_name="US"),
            _editing_source_key="left windows",
            title=Mock(),
        )

        KeyboardWindow._update_title(keyboard)

        self.assertIn("left Command", keyboard.title.call_args.args[0])
        self.assertEqual(keyboard._editing_source_key, "left windows")

    def test_keymap_edit_dialog_shows_display_name_and_returns_saved_key(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        with patch.object(self.app.hook, "suspend_hook_for_dialog"), patch(
            "keyseq.presentation.dialogs.keymap_edit_dialog.grab_modal"
        ):
            dialog = KeymapEditDialog(self.app, "Edit", initial_key="left windows")
        self.addCleanup(lambda: dialog.destroy() if dialog.winfo_exists() else None)

        self.assertEqual(dialog.key_var.get(), "left windows")
        self.assertEqual(dialog.key_display_var.get(), "left Command")
        self.assertEqual(str(dialog.key_entry.cget("textvariable")), str(dialog.key_display_var))
        dialog.key_var.set("right alt")
        self.assertEqual(dialog.key_display_var.get(), "right Option")
        dialog._ok()
        self.assertEqual(dialog.result["key"], "right alt")

    def test_keymap_switch_batch_rows_have_independent_display_and_saved_values(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        rows = [
            ("Map", "First", "One", "left windows"),
            ("Map", "Second", "Two", "right alt"),
        ]
        with patch.object(self.app.hook, "suspend_hook_for_dialog"), patch(
            "keyseq.presentation.dialogs.keymap_switch_batch_dialog.grab_modal"
        ):
            dialog = KeymapSwitchBatchDialog(self.app, "Batch", rows, validate=lambda _values: None)
        self.addCleanup(lambda: dialog.destroy() if dialog.winfo_exists() else None)

        self.assertEqual([var.get() for var in dialog.key_vars], ["left windows", "right alt"])
        self.assertEqual([var.get() for var in dialog.key_display_vars], ["left Command", "right Option"])
        self.assertEqual(
            [str(entry.cget("textvariable")) for entry in dialog.key_entries],
            [str(var) for var in dialog.key_display_vars],
        )
        dialog.key_vars[0].set("left alt")
        self.assertEqual([var.get() for var in dialog.key_display_vars], ["left Option", "right Option"])
        dialog._ok()
        self.assertEqual([row["key"] for row in dialog.result], ["left alt", "right alt"])


if __name__ == "__main__":
    unittest.main()
