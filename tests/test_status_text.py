"""Unit tests for one-line presentation status text."""

import unittest

from keyseq.presentation.status_text import HOOK_STATE_LABELS, hook_display_state, one_line


class OneLineTest(unittest.TestCase):
    def test_replaces_all_supported_line_breaks_with_spaces(self):
        self.assertEqual(one_line("first\r\nsecond\rthird\nfourth"), "first second third fourth")

    def test_preserves_text_without_line_breaks(self):
        self.assertEqual(one_line("single line"), "single line")


class HookDisplayStateTest(unittest.TestCase):
    def test_state_priority(self):
        cases = ((False, False, "off"), (False, True, "off"),
                 (True, False, "paused"), (True, True, "on"))
        for hook_active, custom_enabled, expected in cases:
            with self.subTest(hook_active=hook_active, custom_enabled=custom_enabled):
                self.assertEqual(hook_display_state(hook_active, custom_enabled), expected)

    def test_labels(self):
        self.assertEqual(HOOK_STATE_LABELS, {"on": "ON", "off": "OFF", "paused": "一時停止"})


if __name__ == "__main__":
    unittest.main()
