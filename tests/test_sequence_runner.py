import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner


class FakeScheduler:
    """tk の after / after_cancel の決定的な代替。"""

    def __init__(self):
        self.queue = []
        self._next_id = 1

    def after(self, _delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.queue = [(h, cb) for h, cb in self.queue if h != handle]

    def run_pending(self, limit=100):
        count = 0
        while self.queue and count < limit:
            _, callback = self.queue.pop(0)
            callback()
            count += 1


def make_runner(triggers):
    state = AppState()
    scheduler = FakeScheduler()
    performed = []

    def find_trigger(key):
        for trigger in triggers:
            if trigger["key"] == key:
                return trigger
        return None

    runner = SequenceRunner(
        state=state,
        find_trigger=find_trigger,
        perform_action=performed.append,
        select_trigger=lambda key: None,
        refresh_actions=lambda: None,
        update_status=lambda: None,
        after=scheduler.after,
        after_cancel=scheduler.after_cancel,
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


if __name__ == "__main__":
    unittest.main()
