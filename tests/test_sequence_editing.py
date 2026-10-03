import unittest

from keyseq.domain.sequence_control import MAX_LOOP_DEPTH
from keyseq.domain.sequence_editing import (
    adjust_position_after_insert,
    can_insert_loop,
    can_move,
    closed_loop_range,
    delete_indices,
    insert_actions,
    loop_pair_items,
    pair_index,
    standalone_violation,
)


def system(op: str, **values: object) -> dict[str, object]:
    return {"type": "system", "op": op, **values}


class InsertActionsTest(unittest.TestCase):
    def test_none_inserts_at_end(self) -> None:
        actions = [{"type": "text"}]
        inserted_at = insert_actions(actions, [{"type": "hotkey"}], after_index=None)
        self.assertEqual(inserted_at, 1)
        self.assertEqual(actions, [{"type": "text"}, {"type": "hotkey"}])

    def test_inserts_after_selected_row(self) -> None:
        actions = [{"type": "a"}, {"type": "b"}, {"type": "c"}]
        inserted_at = insert_actions(actions, [{"type": "new"}], after_index=1)
        self.assertEqual(inserted_at, 2)
        self.assertEqual([item["type"] for item in actions], ["a", "b", "new", "c"])

    def test_inserts_after_first_row(self) -> None:
        actions = [{"type": "a"}, {"type": "b"}]
        self.assertEqual(insert_actions(actions, [{"type": "new"}], after_index=0), 1)
        self.assertEqual([item["type"] for item in actions], ["a", "new", "b"])

    def test_inserts_after_last_row(self) -> None:
        actions = [{"type": "a"}, {"type": "b"}]
        self.assertEqual(insert_actions(actions, [{"type": "new"}], after_index=1), 2)
        self.assertEqual([item["type"] for item in actions], ["a", "b", "new"])

    def test_position_adjustment_tracks_original_action(self) -> None:
        self.assertEqual(adjust_position_after_insert(3, 2, 2), 5)
        self.assertEqual(adjust_position_after_insert(3, 3, 2), 5)
        self.assertEqual(adjust_position_after_insert(3, 4, 2), 3)


