import unittest
from unittest.mock import Mock, call

from keyseq.application.action_executor import ActionExecutor
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


if __name__ == "__main__":
    unittest.main()
