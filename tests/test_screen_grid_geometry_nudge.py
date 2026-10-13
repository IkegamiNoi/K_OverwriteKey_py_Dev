import unittest

from keyseq.domain.screen_grid import clamp_point, nudge_step


class ScreenGridNudgeGeometryTest(unittest.TestCase):
    def test_nudge_step_caps_large_frames_and_uses_eighths_for_small_frames(self):
        self.assertEqual(nudge_step(1000, False), 16)
        self.assertEqual(nudge_step(80, False), 10)
        self.assertEqual(nudge_step(7, False), 1)
        self.assertEqual(nudge_step(0, False), 1)
        self.assertEqual(nudge_step(1000, True), 1)

    def test_clamp_point_uses_half_open_rect_bounds(self):
        self.assertEqual(clamp_point((10, 20, 30, 40), 29, 39), (29, 39))
        self.assertEqual(clamp_point((10, 20, 30, 40), 50, 0), (29, 20))
        self.assertEqual(clamp_point((10, 20, 10, 40), 5, 50), (10, 39))
        self.assertEqual(clamp_point((10, 20, 30, 20), 50, 10), (29, 20))
        self.assertEqual(clamp_point((10, 20, 10, 20), 0, 0), (10, 20))


if __name__ == "__main__":
    unittest.main()
