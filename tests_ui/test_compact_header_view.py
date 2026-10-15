"""UI coverage for the compact view header expanders."""

import tkinter as tk
import time
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.compact_header_view import COMPACT_HEADER_VIEW_KEY
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.hook_button_texts import HOOK_START_TEXT, HOOK_STOP_TEXT
from tests_ui.escape_delivery import acquire_focus


class CompactHeaderViewTest(unittest.TestCase):
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
        if self.app._compact_mode:
            self.app.show_full_view()
        self.app.compact_window.cancel_save()
        self.saved = {
            "geometry": self.app.geometry(),
            "minsize": self.app.wm_minsize(),
            "startup": dict(self.app._startup_settings),
            "open": dict(self.app.compact_header.open),
        }
        self.addCleanup(self._restore)
        self.app._startup_settings = {}
        for name in ("hook", "display"):
            if not self.app.compact_header.open[name]:
                self.app.compact_header.toggle(name)
        self.app.show_compact_view()
        self.app.update()

    def _restore(self):
        self.app.compact_window.cancel_save()
        if self.app._compact_mode:
            self.app.show_full_view()
        self.app._startup_settings = self.saved["startup"]
        for name in ("hook", "display"):
            if self.app.compact_header.open[name] != self.saved["open"][name]:
                self.app.compact_header.toggle(name)
        self.app.minsize(*self.saved["minsize"])
        self.app.geometry(self.saved["geometry"])
        self.app.update()

    def test_default_sections_are_open_with_clickable_expander_headings(self):
        view = self.app.compact_view
        self.assertEqual(view.hook_frame.heading.cget("text"), "▾ フック")
        self.assertEqual(view.display_frame.heading.cget("text"), "▾ 表示")
        self.assertEqual(view.hook_frame.cget("text"), "")
        self.assertEqual(view.display_frame.cget("text"), "")

    def test_return_on_collapsed_display_heading_opens_and_keeps_focus(self):
        app = self.app
        view = app.compact_view
        app.compact_header.toggle("display")
        app.update()
        acquire_focus(app, view.display_heading)

        with patch.object(app.startup_io, "write_startup", return_value=True) as write:
            view.display_heading.event_generate("<Return>")
            app.update()

        self.assertTrue(app.compact_header.open["display"])
        self._assert_focus(app, view.display_frame.heading)
        write.assert_called_once_with({
            COMPACT_HEADER_VIEW_KEY: {"hook": True, "display": True},
        })

    def test_space_on_open_hook_heading_closes_and_keeps_focus_on_collapsed_heading(self):
        app = self.app
        view = app.compact_view
        acquire_focus(app, view.hook_frame.heading)

        view.hook_frame.heading.event_generate("<space>")
        app.update()

        self.assertFalse(app.compact_header.open["hook"])
        self.assertEqual(view.hook_heading.cget("text"), "▸ フック")
        self._assert_focus(app, view.hook_heading)

    def _assert_focus(self, app, expected):
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and app.focus_get() is not expected:
            app.update()
            time.sleep(0.001)
        self.assertIs(app.focus_get(), expected)

    def test_both_open_and_collapsed_headings_accept_tab_focus(self):
        view = self.app.compact_view
        for heading in (
            view.hook_frame.heading,
            view.hook_heading,
            view.display_frame.heading,
            view.display_heading,
        ):
            with self.subTest(heading=heading):
                self.assertTrue(heading.cget("takefocus"))

    def test_closing_hook_keeps_order_and_window_size_and_grows_trigger_list(self):
        app = self.app
        view = app.compact_view
        app.update_idletasks()
        geometry = app.geometry()
        size = app.winfo_width(), app.winfo_height()
        open_list_height = view.trigger_box.trigger_list.winfo_height()

        view.hook_frame.heading.event_generate("<Button-1>")
        app.update()

        self.assertEqual(view.hook_heading.cget("text"), "▸ フック")
        self.assertIn(view.hook_heading, view.header_area.pack_slaves())
        self.assertNotIn(view.hook_frame, view.header_area.pack_slaves())
        self.assertIn(view.display_frame, view.header_area.pack_slaves())
        self.assertLess(
            view.header_area.pack_slaves().index(view.hook_heading),
            view.header_area.pack_slaves().index(view.display_frame),
        )
        self.assertEqual((app.winfo_width(), app.winfo_height()), size)
        self.assertEqual(app.geometry(), geometry)
        self.assertGreater(view.trigger_box.trigger_list.winfo_height(), open_list_height)

    def test_each_toggle_writes_both_current_values_once(self):
        app = self.app
        app.compact_window.cancel_save()
        with patch.object(app.startup_io, "write_startup", return_value=True) as write:
            app.compact_header.toggle("hook")
            write.assert_called_once_with({
                COMPACT_HEADER_VIEW_KEY: {"hook": False, "display": True},
            })
            write.reset_mock()
            app.compact_header.toggle("display")
            write.assert_called_once_with({
                "compact_header_view": {"hook": False, "display": False},
            })

    def test_saved_invalid_section_value_starts_closed_without_saving(self):
        with patch.object(
            app_module, "load_startup_settings",
            return_value={COMPACT_HEADER_VIEW_KEY: {"hook": False, "display": "x"}},
        ), patch.object(StartupIo, "load_startup_and_config"), \
                patch.object(StartupIo, "write_startup", return_value=True) as write:
            app = App()
        try:
            self.assertFalse(app.compact_header.open["hook"])
            self.assertTrue(app.compact_header.open["display"])
            self.assertEqual(app.compact_view.hook_heading.cget("text"), "▸ フック")
            self.assertEqual(app.compact_view.display_frame.heading.cget("text"), "▾ 表示")
            write.assert_not_called()
        finally:
            app.destroy()

    def test_minimum_height_tracks_open_sections_and_expands_short_window(self):
        app = self.app
        app.update_idletasks()
        open_minimum = app.compact_window.minimum_height
        app.compact_header.toggle("hook")
        closed_minimum = app.compact_window.minimum_height
        self.assertLess(closed_minimum, open_minimum)
        app.compact_header.toggle("hook")
        self.assertEqual(app.compact_window.minimum_height, open_minimum)

        app.geometry(f"{app.winfo_width()}x{closed_minimum}")
        app.update_idletasks()
        app.compact_header.toggle("hook")
        self.assertGreaterEqual(app.winfo_height(), app.compact_window.minimum_height)

    def test_closing_section_moves_focus_to_trigger_list(self):
        app = self.app
        entry = app.compact_view.hook_frame.stop_key_entry
        acquire_focus(app, entry)
        app.compact_header.toggle("hook")
        expected = app.compact_view.trigger_box.trigger_list
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and app.focus_get() is not expected:
            app.update()
            time.sleep(0.001)
        self.assertIs(app.focus_get(), expected)

    def test_closing_display_keeps_its_collapsed_heading_after_hook_with_padding(self):
        view = self.app.compact_view
        self.app.compact_header.toggle("display")

        siblings = view.header_area.pack_slaves()
        self.assertLess(siblings.index(view.hook_frame), siblings.index(view.display_heading))
        self.assertEqual(view.display_heading.cget("text"), "▸ 表示")
        pady = view.display_heading.pack_info()["pady"]
        if isinstance(pady, str):
            pady = tuple(map(int, pady.split()))
        self.assertEqual(tuple(pady), (8, 0))

    def test_reopening_both_sections_restores_hook_then_display_order(self):
        app = self.app
        app.compact_header.toggle("hook")
        app.compact_header.toggle("display")
        app.compact_header.toggle("display")
        app.compact_header.toggle("hook")

        siblings = app.compact_view.header_area.pack_slaves()
        self.assertLess(siblings.index(app.compact_view.hook_frame), siblings.index(app.compact_view.display_frame))

    def test_focus_lookup_keyerror_still_closes_and_saves_once(self):
        app = self.app
        frame = app.compact_view.hook_frame
        with patch.object(frame, "focus_get", side_effect=KeyError("popdown")), \
                patch.object(
                    app.compact_window, "refresh_minimum_height", wraps=app.compact_window.refresh_minimum_height,
                ) as refresh, \
                patch.object(app.startup_io, "write_startup", return_value=True) as write:
            app.compact_header.toggle("hook")

        self.assertFalse(app.compact_header.open["hook"])
        self.assertIn(app.compact_view.hook_heading, app.compact_view.header_area.pack_slaves())
        write.assert_called_once_with({
            COMPACT_HEADER_VIEW_KEY: {"hook": False, "display": True},
        })
        refresh.assert_called_once_with()

    def test_hook_required_height_is_stable_across_close_and_reopen(self):
        app = self.app
        hook = app.compact_view.hook_frame
        app.update_idletasks()
        original_height = hook.winfo_reqheight()
        app.compact_header.toggle("hook")
        app.compact_header.toggle("hook")
        app.update_idletasks()

        self.assertEqual(hook.winfo_reqheight(), original_height)

    def test_hook_button_registration_survives_collapsing_its_frame(self):
        app = self.app
        hook = app.compact_view.hook_frame
        app.compact_header.toggle("hook")
        old_state = app.hook.hook_active
        self.addCleanup(setattr, app.hook, "hook_active", old_state)
        app.hook.hook_active = True
        app.hook.sync_hook_toggle_buttons()
        self.assertEqual(hook.hook_toggle_btn.cget("text"), HOOK_STOP_TEXT)
        app.hook.hook_active = False
        app.hook.sync_hook_toggle_buttons()
        self.assertEqual(hook.hook_toggle_btn.cget("text"), HOOK_START_TEXT)
