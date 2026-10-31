"""Tests for Tk independent status badge pixel calculations."""

import unittest

from keyseq.presentation.status_icon.badge_shapes import (
    BADGE_BACKGROUND, BADGE_COLORS, badge_pixels, pixel_runs,
)


class BadgeShapesTest(unittest.TestCase):
    def test_badge_region_size_and_position(self):
        for size, side in ((16, 7), (32, 14), (48, 22)):
            pixels = badge_pixels(size, "off")
            self.assertEqual(len(pixels), side * side)
            self.assertEqual((min(x for x, _ in pixels), min(y for _, y in pixels)), (size - side, 0))

    def test_full_badge_covers_canvas_and_white_background_fills_region(self):
        pixels = badge_pixels(16, "on", full=True)
        self.assertEqual(len(pixels), 16 * 16)
        self.assertEqual(pixels[9, 0], BADGE_BACKGROUND)

    def test_off_fills_inner_square(self):
        pixels = badge_pixels(16, "off")
        self.assertEqual(sum(color == BADGE_COLORS["off"] for color in pixels.values()), 25)

    def test_paused_bars_and_gap(self):
        pixels = badge_pixels(16, "paused")
        colors = [pixels[10 + x, 1] for x in range(5)]
        self.assertEqual(colors, [BADGE_COLORS["paused"], BADGE_COLORS["paused"], BADGE_BACKGROUND,
                                  BADGE_COLORS["paused"], BADGE_COLORS["paused"]])

    def test_on_circle_pattern_is_fixed(self):
        pixels = badge_pixels(16, "on")
        inside = [pixels[10 + x, 1 + y] == BADGE_COLORS["on"] for y in range(5) for x in range(5)]
        self.assertEqual(inside, [False, True, True, True, False,
                                  True, True, True, True, True,
                                  True, True, True, True, True,
                                  True, True, True, True, True,
                                  False, True, True, True, False])

    def test_pixel_runs_groups_each_row(self):
        self.assertEqual(pixel_runs({(1, 0): "a", (2, 0): "b", (0, 1): "c"}, 3),
                         [(1, 0, ("a", "b")), (0, 1, ("c",))])


if __name__ == "__main__":
    unittest.main()
