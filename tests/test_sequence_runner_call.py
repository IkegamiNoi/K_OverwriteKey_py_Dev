import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner
from keyseq.application.sequence_steps import LoopFrame


def system(op, **values):
    return {"type": "system", "op": op, **values}


def call(target, *, step=False):
    return system("call", target=target, **({"step": True} if step else {}))


def text(value):
    return {"type": "text", "value": value}


class FakeScheduler:
    def __init__(self):
        self.queue = []
        self.delays = []
        self.cancelled = []
        self._next_id = 1

    def after(self, delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.delays.append(delay_ms)
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.cancelled.append(handle)
        self.queue = [(item, callback) for item, callback in self.queue if item != handle]

    def run_one(self):
        handle, callback = self.queue.pop(0)
        callback()
        return handle


class SequenceRunnerCallTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.trigger_set_id = "set"
        self.trigger_sets = {"set": []}
        self.scheduler = FakeScheduler()
        self.performed = []
        self.messages = []
        self.errors = []
        self.selected = []
        self.begin_results = []
        self.poll_results = []
        self.begin_result = object()
        self.perform_result = True
        self.perform_callback = None
        self.runner = SequenceRunner(
            state=self.state,
            find_trigger=self._find_trigger,
            perform_action=self._perform,
            select_trigger=self.selected.append,
            refresh_actions=lambda: None,
            update_status=lambda: None,
            after=self.scheduler.after,
            after_cancel=self.scheduler.after_cancel,
            get_trigger_set_id=lambda: self.trigger_set_id,
            notify_error=lambda action, message: self.errors.append((action, message)),
            notify_message=self.messages.append,
            begin_file_line=self._begin,
            poll_file_line=self._poll,
        )

    def _find_trigger(self, key):
        return next((item for item in self.trigger_sets.get(self.trigger_set_id, [])
                     if item["key"] == key), None)

    def _perform(self, action):
        self.performed.append(action)
        if self.perform_callback is not None:
            self.perform_callback()
        return self.perform_result

    def _begin(self, action):
        self.begin_results.append(action)
        return self.begin_result

    def _poll(self, handle):
        return self.poll_results.pop(0)

    def trigger(self, key, actions, *, delay=7, trigger_set_id=None, run_to_end=False):
        trigger = {"key": key, "actions": actions, "run_to_end": run_to_end,
                   "run_to_end_delay_ms": delay}
        self.trigger_sets.setdefault(trigger_set_id or self.trigger_set_id, []).append(trigger)
        return trigger

    def run_all(self):
        while self.scheduler.queue:
            self.scheduler.run_one()

    def index(self, key, trigger_set_id="set"):
        return self.state.indices_for(trigger_set_id).get(key, 0)

    def history(self, key="f1", trigger_set_id="set"):
        return self.state.history_for(trigger_set_id).get(key, [])

    def test_01_single_press_calls_target_and_returns_to_callers_next_action(self):
        self.trigger("f1", [call("f5"), text("X")])
        self.trigger("f5", [text("A"), text("B")], delay=17)

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays, [0])
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.scheduler.delays[-1], 17)
        self.scheduler.run_one()

        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])
        self.assertEqual(self.index("f1"), 1)
        self.assertEqual(self.index("f5"), 0)

    def test_step_call_advances_one_target_action_per_press_and_keeps_one_history_step(self):
        self.trigger("f1", [call("f5", step=True), text("X")])
        self.trigger("f5", [system("counter_inc", counter="n"), text("A"),
                             system("stop"), text("B")], delay=17)

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays, [0])
        self.scheduler.run_one()
        pending = self.state.pending_steps[("set", "f1")]
        self.assertTrue(pending.call_paused)
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.index("f1"), 0)
        self.assertEqual(self.history("f1"), [])
        self.assertEqual(self.state.counters.get("n"), 1)

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays[-1], 0)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])
        self.assertNotIn(("set", "f1"), self.state.pending_steps)
        self.assertEqual(self.index("f1"), 1)
        self.assertEqual(len(self.history("f1")), 1)

        self.runner.handle_key("f1")
        self.assertEqual([item["value"] for item in self.performed], ["A", "B", "X"])

        self.trigger("f2", [system("back")])
        self.runner.handle_key("f2")
        self.assertEqual(self.state.counters.get("n"), 1)
        self.runner.handle_key("f2")
        self.assertEqual(self.state.counters.get("n"), 0)

    def test_step_call_allows_other_single_trigger_between_actions(self):
        self.trigger("f1", [call("f5", step=True), text("caller")])
        self.trigger("f5", [text("A"), text("B")])
        self.trigger("f2", [text("other")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertTrue(self.state.pending_steps[("set", "f1")].call_paused)

        self.runner.handle_key("f2")
        self.assertEqual([item["value"] for item in self.performed], ["A", "other"])
        self.assertIn(("set", "f1"), self.state.pending_steps)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "other", "B"])
        self.assertNotIn(("set", "f1"), self.state.pending_steps)
        self.assertEqual(len(self.history("f1")), 1)

    def test_step_call_gap_discards_call_when_other_continuous_run_starts(self):
        self.trigger("f1", [call("f5", step=True), text("caller")])
        self.trigger("f5", [text("A"), text("B")])
        self.trigger("f2", [text("continuous")], run_to_end=True)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertTrue(self.state.pending_steps[("set", "f1")].call_paused)

        self.runner.handle_key("f2")
        self.assertNotIn(("set", "f1"), self.state.pending_steps)
        self.assertEqual(self.index("f1"), 0)
        self.assertEqual(self.performed[-1]["value"], "continuous")
        self.assertTrue(any("一時停止中の実行を破棄しました（f1）" in message
                            for message in self.messages))

    def test_nested_step_call_and_empty_target_do_not_consume_extra_press(self):
        self.trigger("f1", [call("f5", step=True)])
        self.trigger("f5", [call("f7", step=True), text("B")])
        self.trigger("f7", [text("C")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["C"])
        self.assertTrue(self.state.pending_steps[("set", "f1")].call_paused)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["C", "B"])
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

        self.trigger_sets["set"] = []
        self.performed.clear()
        self.trigger("f2", [call("f8", step=True)])
        self.trigger("f8", [call("f9"), text("after empty")])
        self.trigger("f9", [])
        self.runner.handle_key("f2")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["after empty"])
        self.assertNotIn(("set", "f2"), self.state.pending_steps)

        self.trigger_sets["set"] = []
        self.performed.clear()
        self.trigger("f3", [call("f10", step=True)])
        self.trigger("f10", [call("f11"), text("parent next")])
        self.trigger("f11", [text("batch child")])
        self.runner.handle_key("f3")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["batch child"])
        self.assertTrue(self.state.pending_steps[("set", "f3")].call_paused)

        self.runner.handle_key("f3")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed],
                         ["batch child", "parent next"])
        self.assertNotIn(("set", "f3"), self.state.pending_steps)

    def test_step_call_inside_batch_call_keeps_batch_behavior(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [call("f7", step=True), text("B")])
        self.trigger("f7", [text("C")])

        self.runner.handle_key("f1")
        self.run_all()

        self.assertEqual([item["value"] for item in self.performed], ["C", "B"])
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

    def test_step_call_waits_inside_target_without_resume_interval(self):
        self.trigger("f1", [call("f5", step=True)])
        self.trigger("f5", [text("A"), system("wait", ms=100), text("B")], delay=17)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays[-1], 0)
        self.scheduler.run_one()  # call_step reaches wait at the head of this press
        self.assertEqual(self.scheduler.delays[-1], 100)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

    def test_same_key_during_step_call_wait_is_ignored_but_batch_call_still_pauses(self):
        self.trigger("f1", [call("f5", step=True)])
        self.trigger("f5", [system("wait", ms=100), text("A")], delay=17)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(self.scheduler.delays[-1], 100)
        self.assertFalse(self.state.pending_steps[("set", "f1")].call_paused)
        self.runner.handle_key("f1")
        self.assertEqual(len(self.scheduler.queue), 1)
        self.assertFalse(self.state.pending_steps[("set", "f1")].call_paused)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

        self.setUp()
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [system("wait", ms=100), text("A")], delay=17)
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(self.scheduler.delays[-1], 100)
        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.queue, [])
        self.assertTrue(self.state.pending_steps[("set", "f1")].call_paused)

    def test_02_pending_call_ignores_other_triggers_and_rejects_back_target(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [text("A"), system("wait", ms=10)])
        self.trigger("f2", [text("other")])
        self.trigger("f6", [system("back")])
        self.trigger("f7", [system("rewind")])
        self.runner.handle_key("f1")
        self.runner.handle_key("f2")
        self.trigger("f8", [text("continuous")], run_to_end=True)
        self.runner.handle_key("f8")
        self.assertEqual(len(self.scheduler.queue), 1)
        self.assertEqual(self.performed, [])
        self.assertEqual(self.index("f2"), 0)
        self.assertIsNone(self.state.run_to_end_key)

        self.run_all()
        self.assertEqual([item["value"] for item in self.performed], ["A"])

        self.run_all()
        self.trigger("f3", [call("f6")])
        self.runner.handle_key("f3")
        self.run_all()
        self.assertTrue(any("戻す・先頭へのトリガーは呼び出せません" in message
                            for _, message in self.errors))
        self.assertEqual(self.index("f3"), 0)
        self.trigger("f4", [call("f7")])
        self.runner.handle_key("f4")
        self.run_all()
        self.assertEqual(sum("戻す・先頭へのトリガーは呼び出せません" in message
                             for _, message in self.errors), 2)

    def test_single_call_can_pause_for_other_trigger_then_resume_after_target_interval(self):
        self.trigger("f1", [call("f5"), text("caller")])
        self.trigger("f5", [system("counter_inc", counter="n"), text("A"), text("B")], delay=17)
        self.trigger("f2", [text("other")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.scheduler.delays[-1], 17)

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.queue, [])
        self.assertEqual(self.index("f1"), 0)
        self.assertIn(("set", "f1"), self.state.pending_steps)

        self.runner.handle_key("f2")
        self.assertEqual([item["value"] for item in self.performed], ["A", "other"])

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays[-1], 17)
        self.run_all()
        self.assertEqual(
            [item["value"] for item in self.performed],
            ["A", "other", "B"],
        )
        self.assertNotIn(("set", "f1"), self.state.pending_steps)
        self.assertEqual(self.index("f1"), 1)

    def test_paused_call_cannot_resume_while_another_single_file_line_is_loading(self):
        self.trigger("f1", [call("f5"), text("caller")])
        self.trigger("f5", [text("A"), text("B")], delay=17)
        self.trigger("f2", [{"type": "file_line", "path": "rows.txt"}])
        self.poll_results[:] = [True]

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.handle_key("f1")
        self.runner.handle_key("f2")
        self.assertEqual(self.runner.paused_keys(), ("f1",))
        self.runner.handle_key("f1")  # file_line 読込中は一時停止中の呼び出しも再開しない
        self.assertEqual(self.runner.paused_keys(), ("f1",))
        self.assertEqual(self.performed, [text("A")])

        self.scheduler.run_one()
        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays[-1], 17)
        self.run_all()
        self.assertEqual(
            [item["value"] for item in self.performed], ["A", "B"]
        )


    def test_03_wait_nested_call_stop_skip_and_file_line(self):
        self.trigger("f1", [call("f5"), text("X")])
        self.trigger("f5", [system("wait", ms=23), system("stop"),
                             call("f6"), text("after")], delay=9)
        self.trigger("f6", [text("nested")])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(self.scheduler.delays[-1], 23)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["nested"])
        self.assertEqual(self.scheduler.delays[-1], 9)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["nested", "after"])
        self.assertEqual(self.index("f1"), 1)

        self.performed.clear()
        self.trigger("f7", [{"type": "file_line", "path": "rows.txt"}])
        self.trigger("f4", [call("f7")])
        self.poll_results[:] = [None, True]
        self.runner.handle_key("f4")
        self.scheduler.run_one()
        self.assertEqual(self.scheduler.delays[-1], 50)
        self.scheduler.run_one()  # 1 回目の確認は未了で予約し直す
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 1)
        self.assertEqual(self.poll_results, [])
        self.assertNotIn(("set", "f4"), self.state.pending_steps)

    def test_file_line_without_callbacks_reports_for_single_and_run_to_end_calls(self):
        self.runner._begin_file_line = None
        self.runner._poll_file_line = None
        self.trigger("f1", [call("f5"), text("X")])
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(
            self.errors[-1][1],
            "system 実行エラー（call 呼び出し先=f5）: "
            "file_line の読込の仕組みが未設定です / 呼び出し: f5",
        )
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

        self.setUp()
        self.runner._begin_file_line = None
        self.runner._poll_file_line = None
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(
            self.errors[-1][1],
            "system 実行エラー（call 呼び出し先=f5）: "
            "file_line の読込の仕組みが未設定です / 呼び出し: f5",
        )
        self.assertIsNone(self.state.run_to_end_key)

    def test_04_missing_cycle_depth_and_infinite_loop_errors_include_call_chain(self):
        cases = {
            "missing": [call("absent")],
            "cycle": [call("f1")],
            "infinite": [system("loop_start", infinite=True), text("A"),
                         system("loop_end")],
        }
        for key, actions in cases.items():
            with self.subTest(key=key):
                self.trigger_sets["set"] = []
                errors_before = len(self.errors)
                self.trigger("f1", [call(key)])
                if key != "missing":
                    self.trigger(key, actions)
                self.runner.handle_key("f1")
                self.run_all()
                self.assertTrue(any("呼び出し:" in message
                                    for _, message in self.errors[errors_before:]))
                self.assertEqual(self.index("f1"), 0)
                self.assertEqual(len(self.history()), 0)

        self.trigger_sets["set"] = []
        self.trigger("f1", [call("f9")])
        for number in range(9, 19):
            self.trigger(f"f{number}", [call(f"f{number + 1}")])
        self.trigger("f19", [text("too deep")])
        self.runner.handle_key("f1")
        self.run_all()
        self.assertTrue(any("深さ" in message and "呼び出し:" in message
                            for _, message in self.errors))
        self.assertEqual(self.index("f1"), 0)

        self.trigger_sets["set"].insert(0, {"key": "f1", "actions": [
            system("counter_inc", counter="n"), call("absent")], "run_to_end": False})
        self.runner.handle_key("f1")
        self.run_all()
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 1)
        self.assertEqual(self.index("f1"), 1)

    def test_05_call_counter_delta_is_one_undoable_history_step_and_cancel_commits_it(self):
        self.trigger("f1", [call("f5"), text("X")])
        self.trigger("f5", [system("counter_inc", counter="n"), text("A")])
        self.runner.handle_key("f1")
        self.run_all()
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 1)
        self.trigger("f2", [system("back")])
        self.runner.handle_key("f2")
        self.assertEqual(self.state.counters.get("n", 0), 0)

        self.trigger("f3", [call("f6")])
        self.trigger("f6", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("B")])
        self.runner.handle_key("f3")
        self.scheduler.run_one()  # 最初のステップ（after(0)）で counter_inc → 待機
        self.runner.cancel_pending_wait("f3")
        self.assertEqual(self.index("f3"), 0)
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history("f3")), 1)

    def test_successful_call_then_parent_wait_resumes_without_sending(self):
        self.trigger("f1", [call("f5"), system("wait", ms=13), text("X")])
        self.trigger("f5", [text("A")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()  # 呼び出しの成功後、呼び出し元の待機へ進む

        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.index("f1"), 1)
        self.assertEqual(self.scheduler.delays[-1], 13)
        self.assertIn(("set", "f1"), self.state.pending_steps)

        self.scheduler.run_one()

        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.index("f1"), 2)
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

        self.runner.handle_key("f1")
        self.assertEqual([item["value"] for item in self.performed], ["A", "X"])

    def test_06_rechecks_pending_after_perform_returns_true_or_false(self):
        for result in (False, True):
            with self.subTest(result=result):
                self.state.history_for("set").clear()
                self.state.counters.clear()
                self.trigger("f1", [call("f5"), text("X")])
                self.trigger("f5", [system("counter_inc", counter="n"), text("A")])
                self.perform_result = result
                self.perform_callback = lambda: self.runner.cancel_pending_wait("f1")
                self.runner.handle_key("f1")
                self.scheduler.run_one()
                self.assertEqual(self.index("f1"), 0)
                self.assertEqual(len(self.history()), 1)
                self.assertEqual(len(self.state.pending_steps), 0)
                self.trigger_sets["set"] = []
                self.perform_callback = None
        self.perform_result = True

    def test_07_trigger_set_and_missing_caller_drop_pending_without_history(self):
        self.trigger("f1", [call("f5")], trigger_set_id="set")
        self.trigger("f5", [text("A")], trigger_set_id="set")
        self.runner.handle_key("f1")
        self.trigger_set_id = "other"
        self.trigger_sets["other"] = []
        self.scheduler.run_one()
        self.assertEqual(len(self.state.pending_steps), 0)
        self.assertEqual(len(self.history("f1")), 0)

        self.trigger_set_id = "set"
        self.trigger("f1", [call("f5")], trigger_set_id="set")
        self.trigger("f5", [text("A")], trigger_set_id="set")
        self.runner.handle_key("f1")
        self.trigger_sets["set"] = [item for item in self.trigger_sets["set"]
                                     if item["key"] != "f1"]
        self.scheduler.run_one()
        self.assertEqual(len(self.state.pending_steps), 0)
        self.assertEqual(len(self.history("f1")), 0)

    def test_08_call_uses_start_time_copy_of_target_actions(self):
        self.trigger("f1", [call("f5"), text("X")])
        target = self.trigger("f5", [text("A"), text("B")], delay=3)
        self.runner.handle_key("f1")
        target["actions"][:] = [text("changed")]
        self.run_all()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])

    def test_09_call_free_single_action_behavior_is_unchanged(self):
        self.trigger("f1", [text("plain")])
        self.runner.handle_key("f1")
        self.assertEqual([item["value"] for item in self.performed], ["plain"])
        self.assertEqual(self.index("f1"), 0)
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

    def test_10_run_to_end_call_runs_target_then_resumes_caller_with_one_history_step(self):
        self.trigger("f1", [call("f5"), text("X")], delay=7, run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"), text("A"), text("B")],
                     delay=9)

        self.runner.handle_key("f1")
        self.assertEqual(self.scheduler.delays, [0])
        self.scheduler.run_one()
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.scheduler.delays[-1], 9)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])
        self.assertEqual(self.scheduler.delays[-1], 7)
        self.scheduler.run_one()

        self.assertEqual([item["value"] for item in self.performed], ["A", "B", "X"])
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.index("f5"), 0)
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 2)
        self.trigger("f2", [system("back")])
        self.runner.handle_key("f2")
        self.runner.handle_key("f2")
        self.assertEqual(self.state.counters.get("n", 0), 0)

    def test_11_run_to_end_call_pause_resume_keeps_progress_and_skips_wait_remainder(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), text("B")], delay=9)
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.pause_run_to_end()
        self.assertEqual(self.scheduler.queue, [])
        self.runner.resume_run_to_end()
        self.assertEqual(self.scheduler.delays[-1], 9)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)

        self.performed.clear()
        self.trigger_sets["set"] = []
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), system("wait", ms=30), text("B")], delay=9)
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.scheduler.run_one()  # 文脈内の待機を予約
        self.assertEqual(self.scheduler.delays[-1], 30)
        self.runner.pause_run_to_end()
        self.runner.resume_run_to_end()
        self.assertEqual(self.scheduler.delays[-1], 9)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])

    def test_run_to_end_step_call_stop_pauses_at_target_and_resumes_after_stop(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), system("stop"), text("B")], delay=9)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])

        self.assertTrue(self.state.run_to_end_paused)
        self.assertEqual(self.state.run_to_end_key, "f1")
        self.assertIsNotNone(self.runner._run_to_end_call)
        self.assertTrue(self.runner._run_to_end_call.sent)
        self.assertFalse(self.runner._run_to_end_sent)
        self.assertEqual(self.runner._run_to_end_call.stack[-1].position, 2)
        self.assertEqual(self.scheduler.queue, [])

        self.runner.resume_run_to_end()
        self.run_all()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B", "X"])
        self.assertIsNone(self.runner._run_to_end_call)
        self.assertIsNone(self.state.run_to_end_key)

    def test_run_to_end_step_call_skips_initial_stop_until_target_action_is_sent(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [system("stop"), text("A")])

        self.runner.handle_key("f1")
        self.run_all()

        self.assertFalse(self.state.run_to_end_paused)
        self.assertEqual([item["value"] for item in self.performed], ["A", "X"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_run_to_end_step_call_stop_at_target_end_finishes_call_without_pausing(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), system("stop")])

        self.runner.handle_key("f1")
        self.run_all()

        self.assertFalse(self.state.run_to_end_paused)
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertIsNone(self.state.run_to_end_key)
        self.assertIsNone(self.runner._run_to_end_call)
        self.assertEqual(len(self.history("f1")), 1)
        self.assertEqual(self.index("f1"), 1)

    def test_run_to_end_step_call_stop_skips_wait_and_nested_target_resumes(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [call("f7", step=True), text("C")], delay=9)
        self.trigger("f7", [text("A"), system("stop"),
                             system("wait", ms=100), text("B")], delay=11)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])

        self.assertTrue(self.state.run_to_end_paused)
        self.assertEqual(self.runner._run_to_end_call.stack[-1].key, "f7")
        self.assertEqual(self.runner._run_to_end_call.stack[-1].position, 3)
        self.assertNotIn(100, self.scheduler.delays)

        self.runner.resume_run_to_end()
        self.run_all()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B", "C", "X"])

    def test_run_to_end_batch_call_still_skips_target_stop(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), system("stop"), text("B")])

        self.runner.handle_key("f1")
        self.run_all()

        self.assertFalse(self.state.run_to_end_paused)
        self.assertEqual([item["value"] for item in self.performed], ["A", "B", "X"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_run_to_end_batch_call_preserves_caller_stop_skip_marker_on_resume(self):
        self.trigger("f1", [call("f5"), system("stop"), text("Y")], run_to_end=True)
        self.trigger("f5", [text("A"), system("wait", ms=100), text("B")], delay=9)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.runner.pause_run_to_end()
        self.state.indices_for("set")["f1"] = 1
        self.runner.reset_loop_frames("f1")
        self.runner.resume_run_to_end()
        self.run_all()

        self.assertEqual([item["value"] for item in self.performed], ["A", "Y"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_single_step_call_file_line_completion_waits_for_next_press(self):
        self.trigger("f1", [call("f5", step=True)])
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}, text("B")])
        self.poll_results[:] = [True]

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 1)
        self.scheduler.run_one()
        self.assertEqual(self.performed, [])
        self.assertTrue(self.state.pending_steps[("set", "f1")].call_paused)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["B"])

    def test_run_to_end_step_call_stop_keeps_pre_stop_counter_and_defers_following_one(self):
        self.trigger("f1", [call("f5", step=True)], run_to_end=True)
        self.trigger("f5", [text("A"), system("counter_inc", counter="before"),
                             system("stop"), system("counter_inc", counter="after"),
                             system("wait", ms=100), text("B")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertTrue(self.state.run_to_end_paused)
        self.assertEqual(self.state.counters.get("before"), 1)
        self.assertIsNone(self.state.counters.get("after"))
        self.assertNotIn(100, self.scheduler.delays)
        self.runner.resume_run_to_end()
        self.run_all()

        self.assertEqual(self.state.counters.get("after"), 1)
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])

    def test_run_to_end_nested_stop_unwinds_parent_and_skips_parent_wait(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [call("f7", step=True), system("wait", ms=100),
                             text("C")], delay=9)
        self.trigger("f7", [text("A"), system("stop")], delay=11)

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertTrue(self.state.run_to_end_paused)
        self.assertEqual(self.runner._run_to_end_call.stack[-1].key, "f5")
        self.assertEqual(self.runner._run_to_end_call.stack[-1].position, 2)
        self.assertNotIn(100, self.scheduler.delays)
        self.runner.resume_run_to_end()
        self.run_all()

        self.assertEqual([item["value"] for item in self.performed], ["A", "C", "X"])

    def test_run_to_end_nested_batch_action_sets_step_context_sent_marker(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [call("f7"), system("stop"), text("C")], delay=9)
        self.trigger("f7", [text("A"), system("stop"), text("B")], delay=11)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])

        self.assertTrue(self.state.run_to_end_paused)
        self.assertEqual(self.runner._run_to_end_call.stack[-1].key, "f5")
        self.assertEqual(self.runner._run_to_end_call.stack[-1].position, 2)
        self.runner.resume_run_to_end()
        self.run_all()

        self.assertEqual([item["value"] for item in self.performed], ["A", "B", "C", "X"])

    def test_run_to_end_file_line_action_sets_step_context_sent_marker(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"},
                             system("stop"), text("B")])
        self.poll_results[:] = [True]

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 1)
        self.scheduler.run_one()

        self.assertTrue(self.state.run_to_end_paused)
        self.assertEqual(self.runner._run_to_end_call.stack[-1].position, 2)
        self.assertEqual(self.performed, [])
        self.runner.resume_run_to_end()
        self.run_all()

        self.assertEqual([item["value"] for item in self.performed], ["B", "X"])

    def test_run_to_end_step_call_done_after_stop_skips_caller_wait(self):
        self.trigger("f1", [call("f5", step=True), system("wait", ms=100),
                             text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), system("stop")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertFalse(self.state.run_to_end_paused)
        self.assertIsNone(self.state.run_to_end_key)
        self.assertNotIn(100, self.scheduler.delays)
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(len(self.history("f1")), 1)

    def test_run_to_end_nested_stop_at_end_applies_each_frames_deferred_counters(self):
        self.trigger("f1", [call("f5", step=True), text("X")], run_to_end=True)
        self.trigger("f5", [call("f7", step=True),
                             system("counter_inc", counter="parent")])
        self.trigger("f7", [text("A"), system("stop"), system("wait", ms=100),
                             system("counter_inc", counter="child")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(self.state.counters, {"child": 1, "parent": 1})
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertIsNone(self.runner._run_to_end_call)
        self.assertIsNone(self.state.run_to_end_key)
        self.assertFalse(self.state.run_to_end_paused)
        self.assertEqual(self.index("f1"), 1)
        self.assertEqual(len(self.history()), 1)
        self.assertEqual(self.scheduler.queue, [])
        self.assertNotIn(100, self.scheduler.delays)

    def test_run_to_end_call_callback_from_before_pause_is_stale_after_resume(self):
        self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [text("A"), text("B")], delay=9)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        stale_callback = self.scheduler.queue[0][1]
        self.runner.pause_run_to_end()
        self.runner.resume_run_to_end()
        stale_callback()

        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(len(self.scheduler.queue), 1)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])

    def test_12_manual_stop_commits_call_counter_delta_once_and_stale_callback_is_ignored(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("B")])
        self.runner.handle_key("f1")
        stale = self.scheduler.queue[0][1]
        self.scheduler.run_one()
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.runner.stop_run_to_end()
        stale()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.index("f1"), 0)
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 1)

    def test_13_missing_target_and_infinite_call_error_stop_without_empty_history(self):
        cases = (("missing", [call("absent")]),
                 ("infinite", [system("loop_start", infinite=True), text("A"),
                               system("loop_end")]))
        for label, target_actions in cases:
            with self.subTest(label=label):
                self.trigger_sets["set"] = []
                self.errors.clear()
                self.trigger("f1", [call("absent" if label == "missing" else "f5")],
                             run_to_end=True)
                if label == "infinite":
                    self.trigger("f5", target_actions)
                self.runner.handle_key("f1")
                self.scheduler.run_one()
                self.assertIsNone(self.state.run_to_end_key)
                self.assertEqual(self.index("f1"), 0)
                self.assertEqual(len(self.history()), 0)
                self.assertTrue(any("呼び出し:" in message for _, message in self.errors))

    def test_14_reset_loop_frames_discards_call_and_continues_from_new_position(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [text("A"), text("B")], delay=9)
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.state.indices_for("set")["f1"] = 1
        self.runner.reset_loop_frames("f1")

        self.assertEqual(self.scheduler.delays[-1], 7)
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "X"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_15_runtime_reset_discards_active_call_without_history(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("B")])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.on_runtime_reset()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 0)

    def test_16_stop_during_perform_recheck_does_not_commit_twice(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"), text("A")])
        self.perform_callback = self.runner.stop_run_to_end
        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 1)
        self.assertEqual([item["value"] for item in self.performed], ["A"])

    def test_17_call_success_sets_stop_skip_marker_for_caller(self):
        self.trigger("f1", [call("f5"), system("stop"), text("Y")], run_to_end=True)
        self.trigger("f5", [text("A")])
        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_18_call_file_line_pause_resume_reads_line_again(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}], delay=9)
        self.poll_results[:] = [None, True]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 1)
        self.assertEqual(self.scheduler.delays[-1], 50)
        self.runner.pause_run_to_end()
        self.runner.resume_run_to_end()
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 2)
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 2)
        self.scheduler.run_one()
        self.assertEqual(len(self.begin_results), 2)
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)

        self.trigger_sets["set"] = []
        self.state.history_for("set").clear()  # 前半の連続実行で積まれた履歴を消す
        self.begin_results.clear()
        self.errors.clear()
        self.begin_result = None
        self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(len(self.history()), 0)

        self.trigger_sets["set"] = []
        self.state.history_for("set").clear()
        self.begin_result = object()
        self.poll_results[:] = [False]
        self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(len(self.history()), 0)

    def test_19_call_free_run_to_end_keeps_existing_interval_sequence(self):
        self.trigger("f1", [text("A"), text("B")], delay=7, run_to_end=True)
        self.runner.handle_key("f1")
        self.assertEqual([item["value"] for item in self.performed], ["A"])
        self.assertEqual(self.scheduler.delays, [7])
        self.scheduler.run_one()
        self.assertEqual([item["value"] for item in self.performed], ["A", "B"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_20_call_error_pause_still_stops_without_resuming_as_success(self):
        self.trigger("f1", [call("absent"), text("X")], run_to_end=True)
        self.runner._notify_error = lambda action, message: (
            self.errors.append((action, message)), self.runner.pause_run_to_end(),
        )

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.index("f1"), 0)
        self.assertEqual(len(self.history()), 0)
        self.assertEqual(self.performed, [])
        self.runner.resume_run_to_end()
        self.run_all()
        self.assertEqual(self.performed, [])

    def test_21_send_failure_pause_stops_without_retry(self):
        self.trigger("f1", [call("f5"), text("X")], run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"), text("A")])
        self.perform_result = False
        self.perform_callback = self.runner.pause_run_to_end

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.index("f1"), 0)
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history()), 1)
        self.assertEqual([item["value"] for item in self.performed], ["A"])

    def test_22_call_error_notification_includes_target_value(self):
        self.trigger("f1", [call(" z9 ")], run_to_end=True)

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(self.errors[-1][0]["value"], "call 呼び出し先=z9")

    def test_23_single_call_preserves_target_position_and_history(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [system("loop_start", count=2), text("A"),
                             system("loop_end"), text("B")])
        self.runner.handle_key("f5")
        target_index = self.index("f5")
        target_history = list(self.history("f5"))
        target_frames = list(self.state.loop_frames_for("set").get("f5", []))

        self.runner.handle_key("f1")
        self.run_all()

        self.assertEqual(self.index("f5"), target_index)
        self.assertEqual(self.history("f5"), target_history)
        self.assertEqual(self.state.loop_frames_for("set").get("f5", []), target_frames)
        self.assertEqual([item["value"] for item in self.performed], ["A", "A", "A", "B"])

    def test_24_empty_call_counts_as_sent_for_caller_stop(self):
        self.trigger("f1", [call("f5"), system("stop"), text("Y")], run_to_end=True)
        self.trigger("f5", [])

        self.runner.handle_key("f1")
        self.run_all()

        self.assertEqual(self.performed, [])
        self.assertIsNone(self.state.run_to_end_key)

    def test_25_other_run_to_end_is_ignored_during_single_call(self):
        self.trigger("f1", [call("f5"), text("caller")])
        self.trigger("f5", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("target")])
        self.trigger("f2", [text("other")], run_to_end=True)

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.handle_key("f2")
        self.run_all()

        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history("f1")), 1)
        self.assertEqual([item["value"] for item in self.performed], ["target"])
        self.assertIsNone(self.state.run_to_end_key)

    def test_paused_single_call_is_discarded_with_notice_to_start_continuous_run(self):
        self.trigger("f1", [call("f5"), text("caller")])
        self.trigger("f5", [system("counter_inc", counter="n"), text("A"), text("B")], delay=17)
        self.trigger("f2", [text("other")], run_to_end=True)
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.handle_key("f1")
        self.assertEqual(self.runner.paused_keys(), ("f1",))
        self.runner.handle_key("f2")

        self.assertIn("一時停止中の実行を破棄しました（f1）", self.messages)
        self.assertEqual(self.index("f1"), 0)
        self.assertEqual(len(self.history("f1")), 1)
        self.assertEqual(self.performed[-1]["value"], "other")

    def test_back_and_rewind_discard_only_the_paused_call_target_on_second_press(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                self.setUp()
                self.trigger("f1", [call("f5"), text("caller")])
                self.trigger("f5", [system("counter_inc", counter="n"),
                                     system("wait", ms=30), text("A")])
                self.trigger("f2", [call("f6"), text("caller two")])
                self.trigger("f6", [system("counter_inc", counter="m"),
                                     system("wait", ms=30), text("B")])
                self.trigger("f3", [system(op)], run_to_end=True)

                self.runner.handle_key("f1")
                self.scheduler.run_one()
                self.runner.handle_key("f1")
                self.runner.handle_key("f2")
                self.scheduler.run_one()
                self.runner.handle_key("f2")
                self.state.last_trigger = ("set", "f1")

                self.runner.handle_key("f3")
                self.assertEqual(self.runner.paused_keys(), ("f1", "f2"))
                self.assertIn("一時停止中の f1 を破棄します。もう一度押すと実行します", self.messages)
                self.runner.handle_key("f3")

                self.assertIn("一時停止中の実行を破棄しました（f1）", self.messages)
                self.assertEqual(self.runner.paused_keys(), ("f2",))
                self.assertNotIn(("set", "f1"), self.state.pending_steps)
                self.assertIn(("set", "f2"), self.state.pending_steps)
                self.assertEqual(self.state.counters.get("m"), 1)
                if op == "back":
                    self.assertEqual(self.state.counters.get("n"), 0)
                else:
                    self.assertEqual(self.state.counters.get("n"), 1)

    def _prepare_run_to_end_discard_case(self, op):
        self.trigger("f1", [text("A"), text("B")], run_to_end=True)
        self.trigger("f5", [call("f6")])
        self.trigger("f6", [text("C"), text("D")], delay=20)
        self.trigger("f2", [system(op)], run_to_end=True)
        self.runner.handle_key("f1")
        self.runner.handle_key("f1")
        self.runner.handle_key("f5")
        self.scheduler.run_one()
        self.runner.handle_key("f5")
        self.state.last_trigger = ("set", "f1")

    def test_run_to_end_back_and_rewind_use_two_press_discard_for_only_target(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                self.setUp()
                self._prepare_run_to_end_discard_case(op)
                self.assertEqual(self.runner.paused_keys(), ("f1", "f5"))
                position = self.index("f1")

                self.runner.handle_key("f2")
                self.assertEqual(self.index("f1"), position)
                self.assertEqual(set(self.runner.paused_keys()), {"f1", "f5"})
                self.assertIn("一時停止中の f1 を破棄します。もう一度押すと実行します",
                              self.messages)
                self.runner.handle_key("f2")
                self.assertEqual(self.runner.paused_keys(), ("f5",))
                self.assertNotIn(("set", "f1"), self.state.pending_steps)
                self.assertIn(("set", "f5"), self.state.pending_steps)
                self.assertEqual(self.index("f1"), 0)

    def test_run_to_end_standalone_control_executes_when_target_is_not_paused(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                self.setUp()
                self.trigger("f1", [text("A"), text("B")])
                self.trigger("f2", [system(op)], run_to_end=True)
                self.runner.handle_key("f1")
                self.state.last_trigger = ("set", "f1")

                self.runner.handle_key("f2")

                self.assertEqual(self.index("f1"), 0)
                self.assertIsNone(self.state.run_to_end_key)
                self.assertFalse(self.messages)

    def test_other_press_resets_back_discard_prompt(self):
        self.trigger("f1", [call("f5"), text("caller")])
        self.trigger("f5", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("A")])
        self.trigger("f2", [call("f6"), text("caller two")])
        self.trigger("f6", [system("counter_inc", counter="m"),
                             system("wait", ms=30), text("B")])
        self.trigger("f3", [system("back")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.handle_key("f1")
        self.runner.handle_key("f2")
        self.scheduler.run_one()
        self.runner.handle_key("f2")
        self.state.last_trigger = ("set", "f1")
        self.runner.handle_key("f3")
        self.runner.handle_key("f9")
        self.runner.handle_key("f3")

        self.assertEqual(self.runner.paused_keys(), ("f1", "f2"))
        self.assertIn(("set", "f1"), self.state.pending_steps)
        self.assertIn(("set", "f2"), self.state.pending_steps)
        self.assertEqual(self.state.counters.get("n"), 1)
        self.assertEqual(self.state.counters.get("m"), 1)
        self.assertEqual(self.messages.count(
            "一時停止中の f1 を破棄します。もう一度押すと実行します"), 2)

    def test_changed_state_resets_back_discard_prompt(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [system("wait", ms=30), text("A")])
        self.trigger("f2", [system("back")])
        self.runner.handle_key("f1")
        self.runner.handle_key("f1")
        self.state.last_trigger = ("set", "f1")
        self.runner.handle_key("f2")
        self.state.pending_step_generation += 1
        self.state.pending_steps[("set", "f1")].generation = self.state.pending_step_generation
        self.runner.handle_key("f2")
        self.assertIn(("set", "f1"), self.state.pending_steps)
        self.assertEqual(self.messages.count(
            "一時停止中の f1 を破棄します。もう一度押すと実行します"), 2)

    def test_26_reset_indices_drops_call_without_history(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("A")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.state.reset_indices()

        self.run_all()
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history("f1")), 0)
        self.assertEqual(self.performed, [])

    def test_27_removed_run_to_end_caller_stops_without_history(self):
        caller = self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"),
                             system("wait", ms=30), text("A")])

        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.trigger_sets["set"].remove(caller)
        self.run_all()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history("f1")), 0)
        self.assertEqual(self.performed, [])

    def test_28_single_error_notification_stop_commits_one_history_step(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [system("counter_inc", counter="n"), call("absent")])
        self.runner._notify_error = lambda action, message: (
            self.errors.append((action, message)), self.runner.cancel_pending_wait("f1"),
        )

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history("f1")), 1)
        self.assertNotIn(("set", "f1"), self.state.pending_steps)

    def test_29_run_to_end_error_notification_stop_commits_one_history_step(self):
        self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [system("counter_inc", counter="n"), call("absent")])
        self.runner._notify_error = lambda action, message: (
            self.errors.append((action, message)), self.runner.stop_run_to_end(),
        )

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertEqual(self.state.counters.get("n", 0), 1)
        self.assertEqual(len(self.history("f1")), 1)
        self.assertIsNone(self.state.run_to_end_key)

    def test_30_file_line_failure_pause_still_stops_without_retry(self):
        self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [{"type": "file_line", "path": "rows.txt"}])

        def pause_then_fail(_handle):
            self.runner.pause_run_to_end()
            return False

        self.runner._poll_file_line = pause_then_fail
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.scheduler.run_one()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(len(self.begin_results), 1)
        self.assertEqual(self.performed, [])
        self.assertEqual(len(self.history("f1")), 0)

    def test_31_run_to_end_nested_control_loop_hits_limit_and_stops(self):
        self.trigger("f1", [call("f5")], run_to_end=True)
        self.trigger("f5", [system("loop_start", count=20000), call("f6"),
                             system("loop_end")])
        self.trigger("f6", [])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertIsNone(self.state.run_to_end_key)
        self.assertTrue(any(
            "制御アクションの処理が 10000 回を超えました" in message
            for _action, message in self.errors
        ))
        self.assertEqual(len(self.history("f1")), 0)
        self.assertEqual(self.performed, [])


if __name__ == "__main__":
    unittest.main()
