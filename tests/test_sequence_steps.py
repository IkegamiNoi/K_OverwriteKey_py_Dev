import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_steps import (
    LoopFrame, StepResume, advance, after_normal_action,
    format_system_error_notification, settle_after_normal,
)


def control(op, **values):
    return {"type": "system", "op": op, **values}


NORMAL = {"type": "text", "value": "x"}


class SequenceStepsTest(unittest.TestCase):
    def test_call_error_notification_shows_trimmed_target_or_none(self):
        notified, _message = format_system_error_notification(
            control("call", target=" z9 "), "error",
        )
        missing, _message = format_system_error_notification(control("call"), "error")
        non_string, _message = format_system_error_notification(
            control("call", target=9), "error",
        )

        self.assertEqual(notified["value"], "call 呼び出し先=z9")
        self.assertEqual(missing["value"], "call 呼び出し先=(なし)")
        self.assertEqual(non_string["value"], "call 呼び出し先=(なし)")

    def test_advance_stops_at_call_without_counting_it_as_processed(self):
        actions = [control("counter_inc", counter="n"), control("call"), NORMAL]
        counters = {}

        outcome = advance(actions, 0, [], counters, wrap_once=False)

        self.assertEqual((outcome.normal_index, outcome.position), (1, 1))
        self.assertEqual(outcome.processed, 1)
        self.assertEqual(counters, {"n": 1})

        at_limit = advance(
            actions, 1, [], {}, wrap_once=False,
            resume=StepResume(0, False, 10000),
        )
        self.assertEqual((at_limit.normal_index, at_limit.position), (1, 1))
        self.assertEqual(at_limit.processed, 10000)

    def test_advance_call_obeys_single_wrap_start_rules(self):
        actions = [NORMAL, control("call")]
        at_end = advance(actions, 1, [], {}, wrap_once=True)
        self.assertEqual((at_end.normal_index, at_end.position), (1, 1))
        self.assertFalse(at_end.wrapped)

        only_call = advance([control("call")], 0, [], {}, wrap_once=True)
        self.assertEqual((only_call.normal_index, only_call.position), (0, 0))
        self.assertFalse(only_call.wrapped)

    def test_settle_processes_loop_before_stopping_at_call(self):
        actions = [NORMAL, control("loop_start", count=2),
                   control("call"), control("loop_end")]

        settled = settle_after_normal(actions, 1, [], {}, allow_wrap=True)

        self.assertEqual((settled.position, settled.frames), (2, [LoopFrame(1, 1)]))
        self.assertEqual(settled.counter_deltas, ())

    def test_advance_rejects_infinite_loop_only_in_call_context(self):
        actions = [control("loop_start", infinite=True), NORMAL,
                   control("loop_end")]

        called = advance(actions, 0, [], {}, wrap_once=False, in_call=True)
        self.assertEqual(called.error, (0, "呼び出し先に無限ループがあります"))
        self.assertEqual((called.position, called.processed), (0, 0))

        ordinary = advance(actions, 0, [], {}, wrap_once=False)
        self.assertEqual(ordinary.normal_index, 1)
        self.assertEqual(ordinary.frames, [LoopFrame(0, 1)])

    def test_settle_in_call_stops_before_infinite_loop_start(self):
        actions = [NORMAL, control("loop_start", infinite=True), NORMAL,
                   control("loop_end")]

        in_call = settle_after_normal(actions, 1, [], {}, allow_wrap=True,
                                      in_call=True)
        self.assertEqual((in_call.position, in_call.frames), (1, []))

        ordinary = settle_after_normal(actions, 1, [], {}, allow_wrap=True)
        self.assertEqual((ordinary.position, ordinary.frames),
                         (2, [LoopFrame(1, 1)]))

    def test_default_in_call_false_preserves_call_free_behavior(self):
        actions = [control("counter_inc", counter="n"), NORMAL]
        default_counters = {}
        explicit_counters = {}
        default_advance = advance(actions, 0, [], default_counters, wrap_once=False)
        explicit_advance = advance(
            actions, 0, [], explicit_counters, wrap_once=False, in_call=False,
        )
        self.assertEqual(default_advance, explicit_advance)
        self.assertEqual(default_counters, explicit_counters)

        settle_actions = [NORMAL, control("counter_inc", counter="n"), NORMAL]
        default_settle = settle_after_normal(
            settle_actions, 1, [], {}, allow_wrap=True,
        )
        explicit_settle = settle_after_normal(
            settle_actions, 1, [], {}, allow_wrap=True, in_call=False,
        )
        self.assertEqual(default_settle, explicit_settle)

    def test_settle_loops_return_to_body_and_then_exit(self):
        actions = [control("loop_start", count=2), NORMAL,
                   control("loop_end"), NORMAL]
        first = settle_after_normal(actions, 2, [LoopFrame(0, 1)], {}, allow_wrap=True)
        self.assertEqual((first.position, first.frames), (1, [LoopFrame(0, 2)]))
        second = settle_after_normal(actions, 2, first.frames, {}, allow_wrap=True)
        self.assertEqual((second.position, second.frames), (3, []))
        self.assertEqual(second.counter_deltas, ())

    def test_settle_counters_defer_increment_and_reset(self):
        actions = [NORMAL, control("counter_inc", counter=" n "),
                   control("counter_reset", counter="n"), NORMAL]
        counters = {"n": 4}
        settled = settle_after_normal(actions, 1, [], counters, allow_wrap=True)
        self.assertEqual((settled.position, settled.frames), (3, []))
        self.assertEqual(counters, {"n": 4})
        self.assertEqual(settled.counter_deltas, ())
        self.assertEqual(settled.deferred_counters,
                         (("counter_inc", "n"), ("counter_reset", "n")))
        advanced = advance(actions, settled.position, settled.frames, counters,
                           wrap_once=False, deferred_counters=settled.deferred_counters)
        self.assertEqual(advanced.counter_deltas, (("n", 1), ("n", -5)))
        self.assertEqual(counters, {"n": 0})

    def test_advance_skips_stop_when_stop_does_not_end_run(self):
        skipped = advance([control("stop"), NORMAL], 0, [], {}, wrap_once=False)
        self.assertEqual((skipped.normal_index, skipped.position), (1, 1))
        self.assertFalse(skipped.stopped)

        wrapped = advance(
            [NORMAL, control("stop")], 1, [], {}, wrap_once=True,
        )
        self.assertEqual((wrapped.normal_index, wrapped.position), (0, 0))
        self.assertTrue(wrapped.wrapped)
        self.assertFalse(wrapped.stopped)

    def test_advance_stop_ends_run_and_preserves_loop_frames(self):
        stopped = advance(
            [control("stop"), NORMAL], 0, [], {},
            wrap_once=False, stop_ends_run=True,
        )
        self.assertTrue(stopped.stopped)
        self.assertEqual((stopped.normal_index, stopped.position), (None, 1))

        at_end = advance(
            [NORMAL, control("stop")], 1, [], {},
            wrap_once=False, stop_ends_run=True,
        )
        self.assertTrue(at_end.stopped)
        self.assertEqual((at_end.position, at_end.frames), (0, []))

        frames = [LoopFrame(0, 3)]
        in_loop = advance(
            [control("loop_start", infinite=True), NORMAL,
             control("stop"), control("loop_end")],
            2, frames, {}, wrap_once=False, stop_ends_run=True,
        )
        self.assertTrue(in_loop.stopped)
        self.assertEqual((in_loop.position, in_loop.frames), (3, frames))

    def test_advance_stop_after_wait_resume_keeps_counter_deltas(self):
        actions = [NORMAL, control("wait", ms=5), control("stop"), NORMAL]
        counters = {"n": 0}
        waiting = advance(
            actions, 1, [], counters, wrap_once=False,
            deferred_counters=(("counter_inc", "n"),),
        )
        stopped = advance(
            actions, waiting.resume_position, [], counters,
            wrap_once=False, resume=waiting.resume, stop_ends_run=True,
        )
        self.assertTrue(stopped.stopped)
        self.assertEqual(stopped.position, 3)
        self.assertEqual(stopped.counter_deltas, (("n", 1),))

    def test_settle_stop_ends_run_and_preserves_deferred_counters(self):
        actions = [NORMAL, control("counter_inc", counter="n"),
                   control("stop"), NORMAL]
        settled = settle_after_normal(
            actions, 1, [], {}, allow_wrap=True, stop_ends_run=True,
        )
        self.assertTrue(settled.stopped)
        self.assertEqual(settled.position, 3)
        self.assertEqual(settled.deferred_counters, (("counter_inc", "n"),))

        at_end = settle_after_normal(
            [NORMAL, control("stop")], 1, [], {},
            allow_wrap=True, stop_ends_run=True,
        )
        self.assertTrue(at_end.stopped)
        self.assertEqual((at_end.position, at_end.frames), (0, []))

    def test_settle_skips_stop_but_still_stops_before_wait(self):
        actions = [NORMAL, control("stop"), NORMAL]
        settled = settle_after_normal(
            actions, 1, [], {}, allow_wrap=True, stop_ends_run=False,
        )
        self.assertEqual(settled.position, 2)
        self.assertFalse(settled.stopped)

        before_wait = settle_after_normal(
            [NORMAL, control("stop"), control("wait", ms=5), NORMAL],
            1, [], {}, allow_wrap=True, stop_ends_run=False,
        )
        self.assertEqual(before_wait.position, 2)
        self.assertFalse(before_wait.stopped)

    def test_settle_limit_is_checked_before_stop(self):
        settled = settle_after_normal(
            [NORMAL, control("stop"), NORMAL], 1, [], {},
            allow_wrap=True, processed=10000, stop_ends_run=True,
        )
        self.assertFalse(settled.stopped)
        self.assertEqual(settled.position, 1)

    def test_settle_stops_before_wait_back_rewind_and_unknown(self):
        for op in ("wait", "back", "rewind", "unknown"):
            with self.subTest(op=op):
                actions = [NORMAL, control(op), control("counter_inc", counter="n")]
                counters = {}
                settled = settle_after_normal(actions, 1, [], counters, allow_wrap=True)
                self.assertEqual((settled.position, settled.frames), (1, []))
                self.assertEqual(settled.counter_deltas, ())
                self.assertEqual(counters, {})

    def test_settle_error_rows_keep_their_state(self):
        cases = [
            ([NORMAL, control("loop_end")], 1, []),
            ([NORMAL, control("loop_start", count=0), control("loop_end")], 1, []),
            ([NORMAL, control("loop_start", count=1)], 1, []),
            ([NORMAL, control("counter_inc", counter=" ")], 1, []),
        ]
        deep = [control("loop_start", count=1) for _ in range(10)]
        deep += [control("loop_end") for _ in range(10)]
        cases.append((deep, 9, [LoopFrame(i, 1) for i in range(9)]))
        for actions, position, frames in cases:
            with self.subTest(position=position, actions=actions):
                counters = {"n": 3}
                settled = settle_after_normal(actions, position, frames, counters,
                                              allow_wrap=False)
                self.assertEqual((settled.position, settled.frames), (position, frames))
                self.assertEqual(settled.counter_deltas, ())
                self.assertEqual(counters, {"n": 3})

    def test_settle_wraps_once_only_when_allowed(self):
        actions = [control("counter_inc", counter="n"), NORMAL,
                   control("counter_reset", counter="n")]
        counters = {"n": 2}
        wrapped = settle_after_normal(actions, 2, [], counters, allow_wrap=True)
        self.assertEqual((wrapped.position, wrapped.frames, wrapped.wrapped), (1, [], True))
        self.assertEqual(wrapped.counter_deltas, ())
        self.assertEqual(wrapped.deferred_counters,
                         (("counter_reset", "n"), ("counter_inc", "n")))
        self.assertEqual(counters, {"n": 2})
        counters = {"n": 2}
        stopped = settle_after_normal(actions, 2, [], counters, allow_wrap=False)
        self.assertEqual((stopped.position, stopped.frames, stopped.wrapped), (0, [], False))
        self.assertEqual(stopped.counter_deltas, ())
        self.assertEqual(stopped.deferred_counters, (("counter_reset", "n"),))
        self.assertEqual(counters, {"n": 2})

    def test_settle_wrap_limit_and_start_position_rule(self):
        actions = [control("counter_inc", counter="n"), NORMAL,
                   control("counter_inc", counter="n")]
        counters = {}
        settled = settle_after_normal(actions, 2, [], counters, allow_wrap=True)
        self.assertEqual(settled.position, 1)  # 開始位置を越えて先頭を先行処理する
        self.assertEqual(counters, {})
        self.assertEqual(settled.counter_deltas, ())
        self.assertEqual(settled.deferred_counters,
                         (("counter_inc", "n"), ("counter_inc", "n")))
        endless = [control("loop_start", infinite=True), control("loop_end")]
        limited = settle_after_normal(endless, 0, [], {}, allow_wrap=True)
        self.assertEqual((limited.position, limited.frames), (1, [LoopFrame(0, 10000)]))
        self.assertEqual(limited.counter_deltas, ())
        capped = settle_after_normal(
            [NORMAL, control("counter_inc", counter="n"),
             control("counter_inc", counter="n")],
            1, [], counters, allow_wrap=True, processed=9999,
        )
        self.assertEqual(capped.position, 2)
        self.assertEqual(capped.counter_deltas, ())
        self.assertEqual(capped.deferred_counters, (("counter_inc", "n"),))
        self.assertEqual(counters, {})

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
        actions = [control("counter_inc", counter="n"),
                   control("counter_inc", counter="n")]
        outcome = advance(actions, 1, [], counters, wrap_once=True)
        self.assertEqual((outcome.position, outcome.normal_index), (1, None))
        self.assertEqual(counters, {"n": 2})
        empty = advance([control("back")], 0, [], {}, wrap_once=True)
        self.assertEqual((empty.position, empty.normal_index), (0, None))
        wrapped = advance([NORMAL, control("counter_inc", counter="n")], 1, [], {}, wrap_once=True)
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

    def test_counter_deltas_record_increments_and_resets(self):
        counters = {"A": 4}
        actions = [control("counter_inc", counter="A"),
                   control("counter_reset", counter="A"), NORMAL]

        outcome = advance(actions, 0, [], counters, wrap_once=False)

        self.assertEqual(outcome.normal_index, 2)
        self.assertEqual(outcome.counter_deltas, (("A", 1), ("A", -5)))
        self.assertEqual(counters, {"A": 0})

    def test_counter_deltas_accumulate_across_wait(self):
        actions = [control("counter_inc", counter="n"), control("wait", ms=1),
                   control("counter_reset", counter="n"), NORMAL]
        counters = {}

        waiting = advance(actions, 0, [], counters, wrap_once=False)
        self.assertEqual(waiting.counter_deltas, (("n", 1),))
        self.assertEqual(waiting.resume.counter_deltas, (("n", 1),))

        continued = advance(
            actions, waiting.resume_position, waiting.frames, counters,
            wrap_once=False, resume=waiting.resume,
        )
        self.assertEqual(continued.normal_index, 3)
        self.assertEqual(continued.counter_deltas, (("n", 1), ("n", -1)))
        self.assertEqual(counters, {"n": 0})

    def test_back_and_rewind_require_standalone_sequence(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                controls = []
                mixed = advance([NORMAL, control(op)], 1, [], {},
                                wrap_once=False, on_control=controls.append)
                self.assertEqual(mixed.error,
                                 (1, "戻す・先頭へは単独で登録してください"))
                self.assertEqual(mixed.position, 1)
                self.assertEqual(controls, [])
                alone = advance([control(op)], 0, [], {},
                                wrap_once=False, on_control=controls.append)
                self.assertEqual(controls, [op])
                self.assertTrue(alone.reached_end)

    def test_deferred_counters_are_not_reapplied_on_wait_resume(self):
        actions = [control("wait", ms=1), NORMAL]
        counters = {"n": 1}
        waiting = advance(actions, 0, [], counters, wrap_once=False,
                          deferred_counters=(("counter_inc", "n"),))
        self.assertEqual(counters["n"], 2)
        continued = advance(actions, waiting.resume_position, waiting.frames,
                            counters, wrap_once=False, resume=waiting.resume,
                            deferred_counters=(("counter_inc", "n"),))
        self.assertEqual(counters["n"], 2)
        self.assertEqual(continued.counter_deltas, (("n", 1),))

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

    def test_wait_returns_wait_row_and_resume_state(self):
        actions = [control("counter_inc", counter="n"), control("wait", ms="25"), NORMAL]
        counters = {}

        outcome = advance(actions, 0, [], counters, wrap_once=False)

        self.assertEqual(outcome.wait_ms, 25)
        self.assertEqual(outcome.position, 1)  # 中断位置は待機の行
        self.assertEqual(outcome.resume_position, 2)
        self.assertEqual(outcome.frames, [])
        self.assertEqual(outcome.resume, StepResume(
            initial_position=0, wrapped=False, processed=2, counter_deltas=(("n", 1),),
        ))
        self.assertEqual(counters, {"n": 1})

        continued = advance(
            actions, outcome.resume_position, outcome.frames, counters,
            wrap_once=False, resume=outcome.resume,
        )
        self.assertEqual(continued.normal_index, 2)

    def test_invalid_wait_duration_is_an_error_at_wait_row(self):
        for value in ("invalid", "1.5", 0, -1, None):
            with self.subTest(ms=value):
                outcome = advance([control("wait", ms=value)], 0, [], {}, wrap_once=False)
                self.assertEqual(outcome.error, (0, "待機時間が不正です（1 以上の整数・ミリ秒）"))
                self.assertEqual(outcome.position, 0)
                self.assertIsNone(outcome.wait_ms)
                self.assertIsNone(outcome.resume_position)

    def test_wait_at_end_resumes_through_normal_end_handling(self):
        actions = [control("wait", ms=5)]
        outcome = advance(actions, 0, [], {}, wrap_once=True)
        self.assertEqual(outcome.wait_ms, 5)
        self.assertEqual((outcome.position, outcome.resume_position), (0, 1))

        ended = advance(
            actions, outcome.resume_position, outcome.frames, {},
            wrap_once=True, resume=outcome.resume,
        )
        self.assertTrue(ended.reached_end)
        self.assertIsNone(ended.normal_index)
        self.assertEqual((ended.position, ended.frames), (0, []))

    def test_resume_stops_at_original_start_position_after_wrap(self):
        actions = [control("wait", ms=1), control("counter_inc", counter="n")]
        counters = {}
        waiting = advance(actions, 0, [], counters, wrap_once=True)

        ended = advance(
            actions, waiting.resume_position, waiting.frames, counters,
            wrap_once=True, resume=waiting.resume,
        )

        self.assertEqual(counters, {"n": 1})
        self.assertTrue(ended.reached_end)
        self.assertEqual((ended.position, ended.frames), (0, []))

    def test_processing_limit_is_carried_across_waits(self):
        actions = [control("loop_start", infinite=True), control("wait", ms=1),
                   control("loop_end")]
        outcome = advance(actions, 0, [], {}, wrap_once=False)
        self.assertEqual(outcome.wait_ms, 1)
        self.assertEqual(outcome.resume.processed, 2)

        for _ in range(4999):
            outcome = advance(
                actions, outcome.resume_position, outcome.frames, {},
                wrap_once=False, resume=outcome.resume,
            )
            self.assertEqual(outcome.wait_ms, 1)

        self.assertEqual(outcome.resume.processed, 10000)
        limited = advance(
            actions, outcome.resume_position, outcome.frames, {},
            wrap_once=False, resume=outcome.resume,
        )
        self.assertEqual(limited.error[0], 2)
        self.assertIn("10000", limited.error[1])


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

    def test_pending_steps_follow_runtime_state_lifetime(self):
        state = AppState()
        state.pending_steps[("old", "f1")] = object()
        state.pending_steps[("other", "f2")] = object()
        state.forget_trigger_set("old")
        self.assertEqual(set(state.pending_steps), {("other", "f2")})

        state.pending_steps[("old", "f3")] = object()
        state.pending_steps[("new", "f4")] = object()
        state.rekey_trigger_set("old", "new")
        self.assertEqual(set(state.pending_steps), {("other", "f2")})

        state.reset_indices()
        self.assertEqual(state.pending_steps, {})

    def test_deferred_counters_follow_trigger_and_set_lifetime(self):
        state = AppState()
        deferred = [("counter_inc", "n")]
        state.deferred_counters_for("first")["f1"] = list(deferred)
        state.rekey_trigger("first", "f1", "f9")
        self.assertEqual(state.deferred_counters_for("first"), {"f9": deferred})
        state.rekey_trigger_set("first", "second")
        self.assertNotIn("first", state.keymap_deferred_counters)
        self.assertEqual(state.deferred_counters_for("second"), {"f9": deferred})
        state.forget_trigger("second", "f9")
        self.assertEqual(state.deferred_counters_for("second"), {})
        state.deferred_counters_for("second")["f1"] = list(deferred)
        state.forget_trigger_set("second")
        self.assertNotIn("second", state.keymap_deferred_counters)
        state.deferred_counters["f1"] = list(deferred)
        state.reset_indices()
        self.assertEqual((state.deferred_counters, state.keymap_deferred_counters), ({}, {}))


class AppStateResetListenersTest(unittest.TestCase):
    def test_reset_indices_calls_registered_listeners_in_order(self):
        state = AppState()
        calls = []
        state.reset_listeners.extend(
            [lambda: calls.append("first"), lambda: calls.append("second")]
        )

        state.reset_indices()

        self.assertEqual(calls, ["first", "second"])

    def test_reset_indices_works_without_registered_listeners(self):
        state = AppState(indices={"trigger": 3})

        state.reset_indices()

        self.assertEqual(state.indices, {})
