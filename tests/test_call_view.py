import unittest
from types import MappingProxyType

from keyseq.application.call_context import CallContext, CallFrame
from keyseq.application.call_view import CallViewSummary, build_call_view_summary
from keyseq.application.sequence_steps import LoopFrame
from keyseq.domain.call_graph import CallEntry


class BuildCallViewSummaryTests(unittest.TestCase):
    def make_context(self):
        actions = ({"type": "text", "value": "original", "meta": {"items": [1]}},)
        ctx = CallContext(
            trigger_set_id="set",
            root_key="F1",
            first_target="F5",
            snapshot={"F5": CallEntry(({"type": "text", "value": "middle"},), 0),
                      "F7": CallEntry(actions, 0)},
            stack=[CallFrame("F5"), CallFrame("F7", position=2,
                                                 frames=[LoopFrame(0, 2)])],
        )
        return ctx, actions

    def test_builds_normalized_path_and_uses_top_frame_actions_position_and_loop_copy(self):
        ctx, _actions = self.make_context()

        summary = build_call_view_summary(ctx, {})

        self.assertIsInstance(summary, CallViewSummary)
        self.assertEqual(summary.path, ("f1", "f5", "f7"))
        self.assertEqual(summary.position, 2)
        self.assertEqual(summary.loop_frames, (LoopFrame(0, 2),))

    def test_actions_are_deeply_copied_and_loop_frames_are_snapshots(self):
        ctx, actions = self.make_context()
        summary = build_call_view_summary(ctx, {})

        summary.actions[0]["meta"]["items"].append(2)
        summary.actions[0]["value"] = "changed"
        self.assertEqual(actions[0]["meta"]["items"], [1])
        self.assertEqual(actions[0]["value"], "original")

        ctx.stack[-1].frames.append(LoopFrame(3, 1))
        self.assertEqual(summary.loop_frames, (LoopFrame(0, 2),))

    def test_counters_are_read_only_snapshot(self):
        counters = {"n": 4}
        ctx, _actions = self.make_context()

        summary = build_call_view_summary(ctx, counters)

        self.assertEqual(dict(summary.counters), {"n": 4})
        self.assertIsInstance(summary.counters, MappingProxyType)
        counters["n"] = 9
        self.assertEqual(summary.counters["n"], 4)
        with self.assertRaises(TypeError):
            summary.counters["n"] = 5

    def test_returns_none_without_call_frames(self):
        ctx, _actions = self.make_context()
        ctx.stack.clear()

        self.assertIsNone(build_call_view_summary(ctx, {}))


if __name__ == "__main__":
    unittest.main()