class ClosedLoopRangeTest(unittest.TestCase):
    def test_completes_loop_ends_and_starts_with_original_objects(self) -> None:
        start, first, second, end = (
            system("loop_start", label="L1"),
            {"type": "text", "value": "T1"},
            {"type": "text", "value": "T2"},
            system("loop_end", label="L1"),
        )
        actions = [start, first, second, end]
        before = list(actions)

        ending_range = closed_loop_range(actions, 2, 3)
        starting_range = closed_loop_range(actions, 0, 1)

        self.assertEqual(ending_range, [start, second, end])
        self.assertEqual(starting_range, [start, first, end])
        self.assertIs(ending_range[0], start)
        self.assertIs(ending_range[1], second)
        self.assertIs(ending_range[2], end)
        self.assertEqual(actions, before)
        self.assertTrue(
            all(actual is original for actual, original in zip(actions, before))
        )

    def test_completes_multiple_loops_in_source_order(self) -> None:
        actions = [
            system("loop_start", label="L1"),
            {"type": "text", "value": "A"},
            system("loop_end", label="L1"),
            system("loop_start", label="L2"),
            {"type": "text", "value": "B"},
            system("loop_end", label="L2"),
        ]
        self.assertEqual(closed_loop_range(actions, 1, 4), [*actions])

    def test_nested_ranges_keep_pair_order_and_leave_inner_body_alone(self) -> None:
        actions = [
            system("loop_start", label="L1"),
            system("loop_start", label="L2"),
            {"type": "text", "value": "A"},
            system("loop_end", label="L2"),
            system("loop_end", label="L1"),
        ]

        self.assertEqual(
            closed_loop_range(actions, 3, 4),
            [actions[0], actions[1], actions[3], actions[4]],
        )
        self.assertEqual(closed_loop_range(actions, 2, 2), [actions[2]])
        self.assertEqual(closed_loop_range(actions, 1, 2), [actions[1], actions[2], actions[3]])

    def test_closed_ranges_and_unmatched_end_are_returned_without_completion(self) -> None:
        actions = [system("loop_start"), {"type": "text"}, system("loop_end")]
        selected = closed_loop_range(actions, 0, 2)
        self.assertTrue(
            all(actual is original for actual, original in zip(selected, actions))
        )
        plain = [{"type": "text"}, {"type": "text"}]
        self.assertTrue(all(a is b for a, b in zip(closed_loop_range(plain, 0, 1), plain)))
        unmatched = [{"type": "text"}, system("loop_end")]
        self.assertEqual(closed_loop_range(unmatched, 1, 1), [unmatched[1]])

    def test_invalid_ranges_raise_value_error(self) -> None:
        actions = [{"type": "text"}]
        for start, end in ((1, 0), (-1, 0), (0, 1), (2, 2)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                closed_loop_range(actions, start, end)


class StandaloneViolationTest(unittest.TestCase):
    def test_standalone_control_can_be_added_to_empty_sequence(self) -> None:
        self.assertFalse(standalone_violation([], system("back")))
        self.assertFalse(standalone_violation([], system("rewind")))

    def test_standalone_control_cannot_be_added_to_nonempty_sequence(self) -> None:
        self.assertTrue(standalone_violation([{"type": "text"}], system("back")))

    def test_other_row_cannot_be_added_to_sequence_with_standalone_control(self) -> None:
        self.assertTrue(standalone_violation([system("rewind")], {"type": "text"}))

    def test_replacement_with_standalone_control_requires_single_row(self) -> None:
        self.assertFalse(
            standalone_violation([{"type": "text"}], system("back"), replace_index=0)
        )
        self.assertTrue(
            standalone_violation(
                [{"type": "text"}, {"type": "hotkey"}],
                system("rewind"),
                replace_index=0,
            )
        )

    def test_replacing_standalone_control_with_regular_row_is_allowed(self) -> None:
        self.assertFalse(
            standalone_violation([system("back")], {"type": "text"}, replace_index=0)
        )


class LoopEditingTest(unittest.TestCase):
    def test_loop_pair_has_only_schema_fields(self) -> None:
        pair = loop_pair_items(
            {"type": "system", "op": "loop_start", "count": 4, "infinite": True, "label": "repeat", "extra": 1}
        )
        self.assertEqual(
            pair,
            [
                {"type": "system", "op": "loop_start", "count": 4, "infinite": True, "label": "repeat"},
                {"type": "system", "op": "loop_end", "label": ""},
            ],
        )

    def test_loop_depth_limit_allows_nine_and_rejects_ten(self) -> None:
        nine_loops = [system("loop_start") for _ in range(MAX_LOOP_DEPTH)] + [
            system("loop_end") for _ in range(MAX_LOOP_DEPTH)
        ]
        self.assertTrue(can_insert_loop(nine_loops, 0))

        self.assertFalse(can_insert_loop(nine_loops, MAX_LOOP_DEPTH - 1))

    def test_pair_index_handles_start_end_unmatched_and_non_loop(self) -> None:
        actions = [system("loop_start"), {"type": "text"}, system("loop_end"), system("loop_end")]
        self.assertEqual(pair_index(actions, 0), 2)
        self.assertEqual(pair_index(actions, 2), 0)
        self.assertIsNone(pair_index(actions, 1))
        self.assertIsNone(pair_index(actions, 3))
        self.assertIsNone(pair_index(actions, -1))

    def test_delete_removes_matched_pair_but_only_unmatched_row(self) -> None:
        actions = [system("loop_start"), {"type": "text"}, system("loop_end"), system("loop_end")]
        self.assertEqual(delete_indices(actions, 0), [0, 2])
        self.assertEqual(delete_indices(actions, 2), [0, 2])
        self.assertEqual(delete_indices(actions, 3), [3])
        self.assertEqual(delete_indices(actions, 1), [1])
        self.assertEqual(delete_indices(actions, 4), [])


class CanMoveTest(unittest.TestCase):
    def test_regular_rows_can_move_into_or_out_of_loops(self) -> None:
        actions = [{"type": "text"}, system("loop_start"), {"type": "hotkey"}, system("loop_end")]
        self.assertTrue(can_move(actions, 0, 1))
        self.assertTrue(can_move(actions, 2, -1))
        self.assertTrue(can_move(actions, 2, 1))
        self.assertTrue(can_move(actions, 3, -1))

    def test_loop_markers_can_swap_with_non_loop_rows(self) -> None:
        actions = [system("loop_start"), {"type": "text"}, system("loop_end")]
        self.assertTrue(can_move(actions, 0, 1))
        self.assertTrue(can_move(actions, 2, -1))

    def test_loop_markers_cannot_swap_with_each_other(self) -> None:
        actions = [system("loop_start"), system("loop_end")]
        self.assertFalse(can_move(actions, 0, 1))
        self.assertFalse(can_move(actions, 1, -1))

    def test_unmatched_loop_markers_follow_same_move_rule(self) -> None:
        actions = [system("loop_start"), system("loop_start"), {"type": "text"}]
        self.assertFalse(can_move(actions, 0, 1))
        self.assertTrue(can_move(actions, 1, 1))
        self.assertFalse(can_move(actions, 0, -1))
        self.assertFalse(can_move(actions, 3, -1))


class CanMoveBlockTest(unittest.TestCase):
    def test_regular_rows_move_into_and_out_of_loops(self) -> None:
        from keyseq.domain.sequence_editing import can_move_block

        inside = [system("loop_start"), {"type": "text"}, system("loop_end"), {"type": "tail"}]
        self.assertTrue(can_move_block(inside, 1, 1, 3))
        outside = [system("loop_start"), system("loop_end"), {"type": "text"}]
        self.assertTrue(can_move_block(outside, 2, 2, 1))

    def test_complete_loop_can_move_into_another_loop(self) -> None:
        from keyseq.domain.sequence_editing import can_move_block

        actions = [
            system("loop_start"),
            system("loop_end"),
            system("loop_start"),
            system("loop_end"),
        ]
        self.assertTrue(can_move_block(actions, 0, 1, 0))
        self.assertTrue(can_move_block(actions, 0, 1, 1))

    def test_changed_pair_and_reversed_markers_are_rejected(self) -> None:
        from keyseq.domain.sequence_editing import can_move_block

        crossing = [
            system("loop_start"),
            system("loop_start"),
            system("loop_end"),
            system("loop_end"),
        ]
        self.assertFalse(can_move_block(crossing, 1, 1, 2))
        self.assertFalse(can_move_block([system("loop_start"), system("loop_end")], 0, 0, 1))

    def test_unrelated_move_preserves_existing_depth_errors(self) -> None:
        from keyseq.domain.sequence_editing import can_move_block

        actions = [system("loop_start") for _ in range(MAX_LOOP_DEPTH + 1)]
        actions.extend(system("loop_end") for _ in range(MAX_LOOP_DEPTH + 1))
        actions.append({"type": "text"})
        self.assertTrue(can_move_block(actions, len(actions) - 1, len(actions) - 1, 0))

    def test_new_depth_error_and_changed_malformed_rows_are_rejected(self) -> None:
        from keyseq.domain.sequence_editing import can_move_block

        actions = [system("loop_start") for _ in range(MAX_LOOP_DEPTH)]
        actions.extend(system("loop_end") for _ in range(MAX_LOOP_DEPTH))
        actions.extend((system("loop_start"), system("loop_end")))
        self.assertFalse(
            can_move_block(
                actions,
                2 * MAX_LOOP_DEPTH,
                2 * MAX_LOOP_DEPTH + 1,
                MAX_LOOP_DEPTH,
            )
        )
        malformed = [system("loop_end"), system("loop_start"), system("loop_end")]
        self.assertFalse(can_move_block(malformed, 2, 2, 1))


class PasteViolationTest(unittest.TestCase):
    def test_reports_unbalanced_fragment_first(self) -> None:
        from keyseq.domain.sequence_editing import PASTE_UNBALANCED_LOOP, paste_violation

        fragment = [system("back"), system("loop_start")]
        self.assertEqual(paste_violation([], fragment), PASTE_UNBALANCED_LOOP)

    def test_reports_new_depth_error(self) -> None:
        from types import SimpleNamespace
        from unittest.mock import patch

        from keyseq.domain.sequence_editing import PASTE_TOO_DEEP, paste_violation

        actions, fragment = [object()], [system("back")]

        def structure(rows: list[object]) -> SimpleNamespace:
            too_deep = frozenset({1}) if len(rows) == 2 else frozenset()
            return SimpleNamespace(unmatched=frozenset(), too_deep=too_deep)

        with patch("keyseq.domain.sequence_editing.analyze_loops", side_effect=structure):
            self.assertEqual(paste_violation(actions, fragment), PASTE_TOO_DEEP)

    def test_reports_standalone_rule_after_loop_checks(self) -> None:
        from keyseq.domain.sequence_editing import PASTE_STANDALONE, paste_violation

        back = system("back")
        self.assertEqual(paste_violation([{"type": "text"}], [back]), PASTE_STANDALONE)

    def test_accepts_valid_fragments_and_empty_fragment(self) -> None:
        from keyseq.domain.sequence_editing import paste_violation

        self.assertIsNone(paste_violation([], []))
        self.assertIsNone(paste_violation([], [system("loop_start"), system("loop_end")]))
        self.assertIsNone(paste_violation([], [system("back")]))


if __name__ == "__main__":
    unittest.main()
