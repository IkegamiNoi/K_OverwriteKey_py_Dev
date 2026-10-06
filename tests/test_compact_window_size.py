import unittest

from keyseq.presentation.compact_window_size import (
    compact_geometry,
    parse_compact_window_size,
)


class ParseCompactWindowSizeTest(unittest.TestCase):
    def test_non_dict_has_no_saved_dimensions(self):
        for raw in (None, [], "300x400", 1):
            with self.subTest(raw=raw):
                self.assertEqual(parse_compact_window_size(raw), (None, None))

    def test_dimensions_are_validated_independently(self):
        self.assertEqual(parse_compact_window_size({"width": 1, "height": 1}), (1, 1))
        self.assertEqual(
            parse_compact_window_size({"width": 320, "height": 480, "future": 1}),
            (320, 480),
        )
        self.assertEqual(parse_compact_window_size({"width": 320}), (320, None))
        self.assertEqual(parse_compact_window_size({"height": 480}), (None, 480))
        self.assertEqual(parse_compact_window_size({"width": {}, "height": []}), (None, None))
        invalid = (True, False, 0, -1, 1.5, "300")
        for value in invalid:
            with self.subTest(value=value):
                self.assertEqual(
                    parse_compact_window_size({"width": value, "height": 480}),
                    (None, 480),
                )
                self.assertEqual(
                    parse_compact_window_size({"width": 320, "height": value}),
                    (320, None),
                )
        self.assertEqual(parse_compact_window_size({}), (None, None))
        self.assertEqual(parse_compact_window_size({"width": None}), (None, None))


class CompactGeometryTest(unittest.TestCase):
    def test_uses_each_saved_dimension_or_its_default(self):
        self.assertEqual(compact_geometry(400, 500, 700, 420, 1000, 900), (400, 500))
        self.assertEqual(compact_geometry(None, None, 500, 420, 1000, 900), (270, 500))
        self.assertEqual(compact_geometry(None, None, 250, 420, 1000, 900), (270, 420))
        self.assertEqual(compact_geometry(None, None, 250, 300, 1000, 900), (270, 360))
        self.assertEqual(compact_geometry(410, None, 500, 420, 1000, 900), (410, 500))
        self.assertEqual(compact_geometry(None, 510, 500, 420, 1000, 900), (270, 510))

    def test_clamps_to_screen_then_prioritizes_minimum_height(self):
        self.assertEqual(compact_geometry(1200, 1000, 500, 420, 1000, 800), (1000, 800))
        self.assertEqual(compact_geometry(400, 700, 500, 900, 1000, 800), (400, 900))
        self.assertEqual(compact_geometry(400, 350, 500, 420, 1000, 800), (400, 420))


if __name__ == "__main__":
    unittest.main()
