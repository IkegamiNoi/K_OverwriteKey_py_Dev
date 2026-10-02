import unittest

from keyseq.domain.list_editing import (
    index_after_reorder,
    move_block,
    numbered_label,
    numbered_labels,
    shift_block,
)


class MoveBlockTest(unittest.TestCase):
    def test_moves_block_up_and_down(self) -> None:
        items = list("abcdef")
        self.assertEqual(move_block(items, 3, 4, 1), list("adebcf"))
        self.assertEqual(move_block(items, 1, 2, 3), list("adebcf"))

    def test_moves_to_first_and_last_positions(self) -> None:
        items = list("abcdef")
        self.assertEqual(move_block(items, 2, 3, 0), list("cdabef"))
        self.assertEqual(move_block(items, 1, 2, 4), list("adefbc"))

    def test_clamps_target_and_preserves_input(self) -> None:
        items = list("abcd")
        self.assertEqual(move_block(items, 1, 2, -5), list("bcad"))
        self.assertEqual(move_block(items, 1, 2, 50), list("adbc"))
        self.assertEqual(items, list("abcd"))

    def test_invalid_range_raises(self) -> None:
        for start, end in ((-1, 0), (0, 4), (2, 1)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                move_block([1, 2, 3], start, end, 0)


class ShiftBlockTest(unittest.TestCase):
    def test_shifts_by_one_and_respects_edges(self) -> None:
        self.assertEqual(shift_block(6, 2, 3, -1), 1)
        self.assertEqual(shift_block(6, 2, 3, 1), 3)
        self.assertIsNone(shift_block(6, 0, 1, -1))
        self.assertIsNone(shift_block(6, 4, 5, 1))
        self.assertIsNone(shift_block(6, 2, 3, 2))


class IndexAfterReorderTest(unittest.TestCase):
    def test_tracks_same_object(self) -> None:
        row = {"value": 1}
        before = [object(), row, object()]
        self.assertEqual(index_after_reorder(before, [before[2], row, before[0]], 1), 1)

    def test_does_not_confuse_equal_but_distinct_objects(self) -> None:
        selected = {"value": 1}
        equal_but_distinct = {"value": 1}
        self.assertEqual(index_after_reorder([selected], [equal_but_distinct, selected], 0), 1)

    def test_preserves_terminal_position_and_rejects_missing_row(self) -> None:
        row = object()
        self.assertEqual(index_after_reorder([row], [row], 1), 1)
        self.assertEqual(index_after_reorder([row], [], -1), -1)
        with self.assertRaises(ValueError):
            index_after_reorder([row], [], 0)


class NumberedLabelTest(unittest.TestCase):
    def test_unique_and_duplicate_labels(self) -> None:
        self.assertEqual(numbered_label("b", ["a"]), "b")
        self.assertEqual(numbered_label("a", ["a"]), "a (2)")
        self.assertEqual(numbered_label("a (2)", ["a", "a (2)"]), "a (3)")
        self.assertEqual(numbered_label("a (2)", ["a"]), "a (2)")

    def test_suffix_empty_base_and_blank_labels(self) -> None:
        self.assertEqual(numbered_label("(2)", ["(2)"]), "(2) (2)")
        self.assertEqual(numbered_label("   ", ["x"]), "")
        self.assertEqual(numbered_label(" a ", ["a"]), "a (2)")
        self.assertEqual(numbered_label(" a ", ["A"]), " a ")

    def test_numbers_a_batch_sequentially(self) -> None:
        self.assertEqual(numbered_labels(["a", "a", "a (2)"], ["a"]), ["a (2)", "a (3)", "a (4)"])


if __name__ == "__main__":
    unittest.main()
