import copy
import unittest

from keyseq.domain.screen_grid import (
    FIXED_RESERVED_KEYS,
    has_enabled_grid,
    GridCell,
    GridRow,
    SubLayout,
    TopLayout,
    auto_fill_sub_keys,
    can_subdivide,
    default_sub_layout,
    default_top_layout,
    monitor_identifier,
    next_free_key,
    normalize_grid,
    rect_center,
    reassign_top_keys,
    sub_cell_rects,
    sub_layout_of,
    top_cell_rects,
    top_layout_for,
    validate_sub,
    validate_top,
)


class ScreenGridNormalizationTest(unittest.TestCase):
    def test_new_enabled_grid_has_default_shape_and_normalizes_unchanged(self):
        from keyseq.domain.screen_grid import new_enabled_grid

        grid = new_enabled_grid()
        self.assertEqual(grid["enabled"], True)
        self.assertEqual(grid["monitors"], {})
        self.assertEqual(grid["sub"], {
            "rows": 3, "cols": 3, "keys": list("qweasdzxc"),
        })
        self.assertEqual(normalize_grid(grid), grid)

    def test_has_enabled_grid_checks_keymap_grid_dict_and_true_flag(self):
        self.assertTrue(has_enabled_grid([{"grid": {"enabled": True}}]))
        for keymaps in (None, {}, [{"grid": None}], [{"grid": {"enabled": 1}}],
                        [{"grid": {"enabled": False}}], [None]):
            with self.subTest(keymaps=keymaps):
                self.assertFalse(has_enabled_grid(keymaps))

    def test_monitor_identifier_keeps_signed_origin(self):
        self.assertEqual(monitor_identifier(0, -768, 1024, 0), "1024x768+0-768")
        self.assertEqual(monitor_identifier(0, 0, 1920, 966), "1920x966+0+0")
        self.assertEqual(monitor_identifier(-2560, 0, 0, 1440), "2560x1440-2560+0")

    def test_non_dict_is_absent_and_enabled_requires_bool(self):
        self.assertIsNone(normalize_grid(None))
        for enabled in (1, "true", None):
            self.assertFalse(normalize_grid({"enabled": enabled})["enabled"])
        self.assertTrue(normalize_grid({"enabled": True})["enabled"])

    def test_missing_parts_use_defaults_and_default_top_is_implicit(self):
        grid = normalize_grid({"enabled": True})
        self.assertEqual(grid["monitors"], {})
        self.assertEqual(grid["sub"], {"rows": 3, "cols": 3, "keys": list("qweasdzxc")})
        self.assertEqual(top_layout_for(grid, "display"), default_top_layout())
        self.assertEqual(sub_layout_of(grid), default_sub_layout())
        self.assertEqual(normalize_grid({"monitors": []})["monitors"], {})

    def test_ratios_are_normalized_and_keys_are_normalized(self):
        raw = {"monitors": {"m": {"rows": [
            {"h": 2, "cells": [{"w": 2, "key": " Q "}, {"w": 6, "key": "W"}]},
            {"h": 6, "cells": [{"w": 3, "key": "A"}]},
        ]}}}
        grid = normalize_grid(raw)
        rows = grid["monitors"]["m"]["rows"]
        self.assertEqual([row["h"] for row in rows], [0.25, 0.75])
        self.assertEqual([cell["w"] for cell in rows[0]["cells"]], [0.25, 0.75])
        self.assertEqual([cell["key"] for row in rows for cell in row["cells"]], ["q", "w", "a"])

    def test_invalid_monitor_shapes_are_dropped_individually(self):
        valid = {"rows": [{"h": 1, "cells": [{"w": 1, "key": "F1"}]}]}
        invalid = {"rows": [{"h": 1, "cells": [{"w": 1, "key": "q"}, {"w": 1, "key": " Q "}]}]}
        grid = normalize_grid({"monitors": {"good": valid, "bad": invalid}})
        self.assertEqual(set(grid["monitors"]), {"good"})
        self.assertEqual(top_layout_for(grid, "bad"), default_top_layout())

    def test_invalid_shape_warning_includes_reason_once(self):
        with self.assertLogs("keyseq.domain.screen_grid.normalize", level="WARNING") as captured:
            normalize_grid({"monitors": {"bad": {"rows": [{"h": 1, "cells": []}]}}})
        self.assertEqual(len(captured.records), 1)
        self.assertIn("列がありません", captured.output[0])

    def test_sub_rows_above_limit_revert_to_default(self):
        grid = normalize_grid({"sub": {"rows": 10, "cols": 2, "keys": list("abcdefghijklmnopqrst")}})
        self.assertEqual(grid["sub"], {"rows": 3, "cols": 3, "keys": list("qweasdzxc")})

    def test_f12_is_an_ordinary_usable_key_during_load(self):
        raw = {"monitors": {"m": {"rows": [
            {"h": 1, "cells": [{"w": 1, "key": "f12"}]},
        ]}}}
        grid = normalize_grid(raw)
        self.assertEqual(grid["monitors"]["m"]["rows"][0]["cells"][0]["key"], "f12")

    def test_invalid_sub_layout_uses_default(self):
        for raw in (
            {"rows": 0, "cols": 3, "keys": []},
            {"rows": 1, "cols": 1, "keys": ["q"]},
            {"rows": 1, "cols": 2, "keys": ["q"]},
            {"rows": 1, "cols": 2, "keys": ["q", "Q"]},
            {"rows": 1, "cols": 2, "keys": ["q", ""]},
            {"rows": True, "cols": 2, "keys": ["q", "w"]},
            {"rows": 1, "cols": 2, "keys": ["enter", "w"]},
        ):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_grid({"sub": raw})["sub"], {
                    "rows": 3, "cols": 3, "keys": list("qweasdzxc")})

    def test_fixed_reserved_empty_bool_ratio_and_input_immutability(self):
        for key in FIXED_RESERVED_KEYS:
            raw = {"monitors": {"m": {"rows": [{"h": 1, "cells": [{"w": 1, "key": key}]}]}}}
            self.assertNotIn("m", normalize_grid(raw)["monitors"])
        for bad_ratio in (0, -1, True, False, float("inf"), float("nan")):
            raw = {"monitors": {"m": {"rows": [{"h": bad_ratio, "cells": [{"w": 1, "key": "q"}]}]}}}
            self.assertNotIn("m", normalize_grid(raw)["monitors"])
        raw = {"enabled": True, "monitors": {"m": {"rows": [
            {"h": 1, "cells": [{"w": 1, "key": "F1"}]}
        ]}}}
        before = copy.deepcopy(raw)
        normalize_grid(raw)
        self.assertEqual(raw, before)


