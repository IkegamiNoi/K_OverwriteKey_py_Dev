import unittest

from keyseq.domain.call_graph import (
    call_target,
    call_targets,
    edit_call_violation,
    rename_call_targets,
)
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS


def call(target):
    return {"type": "system", "op": "call", "target": target}


def trigger(*actions, delay=DEFAULT_RUN_TO_END_DELAY_MS):
    return {"actions": list(actions), "run_to_end_delay_ms": delay}


def finder(triggers):
    return lambda key: triggers.get(key)


class CallTargetTest(unittest.TestCase):
    def test_normalizes_target_and_rejects_empty_or_non_call_values(self):
        self.assertEqual(call_target(call("  F5  ")), "f5")
        self.assertEqual(call_target(call("  ")), "")
        self.assertEqual(call_target(call(5)), "")
        self.assertEqual(call_target({"type": "system", "op": "wait", "target": "f5"}), "")
        self.assertEqual(call_target({"type": "text", "op": "call", "target": "f5"}), "")

    def test_call_targets_keeps_occurrence_order_and_duplicates(self):
        self.assertEqual(call_targets([call("F5"), call("f6"), call(" f5 "), call("")]), ["f5", "f6", "f5"])


class RenameCallTargetsTest(unittest.TestCase):
    def test_renames_matching_calls_and_copies_rows_without_mutating_source(self):
        original = [
            call(" F5 "),
            {"type": "text", "value": "keep", "label": "text"},
            {"type": "system", "op": "call", "target": "f6", "label": "other"},
            {"type": "system", "op": "call", "target": "f5", "label": "second"},
        ]

        renamed = rename_call_targets(original, "f5", "Z8")

        self.assertEqual(
            renamed,
            [
                call("z8"),
                original[1],
                original[2],
                {"type": "system", "op": "call", "target": "z8", "label": "second"},
            ],
        )
        self.assertEqual(original[0]["target"], " F5 ")
        self.assertIsNot(renamed, original)
        self.assertTrue(all(copy is not source for copy, source in zip(renamed, original)))

    def test_returns_none_when_no_rewrite_is_needed(self):
        self.assertIsNone(rename_call_targets([call("f6")], "f5", "f7"))
        self.assertIsNone(rename_call_targets([call("f5")], "F5", " f5 "))


class EditCallViolationTest(unittest.TestCase):
    def test_empty_missing_and_self_checks_follow_required_order(self):
        find = finder({"f1": trigger()})
        self.assertEqual(edit_call_violation("f1", " ", find), "呼び出し先を選んでください")
        self.assertEqual(
            edit_call_violation("f1", "f1", finder({})),
            "呼び出し先のトリガーがありません（f1）",
        )
        self.assertEqual(edit_call_violation("F1", "f1", find), "自分自身は呼び出せません")

    def test_cycle_reason_includes_path_and_precedes_depth(self):
        triggers = {
            "f1": trigger(),
            "f5": trigger(call("f6"), call("f7")),
            "f6": trigger(call("f1")),
            "f7": trigger(call("f8")),
            "f8": trigger(call("f9")),
            "f9": trigger(call("f10")),
            "f10": trigger(call("f11")),
            "f11": trigger(call("f12")),
            "f12": trigger(call("f13")),
            "f13": trigger(call("f14")),
            "f14": trigger(call("f15")),
            "f15": trigger(),
        }
        self.assertEqual(
            edit_call_violation("f1", "f5", finder(triggers)),
            "呼び出しが循環します（f5 > f6 > f1）",
        )

    def test_depth_counts_only_downstream_and_enforces_nine(self):
        # A long ancestry into the owner does not add to the proposed call depth.
        triggers = {"owner": trigger(), "target": trigger()}
        for index in range(1, 12):
            parent = f"p{index}"
            parent_target = f"p{index + 1}" if index < 11 else "owner"
            triggers[parent] = trigger(call(parent_target))
        self.assertIsNone(edit_call_violation("owner", "target", finder(triggers)))

        allowed = {f"f{i}": trigger(call(f"f{i + 1}")) for i in range(1, 9)}
        allowed["f9"] = trigger()
        self.assertIsNone(edit_call_violation("owner", "f1", finder(allowed)))
        too_deep = dict(allowed)
        too_deep["f9"] = trigger(call("f10"))
        too_deep["f10"] = trigger()
        self.assertEqual(
            edit_call_violation("owner", "f1", finder(too_deep)),
            "呼び出しの深さが 9 を超えます",
        )

    def test_direct_back_or_rewind_only_trigger_is_rejected(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                triggers = {"target": trigger({"type": "system", "op": op})}
                self.assertEqual(
                    edit_call_violation("owner", "target", finder(triggers)),
                    "戻す・先頭へのトリガーは呼び出せません",
                )

    def test_downstream_existing_cycle_terminates(self):
        triggers = {
            "target": trigger(call("loop")),
            "loop": trigger(call("target")),
        }
        self.assertIsNone(edit_call_violation("owner", "target", finder(triggers)))


if __name__ == "__main__":
    unittest.main()
