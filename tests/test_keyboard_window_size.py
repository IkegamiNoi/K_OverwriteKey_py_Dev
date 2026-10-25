import unittest
from types import SimpleNamespace

from keyseq.presentation.keyboard_window_size import (
    KEYBOARD_KEY_MIN_UNIT,
    KEYBOARD_WINDOW_PADDING,
    corrected_size,
    layout_aspect,
    layout_extent,
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

    def test_layout_extent_returns_outer_key_bounds(self):
        keys = (
            SimpleNamespace(x=0, y=0, w=2, h=1),
            SimpleNamespace(x=3, y=1, w=1, h=2),
        )
        self.assertEqual(layout_extent(keys), (4, 3))
        self.assertIsNone(layout_extent(()))
        self.assertIsNone(
            layout_extent((SimpleNamespace(x=0, y=0, w=2, h=0),))
        )

    def test_minimum_size_for_us_tkl_and_jis_meets_unit_and_extent_bounds(self):
        for extent, expected in (
            ((18.25, 6.2), (515, 188)),
            ((14.0, 6.2), (399, 188)),
        ):
            with self.subTest(extent=extent):
                width, height = minimum_size(extent)
                max_x, max_y = extent
                canvas_width = width - 2 * KEYBOARD_WINDOW_PADDING
                canvas_height = height - 2 * KEYBOARD_WINDOW_PADDING
                self.assertGreaterEqual(canvas_width, 27 * max_x)
                self.assertGreaterEqual(canvas_height, 27 * max_y)
                self.assertGreaterEqual(
                    canvas_width / max_x, KEYBOARD_KEY_MIN_UNIT - 0.1
                )
                self.assertGreaterEqual(
                    canvas_height / max_y, KEYBOARD_KEY_MIN_UNIT - 0.1
                )
                self.assertLessEqual(abs(width - expected[0]), 1)
                self.assertLessEqual(abs(height - expected[1]), 1)

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
        self.assertIsNone(
            corrected_size((510, 265), (510, 265), 2, (510, 265))
        )

    def test_corrected_size_uses_width_when_only_width_changed(self):
        self.assertEqual(
            corrected_size((510, 265), (600, 265), 2, (510, 265)),
            (600, 310),
        )

    def test_corrected_size_uses_height_when_only_height_changed(self):
        self.assertEqual(
            corrected_size((510, 265), (510, 300), 2, (510, 265)),
            (580, 300),
        )

    def test_corrected_size_fits_both_changed_dimensions(self):
        self.assertEqual(
            corrected_size((510, 265), (700, 400), 2, (510, 265)),
            (700, 360),
        )
        self.assertEqual(
            corrected_size((510, 265), (700, 300), 2, (510, 265)),
            (580, 300),
        )

    def test_corrected_size_raises_width_below_minimum(self):
        self.assertEqual(
            corrected_size((600, 310), (400, 310), 2, (515, 188)),
            (515, 188),
        )


if __name__ == "__main__":
    unittest.main()
