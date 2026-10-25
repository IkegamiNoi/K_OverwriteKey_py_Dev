import unittest

from keyseq.presentation.keyboard_key_text import fit_key_text


def fake_measure(text_line: str, px_size: int, bold: bool) -> tuple[int, int]:
    del bold
    return int(len(text_line) * px_size * 0.6), int(px_size * 1.3)


class FitKeyTextTest(unittest.TestCase):
    def test_uses_upper_size_when_text_fits(self):
        fit = fit_key_text("A", "", 100, 100, 100, fake_measure)

        self.assertEqual(fit.main_px, 37)
        self.assertEqual(fit.sub_px, 0)

    def test_shrinks_until_width_fits(self):
        fit = fit_key_text("AAAA", "", 30, 100, 100, fake_measure)

        self.assertEqual(fit.main_px, 12)

    def test_accepts_overflow_at_main_text_minimum(self):
        fit = fit_key_text("W" * 100, "", 1, 100, 100, fake_measure)

        self.assertEqual(fit.main_px, 7)
        self.assertGreater(len(fit.main_lines[0]) * fit.main_px * 0.6, 1)

    def test_sub_text_respects_individual_minimum_at_unit_27(self):
        fit = fit_key_text("A", "Key", 30, 30, 27, fake_measure)

        self.assertGreaterEqual(fit.main_px, 7)
        self.assertGreaterEqual(fit.sub_px, 6)

    def test_only_newlines_split_lines(self):
        fit = fit_key_text("A B\nC", "", 100, 100, 100, fake_measure)

        self.assertEqual(fit.main_lines, ["A B", "C"])
        self.assertEqual(fit.sub_lines, [])

    def test_two_line_height_can_require_shrinking(self):
        fit = fit_key_text("A\nA", "", 100, 40, 100, fake_measure)

        self.assertEqual(fit.main_px, 16)


if __name__ == "__main__":
    unittest.main()
