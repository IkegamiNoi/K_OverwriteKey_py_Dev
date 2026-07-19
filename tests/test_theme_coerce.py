import unittest

from keyseq.presentation import theme


class CoerceFontDeltaTest(unittest.TestCase):
    def test_non_numeric_values_return_zero(self):
        for value in ("x", None, object()):
            with self.subTest(value=value):
                self.assertEqual(theme.coerce_font_delta(value), 0)

    def test_in_range_values_are_unchanged(self):
        for value in (-3, -1, 0, 2, 3):
            with self.subTest(value=value):
                self.assertEqual(theme.coerce_font_delta(value), value)

    def test_out_of_range_values_are_clamped(self):
        for value, expected in ((-100, -3), (-4, -3), (4, 3), (100, 3)):
            with self.subTest(value=value):
                self.assertEqual(theme.coerce_font_delta(value), expected)

    def test_numeric_strings_are_converted(self):
        self.assertEqual(theme.coerce_font_delta("2"), 2)
        self.assertEqual(theme.coerce_font_delta("-3"), -3)

    def test_boundary_values_are_preserved(self):
        self.assertEqual(theme.coerce_font_delta(-3), -3)
        self.assertEqual(theme.coerce_font_delta(+3), 3)


if __name__ == "__main__":
    unittest.main()
