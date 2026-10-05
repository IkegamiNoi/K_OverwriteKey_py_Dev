import unittest

from keyseq.domain.control_target import edit_control_target_violation, rename_control_targets


def back(target=None):
    action = {"type": "system", "op": "back"}
    if target is not None:
        action["target"] = target
    return action


def trigger(*actions):
    return {"actions": list(actions)}


class EditControlTargetViolationTest(unittest.TestCase):
    def test_empty_missing_self_and_control_only_violations(self):
        triggers = {
            "f1": trigger({"type": "text", "value": "text"}),
            "f2": trigger({"type": "system", "op": "rewind"}),
            "f3": trigger({"type": "system", "op": "back"}),
        }
        find = triggers.get

        self.assertEqual(edit_control_target_violation("f1", "  ", find), "対象のトリガーを選んでください")
        self.assertEqual(
            edit_control_target_violation("f1", " F9 ", find),
            "対象のトリガーがありません（f9）",
        )
        self.assertEqual(edit_control_target_violation(" F1 ", "f1", find), "自分自身は指定できません")
        self.assertEqual(
            edit_control_target_violation("f1", "f2", find),
            "戻す・先頭へのトリガーは指定できません",
        )
        self.assertEqual(
            edit_control_target_violation("f1", "f3", find),
            "戻す・先頭へのトリガーは指定できません",
        )

    def test_only_a_single_back_or_rewind_row_is_rejected(self):
        triggers = {
            "f4": trigger(back(), {"type": "text", "value": "text"}),
            "f5": trigger({"type": "system", "op": "call", "target": "f9"}),
        }

        self.assertIsNone(edit_control_target_violation("f1", "f4", triggers.get))
        self.assertIsNone(edit_control_target_violation("f1", "f5", triggers.get))

    def test_missing_check_precedes_self_check(self):
        self.assertEqual(
            edit_control_target_violation("f1", " F1 ", lambda key: None),
            "対象のトリガーがありません（f1）",
        )

    def test_calls_deep_chains_and_cycles_are_allowed(self):
        triggers = {
            f"f{index}": trigger({"type": "system", "op": "call", "target": f"f{index + 1}"})
            for index in range(2, 20)
        }
        triggers["f20"] = trigger({"type": "system", "op": "call", "target": "f2"})
        self.assertIsNone(edit_control_target_violation("f1", "f2", triggers.get))


class RenameControlTargetsTest(unittest.TestCase):
    def test_renames_back_and_rewind_targets_without_mutating_source_or_calls(self):
        original = [
            back(" F5 "),
            {"type": "system", "op": "rewind", "target": "f5", "label": "keep"},
            {"type": "system", "op": "call", "target": "f5"},
            back(" "),
            {"type": "text", "value": "keep"},
        ]

        renamed = rename_control_targets(original, " F5 ", " Z8 ")

        self.assertEqual(
            renamed,
            [
                back("z8"),
                {"type": "system", "op": "rewind", "target": "z8", "label": "keep"},
                original[2],
                original[3],
                original[4],
            ],
        )
        self.assertEqual(original[0]["target"], " F5 ")
        self.assertIsNot(renamed, original)
        self.assertTrue(all(copy is not source for copy, source in zip(renamed, original)))

    def test_returns_none_when_no_rewrite_is_needed(self):
        self.assertIsNone(rename_control_targets([back("f6")], "f5", "f7"))
        self.assertIsNone(rename_control_targets([back("f5")], " F5 ", " f5 "))
        self.assertIsNone(rename_control_targets([back("f5")], " ", "f7"))


if __name__ == "__main__":
    unittest.main()
