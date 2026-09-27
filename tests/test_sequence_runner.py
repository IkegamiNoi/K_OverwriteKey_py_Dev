import unittest
from unittest.mock import Mock, call

from keyseq.application.action_executor import ActionExecutor
from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner
from keyseq.application.sequence_steps import LoopFrame, StepResume


class FakeScheduler:
    """tk の after / after_cancel の決定的な代替。"""

    def __init__(self):
        self.queue = []
        self.delays = []
        self._next_id = 1

    def after(self, delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.delays.append(delay_ms)
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.queue = [(h, cb) for h, cb in self.queue if h != handle]

    def run_pending(self, limit=100):
        count = 0
        while self.queue and count < limit:
            self.run_one()
            count += 1

    def run_one(self):
        if self.queue:
            _, callback = self.queue.pop(0)
            callback()


def make_runner(triggers, *, get_trigger_set_id=None, selected=None, messages=None):
    state = AppState()
    scheduler = FakeScheduler()
    performed = []
    selected = selected if selected is not None else []
    messages = messages if messages is not None else []

    def find_trigger(key):
        for trigger in triggers:
            if trigger["key"] == key:
                return trigger
        return None

    runner = SequenceRunner(
        state=state,
        find_trigger=find_trigger,
        perform_action=performed.append,
        select_trigger=selected.append,
        refresh_actions=lambda: None,
        update_status=lambda: None,
        after=scheduler.after,
        after_cancel=scheduler.after_cancel,
        get_trigger_set_id=get_trigger_set_id,
        notify_message=messages.append,
    )
    return runner, state, scheduler, performed


A1 = {"type": "text", "value": "one"}
A2 = {"type": "text", "value": "two"}


class SingleStepTest(unittest.TestCase):
    def test_actions_cycle_one_per_press(self):
        trigger = {"key": "f1", "run_to_end": False, "actions": [A1, A2]}
        runner, state, _scheduler, performed = make_runner([trigger])
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        self.assertEqual(state.indices["f1"], 1)
        runner.handle_key("f1")
        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.indices["f1"], 0)  # 循環して先頭へ
        runner.handle_key("f1")
        self.assertEqual(performed, [A1, A2, A1])

    def test_unknown_key_does_nothing(self):
        runner, _state, _scheduler, performed = make_runner([])
        runner.handle_key("f9")
        self.assertEqual(performed, [])


