"""UI coverage for truncated status labels and their original multiline text."""

import tkinter as tk
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


class StatusTooltipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        # App の破棄・遅延保存まで実 config/ への書き込みを遮断する。
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(app_module, "load_startup_settings", return_value={}))
        stack.enter_context(patch.object(StartupIo, "load_startup_and_config"))
        stack.enter_context(patch.object(StartupIo, "write_startup", return_value=True))
        stack.enter_context(patch.object(
            ConfigService, "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        stack.enter_context(patch.object(
            ConfigService, "save_keymap_set_history",
            side_effect=AssertionError("unexpected history save"),
        ))
        try:
            cls.app = app_module.App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update()

    @classmethod
    def _destroy_app(cls):
        cls.app.pane_layout.cancel_window_width_save()
        cls.app.compact_window.cancel_save()
        cls.app.destroy()

    def setUp(self):
        self.app = type(self).app
        self.app.show_full_view()
        self.app._clear_flash_message()
        self.app.keymap_set_path = "status.json"
        self.app.data = self.app.config_service.normalize_runtime_data({
            "triggers": [],
            "keymaps": [{
                "id": "km1", "label": "Main", "mappings": {"a": "b"},
                "triggers": [{
                    "key": "f1", "label": "f1",
                    "actions": [{"type": "text", "value": "first\nsecond"}],
                }],
            }],
            "active_keymap_id": "km1",
        })
        self.app._selected_trigger_idx = 0
        self.app.state.reset_indices()
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()
        self.app.trigger_panel.update_status()
        self.app._refresh_status_bar()
        self.app.update()

    def tearDown(self):
        for popup in self._popups():
            popup.destroy()
        self.app._clear_flash_message()
        self.app.compact_window.cancel_save()
        self.app.pane_layout.cancel_window_width_save()
        self.app.update()

    def _labels(self):
        result = {}

        def visit(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Toplevel):
                    continue
                try:
                    variable = str(child.cget("textvariable"))
                    for name in ("status", "file_status", "flash_message"):
                        if variable == str(getattr(self.app.ui_vars, f"{name}_var")):
                            result[name] = child
                except tk.TclError:
                    pass
                visit(child)

        visit(self.app)
        self.assertEqual(set(result), {"status", "file_status", "flash_message"})
        return result

    def _popups(self):
        found = []

        def visit(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Toplevel):
                    found.append(child)
                else:
                    visit(child)

        visit(self.app)
        return found

    def _hover(self, label):
        label.event_generate("<Enter>", rootx=10, rooty=10)
        self.app.update()

    def _popup_text(self):
        popups = self._popups()
        self.assertEqual(len(popups), 1)
        return str(popups[0].winfo_children()[0].cget("text"))

    def _resize(self, width):
        self.app.geometry(f"{width}x{self.app.winfo_height()}")
        self.app.update()

    def _enter_compact(self):
        self.app.show_compact_view()
        self.app.update()

    def test_full_status_is_shown_only_when_truncated_and_leave_destroys_popup(self):
        with patch.object(self.app.keymap_panel, "get_active_keymap_text",
                          return_value="long map " * 40):
            self.app.trigger_panel.update_status()
        self._resize(780)
        label = self._labels()["status"]
        self.assertGreater(label.winfo_reqwidth(), label.winfo_width())
        self._hover(label)
        self.assertEqual(self._popup_text(), self.app.ui_vars.status_var.get())
        self.assertEqual(self.app.ui_vars.status_full_var.get(), self.app.ui_vars.status_var.get())
        popup = self._popups()[0]
        label.event_generate("<Leave>")
        self.app.update()
        self.assertFalse(popup.winfo_exists())
        self.assertEqual(self._popups(), [])

    def test_untruncated_status_does_not_show_popup(self):
        self.app.ui_vars.status_var.set("OK")
        self.app.ui_vars.status_full_var.set("OK")
        self.app.update()
        label = self._labels()["status"]
        self.assertGreater(label.winfo_width(), 1)
        self.assertLessEqual(label.winfo_reqwidth(), label.winfo_width())
        self._hover(label)
        self.assertEqual(self._popups(), [])

    def test_compact_status_keeps_original_line_breaks_and_tracks_next_action(self):
        self._enter_compact()
        with patch.object(self.app.keymap_panel, "get_active_keymap_text",
                          return_value="map\n" + "label " * 35):
            self.app.trigger_panel.update_status()
        self.app.update()
        displayed = self.app.ui_vars.status_var.get()
        original = self.app.ui_vars.status_full_var.get()
        self.assertEqual(displayed.count("\n"), 1)
        self.assertIn("first second", displayed)
        self.assertIn("map\n", original)
        self.assertIn("first\nsecond", original)
        label = self._labels()["status"]
        self.assertGreater(label.winfo_reqwidth(), label.winfo_width())
        self._hover(label)
        self.assertEqual(self._popup_text(), original)
        popup = self._popups()[0]
        with patch.object(self.app.trigger_panel, "get_next_action_summary",
                          return_value="changed\n" + "next " * 40), \
                patch.object(self.app.keymap_panel, "get_active_keymap_text", return_value="map"):
            self.app.trigger_panel.update_status()
        self.app.update()
        self.assertIs(self._popups()[0], popup)
        self.assertIn("changed\n", self._popup_text())

    def test_flash_message_preserves_newlines_refreshes_and_closes_when_empty(self):
        for compact in (False, True):
            with self.subTest(compact=compact):
                if compact:
                    self._enter_compact()
                self.app._set_flash_message("first " * 40 + "\nsecond", auto_clear=False)
                self.app.update()
                label = self._labels()["flash_message"]
                self.assertGreater(label.winfo_reqwidth(), label.winfo_width())
                self._hover(label)
                self.assertEqual(self._popup_text(), self.app._flash_message)
                if compact:
                    self.assertNotIn("\n", self.app.ui_vars.flash_message_var.get())
                popup = self._popups()[0]
                self.app._set_flash_message("changed " * 40 + "\nlatest", auto_clear=False)
                self.app.update()
                self.assertIs(self._popups()[0], popup)
                self.assertEqual(self._popup_text(), self.app._flash_message)
                self.app._clear_flash_message()
                self.app.update()
                self.assertEqual(self.app.ui_vars.flash_message_full_var.get(), "")
                self.assertFalse(popup.winfo_exists())
                self.assertEqual(self._popups(), [])

    def test_widening_window_closes_open_status_tooltip(self):
        self._enter_compact()
        self._resize(270)
        with patch.object(self.app.keymap_panel, "get_active_keymap_text", return_value="Main " * 10):
            self.app.trigger_panel.update_status()
        self.app.update()
        label = self._labels()["status"]
        self.assertGreater(label.winfo_reqwidth(), label.winfo_width())
        self._hover(label)
        popup = self._popups()[0]
        self._resize(label.winfo_reqwidth() + 200)
        self.assertLessEqual(label.winfo_reqwidth(), label.winfo_width())
        self.assertFalse(popup.winfo_exists())
        self.assertEqual(self._popups(), [])

    def test_full_text_write_refreshes_and_display_write_closes_tooltip(self):
        self._enter_compact()
        self.app.ui_vars.status_full_var.set("original\ntext")
        self.app.ui_vars.status_var.set("long " * 40)
        self.app.update()
        label = self._labels()["status"]
        self._hover(label)
        self.assertEqual(self._popup_text(), "original\ntext")
        popup = self._popups()[0]
        self.app.ui_vars.status_full_var.set("updated\ntext")
        self.app.update()
        self.assertIs(self._popups()[0], popup)
        self.assertEqual(self._popup_text(), "updated\ntext")
        self.app.ui_vars.status_var.set("OK")
        self.app.update()
        self.assertEqual(self._popups(), [])

    def test_font_change_closes_tooltip_when_text_fits(self):
        self._enter_compact()
        self.app.ui_vars.status_full_var.set("W" * 40)
        self.app.ui_vars.status_var.set("W" * 40)
        label = self._labels()["status"]
        original_font = label.cget("font")
        try:
            label.configure(font=("Arial", 20))
            self.app.update()
            self.assertGreater(label.winfo_reqwidth(), label.winfo_width())
            self._hover(label)
            self.assertEqual(self._popup_text(), "W" * 40)
            label.configure(font=("Arial", 1))
            self.app.update()
            self.assertLessEqual(label.winfo_reqwidth(), label.winfo_width())
            self.assertEqual(self._popups(), [])
        finally:
            label.configure(font=original_font)
            self.app.update()

    def test_file_status_preserves_original_text_in_both_views(self):
        for compact in (False, True):
            with self.subTest(compact=compact):
                if compact:
                    self._enter_compact()
                self.app.keymap_set_path = "file " * 60 + "\nstate.json"
                self.app._update_file_status()
                self.app.update()
                label = self._labels()["file_status"]
                self.assertGreater(label.winfo_reqwidth(), label.winfo_width())
                self._hover(label)
                self.assertEqual(self._popup_text(), self.app.ui_vars.file_status_full_var.get())
                self.assertIn("\nstate.json", self._popup_text())
                if compact:
                    self.assertNotIn("\n", self.app.ui_vars.file_status_var.get())
                label.event_generate("<Leave>")
                self.app.update()
                self.assertEqual(self._popups(), [])


if __name__ == "__main__":
    unittest.main()