class ScreenGridGeometryTest(unittest.TestCase):
    def test_top_rectangles_tile_negative_region_and_match_edges(self):
        region = (-13, -9, 28, 23)
        grid = top_cell_rects(region, default_top_layout())
        self.assertEqual(grid[0][0][0][0:2], region[0:2])
        self.assertEqual(grid[-1][-1][0][2:], region[2:])
        for row in grid:
            for first, second in zip(row, row[1:]):
                self.assertEqual(first[0][2], second[0][0])
        for upper, lower in zip(grid, grid[1:]):
                self.assertEqual(upper[0][0][3], lower[0][0][1])

    def test_top_rectangles_respect_uneven_ratios(self):
        layout = TopLayout((GridRow(1, (GridCell(0.25, "q"), GridCell(0.75, "w"))),))
        rects = top_cell_rects((0, 0, 100, 20), layout)[0]
        self.assertEqual([rect for rect, _ in rects], [(0, 0, 25, 20), (25, 0, 100, 20)])

    def test_sub_rectangles_are_read_order_contiguous_and_centers_floor(self):
        rects = sub_cell_rects((-8, -7, 3, 4), SubLayout(2, 3, tuple("abcdef")))
        self.assertEqual([key for _, key in rects], list("abcdef"))
        self.assertEqual(rects[0][0][:2], (-8, -7))
        self.assertEqual(rects[-1][0][2:], (3, 4))
        self.assertEqual(rect_center((-3, -5, 4, 2)), (0, -2))
        for a, b in zip(rects[:2], rects[1:3]):
            self.assertEqual(a[0][2], b[0][0])

    def test_can_subdivide_4px_boundary(self):
        sub = SubLayout(2, 2, tuple("abcd"))
        region = (0, 0, 8, 8)
        self.assertTrue(can_subdivide(region, sub))
        for rect, _ in sub_cell_rects(region, sub):
            self.assertGreaterEqual(rect[2] - rect[0], 4)
            self.assertGreaterEqual(rect[3] - rect[1], 4)
        self.assertFalse(can_subdivide((0, 0, 7, 8), sub))
        self.assertFalse(can_subdivide((0, 0, 8, 7), sub))