class SystemActionRunnerTest(unittest.TestCase):
    def test_single_steps_through_loop(self):
        actions = [{"type": "system", "op": "loop_start", "count": 2}, A1,
                   {"type": "system", "op": "loop_end"}, A2]
        runner, state, _scheduler, performed = make_runner(
            [{"key": "f1", "actions": actions}])
        for _ in range(3):
            runner.handle_key("f1")
        self.assertEqual(performed, [A1, A1, A2])
        self.assertEqual(state.indices["f1"], 1)  # v0.4 §4.1: 単発は先頭の loop_start も先行処理
        self.assertEqual(state.loop_frames["f1"], [LoopFrame(0, 1)])

    def test_single_loop_prepares_each_iteration_and_exits_on_third_press(self):
        actions = [{"type": "system", "op": "loop_start", "count": 3}, A1,
                   {"type": "system", "op": "loop_end"}, A2]
        runner, state, _scheduler, performed = make_runner([{"key": "f1", "actions": actions}])
        for iteration in (2, 3):
            runner.handle_key("f1")
            self.assertEqual(state.indices["f1"], 1)
            self.assertEqual(state.loop_frames["f1"], [LoopFrame(0, iteration)])
        runner.handle_key("f1")
        self.assertEqual(performed, [A1, A1, A1])
        self.assertEqual((state.indices["f1"], state.loop_frames["f1"]), (3, []))

    def test_single_counter_at_head_is_prepared_after_each_action(self):
        actions = [{"type": "system", "op": "counter_inc", "counter": "n"}, A1]
        runner, state, _scheduler, performed = make_runner([{"key": "f1", "actions": actions}])
        seen = []
        def perform(action):
            seen.append(state.counters["n"])
            performed.append(action)
        runner._perform_action = perform
        for expected in (1, 2, 3):
            runner.handle_key("f1")
            self.assertEqual(seen[-1], expected)
            self.assertEqual(state.counters["n"], expected)
            self.assertEqual(state.indices["f1"], 1)
            self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(performed, [A1, A1, A1])
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas,
                         [("n", 1)])

    def test_other_trigger_file_line_reads_current_counter_before_deferred_step(self):
        actions = [{"type": "system", "op": "counter_inc", "counter": "n"}, A1]
        file_line = {"type": "file_line", "counter": "n"}
        triggers = [{"key": "f1", "actions": actions},
                    {"key": "f2", "actions": [file_line]}]
        runner, state, _scheduler, _performed = make_runner(triggers)
        seen = []
        runner._perform_action = lambda action: seen.append((action, state.counters.get("n", 0)))
        runner.handle_key("f1")
        runner.handle_key("f2")
        self.assertEqual(seen, [(A1, 1), (file_line, 1)])
        runner.handle_key("f1")
        runner.handle_key("f2")
        self.assertEqual(seen[-2:], [(A1, 2), (file_line, 2)])

    def test_settle_stops_at_control_and_error_rows_without_early_notification(self):
        for op in ("wait", "back", "rewind", "unknown"):
            with self.subTest(op=op):
                action = {"type": "system", "op": op, "ms": 4}
                runner, state, scheduler, performed = make_runner(
                    [{"key": "f1", "actions": [A1, action, A2]}]
                )
                runner._notify_error = Mock()
                runner.handle_key("f1")
                self.assertEqual(performed, [A1])
                self.assertEqual(state.indices["f1"], 1)
                self.assertEqual(state.counters, {})
                self.assertEqual(scheduler.queue, [])
                runner._notify_error.assert_not_called()
                if op == "unknown":
                    runner.handle_key("f1")
                    runner._notify_error.assert_called_once()
                    self.assertEqual(state.indices["f1"], 1)

    def test_error_after_deferred_counter_applies_it_at_next_step_only(self):
        actions = [A1, {"type": "system", "op": "counter_inc", "counter": "n"},
                   {"type": "system", "op": "counter_reset", "counter": " "}]
        runner, state, _scheduler, performed = make_runner([{"key": "f1", "actions": actions}])
        runner._notify_error = Mock()
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        self.assertEqual(state.indices["f1"], 2)
        self.assertEqual(state.counters, {})
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [])
        runner._notify_error.assert_not_called()
        runner.handle_key("f1")
        runner._notify_error.assert_called_once()
        self.assertEqual((state.indices["f1"], state.counters["n"]), (2, 1))
        self.assertEqual(state.deferred_counters["f1"], [])

    def test_continuous_settle_reaches_end_and_stops_without_restarting_head(self):
        actions = [A1, {"type": "system", "op": "counter_inc", "counter": "n"}]
        runner, state, scheduler, performed = make_runner(
            [{"key": "f1", "run_to_end": True, "actions": actions}]
        )
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        # v0.6 §2-27: 連続実行が末尾で停止するときは保留をその場で反映し、最後のステップの差分に入れる
        self.assertEqual(state.counters, {"n": 1})
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(scheduler.queue, [])
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [("n", 1)])
        self.assertEqual(state.deferred_counters["f1"], [])

    def test_back_undoes_counter_changes_after_normal_action(self):
        trigger = {"key": "f1", "actions": [
            {"type": "system", "op": "counter_inc", "counter": "n"}, A1,
        ]}
        back = {"key": "f2", "actions": [{"type": "system", "op": "back"}]}
        runner, state, _scheduler, performed = make_runner([trigger, back])
        runner.handle_key("f1")
        self.assertEqual((state.indices["f1"], state.counters["n"]), (1, 1))
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        runner.handle_key("f2")
        self.assertEqual((state.indices["f1"], state.counters["n"]), (0, 0))
        self.assertEqual(state.deferred_counters["f1"], [])
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(performed, [A1])

    def test_single_wait_continuation_settles_after_normal_action(self):
        actions = [{"type": "system", "op": "wait", "ms": 1}, A1,
                   {"type": "system", "op": "counter_inc", "counter": "n"}, A2]
        runner, state, scheduler, performed = make_runner([{"key": "f1", "actions": actions}])
        runner.handle_key("f1")
        self.assertEqual(performed, [])
        scheduler.run_pending()
        self.assertEqual(performed, [A1])
        self.assertEqual(state.indices["f1"], 3)
        self.assertEqual(state.counters, {})
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [])

    def test_deferred_counter_applies_once_before_wait_and_survives_resume(self):
        actions = [A1, {"type": "system", "op": "counter_inc", "counter": "n"},
                   {"type": "system", "op": "wait", "ms": 1}, A2]
        runner, state, scheduler, performed = make_runner([{"key": "f1", "actions": actions}])
        runner.handle_key("f1")
        self.assertEqual(state.counters, {})
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        runner.handle_key("f1")
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.deferred_counters["f1"], [])
        scheduler.run_pending()
        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.history_for("")["f1"][-1].counter_deltas, [("n", 1)])

    def test_continuous_steps_through_system_rows(self):
        actions = [{"type": "system", "op": "counter_inc", "counter": "n"}, A1,
                   {"type": "system", "op": "counter_reset", "counter": "n"}, A2]
        runner, state, scheduler, performed = make_runner(
            [{"key": "f1", "run_to_end": True, "actions": actions}])
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        self.assertEqual(state.counters["n"], 1)  # v0.5 §4.1: reset は次ステップまで保留
        self.assertEqual(state.deferred_counters["f1"], [("counter_reset", "n")])
        scheduler.run_pending()
        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.counters["n"], 0)
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(state.indices["f1"], 0)

    def test_single_system_only_wraps_once(self):
        action = {"type": "system", "op": "counter_inc", "counter": "n"}
        runner, state, _scheduler, performed = make_runner(
            [{"key": "f1", "actions": [action]}])
        runner.handle_key("f1")
        self.assertEqual(state.counters, {"n": 1})
        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(performed, [])
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [("n", 1)])
        self.assertEqual(state.last_trigger, ("", "f1"))

    def test_failed_normal_action_stays_on_row_after_system(self):
        action = {"type": "system", "op": "counter_inc", "counter": "n"}
        runner, state, _scheduler, _performed = make_runner(
            [{"key": "f1", "actions": [action, A1]}])
        runner._perform_action = lambda _action: False
        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(state.counters, {"n": 1})
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [("n", 1)])
        self.assertEqual(state.last_trigger, ("", "f1"))

    def test_error_notifies_and_keeps_position(self):
        for continuous in (False, True):
            action = {"type": "system", "op": "unknown"}
            runner, state, scheduler, performed = make_runner(
                [{"key": "f1", "run_to_end": continuous, "actions": [action]}])
            runner._notify_error = Mock()
            runner.handle_key("f1")
            runner._notify_error.assert_called_once()
            self.assertIsNot(runner._notify_error.call_args.args[0], action)
            self.assertEqual(runner._notify_error.call_args.args[0]["value"], "unknown")
            self.assertEqual(state.indices["f1"], 0)
            self.assertEqual(performed, [])
            self.assertEqual(scheduler.queue, [])
            if continuous:
                self.assertIsNone(state.run_to_end_key)

    def test_reset_loop_frames_uses_current_position(self):
        actions = [{"type": "system", "op": "loop_start", "count": 3}, A1,
                   {"type": "system", "op": "loop_end"}]
        runner, state, _scheduler, _performed = make_runner(
            [{"key": "f1", "actions": actions}])
        state.indices["f1"] = 1
        state.loop_frames["f1"] = [LoopFrame(0, 3)]
        runner.reset_loop_frames("f1")
        self.assertEqual(state.loop_frames["f1"], [LoopFrame(0, 1)])
        actions.pop()
        runner.reset_loop_frames("f1")
        self.assertEqual(state.loop_frames["f1"], [])

    def test_reset_loop_frames_clears_deferred_counters(self):
        actions = [{"type": "system", "op": "counter_inc", "counter": "n"}, A1]
        runner, state, _scheduler, _performed = make_runner(
            [{"key": "f1", "actions": actions}])
        runner.handle_key("f1")
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        runner.reset_loop_frames("f1")
        self.assertNotIn("f1", state.deferred_counters)
        runner.handle_key("f1")
        self.assertEqual(state.counters["n"], 1)


