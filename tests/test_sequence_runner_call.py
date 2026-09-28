import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner


def system(op, **values):
    return {"type": "system", "op": op, **values}


def call(target):
    return system("call", target=target)


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

    def test_02_pending_call_ignores_same_key_allows_other_key_and_rejects_back_target(self):
        self.trigger("f1", [call("f5")])
        self.trigger("f5", [text("A"), system("wait", ms=10)])
        self.trigger("f2", [text("other")])
        self.trigger("f6", [system("back")])
        self.trigger("f7", [system("rewind")])
        self.runner.handle_key("f1")
        self.runner.handle_key("f1")
        self.runner.handle_key("f2")
        self.assertEqual(len(self.scheduler.queue), 1)
        self.assertEqual([item["value"] for item in self.performed], ["other"])

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


if __name__ == "__main__":
    unittest.main()
