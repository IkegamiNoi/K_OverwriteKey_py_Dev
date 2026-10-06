"""Unit tests for one-line presentation status text."""

import unittest

from keyseq.presentation.status_text import one_line


class OneLineTest(unittest.TestCase):
    def test_replaces_all_supported_line_breaks_with_spaces(self):
        self.assertEqual(one_line("first\r\nsecond\rthird\nfourth"), "first second third fourth")

    def test_preserves_text_without_line_breaks(self):
        self.assertEqual(one_line("single line"), "single line")


if __name__ == "__main__":
    unittest.main()