class BackRewindRunnerTest(unittest.TestCase):
    @staticmethod
    def control_trigger(key, op):
        return {"key": key, "run_to_end": False,
                "actions": [{"type": "system", "op": op}]}

    def test_back_restores_each_step_position_frames_and_counter(self):
        trigger = {
            "key": "f1", "run_to_end": False,
            "actions": [
                {"type": "system", "op": "loop_start", "count": 2},
                {"type": "system", "op": "counter_inc", "counter": "n"},
                A1,
                {"type": "system", "op": "loop_end"},
            ],
        }
        back = self.control_trigger("f2", "back")
        selected = []
        messages = []
        runner, state, _scheduler, _performed = make_runner(
            [trigger, back], selected=selected, messages=messages
        )

        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 2)  # v0.4 §4.1: loop_end を先行処理
        self.assertEqual(state.loop_frames["f1"], [LoopFrame(0, 2)])
        self.assertEqual(state.counters["n"], 1)  # v0.5 §4.1: 次の +1 は保留
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(len(state.history_for("")["f1"]), 1)

        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 2)  # v0.4 §4.1: 末尾から先頭の system も先行処理
        self.assertEqual(state.loop_frames["f1"], [LoopFrame(0, 1)])
        self.assertEqual(state.counters["n"], 2)
        self.assertEqual(len(state.history_for("")["f1"]), 2)

        selected.clear()
        runner.handle_key("f2")
        self.assertEqual(state.indices["f1"], 2)  # v0.4 §4.1: 先行処理込みの 1 段を戻す
        self.assertEqual(state.loop_frames["f1"], [LoopFrame(0, 2)])
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.last_trigger, ("", "f1"))
        self.assertEqual(selected, ["f2", "f1"])

        selected.clear()
        runner.handle_key("f2")
        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(state.loop_frames["f1"], [])
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.deferred_counters["f1"], [])
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(state.last_trigger, ("", "f1"))
        self.assertEqual(selected, ["f2", "f1"])

        # 履歴が空なら位置 0 のままで、何も選択・通知しない。
        selected.clear()
        runner.handle_key("f2")
        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(selected, ["f2"])
        self.assertEqual(messages, [])

    def test_rewind_clears_position_frames_and_history_without_changing_counters(self):
        trigger = {
            "key": "f1", "run_to_end": False,
            "actions": [
                {"type": "system", "op": "loop_start", "count": 2},
                {"type": "system", "op": "counter_inc", "counter": "n"},
                A1,
                {"type": "system", "op": "loop_end"},
            ],
        }
        selected = []
        runner, state, _scheduler, _performed = make_runner(
            [trigger, self.control_trigger("f2", "rewind")], selected=selected
        )
        runner.handle_key("f1")
        self.assertTrue(state.history_for("")["f1"])
        state.counters["n"] = 23
        selected.clear()

        runner.handle_key("f2")

        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(state.loop_frames["f1"], [])
        self.assertNotIn("f1", state.deferred_counters)
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(state.counters["n"], 23)
        self.assertEqual(state.last_trigger, ("", "f1"))
        self.assertEqual(selected, ["f2", "f1"])

    def test_back_only_trigger_does_not_replace_last_trigger_and_error_step_does(self):
        failed = {
            "key": "f1", "run_to_end": False,
            "actions": [
                {"type": "system", "op": "counter_inc", "counter": "n"},
                {"type": "system", "op": "not_a_control"},
            ],
        }
        runner, state, _scheduler, _performed = make_runner(
            [failed, self.control_trigger("f2", "back")]
        )

        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.last_trigger, ("", "f1"))

        runner.handle_key("f2")

        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(state.last_trigger, ("", "f1"))

    def test_missing_self_and_inactive_targets_only_show_message(self):
        cases = (
            ("unset", None),
            ("self", ("", "f2")),
            ("missing from active triggers", ("", "gone")),
        )
        for label, last_trigger in cases:
            with self.subTest(target=label):
                messages = []
                selected = []
                runner, state, _scheduler, performed = make_runner(
                    [self.control_trigger("f2", "back")],
                    selected=selected, messages=messages,
                )
                state.last_trigger = last_trigger

                runner.handle_key("f2")

                self.assertEqual(messages, ["戻す対象のトリガーがありません"])
                self.assertEqual(selected, ["f2"])
                self.assertEqual(performed, [])
                self.assertEqual(state.indices_for(""), {"f2": 0})
                self.assertEqual(state.history_for(""), {})
                self.assertEqual(state.counters, {})
                self.assertEqual(state.last_trigger, last_trigger)

    def test_pending_target_only_shows_waiting_message(self):
        target = {
            "key": "f1", "run_to_end": False,
            "actions": [A1, {"type": "system", "op": "wait", "ms": 13}, A2],
        }
        selected = []
        messages = []
        runner, state, scheduler, performed = make_runner(
            [target, self.control_trigger("f2", "back")],
            selected=selected, messages=messages,
        )
        runner.handle_key("f1")  # 完了したステップで f1 が直前のトリガーになる
        runner.handle_key("f1")  # 待機中のステップを作る
        self.assertIn(("", "f1"), state.pending_steps)
        selected.clear()

        runner.handle_key("f2")

        self.assertEqual(messages, ["対象のトリガーが待機中のため操作できません"])
        self.assertEqual(selected, ["f2"])
        self.assertEqual(performed, [A1])
        self.assertEqual(len(scheduler.queue), 1)
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.last_trigger, ("", "f1"))

    def test_cancelled_single_wait_pushes_partial_step_for_back(self):
        target = {
            "key": "f1", "run_to_end": False,
            "actions": [
                {"type": "system", "op": "counter_inc", "counter": "n"},
                {"type": "system", "op": "wait", "ms": 17}, A1,
            ],
        }
        runner, state, scheduler, performed = make_runner(
            [target, self.control_trigger("f2", "back")]
        )

        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.history_for(""), {})
        self.assertEqual(state.last_trigger, None)

        runner.cancel_pending_wait("f1")
        self.assertEqual(state.indices["f1"], 1)  # 待機の行で止まる
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [("n", 1)])
        self.assertEqual(state.last_trigger, ("", "f1"))
        self.assertEqual(scheduler.queue, [])

        runner.handle_key("f2")
        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(performed, [])

    def test_continuous_run_records_each_completed_step(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [
                {"type": "system", "op": "counter_inc", "counter": "n"}, A1,
                {"type": "system", "op": "counter_inc", "counter": "n"}, A2,
            ],
        }
        runner, state, scheduler, performed = make_runner([trigger])

        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.counters["n"], 1)  # v0.5 §4.1: A1 直後の +1 は保留
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas,
                         [("n", 1)])
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(state.last_trigger, ("", "f1"))
        scheduler.run_pending()

        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.counters["n"], 2)
        self.assertEqual(state.history_for("")["f1"][-1].counter_deltas, [("n", 1)])
        self.assertEqual(len(state.history_for("")["f1"]), 2)
        self.assertIsNone(state.run_to_end_key)

    def test_reset_and_runtime_lifecycle_keep_history_with_trigger_state(self):
        trigger = {"key": "f1", "run_to_end": False, "actions": [A1, A2]}
        runner, state, _scheduler, _performed = make_runner([trigger])
        runner.handle_key("f1")
        self.assertTrue(state.history_for("")["f1"])
        self.assertEqual(state.last_trigger, ("", "f1"))

        runner.reset_loop_frames("f1")  # 位置変更・編集時の共通入口
        self.assertNotIn("f1", state.history_for(""))
        self.assertIsNone(state.last_trigger)

        runner.handle_key("f1")
        self.assertTrue(state.history_for("")["f1"])
        state.forget_trigger("", "f1")  # トリガー削除
        self.assertNotIn("f1", state.history_for(""))
        self.assertIsNone(state.last_trigger)

        runner.handle_key("f1")
        self.assertTrue(state.history_for("")["f1"])
        state.rekey_trigger("", "f1", "f9")  # キー変更
        self.assertNotIn("f1", state.history_for(""))
        self.assertTrue(state.history_for("")["f9"])
        self.assertEqual(state.last_trigger, ("", "f9"))

        state.reset_indices()
        self.assertEqual(state.history, {})
        self.assertEqual(state.keymap_history, {})
        self.assertIsNone(state.last_trigger)

    def test_rekey_trigger_set_moves_history_and_last_trigger(self):
        current = {"id": "first"}
        trigger = {"key": "f1", "run_to_end": False, "actions": [A1, A2]}
        runner, state, _scheduler, _performed = make_runner(
            [trigger], get_trigger_set_id=lambda: current["id"]
        )
        runner.handle_key("f1")
        self.assertTrue(state.history_for("first")["f1"])
        self.assertEqual(state.last_trigger, ("first", "f1"))

        current["id"] = "second"
        state.rekey_trigger_set("first", "second")

        self.assertNotIn("first", state.keymap_history)
        self.assertTrue(state.history_for("second")["f1"])
        self.assertEqual(state.last_trigger, ("second", "f1"))

    def test_trigger_set_change_forgets_its_history_and_last_trigger(self):
        current = {"id": "first"}
        trigger = {"key": "f1", "run_to_end": False, "actions": [A1, A2]}
        runner, state, _scheduler, _performed = make_runner(
            [trigger], get_trigger_set_id=lambda: current["id"]
        )
        runner.handle_key("f1")
        self.assertTrue(state.history_for("first")["f1"])
        state.forget_trigger_set("first")

        self.assertNotIn("first", state.keymap_history)
        self.assertIsNone(state.last_trigger)


