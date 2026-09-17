import unittest

from keyseq.presentation.button_width_rules import fixed_button_width_chars


class ButtonWidthRulesTest(unittest.TestCase):
    def test_fixed_button_width_chars(self):
        """暫定仕様17 §3-3 の最大文言幅を順序によらず切り上げる。"""
        for widths, expected in (([85, 130], 19), ([140], 20),
                                 ([141], 21), ([130, 85], 19)):
            with self.subTest(widths=widths):
                self.assertEqual(fixed_button_width_chars(widths, 7), expected)

    def test_empty_text_widths_raises(self):
        with self.assertRaises(ValueError):
            fixed_button_width_chars([], 7)

    def test_nonpositive_zero_width_raises(self):
        for zero_width in (0, -1):
            with self.subTest(zero_width=zero_width):
                with self.assertRaises(ValueError):
                    fixed_button_width_chars([85, 130], zero_width)


if __name__ == "__main__":
    unittest.main()
