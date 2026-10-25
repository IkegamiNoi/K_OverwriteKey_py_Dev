import re
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.presentation.keyboard_layouts import (
    load_layout_from_json,
    resolve_keyboard_layout,
)
from keyseq.presentation.keyboard_window import KeyboardWindow


JIS_LAYOUT_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "user" / "keylayout" / "jis.json"
)


class KeyboardKeyTextUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            try:
                window.destroy()
            except tk.TclError:
                pass
        self.root.update_idletasks()

    def _window(self, layout):
        window = KeyboardWindow(self.root, layout=layout)
        self.windows.append(window)
        self.root.update_idletasks()
        self._redraw_at_unit(window, 27)
        return window

    def _redraw_at_unit(self, window, unit):
        max_x = max(spec.x + spec.w for spec in window._layout.keys)
        max_y = max(spec.y + spec.h for spec in window._layout.keys)
        with (
            patch.object(window.canvas, "winfo_width", return_value=max(2, int(max_x * unit))),
            patch.object(window.canvas, "winfo_height", return_value=max(2, int(max_y * unit))),
        ):
            window.redraw()

    @staticmethod
    def _texts_in_key(window, key):
        _, x1, y1, x2, y2 = next(bounds for bounds in window._key_bounds if bounds[0] == key)
        return [
            item for item in window.canvas.find_all()
            if window.canvas.type(item) == "text"
            and x1 <= window.canvas.coords(item)[0] <= x2
            and y1 <= window.canvas.coords(item)[1] <= y2
        ]

    def test_text_items_have_no_wrap_width_and_use_negative_font_sizes(self):
        layout = load_layout_from_json(str(JIS_LAYOUT_PATH))
        window = self._window(layout)
        window.update_from_config(None, show_physical_key_labels=True)
        self._redraw_at_unit(window, 27)

        text_items = [
            item for item in window.canvas.find_all()
            if window.canvas.type(item) == "text"
        ]
        self.assertTrue(text_items)
        for item in text_items:
            with self.subTest(item=item):
                self.assertEqual(float(window.canvas.itemcget(item, "width")), 0.0)
                font = window.canvas.itemcget(item, "font")
                sizes = re.findall(r"-(\d+)", font)
                self.assertTrue(sizes, font)

    def test_keymap_target_uses_jis_name_table_and_unknown_name_falls_back(self):
        layout = load_layout_from_json(str(JIS_LAYOUT_PATH))
        window = self._window(layout)
        window.update_from_config({
            "active_keymap_id": "default",
            "keymaps": [{
                "id": "default",
                "mappings": {"1": "zenkaku_hankaku", "2": "not_in_table"},
            }],
        })
        self._redraw_at_unit(window, 27)

        mapped_text = [window.canvas.itemcget(item, "text") for item in self._texts_in_key(window, "1")]
        fallback_text = [window.canvas.itemcget(item, "text") for item in self._texts_in_key(window, "2")]
        self.assertIn("半角\n全角", mapped_text)
        self.assertIn("not_in_table", fallback_text)

    def test_home_label_stays_on_one_line_at_unit_27(self):
        window = self._window(resolve_keyboard_layout())

        home_text = [window.canvas.itemcget(item, "text") for item in self._texts_in_key(window, "home")]

        self.assertIn("Home", home_text)
        self.assertNotIn("Home\n", home_text)


if __name__ == "__main__":
    unittest.main()
