import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


class KeyboardWindowLeftRightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._patchers = [
            patch.object(StartupIo, "load_startup_and_config"),
            patch.object(StartupIo, "write_startup"),
            patch.object(KeymapSetIo, "save_keymap_set"),
            patch.object(KeymapSetIo, "save_keymap_set_to"),
        ]
        for patcher in cls._patchers:
            patcher.start()
        cls.app = App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        for patcher in reversed(cls._patchers):
            patcher.stop()

    def setUp(self):
        self.original_data = copy.deepcopy(self.app.data)
        self.app.layout.open_keyboard_window()
        self.window = self.app.layout.keyboard_window
        self.app.update()
        self.addCleanup(self._restore_data)
        self.addCleanup(self._close_keyboard_window)

    def _restore_data(self):
        self.app.data = self.original_data
        self.app.dirty_tracker.set_dirty(False)
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()

    def _close_keyboard_window(self):
        if self.app.layout.keyboard_window is not None:
            self.app.layout.keyboard_window._handle_close()

    def _active_mappings(self):
        keymap = self.app.keymap_service.get_active_keymap(self.app.data)
        return keymap["mappings"]

    def _set_mappings(self, mappings):
        self._active_mappings().clear()
        self._active_mappings().update(mappings)
        self.window.update_from_config(self.app.data)

    def _bounds_for(self, key):
        return next(bounds for bounds in self.window._key_bounds if bounds[0] == key)

    def _click_key(self, key, handler):
        _, x1, y1, x2, y2 = self._bounds_for(key)
        return handler(SimpleNamespace(x=(x1 + x2) / 2, y=(y1 + y2) / 2))

    def _canvas_text_in_key(self, key):
        _, x1, y1, x2, y2 = self._bounds_for(key)
        x, y = (x1 + x2) / 2, (y1 + y2) / 2
        return [
            self.window.canvas.itemcget(item, "text")
            for item in self.window.canvas.find_overlapping(x, y, x, y)
            if self.window.canvas.type(item) == "text"
        ]

    def test_modifier_bounds_use_distinct_left_and_right_names(self):
        keys = {key for key, *_ in self.window._key_bounds}
        for left, right in (
            ("ctrl", "right ctrl"),
            ("shift", "right shift"),
            ("alt", "right alt"),
            ("left windows", "right windows"),
        ):
            self.assertIn(left, keys)
            self.assertIn(right, keys)
        self.assertNotIn("windows", keys)

    def test_left_and_right_keymap_values_render_in_their_own_keys(self):
        self._set_mappings({"ctrl": "a", "right ctrl": "b"})

        self.assertEqual(self.window._display_map["ctrl"], "a")
        self.assertEqual(self.window._display_map["right ctrl"], "b")
        self.assertIn("a", self._canvas_text_in_key("ctrl"))
        self.assertIn("b", self._canvas_text_in_key("right ctrl"))

    def test_right_ctrl_edit_assigns_only_right_ctrl(self):
        self._set_mappings({"ctrl": "a"})
        self._click_key("right ctrl", self.window._on_canvas_left_click)

        self.assertEqual(self.window._editing_source_key, "right ctrl")
        self.assertIn("編集中: right ctrl", self.window.title())
        self.window._on_key_press(SimpleNamespace(keysym="b", keycode=None, state=0))

        self.assertEqual(self._active_mappings()["right ctrl"], "b")
        self.assertEqual(self._active_mappings()["ctrl"], "a")

    def test_right_ctrl_context_click_clears_only_right_ctrl(self):
        self._set_mappings({"ctrl": "a", "right ctrl": "b"})
        self._click_key("right ctrl", self.window._on_canvas_right_click)

        self.assertEqual(self._active_mappings(), {"ctrl": "a"})

    def test_existing_modifier_assignments_render_only_on_left_and_windows_is_hidden(self):
        self._set_mappings(
            {"ctrl": "a", "shift": "b", "alt": "c", "windows": "d"}
        )

        for key, value in (("ctrl", "a"), ("shift", "b"), ("alt", "c")):
            self.assertIn(value, self._canvas_text_in_key(key))
        for key, value in (
            ("right ctrl", "a"),
            ("right shift", "b"),
            ("right alt", "c"),
        ):
            self.assertNotIn(value, self._canvas_text_in_key(key))
        for key in ("left windows", "right windows"):
            self.assertNotIn("d", self._canvas_text_in_key(key))