class RunToEndTest(unittest.TestCase):
    def make_run_to_end_runner(self):
        trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0, "actions": [A1, A2]}
        return make_runner([trigger])

    def test_runs_all_actions_then_stops(self):
        runner, state, scheduler, performed = self.make_run_to_end_runner()
        runner.handle_key("f1")  # 1アクション目は同期実行される
        self.assertEqual(performed, [A1])
        scheduler.run_pending()
        self.assertEqual(performed, [A1, A2])
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(state.indices["f1"], 0)

    def test_same_key_toggles_pause_and_resume(self):
        runner, state, scheduler, performed = self.make_run_to_end_runner()
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        runner.handle_key("f1")  # 実行中に同キー → 一時停止
        self.assertTrue(state.run_to_end_paused)
        self.assertEqual(scheduler.queue, [])  # 予約がキャンセルされている
        runner.handle_key("f1")  # 再開
        self.assertFalse(state.run_to_end_paused)
        scheduler.run_pending()
        self.assertEqual(performed, [A1, A2])
        self.assertIsNone(state.run_to_end_key)

    def test_terminal_deferred_counter_is_applied_and_undone_with_last_step(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [A1, {"type": "system", "op": "counter_inc", "counter": "n"}],
        }
        back = {"key": "f2", "actions": [{"type": "system", "op": "back"}]}
        runner, state, _scheduler, _performed = make_runner([trigger, back])

        runner.handle_key("f1")

        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.deferred_counters["f1"], [])
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [("n", 1)])
        runner.handle_key("f2")
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.deferred_counters["f1"], [])

    def test_old_continuous_callback_cannot_advance_a_new_run(self):
        trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
                   "actions": [A1, A2, {"type": "text", "value": "three"}]}
        runner, state, scheduler, performed = make_runner([trigger])

        runner.handle_key("f1")
        old_callback = scheduler.queue[0][1]
        runner.stop_run_to_end()
        runner.handle_key("f1")
        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.run_to_end_key, "f1")

        old_callback()

        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.run_to_end_key, "f1")


