import unittest

from keyseq.domain.screen_grid import (
    GridCell,
    GridRow,
    TopLayout,
    delete_cell,
    delete_row,
    move_cell_boundary,
    move_row_boundary,
    set_cell_key,
    split_cell,
    split_row,
)


class ScreenGridEditingTests(unittest.TestCase):
    def setUp(self):
        self.layout = TopLayout((
            GridRow(0.4, (GridCell(0.3, "q"), GridCell(0.7, "w"))),
            GridRow(0.6, (GridCell(1.0, "e"),)),
        ))

    def test_split_row_halves_height_and_assigns_fresh_keys(self):
        result = split_row(self.layout, 0, {"a"})

        self.assertEqual([row.h for row in result.rows], [0.2, 0.2, 0.6])
        self.assertEqual([cell.w for cell in result.rows[1].cells], [0.3, 0.7])
        all_keys = [cell.key for row in result.rows for cell in row.cells]
        self.assertEqual(len(all_keys), len(set(all_keys)))
        self.assertNotIn("a", all_keys)

    def test_split_cell_halves_width_and_assigns_fresh_key(self):
        result = split_cell(self.layout, 0, 1, {"a"})

        self.assertEqual([cell.w for cell in result.rows[0].cells], [0.3, 0.35, 0.35])
        all_keys = [cell.key for row in result.rows for cell in row.cells]
        self.assertEqual(len(all_keys), len(set(all_keys)))
        self.assertNotIn("a", all_keys)

    def test_delete_row_expands_next_or_previous_and_preserves_total(self):
        removed_first = delete_row(self.layout, 0)
        removed_last = delete_row(self.layout, 1)

        self.assertEqual(removed_first.rows[0].h, 1.0)
        self.assertEqual(removed_last.rows[0].h, 1.0)
        self.assertEqual(sum(row.h for row in removed_first.rows), 1.0)

    def test_delete_cell_expands_next_or_previous_and_preserves_total(self):
        removed_first = delete_cell(self.layout, 0, 0)
        removed_last = delete_cell(self.layout, 0, 1)

        self.assertEqual([cell.w for cell in removed_first.rows[0].cells], [1.0])
        self.assertEqual([cell.w for cell in removed_last.rows[0].cells], [1.0])
        self.assertEqual(sum(cell.w for cell in removed_first.rows[0].cells), 1.0)

    def test_cannot_delete_last_row_or_last_cell(self):
        single_row = TopLayout((GridRow(1.0, (GridCell(1.0, "q"),)),))

        self.assertIs(delete_row(single_row, 0), single_row)
        self.assertIs(delete_cell(single_row, 0, 0), single_row)

    def test_row_and_cell_boundaries_stop_at_minimum(self):
        row_result = move_row_boundary(self.layout, 0, 0.9, 0.1)
        cell_result = move_cell_boundary(self.layout, 0, 0, 0.9, 0.1)

        self.assertAlmostEqual(row_result.rows[0].h, 0.9)
        self.assertAlmostEqual(row_result.rows[1].h, 0.1)
        self.assertAlmostEqual(cell_result.rows[0].cells[0].w, 0.9)
        self.assertAlmostEqual(cell_result.rows[0].cells[1].w, 0.1)
        self.assertAlmostEqual(sum(row.h for row in row_result.rows), 1.0)
        self.assertAlmostEqual(sum(cell.w for cell in cell_result.rows[0].cells), 1.0)

    def test_row_and_cell_boundaries_clamp_in_both_directions(self):
        row_left = move_row_boundary(self.layout, 0, -1.0, 0.1)
        row_right = move_row_boundary(self.layout, 0, 2.0, 0.1)
        cell_left = move_cell_boundary(self.layout, 0, 0, -1.0, 0.1)
        cell_right = move_cell_boundary(self.layout, 0, 0, 2.0, 0.1)

        self._assert_ratios([row.h for row in row_left.rows[:2]], [0.1, 0.9])
        self._assert_ratios([row.h for row in row_right.rows[:2]], [0.9, 0.1])
        self._assert_ratios([cell.w for cell in cell_left.rows[0].cells], [0.1, 0.9])
        self._assert_ratios([cell.w for cell in cell_right.rows[0].cells], [0.9, 0.1])

    def _assert_ratios(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for got, want in zip(actual, expected):
            self.assertAlmostEqual(got, want)

    def test_nonleading_cell_boundary_uses_cumulative_ratio_and_leaves_others(self):
        layout = TopLayout((GridRow(1.0, (
            GridCell(0.1, "q"), GridCell(0.2, "w"),
            GridCell(0.3, "e"), GridCell(0.4, "r"),
        )),))

        result = move_cell_boundary(layout, 0, 1, 0.4, 0.1)

        for actual, expected in zip(
            (cell.w for cell in result.rows[0].cells), (0.1, 0.3, 0.2, 0.4)
        ):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(result.rows[0].cells[0], layout.rows[0].cells[0])
        self.assertEqual(result.rows[0].cells[3], layout.rows[0].cells[3])

    def test_move_boundary_uses_global_cumulative_ratio(self):
        layout = TopLayout((
            GridRow(0.2, (GridCell(1.0, "q"),)),
            GridRow(0.3, (GridCell(1.0, "w"),)),
            GridRow(0.5, (GridCell(1.0, "e"),)),
        ))

        result = move_row_boundary(layout, 1, 0.7, 0.1)

        self.assertAlmostEqual(result.rows[1].h, 0.5)
        self.assertAlmostEqual(result.rows[2].h, 0.3)

    def test_boundary_stays_when_pair_cannot_fit_two_minimum_sizes(self):
        self.assertIs(move_row_boundary(self.layout, 0, 0.5, 0.6), self.layout)
        self.assertIs(move_cell_boundary(self.layout, 0, 0, 0.5, 0.6), self.layout)

    def test_key_change_returns_new_layout_and_leaves_input_unchanged(self):
        original = self.layout
        changed = set_cell_key(self.layout, 0, 0, "x")

        self.assertIs(self.layout, original)
        self.assertEqual(self.layout.rows[0].cells[0].key, "q")
        self.assertEqual(changed.rows[0].cells[0].key, "x")

    def test_editing_operations_do_not_mutate_input(self):
        original = self.layout
        snapshot = (
            (0.4, ((0.3, "q"), (0.7, "w"))),
            (0.6, ((1.0, "e"),)),
        )
        split_row(original, 0, set())
        split_cell(original, 0, 0, set())
        delete_row(original, 0)
        delete_cell(original, 0, 0)
        move_row_boundary(original, 0, 0.5, 0.1)
        move_cell_boundary(original, 0, 0, 0.5, 0.1)

        self.assertIs(original, self.layout)
        actual = tuple(
            (row.h, tuple((cell.w, cell.key) for cell in row.cells))
            for row in original.rows
        )
        self.assertEqual(actual, snapshot)


if __name__ == "__main__":
    unittest.main()
