import unittest

from keyseq.domain.sequence_control import (
    ACTION_TYPE_FILE_LINE,
    ACTION_TYPE_SYSTEM,
    DEFAULT_ENCODING,
    DEFAULT_OUT_OF_RANGE,
    MAX_LOOP_DEPTH,
    action_type,
    analyze_loops,
    enclosing_loop_starts,
    format_control_value,
    loop_depth_style,
    system_op,
)


def system(op: str, **values: object) -> dict[str, object]:
    return {"type": ACTION_TYPE_SYSTEM, "op": op, **values}


class ActionTypeTest(unittest.TestCase):
    def test_action_type_and_op_are_trimmed_and_lowercased(self) -> None:
        action = {"type": "  SYSTEM ", "op": " Loop_Start "}
        self.assertEqual(action_type(action), ACTION_TYPE_SYSTEM)
        self.assertEqual(system_op(action), "loop_start")

    def test_non_string_type_and_op_become_empty(self) -> None:
        self.assertEqual(action_type({"type": None}), "")
        self.assertEqual(system_op({"op": ["loop_start"]}), "")


class AnalyzeLoopsTest(unittest.TestCase):
    def test_simple_loop_pairs_and_depth(self) -> None:
        structure = analyze_loops([system("loop_start"), {"type": "text"}, system("loop_end")])
        self.assertEqual(structure.pairs, {0: 2})
        self.assertEqual(structure.reverse_pairs, {2: 0})
        self.assertEqual(structure.depth, (1, 1, 1))
        self.assertEqual(structure.unmatched, frozenset())

    def test_nested_loops_use_inner_depth(self) -> None:
        actions = [
            system("loop_start"),
            {"type": "text"},
            system("loop_start"),
            {"type": "hotkey"},
            system("loop_end"),
            system("loop_end"),
            {"type": "text"},
        ]
        structure = analyze_loops(actions)
        self.assertEqual(structure.pairs, {0: 5, 2: 4})
        self.assertEqual(structure.depth, (1, 1, 2, 2, 2, 1, 0))

    def test_sibling_loops_have_independent_depth(self) -> None:
        structure = analyze_loops(
            [system("loop_start"), system("loop_end"), system("loop_start"), system("loop_end")]
        )
        self.assertEqual(structure.pairs, {0: 1, 2: 3})
        self.assertEqual(structure.depth, (1, 1, 1, 1))

    def test_unmatched_start_has_zero_depth(self) -> None:
        structure = analyze_loops([system("loop_start"), {"type": "text"}])
        self.assertEqual(structure.unmatched, frozenset({0}))
        self.assertEqual(structure.depth, (0, 0))

    def test_unmatched_end_has_zero_depth(self) -> None:
        structure = analyze_loops([system("loop_end"), {"type": "text"}])
        self.assertEqual(structure.unmatched, frozenset({0}))
        self.assertEqual(structure.depth, (0, 0))

    def test_reversed_markers_are_both_unmatched(self) -> None:
        structure = analyze_loops([system("loop_end"), system("loop_start")])
        self.assertEqual(structure.pairs, {})
        self.assertEqual(structure.unmatched, frozenset({0, 1}))
        self.assertEqual(structure.depth, (0, 0))

    def test_nine_levels_are_allowed_and_ten_marks_the_extra_start(self) -> None:
        nine = analyze_loops([system("loop_start") for _ in range(9)] + [system("loop_end") for _ in range(9)])
        self.assertEqual(nine.depth, tuple(range(1, 10)) + tuple(range(9, 0, -1)))
        self.assertEqual(nine.too_deep, frozenset())

        ten = analyze_loops([system("loop_start") for _ in range(10)] + [system("loop_end") for _ in range(10)])
        self.assertEqual(ten.depth[9], MAX_LOOP_DEPTH + 1)
        self.assertEqual(ten.too_deep, frozenset({9}))

    def test_non_loop_actions_are_ignored(self) -> None:
        actions = [
            {"type": "hotkey", "op": "loop_start"},
            system("wait", ms=10),
            {"type": "text", "op": "loop_end"},
        ]
        structure = analyze_loops(actions)
        self.assertEqual(structure.pairs, {})
        self.assertEqual(structure.unmatched, frozenset())
        self.assertEqual(structure.depth, (0, 0, 0))

    def test_system_type_and_op_matching_ignore_case_and_surrounding_space(self) -> None:
        structure = analyze_loops(
            [{"type": " SYSTEM ", "op": " Loop_Start "}, {"type": "system", "op": " LOOP_END "}]
        )
        self.assertEqual(structure.pairs, {0: 1})
        self.assertEqual(structure.depth, (1, 1))


class EnclosingLoopStartsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.structure = analyze_loops(
            [
                system("loop_start"),
                system("loop_start"),
                {"type": "text"},
                system("loop_end"),
                system("loop_end"),
                {"type": "text"},
            ]
        )

    def test_start_body_and_end_boundaries(self) -> None:
        self.assertEqual(enclosing_loop_starts(self.structure, 0), ())
        self.assertEqual(enclosing_loop_starts(self.structure, 1), (0,))
        self.assertEqual(enclosing_loop_starts(self.structure, 2), (0, 1))
        self.assertEqual(enclosing_loop_starts(self.structure, 3), (0, 1))
        self.assertEqual(enclosing_loop_starts(self.structure, 4), (0,))
        self.assertEqual(enclosing_loop_starts(self.structure, 5), ())

    def test_out_of_range_positions_return_empty(self) -> None:
        self.assertEqual(enclosing_loop_starts(self.structure, -1), ())
        self.assertEqual(enclosing_loop_starts(self.structure, len(self.structure.depth)), ())


class LoopDepthStyleTest(unittest.TestCase):
    def test_depths_zero_through_ten(self) -> None:
        expected = {
            0: None,
            1: ("blue", "light"),
            2: ("green", "light"),
            3: ("orange", "light"),
            4: ("blue", "medium"),
            5: ("green", "medium"),
            6: ("orange", "medium"),
            7: ("blue", "dark"),
            8: ("green", "dark"),
            9: ("orange", "dark"),
            10: None,
        }
        for depth, style in expected.items():
            with self.subTest(depth=depth):
                self.assertEqual(loop_depth_style(depth), style)


class FormatControlValueTest(unittest.TestCase):
    def test_file_line_constants(self) -> None:
        self.assertEqual((DEFAULT_ENCODING, DEFAULT_OUT_OF_RANGE), ("utf-8", "error"))
        self.assertEqual(ACTION_TYPE_FILE_LINE, "file_line")

    def test_loop_start_displays_count_infinite_and_runtime_iteration(self) -> None:
        self.assertEqual(format_control_value(system("loop_start", count=3)), "[loop] ×3")
        self.assertEqual(format_control_value(system("loop_start", count=3, infinite=True)), "[loop] ×∞")
        self.assertEqual(
            format_control_value(system("loop_start", count=3), loop_iteration=2),
            "[loop] 2/3",
        )
        self.assertEqual(
            format_control_value(system("loop_start", count=3, infinite=True), loop_iteration=2),
            "[loop] 2/∞",
        )

    def test_all_other_system_operations(self) -> None:
        self.assertEqual(format_control_value(system("loop_end")), "[loop_end]")
        self.assertEqual(
            format_control_value(system("counter_inc", counter="n"), counters={"n": 5}),
            "[count+1] n (=5)",
        )
        self.assertEqual(
            format_control_value(system("counter_reset", counter="n"), counters={"n": 5}),
            "[count=0] n (=5)",
        )
        self.assertEqual(format_control_value(system("wait", ms=500)), "[wait] 500ms")
        self.assertEqual(format_control_value(system("back")), "[back]")
        self.assertEqual(format_control_value(system("rewind")), "[rewind]")

    def test_counters_default_to_zero_when_missing_or_unregistered(self) -> None:
        action = system("counter_inc", counter="n")
        self.assertEqual(format_control_value(action), "[count+1] n (=0)")
        self.assertEqual(format_control_value(action, counters={}), "[count+1] n (=0)")
        self.assertEqual(format_control_value(action, counters={"other": 7}), "[count+1] n (=0)")

    def test_unknown_and_empty_system_op_preserve_raw_value(self) -> None:
        self.assertEqual(format_control_value(system(" Missing_Op ")), "[system]  Missing_Op ")
        self.assertEqual(format_control_value({"type": "system"}), "[system] ")

    def test_file_line_uses_both_path_separators_and_counter_value(self) -> None:
        forward = {"type": "file_line", "path": "data/list.txt", "counter": "n"}
        backward = {"type": "file_line", "path": r"data\list.txt", "counter": "n"}
        self.assertEqual(format_control_value(forward, counters={"n": 5}), "[file_line] list.txt #n (=5)")
        self.assertEqual(format_control_value(backward), "[file_line] list.txt #n (=0)")


if __name__ == "__main__":
    unittest.main()