class ActionExecutorRunnerTest(unittest.TestCase):
    def make_executor_runner(self, actions, *, run_to_end=True):
        self.gateway = Mock()
        self.validate_hotkey = Mock(return_value=("", "ctrl+c"))
        self.on_action_error = Mock()
        self.on_runtime_error = Mock()
        executor = ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=self.validate_hotkey,
            on_action_error=self.on_action_error,
            on_runtime_error=self.on_runtime_error,
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
        )
        state = AppState()
        scheduler = FakeScheduler()
        trigger = {
            "key": "f1", "run_to_end": run_to_end,
            "run_to_end_delay_ms": 0, "actions": actions,
        }
        runner = SequenceRunner(
            state=state, find_trigger=Mock(return_value=trigger),
            perform_action=executor.execute, select_trigger=Mock(),
            refresh_actions=Mock(), update_status=Mock(),
            after=scheduler.after, after_cancel=scheduler.after_cancel,
        )
        return runner, state, scheduler

    def test_run_to_end_stops_at_invalid_type(self):
        runner, state, scheduler = self.make_executor_runner(
            [A1, {"type": "hotky"}, A2]
        )
        runner.handle_key("f1")
        self.gateway.write_text.assert_called_once_with("one")
        scheduler.run_pending()
        self.assertIsNone(state.run_to_end_key)
        self.assertFalse(state.run_to_end_paused)
        self.assertIsNone(state.run_to_end_after_id)
        self.assertEqual(scheduler.queue, [])
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(self.gateway.method_calls, [call.write_text("one")])
        self.on_action_error.assert_called_once()

    def test_single_invalid_type_can_be_retried_without_advancing(self):
        runner, state, _scheduler = self.make_executor_runner(
            [{"type": "hotky"}], run_to_end=False
        )
        for count in (1, 2):
            runner.handle_key("f1")
            self.assertEqual(state.indices.get("f1", 0), 0)
            self.assertEqual(state.reentry_guard, set())
            self.assertEqual(self.on_action_error.call_count, count)
        self.assertEqual(self.gateway.method_calls, [])

    def test_single_action_keeps_index_after_valid_then_invalid(self):
        runner, state, _scheduler = self.make_executor_runner(
            [A1, {"type": "hotky"}], run_to_end=False
        )
        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 1)
        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(state.reentry_guard, set())
        self.assertEqual(self.gateway.method_calls, [call.write_text("one")])
        self.on_action_error.assert_called_once()

    def test_error_notification_pause_resume_leaves_no_pending_action(self):
        runner, state, scheduler = self.make_executor_runner(
            [A1, {"type": "hotky"}, A2]
        )

        def reenter(_action, _error):
            runner.handle_key("f1")
            self.assertTrue(state.run_to_end_paused)
            self.assertEqual(scheduler.queue, [])
            runner.handle_key("f1")
            self.assertFalse(state.run_to_end_paused)
            self.assertEqual(len(scheduler.queue), 1)

        self.on_action_error.side_effect = reenter
        runner.handle_key("f1")
        scheduler.run_pending()
        self.assertEqual(self.gateway.method_calls, [call.write_text("one")])
        self.on_action_error.assert_called_once()
        self.assertEqual(state.indices["f1"], 1)
        self.assertIsNone(state.run_to_end_key)
        self.assertFalse(state.run_to_end_paused)
        self.assertIsNone(state.run_to_end_after_id)
        self.assertEqual(scheduler.queue, [])

    def test_known_type_errors_allow_run_to_end_to_finish(self):
        bad_hotkey = {"type": "hotkey", "value": "bad"}
        bad_mouse = {"type": "mouse_click", "x": "bad", "y": 200}
        runner, state, scheduler = self.make_executor_runner(
            [bad_hotkey, bad_mouse, A2]
        )
        self.validate_hotkey.return_value = ("エラー", "")
        runner.handle_key("f1")
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(state.run_to_end_key, "f1")
        self.on_action_error.assert_called_once_with(bad_hotkey, "エラー")
        scheduler.run_pending()
        self.on_runtime_error.assert_called_once_with(
            "送信エラー", "mouse_click の x/y が不正です（整数で指定してください）。"
        )
        self.assertEqual(self.gateway.method_calls, [call.write_text("two")])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(scheduler.queue, [])

    def test_none_result_keeps_advancing_in_both_modes(self):
        for run_to_end in (False, True):
            with self.subTest(run_to_end=run_to_end):
                trigger = {
                    "key": "f1", "run_to_end": run_to_end, "actions": [A1, A2]
                }
                runner, state, scheduler, performed = make_runner([trigger])
                runner.handle_key("f1")
                self.assertEqual(state.indices["f1"], 1)
                if run_to_end:
                    scheduler.run_pending()
                else:
                    runner.handle_key("f1")
                self.assertEqual(performed, [A1, A2])
                self.assertEqual(state.indices["f1"], 0)
                self.assertIsNone(state.run_to_end_key)
                self.assertEqual(scheduler.queue, [])