class ScreenGridAssignmentTest(unittest.TestCase):
    def test_next_free_key_skips_used_reserved_and_fixed(self):
        self.assertEqual(next_free_key({"q", "w"}, {"e", "ENTER"}), "r")
        self.assertEqual(next_free_key(set("qwertyuiopasdfghjkl;zxcvbnm,./1234567890"), set()), "")

    def test_reassign_top_keys_handles_fourth_fifth_rows_and_reservations(self):
        base = default_top_layout()
        five_rows = TopLayout(base.rows + (
            GridRow(1, tuple(GridCell(1, "x") for _ in range(4))),
            GridRow(1, tuple(GridCell(1, "x") for _ in range(2))),
        ))
        result = reassign_top_keys(five_rows, {"q", "1"})
        keys = [cell.key for row in result.rows for cell in row.cells]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertNotIn("q", keys)
        self.assertNotIn("1", keys)
        self.assertEqual(result.rows[3].cells[0].key, "2")
        self.assertTrue(result.rows[4].cells[0].key)

    def test_auto_fill_sub_keys(self):
        self.assertEqual(auto_fill_sub_keys(2, 2, {"q"}), ("w", "e", "r", "t"))
        self.assertEqual(auto_fill_sub_keys(1, 1, set()), ())


class ScreenGridValidationTest(unittest.TestCase):
    def test_validate_top_reports_empty_duplicate_fixed_reserved_and_ratio(self):
        layout = TopLayout((GridRow(True, (
            GridCell(0, ""), GridCell(1, "q"), GridCell(1, "q"), GridCell(1, "enter"),
        )),))
        errors = validate_top(layout, {"f1"})
        self.assertTrue(any("高さ" in error for error in errors))
        self.assertTrue(any("幅" in error for error in errors))
        self.assertTrue(any("空" in error for error in errors))
        self.assertTrue(any("重複" in error for error in errors))
        self.assertTrue(any("固定予約" in error for error in errors))
        reserved_error = validate_top(
            TopLayout((GridRow(1, (GridCell(1, "f1"),)),)), {"F1"},
        )
        self.assertTrue(any("予約キー" in error for error in reserved_error))
        self.assertTrue(any("行がありません" in error for error in validate_top(TopLayout(()), set())))
        self.assertTrue(any("列がありません" in error for error in validate_top(
            TopLayout((GridRow(1, ()),)), set(),
        )))

    def test_validate_sub_reports_shape_and_reserved_reasons(self):
        errors = validate_sub(SubLayout(1, 2, ("f1", "f1")), {"f1"})
        self.assertTrue(any("予約キー" in error for error in errors))
        self.assertTrue(any("重複" in error for error in errors))
        self.assertTrue(any("枠を2つ以上" in error for error in validate_sub(SubLayout(1, 1, ("q",)), set())))
        self.assertTrue(any("行数" in error for error in validate_sub(SubLayout(10, 1, ()), set())))
        self.assertTrue(any("列数" in error for error in validate_sub(SubLayout(1, 10, ()), set())))
        self.assertTrue(any("キー数" in error for error in validate_sub(SubLayout(2, 2, ("q",)), set())))
        self.assertTrue(any("キーが空" in error for error in validate_sub(SubLayout(1, 2, ("", "q")), set())))
        self.assertTrue(any("固定予約" in error for error in validate_sub(
            SubLayout(1, 2, ("enter", "q")), set(),
        )))
        self.assertEqual(validate_sub(default_sub_layout(), set()), [])
        self.assertEqual(validate_top(default_top_layout(), set()), [])

    def test_validate_top_uses_row_wording_for_top_layout_locations(self):
        self.assertIn("行がありません", validate_top(TopLayout(()), set()))
        location_errors = validate_top(
            TopLayout((GridRow(1, (GridCell(1, "f1"),)),)), {"f1"},
        )
        self.assertIn("行 1・列 1: 予約キー 'f1' は使えません", location_errors)


if __name__ == "__main__":
    unittest.main()
