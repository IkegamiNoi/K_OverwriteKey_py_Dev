import unittest

from keyseq.application.call_context import (
    call_step,
    chain_text,
    finish_call_action,
    start_call,
    top_interval,
)


def control(op, **values):
    return {"type": "system", "op": op, **values}


def trigger(actions, interval=25):
    return {"actions": actions, "run_to_end_delay_ms": interval}


class CallContextTest(unittest.TestCase):
    def run_call(self, root_key, target_key, triggers):
        return start_call("set", root_key, target_key, triggers.get)

    def test_linear_actions_finish_and_report_interval(self):
        actions = [{"type": "text", "value": value} for value in ("A", "B")]
        ctx = self.run_call("root", "f5", {"f5": trigger(actions, 43)})
        counters = {}

        first = call_step(ctx, counters)
        self.assertEqual((first.kind, first.action["value"]), ("action", "A"))
        next_step = finish_call_action(ctx, counters)
        self.assertEqual((next_step.kind, next_step.interval_ms), ("next", 43))
        second = call_step(ctx, counters)
        self.assertEqual((second.kind, second.action["value"]), ("action", "B"))
        done = finish_call_action(ctx, counters)
        self.assertEqual(done.kind, "done")

    def test_empty_sequence_finishes_immediately(self):
        ctx = self.run_call("root", "f5", {"f5": trigger([])})
        self.assertEqual(call_step(ctx, {}).kind, "done")

    def test_nested_call_advances_in_same_step_and_reports_chain(self):
        ctx = self.run_call("root", "f5", {
            "f5": trigger([
                {"type": "text", "value": "A"}, control("call", target="f6"),
                {"type": "text", "value": "C"},
            ]),
            "f6": trigger([{"type": "text", "value": "B"}], interval=51),
        })
        counters = {}
        first = call_step(ctx, counters)
        self.assertEqual((first.kind, first.action["value"]), ("action", "A"))
        finish_call_action(ctx, counters)
        nested = call_step(ctx, counters)
        self.assertEqual((nested.kind, nested.action["value"]), ("action", "B"))
        self.assertEqual(nested.chain, ("f5", "f6"))
        self.assertEqual(chain_text(nested.chain), "呼び出し: f5 > f6")
        finish_call_action(ctx, counters)
        parent_next = call_step(ctx, counters)
        self.assertEqual((parent_next.kind, parent_next.action["value"]), ("action", "C"))
        self.assertEqual(parent_next.chain, ("f5",))
        self.assertEqual(finish_call_action(ctx, counters).kind, "done")

    def test_wait_resumes_at_following_action(self):
        ctx = self.run_call("root", "f5", {"f5": trigger([
            {"type": "text", "value": "A"}, control("wait", ms=100),
            {"type": "text", "value": "B"},
        ])})
        counters = {}
        self.assertEqual(call_step(ctx, counters).action["value"], "A")
        self.assertEqual(finish_call_action(ctx, counters).kind, "next")
        wait = call_step(ctx, counters)
        self.assertEqual((wait.kind, wait.wait_ms), ("wait", 100))
        resumed = call_step(ctx, counters)
        self.assertEqual((resumed.kind, resumed.action["value"]), ("action", "B"))

    def test_stop_is_skipped_and_infinite_loop_is_an_error(self):
        ctx = self.run_call("root", "f5", {"f5": trigger([
            {"type": "text", "value": "A"}, control("stop"),
            {"type": "text", "value": "B"},
        ])})
        counters = {}
        self.assertEqual(call_step(ctx, counters).action["value"], "A")
        finish_call_action(ctx, counters)
        self.assertEqual(call_step(ctx, counters).action["value"], "B")

        infinite = self.run_call("root", "f5", {"f5": trigger([
            control("loop_start", infinite=True),
            {"type": "text", "value": "A"}, control("loop_end"),
        ])})
        error = call_step(infinite, {})
        self.assertEqual((error.kind, error.message), ("error", "呼び出し先に無限ループがあります"))

    def test_counter_deltas_are_new_per_step_and_deferred_on_pop(self):
        ctx = self.run_call("root", "f5", {"f5": trigger([
            control("counter_inc", counter="n"),
            {"type": "text", "value": "A"},
            control("counter_inc", counter="n"),
        ])})
        counters = {}
        first = call_step(ctx, counters)
        self.assertEqual(first.counter_deltas, (("n", 1),))
        finished = finish_call_action(ctx, counters)
        self.assertEqual((finished.kind, finished.counter_deltas), ("done", (("n", 1),)))
        self.assertEqual(counters, {"n": 2})

        final_action = self.run_call("root", "f5", {"f5": trigger([
            control("counter_inc", counter="n"), {"type": "text", "value": "A"},
        ])})
        final_counters = {}
        self.assertEqual(call_step(final_action, final_counters).counter_deltas, (("n", 1),))
        final = finish_call_action(final_action, final_counters)
        self.assertEqual((final.kind, final.counter_deltas), ("done", ()))
        self.assertEqual(final_counters, {"n": 1})

        waiting = self.run_call("root", "f5", {"f5": trigger([
            control("counter_inc", counter="n"),
            {"type": "text", "value": "A"}, control("wait", ms=10),
            {"type": "text", "value": "B"},
        ])})
        wait_counters = {}
        action = call_step(waiting, wait_counters)
        self.assertEqual(action.counter_deltas, (("n", 1),))
        finish_call_action(waiting, wait_counters)
        self.assertEqual(call_step(waiting, wait_counters).counter_deltas, ())
        resumed = call_step(waiting, wait_counters)
        self.assertEqual((resumed.action["value"], resumed.counter_deltas), ("B", ()))

    def test_depth_error_precedes_missing_target_and_includes_attempted_key(self):
        deep_triggers = {}
        for index in range(1, 11):
            actions = [control("call", target=f"f{index + 1}")] if index < 10 else [
                {"type": "text", "value": "Z"}
            ]
            deep_triggers[f"f{index}"] = trigger(actions)
        deep = self.run_call("root", "f1", deep_triggers)
        result = call_step(deep, {})
        self.assertEqual(result.kind, "error")
        self.assertEqual(result.message, "呼び出しの深さが 9 を超えます")
        self.assertEqual(result.chain[-1], "f10")

    def test_root_and_stack_cycles_report_chain(self):
        root_cycle = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="root")]),
            "root": trigger([]),
        })
        cycle = call_step(root_cycle, {})
        self.assertEqual(cycle.message, "呼び出しが循環します（f5 > root）")
        self.assertEqual(cycle.chain, ("f5", "root"))

        stack_cycle = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="f6")]),
            "f6": trigger([control("call", target="f5")]),
        })
        cycle = call_step(stack_cycle, {})
        self.assertEqual(cycle.message, "呼び出しが循環します（f5 > f6 > f5）")
        self.assertEqual(cycle.chain, ("f5", "f6", "f5"))

    def test_missing_target_is_reported(self):
        missing = self.run_call("root", "f5", {"f5": trigger([control("call", target="absent")])})
        self.assertEqual(call_step(missing, {}).message, "呼び出し先のトリガーがありません（absent）")

    def test_single_back_and_rewind_targets_are_rejected(self):
        for op in ("back", "rewind"):
            rejected = self.run_call("root", "f5", {"f5": trigger([control(op)])})
            self.assertEqual(call_step(rejected, {}).message, "戻す・先頭へのトリガーは呼び出せません")

    def test_empty_nested_target_is_reported(self):
        empty = self.run_call("root", "f5", {"f5": trigger([control("call")])})
        self.assertEqual(call_step(empty, {}).message, "呼び出し先が指定されていません")

    def test_snapshot_freezes_actions_and_interval_at_start(self):
        original = trigger([{"type": "text", "value": "before"}], interval=67)
        ctx = self.run_call("root", "f5", {"f5": original})
        original["actions"][0]["value"] = "after"
        original["actions"].append({"type": "text", "value": "extra"})
        original["run_to_end_delay_ms"] = 999
        result = call_step(ctx, {})
        self.assertEqual(top_interval(ctx), 67)
        self.assertEqual(result.action["value"], "before")

    def test_nested_call_inside_finite_loop_runs_twice(self):
        ctx = self.run_call("root", "f5", {
            "f5": trigger([
                control("loop_start", count=2), control("call", target="f6"),
                control("loop_end"),
            ]),
            "f6": trigger([{"type": "text", "value": "B"}]),
        })
        counters = {}
        values = []
        for _ in range(2):
            action = call_step(ctx, counters)
            self.assertEqual(action.kind, "action")
            values.append(action.action["value"])
            finish_call_action(ctx, counters)
        self.assertEqual(values, ["B", "B"])
        self.assertEqual(call_step(ctx, counters).kind, "done")


if __name__ == "__main__":
    unittest.main()
