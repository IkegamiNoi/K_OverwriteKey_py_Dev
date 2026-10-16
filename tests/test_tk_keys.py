import unittest
from types import SimpleNamespace

from keyseq.presentation.tk_keys import (
    is_unresolved_capture_key,
    normalize_key_hold_tk_key_event,
    normalize_key_hold_tk_keysym,
    normalize_tk_key_event,
    normalize_tk_keysym,
    numpad_name_from_tk_event,
)


class TkKeysTest(unittest.TestCase):
    def test_unresolved_capture_key(self):
        self.assertTrue(is_unresolved_capture_key("??"))
        self.assertFalse(is_unresolved_capture_key("a"))
        self.assertFalse(is_unresolved_capture_key(""))

    def test_numpad_names_by_keycode_and_extended_state(self):
        cases = {
            **{keycode: f"num {digit}" for digit, keycode in enumerate(range(96, 106))},
            110: "num decimal",
            106: "num multiply",
            109: "num subtract",
            107: "num add",
            111: "num divide",
            45: "num 0",
            35: "num 1",
            40: "num 2",
            34: "num 3",
            37: "num 4",
            12: "num 5",
            39: "num 6",
            36: "num 7",
            38: "num 8",
            33: "num 9",
            46: "num decimal",
        }
        for keycode, expected in cases.items():
            with self.subTest(keycode=keycode):
                self.assertEqual(numpad_name_from_tk_event(keycode, 0), expected)
                if 96 <= keycode <= 111:
                    self.assertEqual(
                        numpad_name_from_tk_event(keycode, 0x40000), expected
                    )
        self.assertEqual(numpad_name_from_tk_event(35, 0x40000), "")
        self.assertEqual(numpad_name_from_tk_event(13, 0), "")
        self.assertEqual(numpad_name_from_tk_event(13, 0x40000), "num enter")
        self.assertEqual(numpad_name_from_tk_event(96, 0x40000), "num 0")
        for keycode, state in (("bad", 0), (96, "bad"), (None, 0), (96, None)):
            with self.subTest(keycode=keycode, state=state):
                self.assertEqual(numpad_name_from_tk_event(keycode, state), "")

    def test_event_normalizers_prefer_numpad_and_fall_back_to_keysym(self):
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="End", keycode=97, state=0)),
            "num 1",
        )
        self.assertEqual(
            normalize_key_hold_tk_key_event(
                SimpleNamespace(keysym="End", keycode=97, state=0)
            ),
            "num 1",
        )
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="End", keycode=35, state=0x40000)),
            "end",
        )
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="1", keycode=49, state=0)),
            "1",
        )
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="Return")), "enter"
        )
        self.assertEqual(
            normalize_key_hold_tk_key_event(SimpleNamespace(keysym="Shift_L")),
            "left shift",
        )
        self.assertEqual(normalize_tk_keysym("Return"), "enter")
        self.assertEqual(normalize_key_hold_tk_keysym("Shift_L"), "left shift")


if __name__ == "__main__":
    unittest.main()
