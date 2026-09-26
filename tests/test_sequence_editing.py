import unittest

from keyseq.domain.sequence_control import MAX_LOOP_DEPTH
from keyseq.domain.sequence_editing import (
    adjust_position_after_insert,
    can_insert_loop,
    can_move,
    delete_indices,
    insert_actions,
    loop_pair_items,
    pair_index,
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


if __name__ == "__main__":
    unittest.main()
