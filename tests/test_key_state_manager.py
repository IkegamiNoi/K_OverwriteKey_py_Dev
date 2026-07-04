import unittest
from types import SimpleNamespace

from keyseq.application.key_state_manager import KeyStateManager


class KeyStateManagerTest(unittest.TestCase):
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
