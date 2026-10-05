import unittest

from keyseq.application.call_context import (
    call_step,
    chain_text,
    finish_call_action,
    start_linked_call,
    top_interval,
)
from keyseq.application.app_state import AppState


def control(op, **values):
    return {"type": "system", "op": op, **values}


def trigger(actions, interval=25):
    return {"actions": actions, "run_to_end_delay_ms": interval}


class CallContextTest(unittest.TestCase):
    def run_call(self, root_key, target_key, triggers, *, step=False):
        return start_linked_call(
            "set", root_key, target_key, triggers.get, AppState(), step=step,
        )

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

    def test_top_is_step_tracks_call_row_and_inherits_parent_step(self):
        stepped = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="f6"),
                           {"type": "text", "value": "B"}]),
            "f6": trigger([{"type": "text", "value": "A"}]),
        }, step=True)
        self.assertFalse(stepped.top_is_step())  # 文脈開始前は段がまだない
        self.assertEqual(call_step(stepped, {}).action["value"], "A")
        self.assertTrue(stepped.top_is_step())
        self.assertEqual([frame.step for frame in stepped.stack], [True, True])
        self.assertEqual(finish_call_action(stepped, {}).kind, "next")
        self.assertEqual(call_step(stepped, {}).action["value"], "B")

        batch_parent = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="f6")]),
            "f6": trigger([{"type": "text", "value": "A"}]),
        })
        self.assertFalse(batch_parent.top_is_step())
        self.assertEqual(call_step(batch_parent, {}).action["value"], "A")
        self.assertFalse(batch_parent.top_is_step())
        self.assertEqual([frame.step for frame in batch_parent.stack], [False, False])
        finish_call_action(batch_parent, {})
        self.assertFalse(batch_parent.top_is_step())

    def test_step_context_stays_true_while_nested_batch_runs(self):
        ctx = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="f6", all=True), {"type": "text", "value": "B"}]),
            "f6": trigger([{"type": "text", "value": "A"}]),
        }, step=True)
        self.assertTrue(ctx.is_step_context())
        self.assertEqual(call_step(ctx, {}).action["value"], "A")
        self.assertFalse(ctx.top_is_step())  # 最上段は一括の段
        self.assertTrue(ctx.is_step_context())  # 文脈はステップのまま（処理中の同じキーは無視）

    def test_nested_call_advances_in_same_step_and_reports_chain(self):
        ctx = self.run_call("root", "f5", {
            "f5": trigger([
                {"type": "text", "value": "A"}, control("call", target="f6", all=True),
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
            actions = [control("call", target=f"f{index + 1}", all=True)] if index < 10 else [
                {"type": "text", "value": "Z"}
            ]
            deep_triggers[f"f{index}"] = trigger(actions)
        deep = self.run_call("root", "f1", deep_triggers)
        result = call_step(deep, {})
        self.assertEqual(result.kind, "error")
        self.assertEqual(result.message, "呼び出しの深さが 9 を超えます")
        self.assertEqual(result.chain[-1], "f10")

    def test_root_and_stack_cycles_report_key_and_chain(self):
        root_cycle = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="root", all=True)]),
            "root": trigger([]),
        })
        cycle = call_step(root_cycle, {})
        self.assertEqual(cycle.message, "呼び出しが循環します（root）")
        self.assertEqual(cycle.chain, ("f5", "root"))

        stack_cycle = self.run_call("root", "f5", {
            "f5": trigger([control("call", target="f6", all=True)]),
            "f6": trigger([control("call", target="f5", all=True)]),
        })
        cycle = call_step(stack_cycle, {})
        self.assertEqual(cycle.message, "呼び出しが循環します（f5）")
        self.assertEqual(cycle.chain, ("f5", "f6", "f5"))

    def test_failed_first_push_does_not_mark_call_started(self):
        missing = self.run_call("root", "absent", {})

        first = call_step(missing, {})
        second = call_step(missing, {})

        self.assertEqual((first.kind, second.kind), ("error", "error"))
        self.assertFalse(missing.started)

    def test_nested_call_loop_controls_share_one_processing_limit(self):
        ctx = self.run_call("root", "f5", {
            "f5": trigger([
                control("loop_start", count=20000), control("call", target="f6", all=True),
                control("loop_end"),
            ]),
            "f6": trigger([]),
        })

        result = call_step(ctx, {})

        self.assertEqual(result.kind, "error")
        self.assertEqual(
            result.message,
            "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）",
        )

    def test_finish_call_action_counts_settled_controls_across_returned_frames(self):
        stop_tail = [control("stop") for _ in range(4000)]
        ctx = self.run_call("root", "f4", {
            "f4": trigger([control("call", target="f5", all=True), *stop_tail]),
            "f5": trigger([control("call", target="f6", all=True), *stop_tail]),
            "f6": trigger([control("call", target="f7", all=True), *stop_tail]),
            "f7": trigger([{"type": "text", "value": "A"}]),
        })
        self.assertEqual(call_step(ctx, {}).action["value"], "A")

        result = finish_call_action(ctx, {})

        self.assertEqual(result.kind, "error")
        self.assertEqual(
            result.message,
            "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）",
        )

    def test_processing_limit_counts_controls_before_and_after_sent_action(self):
        for count, expected in ((6000, "error"), (5000, "done")):
            with self.subTest(count=count):
                actions = [control("stop") for _ in range(count)]
                actions.append({"type": "text", "value": "A"})
                actions.extend(control("stop") for _ in range(count))
                ctx = self.run_call("root", "f5", {"f5": trigger(actions)})

                sent = call_step(ctx, {})
                self.assertEqual(sent.kind, "action")
                result = finish_call_action(ctx, {})

                self.assertEqual(result.kind, expected)
                if expected == "error":
                    self.assertEqual(
                        result.message,
                        "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）",
                    )

    def test_processing_limit_carries_before_count_through_returned_frames(self):
        def stops(count):
            return [control("stop") for _ in range(count)]

        ctx = self.run_call("root", "f5", {
            "f5": trigger([*stops(3000), control("call", target="f6", all=True), *stops(3000)]),
            "f6": trigger([*stops(3000), {"type": "text", "value": "A"}, *stops(3000)]),
        })

        self.assertEqual(call_step(ctx, {}).kind, "action")
        result = finish_call_action(ctx, {})

        self.assertEqual(result.kind, "error")
        self.assertEqual(
            result.message,
            "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）",
        )

    def test_missing_target_is_reported(self):
        missing = self.run_call("root", "f5", {"f5": trigger([control("call", target="absent", all=True)])})
        self.assertEqual(call_step(missing, {}).message, "呼び出し先のトリガーがありません（absent）")

    def test_single_back_and_rewind_targets_are_rejected(self):
        for op in ("back", "rewind"):
            rejected = self.run_call("root", "f5", {"f5": trigger([control(op)])})
            self.assertEqual(call_step(rejected, {}).message, "戻す・先頭へのトリガーは呼び出せません")

    def test_back_and_rewind_with_another_action_report_single_action_error(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                rejected = self.run_call("root", "f5", {
                    "f5": trigger([control(op), {"type": "text", "value": "A"}]),
                })

                error = call_step(rejected, {})

                self.assertEqual(error.kind, "error")
                self.assertEqual(error.message, "戻す・先頭へは単独で登録してください")

    def test_empty_nested_target_is_reported(self):
        empty = self.run_call("root", "f5", {"f5": trigger([control("call", all=True)])})
        self.assertEqual(call_step(empty, {}).message, "呼び出し先が指定されていません")

    def test_linked_call_reads_live_actions_interval_and_current_position(self):
        state = AppState()
        original = trigger([{"type": "text", "value": "before"}], interval=67)
        original["actions"].append({"type": "text", "value": "extra"})
        state.indices_for("set")["f5"] = 1
        ctx = start_linked_call("set", "root", "f5", {"f5": original}.get,
                                state, step=False)
        original["actions"][1]["value"] = "after"
        original["run_to_end_delay_ms"] = 999
        result = call_step(ctx, {})
        self.assertEqual(top_interval(ctx), 999)
        self.assertEqual(result.action["value"], "after")

    def test_linked_single_uses_current_position_and_live_actions(self):
        state = AppState()
        state.indices_for("set")["f5"] = 1
        original = trigger([{"type": "text", "value": "a"},
                            {"type": "text", "value": "b"}], interval=67)
        ctx = start_linked_call("set", "root", "f5", {"f5": original}.get,
                                state, step=True)
        original["actions"][1]["value"] = "changed"
        original["run_to_end_delay_ms"] = 99
        self.assertEqual(call_step(ctx, {}).action["value"], "changed")
        self.assertEqual(top_interval(ctx), 99)
        self.assertEqual(finish_call_action(ctx, {}).kind, "done")
        self.assertEqual(ctx.changed_frames["f5"].position, 0)
        self.assertEqual(ctx.completed, ["f5"])

    def test_linked_counter_deltas_belong_to_each_nested_trigger(self):
        state = AppState()
        triggers = {
            "f5": trigger([control("call", target="f6"), {"type": "text", "value": "d"}]),
            "f6": trigger([control("counter_inc", counter="n"),
                           {"type": "text", "value": "u"}]),
        }
        ctx = start_linked_call("set", "root", "f5", triggers.get, state, step=True)
        counters = {}
        self.assertEqual(call_step(ctx, counters).action["value"], "u")
        self.assertEqual(finish_call_action(ctx, counters).kind, "next")
        self.assertEqual(ctx.deltas_by_key["f6"], [("n", 1)])
        self.assertEqual(ctx.changed_frames["f5"].position, 1)

    def test_linked_call_rejects_entry_inside_an_active_infinite_loop(self):
        state = AppState()
        state.indices_for("set")["f5"] = 1
        ctx = start_linked_call("set", "root", "f5", {"f5": trigger([
            control("loop_start", infinite=True), {"type": "text", "value": "a"},
            control("loop_end"),
        ])}.get, state, step=True)
        self.assertEqual(call_step(ctx, {}).message, "呼び出し先に無限ループがあります")

    def test_linked_call_validates_marked_upstream_depth_and_cycle(self):
        for target, ancestors, depth, message in (
            ("f5", ("f5",), 1, "循環"),
            ("f5", (), 9, "深さ"),
        ):
            with self.subTest(message=message):
                ctx = start_linked_call("set", "root", target,
                                        {"f5": trigger([])}.get, AppState(), step=True,
                                        ancestors=ancestors, ancestor_depth=depth)
                result = call_step(ctx, {})
                self.assertEqual(result.kind, "error")
                self.assertIn(message, result.message)

    def test_linked_batch_shares_processing_limit_across_delivered_actions(self):
        stops = [control("stop") for _ in range(6000)]
        ctx = start_linked_call("set", "root", "f5", {"f5": trigger([
            {"type": "text", "value": "a"}, *stops,
            {"type": "text", "value": "b"}, *stops,
            {"type": "text", "value": "c"},
        ])}.get, AppState(), step=False)
        self.assertEqual(call_step(ctx, {}).action["value"], "a")
        self.assertEqual(finish_call_action(ctx, {}).kind, "next")
        self.assertEqual(call_step(ctx, {}).action["value"], "b")
        self.assertEqual(finish_call_action(ctx, {}).kind, "error")

    def test_nested_call_inside_finite_loop_runs_twice(self):
        ctx = self.run_call("root", "f5", {
            "f5": trigger([
                control("loop_start", count=2), control("call", target="f6", all=True),
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
