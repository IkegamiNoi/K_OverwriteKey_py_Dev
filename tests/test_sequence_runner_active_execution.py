import unittest
from types import SimpleNamespace

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner


class FakeScheduler:
    def __init__(self):
        self.queue = []
        self._next_id = 1

    def after(self, delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.queue = [(item, callback) for item, callback in self.queue
                      if item != handle]

    def run_one(self):
        _handle, callback = self.queue.pop(0)
        callback()


class SequenceRunnerActiveExecutionTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.trigger_set_id = "active"
        self.trigger_sets = {self.trigger_set_id: []}
        self.scheduler = FakeScheduler()
        self.runner = SequenceRunner(
            state=self.state,
            find_trigger=lambda key: next(
                (item for item in self.trigger_sets[self.trigger_set_id]
                 if item["key"] == key), None,
            ),
            perform_action=lambda _action: True,
            select_trigger=lambda _key: None,
            refresh_actions=lambda: None,
            update_status=lambda: None,
            after=self.scheduler.after,
            after_cancel=self.scheduler.after_cancel,
            get_trigger_set_id=lambda: self.trigger_set_id,
            begin_file_line=lambda _action: object(),
            poll_file_line=lambda _handle: None,
        )

    def add_trigger(self, key, actions, *, run_to_end=False, delay=0):
        trigger = {"key": key, "actions": actions, "run_to_end": run_to_end,
                   "run_to_end_delay_ms": delay}
        self.trigger_sets[self.trigger_set_id].append(trigger)
        return trigger

    def test_continuous_execution_is_active_while_running_and_paused(self):
        self.add_trigger("f1", [{"type": "text", "value": "one"}, {"type": "text", "value": "two"}],
                         run_to_end=True, delay=100)

        self.runner.handle_key("f1")
        self.assertTrue(self.runner.has_active_execution(" F1 "))

        self.runner.pause_run_to_end()
        self.assertTrue(self.runner.has_active_execution("f1"))

    def test_single_wait_is_active(self):
        self.add_trigger("f1", [
            {"type": "text", "value": "one"},
            {"type": "system", "op": "wait", "ms": 100},
        ])

        self.runner.handle_key("f1")

        self.assertIn((self.trigger_set_id, "f1"), self.state.pending_steps)
        self.assertTrue(self.runner.has_active_execution("f1"))

    def test_single_call_interval_wait_marks_caller_and_active_frame(self):
        self.add_trigger("f1", [{"type": "system", "op": "call", "target": "f2", "all": True}])
        self.add_trigger("f2", [
            {"type": "text", "value": "one"},
            {"type": "text", "value": "two"},
        ], delay=25)

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        pending = self.state.pending_steps[(self.trigger_set_id, "f1")]
        call_context = pending.call
        original_state = (pending.generation, pending.after_id,
                          tuple(frame.key for frame in call_context.stack),
                          tuple(self.scheduler.queue))
        self.assertTrue(self.runner.has_active_execution("f1"))
        self.assertTrue(self.runner.has_active_execution(" F2 "))
        self.assertEqual(
            (pending.generation, pending.after_id,
             tuple(frame.key for frame in call_context.stack),
             tuple(self.scheduler.queue)),
            original_state,
        )

        self.runner.handle_key("f1")
        self.assertTrue(pending.call_paused)
        self.assertTrue(self.runner.has_active_execution("f1"))
        self.assertTrue(self.runner.has_active_execution("f2"))

    def test_call_frame_of_continuous_execution_is_active(self):
        self.add_trigger("f1", [{"type": "system", "op": "call", "target": "f2", "all": True}],
                         run_to_end=True)
        self.add_trigger("f2", [
            {"type": "text", "value": "one"},
            {"type": "text", "value": "two"},
        ], delay=25)

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertTrue(self.runner.has_active_execution("f2"))

    def test_nested_call_frame_of_continuous_execution_is_active(self):
        self.add_trigger("f1", [{"type": "system", "op": "call", "target": "f2", "all": True}],
                         run_to_end=True)
        self.add_trigger("f2", [{"type": "system", "op": "call", "target": "f3", "all": True}])
        self.add_trigger("f3", [
            {"type": "text", "value": "one"},
            {"type": "text", "value": "two"},
        ])

        self.runner.handle_key("f1")
        self.scheduler.run_one()

        self.assertTrue(self.runner.has_active_execution("f3"))

    def test_file_line_read_during_continuous_execution_is_active(self):
        self.add_trigger("f1", [{"type": "file_line"}], run_to_end=True)

        self.runner.handle_key("f1")

        self.assertIsNotNone(self.runner._run_to_end_file_line)
        self.assertTrue(self.runner.has_active_execution("f1"))

    def test_single_file_line_read_is_active(self):
        self.add_trigger("f1", [{"type": "file_line"}])

        self.runner.handle_key("f1")

        self.assertIsNotNone(self.state.pending_steps[(self.trigger_set_id, "f1")].file_line)
        self.assertTrue(self.runner.has_active_execution("f1"))

    def test_no_execution_is_inactive(self):
        self.add_trigger("f1", [{"type": "text", "value": "one"}])

        self.assertFalse(self.runner.has_active_execution("f1"))
        self.assertFalse(self.runner.has_active_execution("f2"))

    def test_empty_key_and_pending_execution_from_another_set_are_inactive(self):
        self.state.pending_steps[("inactive", "f1")] = SimpleNamespace(
            call=SimpleNamespace(
                trigger_set_id="inactive", root_key="f1", first_target="f2",
                stack=[SimpleNamespace(key="f3")],
            ),
        )

        self.assertFalse(self.runner.has_active_execution(""))
        self.assertFalse(self.runner.has_active_execution("f1"))
        self.assertFalse(self.runner.has_active_execution("f2"))
        self.assertFalse(self.runner.has_active_execution("f3"))


if __name__ == "__main__":
    unittest.main()