class WaitSequenceRunnerTest(unittest.TestCase):
    def test_single_wait_resumes_with_next_action(self):
        trigger = {"key": "f1", "run_to_end": False,
                   "actions": [{"type": "system", "op": "wait", "ms": "17"}, A1]}
        runner, state, scheduler, performed = make_runner([trigger])

        runner.handle_key("f1")

        self.assertEqual(performed, [])
        self.assertEqual(state.indices["f1"], 0)  # 単発の保留中は待機行を保持
        self.assertEqual(scheduler.delays, [17])
        pending = state.pending_steps[("", "f1")]
        self.assertEqual(pending.position, 1)  # 続きは待機の次から
        self.assertIsInstance(pending.resume, StepResume)
        self.assertEqual(len(scheduler.queue), 1)

        scheduler.run_pending()

        self.assertEqual(performed, [A1])
        self.assertNotIn(("", "f1"), state.pending_steps)
        self.assertEqual(state.reentry_guard, set())

    def test_continuation_can_wait_again_and_old_generation_is_ignored(self):
        trigger = {
            "key": "f1", "run_to_end": False,
            "actions": [
                {"type": "system", "op": "wait", "ms": 2},
                {"type": "system", "op": "wait", "ms": 3},
                A1,
            ],
        }
        runner, state, scheduler, performed = make_runner([trigger])

        runner.handle_key("f1")
        first_callback = scheduler.queue[0][1]
        first_generation = state.pending_steps[("", "f1")].generation
        scheduler.run_one()

        second_pending = state.pending_steps[("", "f1")]
        self.assertGreater(second_pending.generation, first_generation)
        self.assertEqual(second_pending.position, 2)
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(scheduler.delays, [2, 3])

        first_callback()  # 古い世代の callback は新しい保留を消さない
        self.assertEqual(performed, [])
        self.assertIn(("", "f1"), state.pending_steps)
        scheduler.run_pending()
        self.assertEqual(performed, [A1])

    def test_pending_single_wait_blocks_same_key_but_allows_another_key(self):
        triggers = [
            {"key": "f1", "run_to_end": False,
             "actions": [{"type": "system", "op": "wait", "ms": 9}, A1]},
            {"key": "f2", "run_to_end": False, "actions": [A2]},
        ]
        runner, _state, scheduler, performed = make_runner(triggers)

        runner.handle_key("f1")
        runner.handle_key("f1")
        self.assertEqual(len(scheduler.queue), 1)
        self.assertEqual(performed, [])

        runner.handle_key("f2")
        self.assertEqual(performed, [A2])
        scheduler.run_pending()
        self.assertEqual(performed, [A2, A1])

    def test_cancelled_wait_callbacks_are_stale_and_keep_wait_position(self):
        cancel_operations = (
            ("cancel one", lambda runner, state: runner.cancel_pending_wait("f1")),
            ("cancel all", lambda runner, state: runner.cancel_pending_waits()),
            ("reset frames", lambda runner, state: runner.reset_loop_frames("f1")),
            ("reset indices", lambda _runner, state: state.reset_indices()),
        )
        for name, cancel in cancel_operations:
            with self.subTest(operation=name):
                trigger = {"key": "f1", "run_to_end": False,
                           "actions": [{"type": "system", "op": "wait", "ms": 11}, A1]}
                runner, state, scheduler, performed = make_runner([trigger])
                runner.handle_key("f1")
                stale_callback = scheduler.queue[0][1]

                cancel(runner, state)
                if name == "reset indices":
                    scheduler.run_pending()  # 残った予約が発火しても何もしない
                else:
                    stale_callback()  # 取消後も出列済みの callback が呼ばれた場合を再現

                self.assertEqual(performed, [])
                self.assertEqual(state.indices.get("f1", 0), 0)
                self.assertNotIn(("", "f1"), state.pending_steps)
                self.assertEqual(scheduler.queue, [])

    def test_callback_is_ignored_when_trigger_set_changes(self):
        current = {"id": "first"}
        trigger = {"key": "f1", "run_to_end": False,
                   "actions": [{"type": "system", "op": "wait", "ms": 13}, A1]}
        runner, state, scheduler, performed = make_runner(
            [trigger], get_trigger_set_id=lambda: current["id"]
        )
        runner.handle_key("f1")
        stale_callback = scheduler.queue[0][1]

        current["id"] = "second"
        stale_callback()

        self.assertEqual(performed, [])
        self.assertEqual(state.indices_for("first").get("f1"), 0)

    def test_continuous_wait_uses_wait_duration_without_an_extra_interval(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 3,
            "actions": [A1, {"type": "system", "op": "wait", "ms": 40}, A2],
        }
        runner, state, scheduler, performed = make_runner([trigger])

        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        scheduler.run_one()  # 通常間隔の後に待機行を処理

        self.assertEqual(scheduler.delays, [3, 40])
        self.assertEqual(state.indices["f1"], 2)  # 連続実行は待機の次を保存
        scheduler.run_pending()

        self.assertEqual(performed, [A1, A2])
        self.assertEqual(scheduler.delays, [3, 40])  # 待機後に通常間隔を足さない
        self.assertIsNone(state.run_to_end_key)

    def test_pausing_wait_discards_it_and_resume_starts_after_wait(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 7,
            "actions": [A1, {"type": "system", "op": "wait", "ms": 50}, A2],
        }
        runner, state, scheduler, performed = make_runner([trigger])

        runner.handle_key("f1")
        scheduler.run_one()  # interval callback reaches the wait
        self.assertEqual(state.indices["f1"], 2)
        self.assertEqual(scheduler.delays, [7, 50])

        runner.handle_key("f1")
        self.assertTrue(state.run_to_end_paused)
        self.assertEqual(scheduler.queue, [])
        runner.handle_key("f1")
        self.assertFalse(state.run_to_end_paused)
        self.assertEqual(scheduler.delays, [7, 50, 7])
        scheduler.run_pending()

        self.assertEqual(performed, [A1, A2])
        self.assertIsNone(state.run_to_end_key)

    def test_other_continuous_run_cancels_single_wait(self):
        triggers = [
            {"key": "f1", "run_to_end": False,
             "actions": [{"type": "system", "op": "wait", "ms": 19}, A1]},
            {"key": "f2", "run_to_end": True, "run_to_end_delay_ms": 0,
             "actions": [A2]},
        ]
        runner, state, scheduler, performed = make_runner(triggers)

        runner.handle_key("f1")
        stale_callback = scheduler.queue[0][1]
        runner.handle_key("f2")
        stale_callback()

        self.assertEqual(performed, [A2])
        self.assertNotIn(("", "f1"), state.pending_steps)
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)

    def test_reset_loop_frames_during_paused_run_discards_old_wait_snapshot(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [
                {"type": "system", "op": "counter_inc", "counter": "n"},
                {"type": "system", "op": "wait", "ms": 25}, A1,
            ],
        }
        runner, state, scheduler, performed = make_runner([trigger])
        runner.handle_key("f1")
        runner.pause_run_to_end()
        state.indices["f1"] = 2

        runner.reset_loop_frames("f1")
        runner.resume_run_to_end()
        scheduler.run_pending()

        self.assertEqual(performed, [A1])
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [])

    def test_stopping_during_continuous_wait_records_partial_step_for_back(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [
                {"type": "system", "op": "counter_inc", "counter": "n"},
                {"type": "system", "op": "wait", "ms": 25}, A1,
            ],
        }
        back = {"key": "f2", "actions": [{"type": "system", "op": "back"}]}
        runner, state, scheduler, performed = make_runner([trigger, back])
        runner.handle_key("f1")

        runner.stop_run_to_end()

        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        self.assertEqual(state.history_for("")["f1"][0].counter_deltas, [("n", 1)])
        self.assertEqual(state.last_trigger, ("", "f1"))
        self.assertEqual(scheduler.queue, [])
        runner.handle_key("f2")
        self.assertEqual(state.indices["f1"], 0)
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.history_for("")["f1"], [])
        self.assertEqual(performed, [])

    def test_pausing_and_resuming_continuous_wait_keeps_resume_semantics(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [A1, {"type": "system", "op": "wait", "ms": 25}, A2],
        }
        runner, state, scheduler, performed = make_runner([trigger])
        runner.handle_key("f1")
        self.assertEqual(len(state.history_for("")["f1"]), 1)
        scheduler.run_one()  # 到達した待機を一時停止する
        runner.pause_run_to_end()
        runner.resume_run_to_end()
        scheduler.run_pending()

        self.assertEqual(performed, [A1, A2])
        self.assertEqual(len(state.history_for("")["f1"]), 2)
        self.assertIsNone(state.run_to_end_key)

    def test_system_runtime_error_notification_describes_action_and_label(self):
        action = {"type": "system", "op": "loop_start", "count": "abc", "label": "outer"}
        trigger = {"key": "f1", "actions": [action]}
        runner, _state, _scheduler, _performed = make_runner([trigger])
        runner._notify_error = Mock()

        runner.handle_key("f1")

        notified_action, message = runner._notify_error.call_args.args
        self.assertEqual(notified_action["value"], "loop_start 回数=abc")
        self.assertIn("loop_start 回数=abc", message)
        self.assertIn("ラベル: outer", message)
        self.assertNotIn("value", action)

    def test_continuous_wait_stop_does_not_flush_future_counter(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [A1, {"type": "system", "op": "wait", "ms": 25},
                        {"type": "system", "op": "counter_inc", "counter": "n"}],
        }
        runner, state, scheduler, _performed = make_runner([trigger])
        runner.handle_key("f1")
        scheduler.run_one()

        runner.stop_run_to_end()

        self.assertEqual(state.counters.get("n", 0), 0)

    def test_continuous_error_stop_does_not_flush_later_counter(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [A1, {"type": "system", "op": "wait", "ms": "bad"},
                        {"type": "system", "op": "counter_inc", "counter": "n"}],
        }
        runner, state, scheduler, _performed = make_runner([trigger])
        runner.handle_key("f1")
        scheduler.run_one()

        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(state.counters.get("n", 0), 0)

    def test_continuous_pause_does_not_flush_future_counter(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [A1, {"type": "system", "op": "wait", "ms": 25},
                        {"type": "system", "op": "counter_inc", "counter": "n"}],
        }
        runner, state, scheduler, _performed = make_runner([trigger])
        runner.handle_key("f1")
        scheduler.run_one()

        runner.pause_run_to_end()

        self.assertEqual(state.counters.get("n", 0), 0)

    def test_cancelled_wait_with_deferred_counter_can_be_undone(self):
        trigger = {
            "key": "f1", "run_to_end": False,
            "actions": [
                A1,
                {"type": "system", "op": "counter_inc", "counter": "n"},
                {"type": "system", "op": "wait", "ms": 5}, A2,
            ],
        }
        back = {"key": "f2", "actions": [{"type": "system", "op": "back"}]}
        runner, state, _scheduler, _performed = make_runner([trigger, back])
        runner.handle_key("f1")
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        runner.handle_key("f1")
        runner.cancel_pending_wait("f1")

        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.deferred_counters["f1"], [])
        runner.handle_key("f2")
        self.assertEqual(state.indices["f1"], 2)
        self.assertEqual(state.deferred_counters["f1"], [("counter_inc", "n")])
        self.assertEqual(state.counters["n"], 0)

    def test_uppercase_wait_error_notification_includes_value(self):
        trigger = {"key": "f1", "actions": [{"type": "system", "op": "WAIT", "ms": 0}]}
        runner, _state, _scheduler, _performed = make_runner([trigger])
        runner._notify_error = Mock()

        runner.handle_key("f1")

        notified_action, message = runner._notify_error.call_args.args
        self.assertEqual(notified_action["value"], "WAIT 0ms")
        self.assertIn("WAIT 0ms", message)


if __name__ == "__main__":
    unittest.main()
