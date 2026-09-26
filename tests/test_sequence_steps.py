import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_steps import LoopFrame, advance, after_normal_action


def control(op, **values):
    return {"type": "system", "op": op, **values}


NORMAL = {"type": "text", "value": "x"}


class SequenceStepsTest(unittest.TestCase):
    def test_finite_loop_counts(self):
        for count in (1, 3):
            actions = [control("loop_start", count=count), NORMAL, control("loop_end")]
            position, frames = 0, []
            for iteration in range(1, count + 1):
                outcome = advance(actions, position, frames, {}, wrap_once=False)
                self.assertEqual(outcome.normal_index, 1)
                self.assertEqual(outcome.frames, [LoopFrame(0, iteration)])
                position, frames = after_normal_action(actions, 1, outcome.frames)
            outcome = advance(actions, position, frames, {}, wrap_once=False)
            self.assertIsNone(outcome.normal_index)
            self.assertEqual((outcome.position, outcome.frames), (0, []))

    def test_infinite_loop_continues(self):
        actions = [control("loop_start", infinite=True), NORMAL, control("loop_end")]
        first = advance(actions, 0, [], {}, wrap_once=False)
        second = advance(actions, 2, first.frames, {}, wrap_once=False)
        self.assertEqual(second.normal_index, 1)
        self.assertEqual(second.frames, [LoopFrame(0, 2)])

    def test_nested_and_sibling_loops(self):
        actions = [control("loop_start", count=2), control("loop_start", count=2),
                   NORMAL, control("loop_end"), control("loop_end"),
                   control("loop_start", count=1), NORMAL, control("loop_end")]
        position, frames, visits = 0, [], []
        while True:
            outcome = advance(actions, position, frames, {}, wrap_once=False)
            if outcome.normal_index is None:
                break
            visits.append((outcome.normal_index, tuple(frame.iteration for frame in outcome.frames)))
            position, frames = after_normal_action(actions, outcome.normal_index, outcome.frames)
        self.assertEqual(visits, [(2, (1, 1)), (2, (1, 2)), (2, (2, 1)),
                                  (2, (2, 2)), (6, (1,))])

    def test_single_wrap_stops_before_start_position(self):
        counters = {}
        actions = [control("counter_inc", counter="n"), control("back")]
        outcome = advance(actions, 1, [], counters, wrap_once=True)
        self.assertEqual((outcome.position, outcome.normal_index), (1, None))
        self.assertEqual(counters, {"n": 1})
        empty = advance([control("back")], 0, [], {}, wrap_once=True)
        self.assertEqual((empty.position, empty.normal_index), (0, None))
        wrapped = advance([NORMAL, control("back")], 1, [], {}, wrap_once=True)
        self.assertEqual(wrapped.normal_index, 0)

    def test_continuous_end_and_plain_actions(self):
        actions = [NORMAL, NORMAL]
        first = advance(actions, 0, [], {}, wrap_once=False)
        self.assertEqual(first.normal_index, 0)
        position, frames = after_normal_action(actions, 0, first.frames)
        self.assertEqual(advance(actions, position, frames, {}, wrap_once=False).normal_index, 1)
        self.assertEqual(after_normal_action(actions, 1, []), (0, []))
        ended = advance([control("back")], 0, [], {}, wrap_once=False)
        self.assertTrue(ended.reached_end)
        self.assertEqual(ended.position, 0)

    def test_counters_are_shared_and_trimmed(self):
        counters = {}
        actions = [control("counter_inc", counter=" A "),
                   control("counter_inc", counter="A"), NORMAL]
        self.assertEqual(advance(actions, 0, [], counters, wrap_once=False).normal_index, 2)
        self.assertEqual(counters, {"A": 2})
        advance([control("counter_reset", counter="A"), NORMAL], 0, [], counters, wrap_once=False)
        self.assertEqual(counters, {"A": 0})
        self.assertIsNotNone(advance([control("counter_inc", counter=" ")], 0, [], counters,
                                      wrap_once=False).error)

    def test_invalid_system_rows_stop_at_row(self):
        cases = [([control("loop_start", count=1)], 0),
                 ([control("loop_end")], 0),
                 ([control("loop_start", count=0), control("loop_end")], 0),
                 ([control("unknown")], 0), ([control("")], 0)]
        for actions, index in cases:
            outcome = advance(actions, 0, [], {}, wrap_once=False)
            self.assertEqual(outcome.error[0], index)
            self.assertEqual(outcome.position, index)

    def test_depth_and_processing_limit(self):
        actions = [control("loop_start", count=1) for _ in range(10)]
        actions += [control("loop_end") for _ in range(10)]
        depth = advance(actions, 0, [], {}, wrap_once=False)
        self.assertEqual(depth.error[0], 9)
        self.assertEqual(len(depth.frames), 9)
        endless = [control("loop_start", infinite=True), control("loop_end")]
        limit = advance(endless, 0, [], {}, wrap_once=False)
        self.assertEqual(limit.error[0], limit.position)
        self.assertIn("10000", limit.error[1])

    def test_frame_alignment_and_broken_pairs(self):
        actions = [control("loop_start", count=2), NORMAL, control("loop_end")]
        matching = advance(actions, 1, [LoopFrame(0, 3)], {}, wrap_once=False)
        self.assertEqual(matching.frames, [LoopFrame(0, 3)])
        reset = advance(actions, 1, [LoopFrame(8, 3)], {}, wrap_once=False)
        self.assertEqual(reset.frames, [LoopFrame(0, 1)])
        broken = advance([control("loop_start", count=2), NORMAL], 1,
                         [LoopFrame(8, 3)], {}, wrap_once=False)
        self.assertEqual(broken.frames, [LoopFrame(8, 3)])


class AppStateLoopFramesTest(unittest.TestCase):
    def test_lifetime_and_counters(self):
        state = AppState()
        state.counters["shared"] = 7
        state.loop_frames_for("first")["a"] = [LoopFrame(0, 2)]
        state.rekey_trigger_set("first", "second")
        self.assertEqual(state.loop_frames_for("second")["a"], [LoopFrame(0, 2)])
        state.forget_trigger_set("second")
        self.assertNotIn("second", state.keymap_loop_frames)
        state.loop_frames["a"] = [LoopFrame(0, 1)]
        state.reset_indices()
        self.assertEqual((state.loop_frames, state.keymap_loop_frames), ({}, {}))
        self.assertEqual(state.counters, {"shared": 7})
