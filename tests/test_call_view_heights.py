import unittest

from keyseq.presentation.call_view_heights import (
    default_call_view_height,
    displayed_call_view_height,
    parse_call_view_heights,
)


class ParseCallViewHeightsTests(unittest.TestCase):
    def test_keeps_each_positive_integer_independently(self):
        self.assertEqual(
            parse_call_view_heights({"full": 240, "compact": 120, "other": 30}),
            {"full": 240, "compact": 120},
        )
        self.assertEqual(
            parse_call_view_heights({"full": True, "compact": 120}),
            {"compact": 120},
        )
        self.assertEqual(
            parse_call_view_heights({"full": 240, "compact": 0}),
            {"full": 240},
        )

    def test_discards_bool_non_integer_and_non_positive_values(self):
        self.assertEqual(
            parse_call_view_heights({
                "full": False, "compact": "120", "extra": 90,
            }),
            {},
        )
        self.assertEqual(parse_call_view_heights({"full": 120.0}), {})
        self.assertEqual(
            parse_call_view_heights({"full": 0, "compact": -1}),
            {},
        )

    def test_non_dictionary_is_ignored(self):
        self.assertEqual(parse_call_view_heights(None), {})
        self.assertEqual(parse_call_view_heights([("full", 200)]), {})


class CallViewHeightRulesTests(unittest.TestCase):
    def test_default_is_one_third_of_available_height_with_positive_floor(self):
        self.assertEqual(default_call_view_height(300), 100)
        self.assertEqual(default_call_view_height(2), 1)
        self.assertEqual(default_call_view_height(0), 1)

    def test_display_height_preserves_desired_height_when_it_fits(self):
        self.assertEqual(
            displayed_call_view_height(180, 90, 500, 200, 6),
            180,
        )

    def test_display_height_raises_to_minimum_and_clamps_to_available_space(self):
        self.assertEqual(
            displayed_call_view_height(40, 90, 500, 200, 6),
            90,
        )
        self.assertEqual(
            displayed_call_view_height(450, 90, 500, 200, 6),
            294,
        )


if __name__ == "__main__":
    unittest.main()
