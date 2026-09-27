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

if __name__ == "__main__":
    unittest.main()
