import unittest

from keyseq.presentation.compact_pane_heights import (
    COMPACT_SEQUENCE_VIEW_KEY,
    parse_compact_sequence_view,
    plan_compact_heights,
)


class ParseCompactSequenceViewTests(unittest.TestCase):
    def test_constant_and_valid_values(self):
        self.assertEqual(COMPACT_SEQUENCE_VIEW_KEY, "compact_sequence_view")
        self.assertEqual(parse_compact_sequence_view({"open": False, "height": 240}), (False, 240))
        self.assertEqual(parse_compact_sequence_view({"open": True, "height": 1}), (True, 1))

    def test_values_are_validated_independently(self):
        self.assertEqual(parse_compact_sequence_view({"open": False, "height": True}), (False, None))
        self.assertEqual(parse_compact_sequence_view({"open": 0, "height": 240}), (True, 240))
        self.assertEqual(parse_compact_sequence_view({"open": "false", "height": 0}), (True, None))
        for invalid_height in (-1, 2.5, "240"):
            with self.subTest(height=invalid_height):
                self.assertEqual(
                    parse_compact_sequence_view({"open": False, "height": invalid_height}),
                    (False, None),
                )

    def test_non_dictionary_and_missing_values_use_defaults(self):
        for raw in (None, [], "invalid"):
            with self.subTest(raw=raw):
                self.assertEqual(parse_compact_sequence_view(raw), (True, None))
        self.assertEqual(parse_compact_sequence_view({}), (True, None))


class PlanCompactHeightsTests(unittest.TestCase):
    def test_rule_1_keeps_desired_heights_and_raises_to_minimum(self):
        self.assertEqual(
            plan_compact_heights(500, 120, 0, (80, 100, 24), (140, 90, 24)),
            (100, 140),
        )

    def test_rule_2_shrinks_call_before_sequence_to_minimum(self):
        self.assertEqual(
            plan_compact_heights(380, 180, 0, (120, 80, 20), (130, 90, 20)),
            (110, 90),
        )

    def test_rule_2_can_shrink_only_the_call_pane(self):
        self.assertEqual(
            plan_compact_heights(400, 180, 0, (120, 80, 20), (130, 90, 20)),
            (120, 100),
        )

    def test_rule_3_allows_trigger_list_to_shrink_to_its_floor(self):
        self.assertEqual(
            plan_compact_heights(220, 120, 24, (100, 80, 20), (100, 80, 20)),
            (80, 80),
        )

    def test_rule_4_shrinks_call_then_sequence_below_minimum_but_keeps_headings(self):
        self.assertEqual(
            plan_compact_heights(150, 120, 24, (100, 80, 20), (100, 80, 20)),
            (80, 46),
        )
        self.assertEqual(
            plan_compact_heights(30, 120, 24, (100, 80, 20), (100, 80, 20)),
            (20, 20),
        )

    def test_rule_4_reaches_call_heading_before_shrinking_sequence(self):
        self.assertEqual(
            plan_compact_heights(100, 120, 24, (100, 80, 20), (100, 80, 20)),
            (56, 20),
        )

    def test_only_one_open_pane_is_allocated_and_closed_pane_is_none(self):
        self.assertEqual(
            plan_compact_heights(300, 120, 24, (120, 80, 20), None),
            (120, None),
        )
        self.assertEqual(
            plan_compact_heights(300, 120, 0, None, (120, 80, 20)),
            (None, 120),
        )

    def test_one_open_pane_can_shrink_and_both_closed_panes_return_none(self):
        self.assertEqual(
            plan_compact_heights(50, 120, 24, None, (100, 80, 20)),
            (None, 26),
        )
        self.assertEqual(
            plan_compact_heights(300, 120, 24, None, None),
            (None, None),
        )


if __name__ == "__main__":
    unittest.main()
