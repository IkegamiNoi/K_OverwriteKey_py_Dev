import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import FILE_LINE_POLL_INTERVAL_MS, SequenceRunner


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
        return handle, callback


class SequenceRunnerFileLineTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.trigger_set_id = ""
        self.scheduler = FakeScheduler()
        self.triggers = []
        self.performed = []
        self.selected = []
        self.messages = []
        self.errors = []
        self.begun = []
        self.begin_none = False
        self.poll_results = []
        self.polled = []
        self.runner = SequenceRunner(
            state=self.state,
            find_trigger=lambda key: next((t for t in self.triggers if t["key"] == key), None),
            perform_action=self._perform,
            select_trigger=self.selected.append,
            refresh_actions=lambda: None,
            update_status=lambda: None,
            after=self.scheduler.after,
            after_cancel=self.scheduler.after_cancel,
            get_trigger_set_id=lambda: self.trigger_set_id,
            notify_message=self.messages.append,
            notify_error=lambda action, message: self.errors.append((action, message)),
            begin_file_line=self._begin,
            poll_file_line=self._poll,
        )

    def _perform(self, action):
        self.performed.append(action)
        return True

    def _begin(self, action):
        self.begun.append(action)
        return None if self.begin_none else object()

    def _poll(self, handle):
        self.polled.append(handle)
        return self.poll_results.pop(0)

    def trigger(self, key, actions):
        trigger = {"key": key, "actions": actions, "run_to_end": False}
        self.triggers.append(trigger)
        return trigger

    def run_to_end_trigger(self, key, actions, delay=7):
        trigger = {
            "key": key, "actions": actions, "run_to_end": True,
            "run_to_end_delay_ms": delay,
        }
        self.triggers.append(trigger)
        return trigger

    @staticmethod
    def file_line():
        return {"type": " FILE_LINE ", "path": "unused", "counter": "row"}

    def test_pending_file_line_blocks_same_key_but_allows_other_trigger(self):
        self.trigger("f1", [self.file_line(), {"type": "text", "value": "after"}])
        self.trigger("f2", [{"type": "text", "value": "other"}])
        self.runner.handle_key("f1")
        self.assertEqual(self.state.indices["f1"], 0)
        self.assertIn(("", "f1"), self.state.pending_steps)
        self.assertEqual(self.scheduler.delays, [FILE_LINE_POLL_INTERVAL_MS])
        self.runner.handle_key("f1")
        self.assertEqual(len(self.begun), 1)
        self.runner.handle_key("f2")
        self.assertEqual(self.performed, [{"type": "text", "value": "other"}])

    def test_pending_poll_repeats_then_success_settles_following_counter(self):
        self.trigger("f1", [self.file_line(),
                             {"type": "system", "op": "counter_inc", "counter": "n"},
                             {"type": "text", "value": "after"}])
        self.poll_results[:] = [None, True]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(self.scheduler.delays, [50, 50])
        self.assertIn(("", "f1"), self.state.pending_steps)
        self.scheduler.run_one()
        self.assertNotIn(("", "f1"), self.state.pending_steps)
        self.assertEqual(self.state.indices["f1"], 2)
        self.assertEqual(self.state.deferred_counters["f1"], [("counter_inc", "n")])
        self.runner.handle_key("f1")
        self.assertEqual(self.state.counters["n"], 1)
        self.assertEqual(self.performed[-1]["value"], "after")

    def test_poll_error_keeps_file_line_row_and_commits_one_reversible_step(self):
        self.trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"},
                             self.file_line()])
        self.poll_results[:] = [False]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(self.state.indices["f1"], 1)
        history = self.state.history["f1"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].counter_deltas, [("n", 1)])

    def test_cancellation_modes_cancel_poll_and_stale_callback(self):
        cases = (
            ("one", lambda: self.runner.cancel_pending_wait("f1")),
            ("all", lambda: self.runner.cancel_pending_waits()),
            ("reset", lambda: self.runner.reset_loop_frames("f1")),
        )
        for name, cancel in cases:
            with self.subTest(name=name):
                self.setUp()
                self.trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"},
                                     self.file_line()])
                self.runner.handle_key("f1")
                _handle, stale = self.scheduler.queue[0]
                cancel()
                self.assertFalse(self.scheduler.queue)
                self.assertTrue(self.scheduler.cancelled)
                self.assertEqual(len(self.state.history.get("f1", [])), 1 if name != "reset" else 0)
                stale()
                self.assertEqual(self.polled, [])
                self.assertNotIn(("", "f1"), self.state.pending_steps)

    def test_control_rejects_pending_file_line_target(self):
        self.trigger("f1", [self.file_line()])
        self.trigger("f2", [{"type": "system", "op": "back"}])
        self.runner.handle_key("f1")
        self.state.last_trigger = ("", "f1")
        self.runner.handle_key("f2")
        self.assertEqual(self.messages, ["対象のトリガーが待機中のため操作できません"])

    def test_begin_none_does_not_wait_and_records_file_line_position(self):
        self.begin_none = True
        self.trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"},
                             self.file_line()])
        self.runner.handle_key("f1")
        self.assertNotIn(("", "f1"), self.state.pending_steps)
        self.assertEqual(self.state.indices["f1"], 1)
        self.assertEqual(len(self.state.history["f1"]), 1)

    def test_wait_then_file_line_completes_as_one_history_step(self):
        self.trigger("f1", [
            {"type": "system", "op": "counter_inc", "counter": "n"},
            {"type": "system", "op": "wait", "ms": 5},
            self.file_line(),
            {"type": "text", "value": "after"},
        ])
        self.poll_results[:] = [True]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        pending = self.state.pending_steps[("", "f1")]
        self.assertEqual(pending.position, 2)
        self.scheduler.run_one()
        self.assertEqual(self.state.indices["f1"], 3)
        self.assertEqual(len(self.state.history["f1"]), 1)
        self.assertEqual(self.state.history["f1"][0].counter_deltas, [("n", 1)])


    def test_missing_trigger_at_poll_drops_pending_without_polling(self):
        self.trigger("f1", [self.file_line()])
        self.runner.handle_key("f1")
        self.triggers.clear()
        self.scheduler.run_one()
        self.assertEqual(self.polled, [])
        self.assertNotIn(("", "f1"), self.state.pending_steps)
        self.assertFalse(self.scheduler.queue)

    def test_reset_indices_makes_single_file_line_confirmation_stale(self):
        self.trigger("f1", [self.file_line()])
        self.runner.handle_key("f1")
        _handle, stale = self.scheduler.queue[0]
        self.state.reset_indices()
        stale()
        self.assertEqual(self.polled, [])
        self.assertFalse(self.state.pending_steps)

    def test_other_run_to_end_cancels_single_file_line_once(self):
        self.trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"},
                             self.file_line()])
        self.run_to_end_trigger("f2", [{"type": "text", "value": "other"}])
        self.runner.handle_key("f1")
        _handle, stale = self.scheduler.queue[0]
        self.runner.handle_key("f2")
        self.assertNotIn(("", "f1"), self.state.pending_steps)
        self.assertEqual(len(self.state.history.get("f1", [])), 1)
        stale()
        self.assertEqual(self.polled, [])
        self.assertEqual(len(self.state.history["f1"]), 1)

    def test_run_to_end_reset_during_file_line_reschedules_from_new_position(self):
        self.run_to_end_trigger("f1", [self.file_line(), {"type": "text", "value": "new position"}])
        self.runner.handle_key("f1")
        _old_handle, stale = self.scheduler.queue[0]
        self.state.indices["f1"] = 1
        self.runner.reset_loop_frames("f1")
        self.assertEqual(self.scheduler.delays, [FILE_LINE_POLL_INTERVAL_MS, 7])
        self.assertEqual(len(self.scheduler.queue), 1)
        stale()
        self.assertEqual(self.polled, [])
        self.assertEqual(len(self.scheduler.queue), 1)
        self.scheduler.run_one()
        self.assertEqual(self.performed, [{"type": "text", "value": "new position"}])

    def test_run_to_end_reset_while_paused_does_not_reschedule(self):
        self.run_to_end_trigger("f1", [self.file_line(), {"type": "text", "value": "after"}])
        self.runner.handle_key("f1")
        self.runner.pause_run_to_end()
        self.runner.reset_loop_frames("f1")
        self.assertFalse(self.scheduler.queue)
        self.assertTrue(self.state.run_to_end_paused)

    def test_run_to_end_poll_aborts_without_history_if_trigger_removed(self):
        self.run_to_end_trigger("f1", [self.file_line()])
        self.runner.handle_key("f1")
        self.triggers.clear()
        self.scheduler.run_one()
        self.assertEqual(self.polled, [])
        self.assertEqual(self.performed, [])
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.history.get("f1", []), [])

    def test_run_to_end_poll_aborts_without_history_if_trigger_set_changes(self):
        self.run_to_end_trigger("f1", [self.file_line()])
        self.runner.handle_key("f1")
        self.trigger_set_id = "changed"
        self.scheduler.run_one()
        self.assertEqual(self.polled, [])
        self.assertEqual(self.performed, [])
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.history.get("f1", []), [])

    def test_run_to_end_file_line_waits_then_schedules_next_step_or_stops_at_end(self):
        self.run_to_end_trigger(
            "f1", [self.file_line(), {"type": "text", "value": "after"}],
        )
        self.poll_results[:] = [True]
        self.runner.handle_key("f1")
        self.assertEqual(len(self.scheduler.queue), 1)
        self.assertEqual(self.scheduler.delays, [FILE_LINE_POLL_INTERVAL_MS])
        self.scheduler.run_one()
        self.assertEqual(self.performed, [])
        self.assertEqual(self.scheduler.delays, [50, 7])
        self.assertEqual(len(self.scheduler.queue), 1)
        self.scheduler.run_one()
        self.assertEqual(self.performed, [{"type": "text", "value": "after"}])

        self.setUp()
        self.run_to_end_trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"}, self.file_line()])
        self.poll_results[:] = [True]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(len(self.state.history["f1"]), 1)

    def test_run_to_end_file_line_poll_pending_requeues_after_50_ms(self):
        self.run_to_end_trigger("f1", [self.file_line(), {"type": "text", "value": "next"}])
        self.poll_results[:] = [None, True]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertEqual(self.scheduler.delays, [50, 50])
        self.assertEqual(len(self.scheduler.queue), 1)
        self.assertEqual(len(self.polled), 1)
        self.scheduler.run_one()
        self.assertEqual(len(self.polled), 2)
        self.assertEqual(self.scheduler.delays[-1], 7)

    def test_run_to_end_file_line_false_stops_on_row_and_commits_one_step(self):
        self.run_to_end_trigger("f1", [
            {"type": "system", "op": "counter_inc", "counter": "n"},
            self.file_line(),
        ])
        self.poll_results[:] = [False]
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.indices["f1"], 1)
        self.assertEqual(len(self.state.history["f1"]), 1)
        self.assertEqual(self.state.history["f1"][0].counter_deltas, [("n", 1)])

    def test_run_to_end_pause_discards_old_read_and_resume_rebegins_one_step(self):
        self.run_to_end_trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"}, self.file_line()])
        self.poll_results[:] = [True]
        self.runner.handle_key("f1")
        _handle, stale = self.scheduler.queue[0]
        self.runner.pause_run_to_end()
        self.assertFalse(self.scheduler.queue)
        self.assertIsNotNone(self.runner._run_to_end_resume)
        self.assertIsNotNone(self.runner._run_to_end_snapshot)
        self.assertEqual(self.runner._run_to_end_wait_position, 1)
        stale()
        self.assertEqual(self.polled, [])
        self.runner.resume_run_to_end()
        self.assertEqual(self.scheduler.delays[-1], 7)
        self.scheduler.run_one()
        self.assertEqual(len(self.begun), 2)
        self.scheduler.run_one()
        self.assertEqual(len(self.state.history["f1"]), 1)
        self.assertEqual(self.state.counters["n"], 1)
        self.assertEqual(self.state.history["f1"][0].counter_deltas, [("n", 1)])

    def test_run_to_end_stop_during_file_line_commits_once_and_stale_poll_is_ignored(self):
        self.run_to_end_trigger("f1", [
            {"type": "system", "op": "counter_inc", "counter": "n"},
            self.file_line(),
        ])
        self.runner.handle_key("f1")
        _handle, stale = self.scheduler.queue[0]
        self.runner.stop_run_to_end()
        self.assertEqual(self.state.indices["f1"], 1)
        self.assertEqual(len(self.state.history["f1"]), 1)
        stale()
        self.assertEqual(self.polled, [])
        self.assertEqual(len(self.state.history["f1"]), 1)

    def test_run_to_end_pause_then_stop_commits_one_step_at_file_line_row(self):
        self.run_to_end_trigger("f1", [
            {"type": "system", "op": "counter_inc", "counter": "n"},
            self.file_line(),
        ])
        self.runner.handle_key("f1")
        self.runner.pause_run_to_end()
        self.runner.stop_run_to_end()
        self.assertEqual(self.state.indices["f1"], 1)
        self.assertEqual(len(self.state.history["f1"]), 1)
        self.assertEqual(self.state.history["f1"][0].counter_deltas, [("n", 1)])

    def test_run_to_end_pause_resume_then_poll_error_commits_one_step(self):
        self.run_to_end_trigger("f1", [
            {"type": "system", "op": "counter_inc", "counter": "n"},
            self.file_line(),
        ])
        self.poll_results[:] = [False]
        self.runner.handle_key("f1")
        self.runner.pause_run_to_end()
        self.runner.resume_run_to_end()
        self.scheduler.run_one()
        self.assertEqual(len(self.begun), 2)
        self.scheduler.run_one()
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.indices["f1"], 1)
        self.assertEqual(len(self.state.history["f1"]), 1)
        self.assertEqual(self.state.history["f1"][0].counter_deltas, [("n", 1)])

    def test_run_to_end_file_line_reset_cancels_old_timer_before_single_reschedule(self):
        self.run_to_end_trigger("f1", [self.file_line(), {"type": "text", "value": "next"}])
        self.runner.handle_key("f1")
        old_handle = self.state.run_to_end_after_id
        self.runner.reset_loop_frames("f1")
        self.assertEqual(self.scheduler.cancelled, [old_handle])
        self.assertEqual(len(self.scheduler.queue), 1)

    def test_run_to_end_begin_none_stops_with_one_history_step(self):
        self.begin_none = True
        self.run_to_end_trigger("f1", [
            {"type": "system", "op": "counter_inc", "counter": "n"},
            self.file_line(),
        ])
        self.runner.handle_key("f1")
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(self.state.indices["f1"], 1)
        self.assertEqual(len(self.state.history["f1"]), 1)
        self.assertEqual(self.state.history["f1"][0].counter_deltas, [("n", 1)])

    def test_file_line_without_callbacks_reports_error_for_single_and_run_to_end(self):
        self.runner._begin_file_line = None
        self.runner._poll_file_line = None
        self.trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"}, self.file_line()])
        self.runner.handle_key("f1")
        self.assertEqual(self.errors[-1][1], "file_line の読込の仕組みが未設定です")
        self.assertEqual(self.performed, [])
        self.assertEqual(len(self.state.history["f1"]), 1)

        self.setUp()
        self.runner._begin_file_line = None
        self.runner._poll_file_line = None
        self.run_to_end_trigger("f1", [{"type": "system", "op": "counter_inc", "counter": "n"}, self.file_line()])
        self.runner.handle_key("f1")
        self.assertEqual(self.errors[-1][1], "file_line の読込の仕組みが未設定です")
        self.assertEqual(self.performed, [])
        self.assertIsNone(self.state.run_to_end_key)
        self.assertEqual(len(self.state.history["f1"]), 1)

if __name__ == "__main__":
    unittest.main()
