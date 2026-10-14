import copy
import unittest

from keyseq.domain.screen_grid import (
    DEFAULT_OPS,
    ARROW_OPS,
    FIXED_BACK_KEY,
    FIXED_CLICK_KEY,
    FIXED_OP_KEYS,
    GRID_OPS,
    OP_LABELS,
    default_operation_keys,
    arrow_keys,
    default_top_layout,
    normalize_grid,
    normalize_ops,
    operation_keys,
    ops_of,
    ops_to_json,
    validate_ops,
)


class ScreenGridOperationsTest(unittest.TestCase):
    def test_arrow_keys_uses_configured_arrow_operations(self):
        self.assertEqual(ARROW_OPS, ("up", "down", "left", "right"))
        self.assertEqual(arrow_keys(DEFAULT_OPS), {"up", "down", "left", "right"})

        custom_ops = dict(DEFAULT_OPS)
        custom_ops.update({"up": "i", "down": "k", "left": "j", "right": "l"})
        self.assertEqual(arrow_keys(custom_ops), {"i", "k", "j", "l"})

    def test_normalize_ops_defaults_invalid_values_and_drops_unknown_operations(self):
        normalized, reverted = normalize_ops({
            "deepen": " H ", "back": "", "click": 12, "next_screen": "shift",
            "up": FIXED_BACK_KEY, "down": FIXED_CLICK_KEY, "left": "L", "extra": "x",
        })
        self.assertEqual(normalized, {
            "deepen": "h", "back": DEFAULT_OPS["back"], "click": DEFAULT_OPS["click"],
            "next_screen": DEFAULT_OPS["next_screen"], "up": DEFAULT_OPS["up"],
            "down": DEFAULT_OPS["down"], "left": "l", "right": DEFAULT_OPS["right"],
        })
        self.assertEqual(reverted, ("back", "click", "next_screen", "up", "down"))
        self.assertEqual(normalize_ops(None), (dict(DEFAULT_OPS), GRID_OPS))

    def test_normalize_ops_does_not_revert_collisions(self):
        normalized, reverted = normalize_ops({"deepen": "x", "back": "X", "click": "q"})
        self.assertEqual(normalized["deepen"], "x")
        self.assertEqual(normalized["back"], "x")
        self.assertEqual(reverted, ())

    def test_normalize_grid_ops_optional_elision_warnings_and_input_immutability(self):
        base = {"enabled": True}
        self.assertNotIn("ops", normalize_grid(base))
        self.assertNotIn("ops", normalize_grid({**base, "ops": dict(DEFAULT_OPS)}))
        raw = {**base, "ops": {"deepen": "h"}}
        before = copy.deepcopy(raw)
        normalized = normalize_grid(raw)
        self.assertEqual(tuple(normalized["ops"]), GRID_OPS)
        self.assertEqual(normalized["ops"]["deepen"], "h")
        self.assertEqual(raw, before)
        with self.assertLogs("keyseq.domain.screen_grid.normalize", level="WARNING") as captured:
            normalize_grid({**base, "ops": None})
        self.assertEqual(len(captured.records), 1)
        self.assertIn("Invalid screen grid ops", captured.output[0])
        with self.assertLogs("keyseq.domain.screen_grid.normalize", level="WARNING") as captured:
            normalize_grid({**base, "ops": {"deepen": "shift"}})
        self.assertEqual(len(captured.records), 1)
        self.assertIn("deepen", captured.output[0])
        with self.assertNoLogs("keyseq.domain.screen_grid.normalize", level="WARNING"):
            normalize_grid({**base, "ops": {"deepen": "space"}})

    def test_ops_accessors_and_key_sets(self):
        self.assertEqual(ops_of(None), dict(DEFAULT_OPS))
        self.assertEqual(ops_of({"ops": {"deepen": "H"}})["deepen"], "h")
        self.assertEqual(ops_to_json(DEFAULT_OPS), None)
        custom = dict(DEFAULT_OPS)
        custom["deepen"] = "h"
        self.assertEqual(list(ops_to_json(custom)), list(GRID_OPS))
        self.assertEqual(operation_keys(DEFAULT_OPS), default_operation_keys())
        self.assertTrue(FIXED_OP_KEYS.issubset(operation_keys(DEFAULT_OPS)))

    def test_validate_ops_reports_each_reason_and_operation_order(self):
        ops = dict(DEFAULT_OPS)
        ops.update({
            "deepen": "", "back": "shift", "click": FIXED_BACK_KEY,
            "next_screen": "x", "up": "X", "down": "f1", "left": "q", "right": "z",
        })
        errors = validate_ops(ops, {" F1 "}, {"Q", "z"})
        self.assertEqual([error.split("）", 1)[0] + "）" for error in errors], [
            f"操作キー（{OP_LABELS[name]}）" for name in GRID_OPS if name != "next_screen"
        ])
        self.assertIn("キーが空", errors[0])
        self.assertIn("修飾キー", errors[1])
        self.assertIn("固定の操作キー", errors[2])
        self.assertIn("先の操作と重複", errors[3])
        self.assertIn("予約キー", errors[4])
        self.assertIn("枠のキー", errors[5])
        self.assertIn("枠のキー", errors[6])

    def test_validate_ops_rejects_fixed_operation_keys_overlapping_frame_keys(self):
        expected = {
            "esc": "操作キー（戻る・固定）: 枠のキー 'esc' と重なっています",
            "num enter": "操作キー（クリック・固定）: 枠のキー 'num enter' と重なっています",
        }
        for frame_keys, errors in (
            ({"esc"}, [expected["esc"]]),
            ({"num enter"}, [expected["num enter"]]),
            ({"esc", "num enter"}, [expected["esc"], expected["num enter"]]),
        ):
            with self.subTest(frame_keys=frame_keys):
                self.assertEqual(validate_ops(DEFAULT_OPS, set(), frame_keys), errors)

    def test_default_ops_do_not_overlap_default_frame_keys(self):
        frame_keys = {cell.key for row in default_top_layout().rows for cell in row.cells}
        frame_keys.update("qweasdzxc")
        self.assertEqual(validate_ops(DEFAULT_OPS, set(), frame_keys), [])


if __name__ == "__main__":
    unittest.main()
