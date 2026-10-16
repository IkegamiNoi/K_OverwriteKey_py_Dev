import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation.keyboard_layouts import (
    KeyboardLayout,
    KeySpec,
    load_layout_from_json,
    resolve_keyboard_layout,
)
from keyseq.presentation.keyboard_window import KeyboardWindow


JIS_LAYOUT_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "user" / "keylayout" / "jis.json"
)


class KeyboardWindowScanCodeTest(unittest.TestCase):
    def _normalize(self, layout, keysym, keycode, scan_code, state=0):
        event = SimpleNamespace(keysym=keysym, keycode=keycode, state=state)
        window = SimpleNamespace(_layout=layout)
        with patch(
            "keyseq.presentation.keyboard_window.win32_window.vk_to_scan_code",
            return_value=scan_code,
        ) as convert:
            result = KeyboardWindow._normalize_tk_key(window, event)
        return result, convert

    def test_function_keys_resolve_for_default_and_jis_layouts(self):
        cases = (("F1", 112, 59, "f1"), ("F10", 121, 68, "f10"), ("F12", 123, 88, "f12"))
        layouts = (resolve_keyboard_layout(), load_layout_from_json(str(JIS_LAYOUT_PATH)))
        for layout in layouts:
            for keysym, keycode, scan_code, expected in cases:
                with self.subTest(layout=layout.layout_id, keysym=keysym):
                    result, convert = self._normalize(layout, keysym, keycode, scan_code)
                    self.assertEqual(result, expected)
                    convert.assert_called_once_with(keycode)

    def test_jis_special_keys_resolve_from_layout_scan_codes(self):
        layout = load_layout_from_json(str(JIS_LAYOUT_PATH))
        cases = (
            ("Muhenkan", 0x1D, 123, "muhenkan"),
            ("Henkan", 0x1C, 121, "henkan"),
            ("Zenkaku_Hankaku", 0xF3, 41, "zenkaku_hankaku"),
        )
        for keysym, keycode, scan_code, expected in cases:
            with self.subTest(keysym=keysym):
                result, _ = self._normalize(layout, keysym, keycode, scan_code)
                self.assertEqual(result, expected)

    def test_us_grave_does_not_use_known_special_key_fallback(self):
        result, _ = self._normalize(resolve_keyboard_layout(), "grave", 0xC0, 41)

        self.assertEqual(result, "grave")

    def test_missing_scan_code_falls_back_to_keysym(self):
        result, convert = self._normalize(resolve_keyboard_layout(), "Kana", 0x15, None)

        self.assertEqual(result, "kana")
        convert.assert_called_once_with(0x15)

    def test_numpad_and_keysym_table_take_precedence(self):
        window = SimpleNamespace(_layout=resolve_keyboard_layout())
        with patch(
            "keyseq.presentation.keyboard_window.win32_window.vk_to_scan_code"
        ) as convert:
            numpad = KeyboardWindow._normalize_tk_key(
                window, SimpleNamespace(keysym="End", keycode=96, state=0)
            )
            enter = KeyboardWindow._normalize_tk_key(
                window, SimpleNamespace(keysym="Return", keycode=13, state=0)
            )

        self.assertEqual(numpad, "num 0")
        self.assertEqual(enter, "enter")
        convert.assert_not_called()

    def test_numpad_layout_name_does_not_override_extended_insert(self):
        layout = KeyboardLayout(
            layout_id="numpad_scan_code_collision",
            display_name="Numpad scan code collision",
            keys=(KeySpec("num 0", "0", 0.0, 0.0, scan_code=82),),
        )

        insert, insert_convert = self._normalize(
            layout, "Insert", 45, 82, state=0x40000
        )
        numpad_zero, numpad_convert = self._normalize(layout, "End", 96, 82)

        self.assertEqual(insert, "insert")
        insert_convert.assert_called_once_with(45)
        self.assertEqual(numpad_zero, "num 0")
        numpad_convert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
