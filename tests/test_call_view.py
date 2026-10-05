import unittest
from types import MappingProxyType, SimpleNamespace

from keyseq.application.call_context import CallContext, CallFrame
from keyseq.application.call_view import CallViewSummary, build_call_view_summary
from keyseq.application.app_state import AppState
from keyseq.application.sequence_steps import LoopFrame
from keyseq.application.sequence_runner import SequenceRunner


class BuildCallViewSummaryTests(unittest.TestCase):
    @staticmethod
    def build(ctx, counters):
        path = (ctx.root_key, *(frame.key for frame in ctx.stack))
        top = ctx.stack[-1] if ctx.stack else CallFrame(ctx.root_key)
        entry = ctx.entry_for(top.key)
        return build_call_view_summary(path, entry.actions if entry else [],
                                       top.position, top.frames, counters)

    def make_context(self):
        actions = [{"type": "text", "value": "original", "meta": {"items": [1]}}]
        triggers = {
            "f5": {"actions": [{"type": "text", "value": "middle"}]},
            "f7": {"actions": actions},
        }
        ctx = CallContext(
            trigger_set_id="set",
            root_key="F1",
            first_target="f5",
            state=AppState(),
            find_trigger=triggers.get,
            stack=[CallFrame("f5"), CallFrame("f7", position=2,
                                                 frames=[LoopFrame(0, 2)])],
        )
        return ctx, actions

    def test_builds_normalized_path_and_uses_top_frame_actions_position_and_loop_copy(self):
        ctx, _actions = self.make_context()

        summary = self.build(ctx, {})

        self.assertIsInstance(summary, CallViewSummary)
        self.assertEqual(summary.path, ("f1", "f5", "f7"))
        self.assertEqual(summary.position, 2)
        self.assertEqual(summary.loop_frames, (LoopFrame(0, 2),))

    def test_actions_are_deeply_copied_and_loop_frames_are_snapshots(self):
        ctx, actions = self.make_context()
        summary = self.build(ctx, {})

        summary.actions[0]["meta"]["items"].append(2)
        summary.actions[0]["value"] = "changed"
        self.assertEqual(actions[0]["meta"]["items"], [1])
        self.assertEqual(actions[0]["value"], "original")

        ctx.stack[-1].frames.append(LoopFrame(3, 1))
        self.assertEqual(summary.loop_frames, (LoopFrame(0, 2),))

    def test_counters_are_read_only_snapshot(self):
        counters = {"n": 4}
        ctx, _actions = self.make_context()

        summary = self.build(ctx, counters)

        self.assertEqual(dict(summary.counters), {"n": 4})
        self.assertIsInstance(summary.counters, MappingProxyType)
        counters["n"] = 9
        self.assertEqual(summary.counters["n"], 4)
        with self.assertRaises(TypeError):
            summary.counters["n"] = 5

    def test_returns_none_without_call_frames(self):
        ctx, _actions = self.make_context()
        ctx.stack.clear()

        self.assertIsNone(self.build(ctx, {}))


class CallViewQueryTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.active_set = "set"
        self.triggers = {
            "f1": {"actions": [{"type": "system", "op": "call", "target": "f5"}]},
            "f5": {"actions": [{"type": "system", "op": "call", "target": "f7"},
                               {"type": "text", "value": "middle"}]},
            "f7": {"actions": [{"type": "text", "value": "deep", "meta": {"items": [1]}}]},
        }
        self.runner = SequenceRunner(
            state=self.state, find_trigger=self.triggers.get, perform_action=lambda _action: True,
            select_trigger=lambda _key: None, refresh_actions=lambda: None, update_status=lambda: None,
            after=lambda _delay, _callback: "timer", after_cancel=lambda _timer: None,
            get_trigger_set_id=lambda: self.active_set,
        )

    def test_unmarked_trigger_has_no_summary(self):
        self.assertIsNone(self.runner.call_view_summary_for("f1"))

    def test_two_and_three_level_chains_use_deepest_current_sequence(self):
        self.state.call_refs_for("set").add("f1")
        self.state.indices_for("set")["f5"] = 1
        summary = self.runner.call_view_summary_for("F1")
        self.assertEqual(summary.path, ("f1", "f5"))
        self.assertEqual(summary.position, 1)
        self.assertEqual(summary.actions[1]["value"], "middle")
        self.state.indices_for("set")["f5"] = 0
        self.state.call_refs_for("set").add("f5")
        self.assertEqual(self.runner.call_view_summary_for("f1").path, ("f1", "f5", "f7"))
        self.assertEqual(self.runner.call_view_summary_for("f5").path, ("f5", "f7"))
        self.triggers["f7"]["actions"][0]["value"] = "edited"
        self.assertEqual(self.runner.call_view_summary_for("f1").actions[0]["value"], "edited")

    def test_in_flight_single_and_continuous_context_override_before_writeback(self):
        for continuous in (False, True):
            with self.subTest(continuous=continuous):
                ctx = CallContext("set", "f1", "f5", self.state, self.triggers.get,
                                  stack=[CallFrame("f5"), CallFrame("f7", 2, [LoopFrame(0, 3)])],
                                  started=True)
                ctx.changed_frames = {frame.key: frame for frame in ctx.stack}
                self.state.indices_for("set")["f5"] = 1
                self.state.loop_frames_for("set")["f7"] = [LoopFrame(0, 1)]
                self.state.pending_steps.clear()
                self.runner._run_to_end_call = ctx if continuous else None
                if not continuous:
                    self.state.pending_steps[("set", "f1")] = SimpleNamespace(call=ctx, call_paused=False)
                summary = self.runner.call_view_summary_for("f1")
                self.assertEqual(summary.path, ("f1", "f5", "f7"))
                self.assertEqual(summary.position, 2)
                self.assertEqual(summary.loop_frames, (LoopFrame(0, 3),))
                self.assertEqual(self.state.indices_for("set"), {"f5": 1})
                self.assertEqual(self.state.loop_frames_for("set")["f7"], [LoopFrame(0, 1)])
                self.assertEqual(self.state.call_refs_for("set"), set())
                self.assertEqual(ctx.stack[-1].position, 2)

    def test_paused_context_does_not_override_shared_progress(self):
        self.state.call_refs_for("set").add("f1")
        self.state.indices_for("set")["f5"] = 1
        ctx = CallContext("set", "f1", "f5", self.state, self.triggers.get,
                          stack=[CallFrame("f5", 0)], started=True)
        ctx.changed_frames = {"f5": ctx.stack[0]}
        self.state.pending_steps[("set", "f1")] = SimpleNamespace(call=ctx, call_paused=True)
        self.runner._run_to_end_call = ctx
        self.state.run_to_end_paused = True
        self.assertEqual(self.runner.call_view_summary_for("f1").position, 1)

    def test_query_returns_detached_actions_frames_and_current_counters(self):
        self.state.call_refs_for("set").update(("f1", "f5"))
        self.state.loop_frames_for("set")["f7"] = [LoopFrame(0, 2)]
        self.state.counters["n"] = 4
        summary = self.runner.call_view_summary_for("f1")
        self.triggers["f7"]["actions"][0]["meta"]["items"].append(2)
        self.state.loop_frames_for("set")["f7"].clear()
        self.state.counters["n"] = 9
        self.assertEqual(summary.actions[0]["meta"]["items"], [1])
        self.assertEqual(summary.loop_frames, (LoopFrame(0, 2),))
        self.assertEqual(summary.counters["n"], 4)
        self.assertEqual(self.runner.call_view_summary_for("f1").counters["n"], 9)
        with self.assertRaises(TypeError):
            summary.counters["n"] = 5

    def test_query_uses_active_trigger_set_only(self):
        self.state.call_refs_for("set").add("f1")
        self.assertIsNotNone(self.runner.call_view_summary_for("f1"))
        self.active_set = "other"
        self.assertIsNone(self.runner.call_view_summary_for("f1"))

    def test_completed_in_flight_frame_does_not_restore_saved_mark(self):
        self.state.call_refs_for("set").add("f1")
        ctx = CallContext("set", "f1", "f5", self.state, self.triggers.get, started=True)
        ctx.changed_frames = {"f5": CallFrame("f5", 0)}
        self.runner._run_to_end_call = ctx
        self.assertIsNone(self.runner.call_view_summary_for("f1"))
        self.assertIn("f1", self.state.call_refs_for("set"))


if __name__ == "__main__":
    unittest.main()
