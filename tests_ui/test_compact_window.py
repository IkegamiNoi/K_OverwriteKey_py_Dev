"""UI coverage for compact-window sizing and fixed status rows."""

import tkinter as tk
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.compact_window_size import COMPACT_WINDOW_SIZE_KEY
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height


def _trigger(key, values):
    return {
        "key": key,
        "label": key,
        "actions": [{"type": "text", "value": value} for value in values],
    }


class CompactWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
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
            side_effect=AssertionError("unexpected keymap history save"),
        ))
        try:
            cls.app = App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update_idletasks()

    @classmethod
    def _destroy_app(cls):
        cls.app.compact_window.cancel_save()
        cls.app.destroy()

    def setUp(self):
        self.app = type(self).app
        self.controller = self.app.compact_window
        if self.app._compact_mode:
            self.app.show_full_view()
        self.controller.cancel_save()
        self.saved = {
            "geometry": self.app.geometry(),
            "minsize": self.app.wm_minsize(),
            "startup": dict(self.app._startup_settings),
            "full_geometry": self.app._full_geometry,
            "font_delta": self.app._ui_font_delta_pt,
            "keymap_set_path": self.app.keymap_set_path,
            "sequence_open": self.app.compact_sequence.is_open,
            "call_open": self.app.call_view.hosts["compact"].is_open,
            "status": self.app.ui_vars.status_var.get(),
            "file": self.app.ui_vars.file_status_var.get(),
            "flash": self.app.ui_vars.flash_message_var.get(),
            "flash_message": self.app._flash_message,
        }
        self.addCleanup(self._restore)
        self.app._startup_settings = {}
        if self.app.compact_sequence.is_open:
            self.app.compact_sequence.on_heading_click()
        if self.app.call_view.hosts["compact"].is_open:
            self.app.call_view.on_heading_click()
        self.app.data = self.app.config_service.normalize_runtime_data({
            "triggers": [],
            "keymaps": [{
                "id": "km1", "label": "Main", "mappings": {"a": "b"},
                "triggers": [_trigger("f1", ["first", "second"])],
            }],
            "active_keymap_id": "km1",
        })
        self.app._selected_trigger_idx = 0
        self.app.state.reset_indices()
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()
        self.app.trigger_panel.update_status()
        self.app.update()

    def _restore(self):
        self.controller.cancel_save()
        if self.app._compact_mode:
            self.app.show_full_view()
        self.app._startup_settings = self.saved["startup"]
        self.app._full_geometry = self.saved["full_geometry"]
        self.app._apply_font_delta(self.saved["font_delta"])
        self.app.keymap_set_path = self.saved["keymap_set_path"]
        if self.saved["sequence_open"] != self.app.compact_sequence.is_open:
            self.app.compact_sequence.on_heading_click()
        if self.saved["call_open"] != self.app.call_view.hosts["compact"].is_open:
            self.app.call_view.on_heading_click()
        self.app.ui_vars.status_var.set(self.saved["status"])
        self.app.ui_vars.file_status_var.set(self.saved["file"])
        self.app._flash_message = self.saved["flash_message"]
        self.app.ui_vars.flash_message_var.set(self.saved["flash"])
        self.app.minsize(*self.saved["minsize"])
        self.app.geometry(self.saved["geometry"])
        self.app.update()

    def _enter_compact(self):
        self.app.show_compact_view()
        self.app.update()

    def _wait_for_save_delay(self):
        # Tk の after を回して実際の 500ms 予約を消化する。
        self.app.after(600, self.app.quit)
        self.app.mainloop()

    def _resize(self, width, height):
        self.app.geometry(f"{width}x{height}")
        self.app.update()

    def test_default_and_saved_sizes_apply_across_view_round_trip(self):
        old_height = self.app.winfo_height()
        self._enter_compact()
        self.assertAlmostEqual(self.app.winfo_width(), 270, delta=8)
        expected_height = max(
            self.controller.minimum_height,
            min(max(360, old_height), self.app.winfo_screenheight()),
        )
        self.assertAlmostEqual(self.app.winfo_height(), expected_height, delta=8)

        self.app.show_full_view()
        self.app._startup_settings[COMPACT_WINDOW_SIZE_KEY] = {"width": 390, "height": 720}
        self._enter_compact()
        expected_width = min(390, self.app.winfo_screenwidth())
        expected_height = max(
            self.controller.minimum_height, min(720, self.app.winfo_screenheight()),
        )
        self.assertAlmostEqual(self.app.winfo_width(), expected_width, delta=8)
        self.assertAlmostEqual(self.app.winfo_height(), expected_height, delta=8)
        self.app.show_full_view()
        self._enter_compact()
        self.assertAlmostEqual(self.app.winfo_width(), expected_width, delta=8)
        self.assertAlmostEqual(self.app.winfo_height(), expected_height, delta=8)

    def test_compact_resize_is_saved_after_quiet_period_once(self):
        self._enter_compact()
        self.app.startup_io.write_startup.reset_mock()
        before = self.app.winfo_width(), self.app.winfo_height()
        self._resize(before[0] + 70, before[1] + 80)
        first_reservation = self.controller._save_id
        self.app.startup_io.write_startup.assert_not_called()
        self._resize(self.app.winfo_width() + 30, self.app.winfo_height() + 20)
        expected = self.app.winfo_width(), self.app.winfo_height()
        self.assertIsNotNone(self.controller._save_id)
        self.assertNotEqual(self.controller._save_id, first_reservation)
        self.app.startup_io.write_startup.assert_not_called()
        self._wait_for_save_delay()
        self.app.startup_io.write_startup.assert_called_once_with({
            COMPACT_WINDOW_SIZE_KEY: {"width": expected[0], "height": expected[1]},
        })
        self.assertIsNone(self.controller._save_id)

    def test_automatic_full_view_and_maximized_sizes_are_not_saved(self):
        self._enter_compact()
        self.app.startup_io.write_startup.reset_mock()
        self._wait_for_save_delay()
        self.app.startup_io.write_startup.assert_not_called()

        self._resize(self.app.winfo_width() + 45, self.app.winfo_height() + 45)
        same_width, same_height = self.app.winfo_width(), self.app.winfo_height()
        self.app._startup_settings[COMPACT_WINDOW_SIZE_KEY] = {
            "width": same_width, "height": same_height,
        }
        self._wait_for_save_delay()
        self.app.startup_io.write_startup.assert_not_called()

        self._resize(same_width + 60, same_height + 60)
        with patch.object(self.app, "wm_state", return_value="zoomed"):
            self._wait_for_save_delay()
        self.app.startup_io.write_startup.assert_not_called()

        self._resize(same_width + 90, same_height + 90)
        self.assertIsNotNone(self.controller._save_id)
        self.app.show_full_view()
        self.assertIsNone(self.controller._save_id)
        self._wait_for_save_delay()
        self._resize(self.app.winfo_width() + 60, self.app.winfo_height() + 60)
        self._wait_for_save_delay()
        self.assertFalse(any(
            COMPACT_WINDOW_SIZE_KEY in call.args[0]
            for call in self.app.startup_io.write_startup.call_args_list
        ))

    def test_minimum_height_keeps_status_header_and_both_headings_visible(self):
        self._enter_compact()
        minimum = self.controller.minimum_height
        self.assertEqual(self.app.wm_minsize()[1], minimum)
        self._resize(self.app.winfo_width(), max(1, minimum - 80))
        self.assertGreaterEqual(self.app.winfo_height(), minimum - 4)
        self.assertTrue(self._labels_for(self.app.ui_vars.status_var))
        self.assertTrue(self._labels_for(self.app.ui_vars.file_status_var))

        widgets = [
            self.app.compact_view.header_area,
            self.app.compact_view.trigger_box,
            self.app.compact_view.trigger_box.sequence_frame.heading,
            self.app.compact_view.trigger_box.call_view_frame.heading,
            *self._labels_for(self.app.ui_vars.status_var),
            *self._labels_for(self.app.ui_vars.file_status_var),
        ]
        for widget in widgets:
            with self.subTest(widget=str(widget)):
                self.assertTrue(widget.winfo_ismapped())
                top = widget.winfo_rooty() - self.app.winfo_rooty()
                self.assertGreaterEqual(top, 0)
                self.assertGreaterEqual(
                    self.app.winfo_height() - (top + widget.winfo_height()), -4,
                )

        for toggle in (
            self.app.compact_sequence.on_heading_click,
            self.app.call_view.on_heading_click,
        ):
            toggle()
            self.app.update()
            self.assertEqual(self.app.wm_minsize()[1], minimum)

        self.app.compact_sequence.on_heading_click()
        self.app.call_view.on_heading_click()
        self.app.update()
        # 両方閉じると境界は無く、閉じたシーケンスの見出しはトリガー一覧の欄の下端にある。
        box = self.app.compact_view.trigger_box
        self.assertEqual(len(box.trigger_panes.panes()), 1)
        # 唯一の欄なので実寸が入る。見出しの実寸を除いた分が一覧の欄の高さ。
        trigger_height = (
            box.trigger_frame.winfo_height() - box.sequence_frame.heading.winfo_height()
        )
        self.assertGreaterEqual(
            trigger_height,
            list_minimum_height(self.app.compact_view.trigger_box.trigger_list),
        )

    def test_full_view_restores_its_existing_minimum(self):
        self._enter_compact()
        self.app.show_full_view()
        self.app.update()
        self.assertFalse(self.app._compact_mode)
        self.assertEqual(self.app.wm_minsize()[1], self.app.pane_layout.window_min_height)

    def test_status_text_is_flattened_only_while_compact(self):
        self.app.data = self.app.config_service.normalize_runtime_data({
            "triggers": [],
            "keymaps": [{
                "id": "km1", "label": "Main", "mappings": {"a": "b"},
                "triggers": [_trigger("f1", ["next\nline", "other"])],
            }],
            "active_keymap_id": "km1",
        })
        self.app._selected_trigger_idx = 0
        self.app._indices["f1"] = 0
        self.app.trigger_panel.refresh_triggers()
        with patch.object(self.app.keymap_panel, "get_active_keymap_text", return_value="map\nlabel"), \
                patch.object(self.app, "keymap_set_path", "file\nstate"):
            self.app._update_file_status()
            self.app._set_flash_message("first\nsecond", auto_clear=False)
            self._enter_compact()
            self.app.trigger_panel.update_status()
            self.assertEqual(self.app.ui_vars.status_var.get().count("\n"), 1)
            self.assertEqual(self.app.ui_vars.flash_message_var.get(), "first second")
            self.assertIn("file state", self.app.ui_vars.file_status_var.get())
            self.assertEqual(self.app.ui_vars.file_status_var.get().count("\n"), 0)

            self.app.show_full_view()
            self.app.update()
            self.assertEqual(self.app.ui_vars.status_var.get().count("\n"), 1)
            self.assertEqual(self.app.ui_vars.flash_message_var.get(), "first\nsecond")
            self.assertIn("\n", self.app.ui_vars.file_status_var.get())

    def test_destroy_cancels_pending_size_save(self):
        app = App()
        try:
            app.update()
            app.show_compact_view()
            app.update()
            app.geometry(f"{app.winfo_width() + 50}x{app.winfo_height() + 50}")
            app.update()
            pending = app.compact_window._save_id
            self.assertIsNotNone(pending)
            app.destroy()
            self.assertIsNone(app.compact_window._save_id)
        finally:
            try:
                if app.winfo_exists():
                    app.destroy()
            except tk.TclError:
                pass

    def test_font_growth_to_minimum_is_treated_as_automatic_size(self):
        self._enter_compact()
        normal_minimum = self.controller.minimum_height
        self._resize(self.app.winfo_width(), normal_minimum)
        self.app.startup_io.write_startup.reset_mock()
        self.app._apply_font_delta(3)
        self.app.update()
        self.assertGreater(self.controller.minimum_height, normal_minimum)
        self.assertGreaterEqual(self.app.winfo_height(), self.controller.minimum_height - 4)
        self._wait_for_save_delay()
        for call in self.app.startup_io.write_startup.call_args_list:
            self.assertNotIn(COMPACT_WINDOW_SIZE_KEY, call.args[0])

    @staticmethod
    def _labels_for(variable):
        target = str(variable)
        found = []

        def visit(widget):
            for child in widget.winfo_children():
                try:
                    if str(child.cget("textvariable")) == target:
                        found.append(child)
                except tk.TclError:
                    pass
                visit(child)

        visit(variable._root)
        return found


if __name__ == "__main__":
    unittest.main()
