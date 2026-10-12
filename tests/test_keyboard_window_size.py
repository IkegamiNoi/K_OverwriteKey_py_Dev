import unittest
from types import SimpleNamespace

from keyseq.presentation.keyboard_window_size import (
    KEYBOARD_WINDOW_MIN_WIDTH,
    KEYBOARD_WINDOW_PADDING,
    corrected_size,
    layout_aspect,
    minimum_size,
    size_from_height,
    size_from_width,
)


class KeyboardWindowSizeTest(unittest.TestCase):
    def test_layout_aspect_uses_outer_key_bounds(self):
        keys = (
            SimpleNamespace(x=0, y=0, w=2, h=1),
            SimpleNamespace(x=3, y=1, w=1, h=2),
        )
        self.assertAlmostEqual(layout_aspect(keys), 4 / 3)

    def test_layout_aspect_returns_none_without_valid_height(self):
        self.assertIsNone(layout_aspect(()))
        self.assertIsNone(layout_aspect((SimpleNamespace(x=0, y=0, w=2, h=0),)))

    def test_size_conversions_include_padding_and_round_trip(self):
        width_size = size_from_width(511, 4 / 3)
        self.assertEqual(width_size[0], 511)
        self.assertEqual(width_size[1], round((511 - 2 * KEYBOARD_WINDOW_PADDING) / (4 / 3)) + 20)
        height_size = size_from_height(400, 4 / 3)
        self.assertEqual(height_size[1], 400)
        self.assertEqual(height_size[0], round((400 - 20) * (4 / 3)) + 20)
        self.assertLessEqual(abs(size_from_height(width_size[1], 4 / 3)[0] - 511), 1)
        self.assertLessEqual(abs(size_from_width(height_size[0], 4 / 3)[1] - 400), 1)

    def test_corrected_size_returns_none_for_move_only(self):
        self.assertIsNone(corrected_size((510, 265), (510, 265), 2))

    def test_corrected_size_uses_width_when_only_width_changed(self):
        self.assertEqual(corrected_size((510, 265), (600, 265), 2), (600, 310))

    def test_corrected_size_uses_height_when_only_height_changed(self):
        self.assertEqual(corrected_size((510, 265), (510, 300), 2), (580, 300))

    def test_corrected_size_fits_both_changed_dimensions(self):
        self.assertEqual(corrected_size((510, 265), (700, 400), 2), (700, 360))
        self.assertEqual(corrected_size((510, 265), (700, 300), 2), (580, 300))

    def test_corrected_size_raises_width_below_minimum(self):
        self.assertEqual(
            corrected_size((510, 265), (400, 265), 2),
            minimum_size(2),
        )
        self.assertEqual(minimum_size(2)[0], KEYBOARD_WINDOW_MIN_WIDTH)


if __name__ == "__main__":
    unittest.main()
