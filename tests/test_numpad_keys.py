import unittest

from keyseq.domain.numpad_keys import (
    is_numpad_key_name,
    is_reserved_numpad_name,
    numpad_key_spec,
    numpad_name_from_event,
)


class NumpadKeysTest(unittest.TestCase):
    def test_specs_cover_all_sixteen_names_and_normalize(self):
        expected = {
            "num 0": (82, False),
            "num 1": (79, False),
            "num 2": (80, False),
            "num 3": (81, False),
            "num 4": (75, False),
            "num 5": (76, False),
            "num 6": (77, False),
            "num 7": (71, False),
            "num 8": (72, False),
            "num 9": (73, False),
            "num decimal": (83, False),
            "num multiply": (55, False),
            "num subtract": (74, False),
            "num add": (78, False),
            "num divide": (53, True),
            "num enter": (28, True),
        }
        for name, spec in expected.items():
            with self.subTest(name=name):
                self.assertEqual(numpad_key_spec(name), spec)
                self.assertEqual(numpad_key_spec(f"  {name.upper()}  "), spec)
                self.assertTrue(is_numpad_key_name(name))
        self.assertIsNone(numpad_key_spec("num lock"))

    def test_event_names_require_keypad_and_known_scan_code(self):
        expected = {
            "num 0": 82, "num 1": 79, "num 2": 80, "num 3": 81,
            "num 4": 75, "num 5": 76, "num 6": 77, "num 7": 71,
            "num 8": 72, "num 9": 73, "num decimal": 83,
            "num multiply": 55, "num subtract": 74, "num add": 78,
            "num divide": 53, "num enter": 28,
        }
        for name, scan_code in expected.items():
            with self.subTest(name=name):
                self.assertEqual(numpad_name_from_event(scan_code, True), name)
        self.assertEqual(numpad_name_from_event(79, False), "")
        self.assertEqual(numpad_name_from_event(69, True), "")
        self.assertEqual(numpad_name_from_event(126, True), "")
        self.assertEqual(numpad_name_from_event("invalid", True), "")
        self.assertEqual(numpad_name_from_event(None, True), "")

    def test_reserved_numpad_names(self):
        for name in ("num +", "num plus", "num del", "num_1", "NUM_ADD", "num_plus"):
            with self.subTest(name=name):
                self.assertTrue(is_reserved_numpad_name(name))
        for name in (
            "num 0", "num 1", "num 2", "num 3", "num 4", "num 5", "num 6",
            "num 7", "num 8", "num 9", "num decimal", "num multiply",
            "num subtract", "num add", "num divide", "num enter", "num lock",
            "1", "end",
        ):
            with self.subTest(name=name):
                self.assertFalse(is_reserved_numpad_name(name))


if __name__ == "__main__":
    unittest.main()
