import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner


class FakeScheduler:
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
        self.queue = [(item, callback) for item, callback in self.queue if item != handle]

    def run_one(self):
        if self.queue:
            _, callback = self.queue.pop(0)
            callback()

    def run_pending(self, limit=100):
        count = 0
        while self.queue and count < limit:
            self.run_one()
            count += 1


class SequenceRunnerStopTests(unittest.TestCase):
    def make_runner(self, actions, *, delay=0, run_to_end=True,
                    begin_file_line=None, poll_file_line=None):
        trigger = {
            "key": "f1", "run_to_end": run_to_end,
            "run_to_end_delay_ms": delay, "actions": actions,
        }
        back = {"key": "f2", "actions": [{"type": "system", "op": "back"}]}
        triggers = [trigger, back]
        state = AppState()
        scheduler = FakeScheduler()
        performed = []
        runner = SequenceRunner(
            state=state,
            find_trigger=lambda key: next((t for t in triggers if t["key"] == key), None),
            perform_action=lambda action: performed.append(action) or True,
            select_trigger=lambda _key: None,
            refresh_actions=lambda: None,
            update_status=lambda: None,
            after=scheduler.after,
            after_cancel=scheduler.after_cancel,
            begin_file_line=begin_file_line,
            poll_file_line=poll_file_line,
        )
        return runner, state, scheduler, performed

    @staticmethod
    def stop():
        return {"type": "system", "op": "stop"}

    @staticmethod
    def counter_inc():
        return {"type": "system", "op": "counter_inc", "counter": "n"}

    def test_01_stop_ends_run_immediately_and_next_run_starts_after_stop(self):
        a = {"type": "text", "value": "A"}
        b = {"type": "text", "value": "B"}
        runner, state, scheduler, performed = self.make_runner([a, self.stop(), b], delay=25)

        runner.handle_key("f1")
        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 2)
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(scheduler.queue, [])

        runner.handle_key("f1")
        self.assertEqual(performed, [a, b])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)

    def test_02_stop_applies_deferred_counter_in_same_reversible_step(self):
        a = {"type": "text", "value": "A"}
        runner, state, _scheduler, performed = self.make_runner(
            [a, self.counter_inc(), self.stop(), {"type": "text", "value": "B"}],
        )

        runner.handle_key("f1")
        self.assertEqual(performed, [a])
        self.assertEqual(state.counters["n"], 1)
        self.assertEqual(state.indices["f1"], 3)
        history = state.history_for("")["f1"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].counter_deltas, [("n", 1)])

        runner.handle_key("f2")
        self.assertEqual(state.counters["n"], 0)
        self.assertEqual(state.history_for("")["f1"], [])

    def test_03_stop_at_end_wraps_position_to_zero(self):
        a = {"type": "text", "value": "A"}
        runner, state, scheduler, performed = self.make_runner([a, self.stop()], delay=30)

        runner.handle_key("f1")

        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(scheduler.queue, [])

    def test_04_initial_stops_are_skipped_until_action_or_end(self):
        a = {"type": "text", "value": "A"}
        b = {"type": "text", "value": "B"}
        runner, state, _scheduler, performed = self.make_runner([a, self.stop(), b])
        state.indices["f1"] = 1

        runner.handle_key("f1")
        self.assertEqual(performed, [b])
        self.assertEqual(state.indices["f1"], 0)

        runner2, state2, scheduler2, performed2 = self.make_runner(
            [a, self.stop(), self.stop()], delay=10,
        )
        state2.indices["f1"] = 1
        runner2.handle_key("f1")
        self.assertEqual(performed2, [])
        self.assertEqual(state2.indices["f1"], 0)
        self.assertIsNone(state2.run_to_end_key)
        self.assertEqual(scheduler2.queue, [])

    def test_05_pause_and_resume_preserve_sent_marker_through_wait(self):
        a = {"type": "text", "value": "A"}
        wait = {"type": "system", "op": "wait", "ms": 20}
        b = {"type": "text", "value": "B"}
        runner, state, scheduler, performed = self.make_runner([a, wait, self.stop(), b])

        runner.handle_key("f1")
        self.assertTrue(runner._run_to_end_sent)
        scheduler.run_one()
        self.assertEqual(state.indices["f1"], 2)
        runner.pause_run_to_end()
        self.assertTrue(runner._run_to_end_sent)
        runner.resume_run_to_end()
        self.assertTrue(runner._run_to_end_sent)
        scheduler.run_pending()

        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 3)
        self.assertIsNone(state.run_to_end_key)

    def test_06_wait_continuation_stops_at_following_stop_without_interval(self):
        a = {"type": "text", "value": "A"}
        wait = {"type": "system", "op": "wait", "ms": 20}
        b = {"type": "text", "value": "B"}
        runner, state, scheduler, performed = self.make_runner([a, wait, self.stop(), b], delay=5)

        runner.handle_key("f1")
        scheduler.run_pending()

        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 3)
        self.assertEqual(scheduler.delays, [5, 20])
        self.assertIsNone(state.run_to_end_key)

    def test_07_stop_inside_loop_ends_each_run_and_preserves_loop_progress(self):
        a = {"type": "text", "value": "A"}
        actions = [
            {"type": "system", "op": "loop_start", "count": 3},
            a, self.stop(), {"type": "system", "op": "loop_end"},
        ]
        runner, state, _scheduler, performed = self.make_runner(actions)

        runner.handle_key("f1")
        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 3)
        self.assertIsNone(state.run_to_end_key)
        runner.handle_key("f1")
        self.assertEqual(performed, [a, a])
        self.assertEqual(state.indices["f1"], 3)
        runner.handle_key("f1")
        self.assertEqual(performed, [a, a, a])
        self.assertEqual(state.indices["f1"], 3)
        runner.handle_key("f1")
        self.assertEqual(performed, [a, a, a])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)

    def test_08_single_step_skips_stop_without_consuming_next_press(self):
        a = {"type": "text", "value": "A"}
        b = {"type": "text", "value": "B"}
        runner, state, _scheduler, performed = self.make_runner(
            [a, self.stop(), b], run_to_end=False,
        )

        runner.handle_key("f1")
        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 2)  # 先行処理で停止を通過し、次に実行は B
        runner.handle_key("f1")
        self.assertEqual(performed, [a, b])
        self.assertEqual(state.indices["f1"], 0)

    def test_09_successful_file_line_completion_sets_marker_before_stop(self):
        file_line = {"type": "file_line", "path": "input.txt"}
        b = {"type": "text", "value": "B"}
        polls = [True]
        runner, state, scheduler, performed = self.make_runner(
            [file_line, self.stop(), b],
            begin_file_line=lambda _action: object(),
            poll_file_line=lambda _handle: polls.pop(0),
        )

        runner.handle_key("f1")
        self.assertFalse(runner._run_to_end_sent)
        scheduler.run_one()

        self.assertTrue(runner._run_to_end_sent)
        self.assertEqual(performed, [])
        self.assertEqual(state.indices["f1"], 2)
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(scheduler.queue, [])

    def test_10_run_without_stop_keeps_existing_continuous_behavior(self):
        a = {"type": "text", "value": "A"}
        b = {"type": "text", "value": "B"}
        runner, state, scheduler, performed = self.make_runner([a, b], delay=5)

        runner.handle_key("f1")
        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 1)
        self.assertEqual(len(scheduler.queue), 1)
        scheduler.run_pending()

        self.assertEqual(performed, [a, b])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)

    def test_11_consecutive_stops_are_skipped_on_second_run(self):
        a = {"type": "text", "value": "A"}
        b = {"type": "text", "value": "B"}
        runner, state, _scheduler, performed = self.make_runner(
            [a, self.stop(), self.stop(), b],
        )

        runner.handle_key("f1")
        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 2)
        self.assertIsNone(state.run_to_end_key)

        runner.handle_key("f1")
        self.assertEqual(performed, [a, b])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)

    def test_12_pause_and_resume_during_wait_skips_following_stop(self):
        wait = {"type": "system", "op": "wait", "ms": 20}
        a = {"type": "text", "value": "A"}
        runner, state, scheduler, performed = self.make_runner(
            [wait, self.stop(), a],
        )

        runner.handle_key("f1")
        runner.pause_run_to_end()
        runner.resume_run_to_end()
        scheduler.run_pending()

        self.assertEqual(performed, [a])
        self.assertEqual(state.indices["f1"], 0)
        self.assertIsNone(state.run_to_end_key)


if __name__ == "__main__":
    unittest.main()
