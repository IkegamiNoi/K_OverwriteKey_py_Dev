import unittest
from types import SimpleNamespace

from keyseq.application.key_state_manager import KeyStateManager


class KeyStateManagerTest(unittest.TestCase):
    def test_keypad_names_override_event_names_and_pair_across_numlock_change(self):
        manager = KeyStateManager()
        manager.handle_event(SimpleNamespace(
            name="1", event_type="down", scan_code=79, is_keypad=True
        ))
        self.assertEqual(manager.pressed_keys, frozenset({"num 1"}))
        manager.handle_event(SimpleNamespace(
            name="end", event_type="up", scan_code=79, is_keypad=True
        ))
        self.assertEqual(manager.pressed_keys, frozenset())

    def test_layout_numpad_name_is_ignored_for_non_keypad_event(self):
        manager = KeyStateManager(resolve_scan_code=lambda _code: "num 1")
        manager.handle_event(SimpleNamespace(
            name="end", event_type="down", scan_code=79, is_keypad=False
        ))
        self.assertEqual(manager.pressed_keys, frozenset({"end"}))

    def test_event_without_keypad_attribute_keeps_existing_extraction(self):
        manager = KeyStateManager(resolve_scan_code=lambda _code: "F1")
        manager.handle_event(SimpleNamespace(
            name="unknown", event_type="down", scan_code=59
        ))
        self.assertEqual(manager.pressed_keys, frozenset({"f1"}))

    def test_modifier_alias(self):
        manager = KeyStateManager()
        manager.handle_event(SimpleNamespace(name="Left Shift", event_type="down", scan_code=None))
        self.assertTrue(manager.is_pressed("shift"))
        manager.handle_event(SimpleNamespace(name="left shift", event_type="up", scan_code=None))
        self.assertFalse(manager.is_pressed("shift"))

    def test_clear(self):
        manager = KeyStateManager()
        manager.key_down("a")
        manager.clear()
        self.assertEqual(manager.pressed_keys, frozenset())


if __name__ == "__main__":
    unittest.main()
