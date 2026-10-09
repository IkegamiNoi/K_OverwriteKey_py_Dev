import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.action_executor import ActionExecutor, FileLineHandle
from keyseq.application.app_state import AppState
from keyseq.application.held_inputs import HeldInputs
from keyseq.application.sequence_runner import SequenceRunner


class FakeScheduler:
    def __init__(self):
        self.queue = []
        self._next_id = 1

    def after(self, _delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.queue = [(item, callback) for item, callback in self.queue if item != handle]

    def run_one(self):
        if self.queue:
            _, callback = self.queue.pop(0)
            callback()

    def run_pending(self):
        while self.queue:
            self.run_one()


class FakeGateway:
    """記録だけ行い、OS へキー入力を送らない gateway。"""

    def __init__(self):
        self.events = []

    def key_identity(self, key):
        return {"shift": (42, False), "ctrl": (29, False)}.get(key, (30, False))

    def validate_key_name(self, key):
        self.events.append(("validate", key))

    def press_key(self, key):
        self.events.append(("key_down", key))

    def release_key(self, key):
        self.events.append(("key_up", key))

    def write_text(self, value):
        self.events.append(("text", value))

    def mouse_down(self, button, x=None, y=None):
        self.events.append(("mouse_down", button, x, y))

    def mouse_up(self, button, x=None, y=None):
        self.events.append(("mouse_up", button, x, y))


class FakeHeldInputs:
    def __init__(self, gateway, *, release_errors=(), release_all_errors=()):
        self.gateway = gateway
        self.current_owner = None
        self.release_errors = tuple(release_errors)
        self.release_all_errors = tuple(release_all_errors)

    @contextmanager
    def owner_scope(self, owner):
        previous = self.current_owner
        self.current_owner = owner
        try:
            yield
        finally:
            self.current_owner = previous

    def release_owner(self, owner):
        self.gateway.events.append(("release", owner))
        return list(self.release_errors)

    def release_all(self):
        self.gateway.events.append(("release_all",))
        return list(self.release_all_errors)


class SequenceRunnerKeyHoldTests(unittest.TestCase):
    def make_runner(self, triggers, *, notify_error=None, begin_file_line=None,
                    poll_file_line=None, inject_held=True, release_errors=(),
                    release_all_errors=()):
        state = AppState()
        scheduler = FakeScheduler()
        gateway = FakeGateway()
        held_inputs = FakeHeldInputs(
            gateway, release_errors=release_errors,
            release_all_errors=release_all_errors,
        )

        def find_trigger(key):
            return next((trigger for trigger in triggers if trigger["key"] == key), None)

        def perform_action(action):
            gateway.events.append(("send", held_inputs.current_owner, action))
            return action.get("type") != "error"

        def begin_owned_file_line(action):
            gateway.events.append(("begin_file_line", held_inputs.current_owner))
            return begin_file_line(action)

        def poll_owned_file_line(handle):
            gateway.events.append(("poll_file_line", held_inputs.current_owner))
            return poll_file_line(handle)

        runner_args = dict(
            state=state,
            find_trigger=find_trigger,
            perform_action=perform_action,
            select_trigger=lambda _key: None,
            refresh_actions=lambda: None,
            update_status=lambda: None,
            after=scheduler.after,
            after_cancel=scheduler.after_cancel,
            notify_error=notify_error,
            begin_file_line=(begin_owned_file_line if begin_file_line is not None else None),
            poll_file_line=(poll_owned_file_line if poll_file_line is not None else None),
        )
        if inject_held:
            runner_args["held_inputs"] = held_inputs
        runner = SequenceRunner(**runner_args)
        return runner, state, scheduler, gateway, held_inputs

    @staticmethod
    def down():
        return {"type": "key_hold", "edge": "down", "value": "shift"}

    def test_single_steps_keep_the_top_level_owner_without_releasing_between_presses(self):
        trigger = {"key": "f1", "actions": [
            self.down(), {"type": "text", "value": "x"}, {"type": "text", "value": "y"},
        ]}
        runner, _state, _scheduler, gateway, held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.handle_key("f1")

        self.assertEqual([event[:2] for event in gateway.events], [
            ("send", "f1"), ("send", "f1"),
        ])
        self.assertIsNone(held.current_owner)
        self.assertFalse(any(event[0] == "release" for event in gateway.events))

    def test_continuous_completion_releases_its_owner(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [self.down(), {"type": "text", "value": "x"}],
        }
        runner, state, scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        scheduler.run_pending()

        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(gateway.events[-1], ("release", "f1"))

    def test_stop_row_boundary_does_not_release(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [self.down(), {"type": "system", "op": "stop"}, {"type": "text", "value": "x"}],
        }
        runner, state, scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        scheduler.run_pending()

        self.assertIsNone(state.run_to_end_key)
        self.assertFalse(any(event[0] == "release" for event in gateway.events))

    def test_stop_row_at_last_row_releases_as_sequence_end(self):
        # 最後の行の停止は末尾として離す（暫定 35 §2-18）。
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
            "actions": [self.down(), {"type": "system", "op": "stop"}],
        }
        runner, state, scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        scheduler.run_pending()

        self.assertIsNone(state.run_to_end_key)
        self.assertIn(("release", "f1"), gateway.events)

    def test_pause_releases_continuous_run_owner(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 50,
            "actions": [self.down(), {"type": "text", "value": "x"}],
        }
        runner, state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.pause_run_to_end()

        self.assertTrue(state.run_to_end_paused)
        self.assertIn(("release", "f1"), gateway.events)

    def test_pausing_single_call_releases_root_owner(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2", "all": True},
        ]}
        callee = {"key": "f2", "actions": [
            self.down(), {"type": "system", "op": "wait", "ms": 100},
            {"type": "text", "value": "after"},
        ]}
        runner, state, scheduler, gateway, _held = self.make_runner([caller, callee])

        runner.handle_key("f1")
        scheduler.run_one()
        scheduler.run_one()
        self.assertIn(("", "f1"), state.pending_steps)
        runner.handle_key("f1")

        self.assertTrue(state.pending_steps[("", "f1")].call_paused)
        self.assertIn(("release", "f1"), gateway.events)

    def test_cancel_pending_single_wait_releases_waiting_owner(self):
        trigger = {
            "key": "f1", "actions": [
                self.down(), {"type": "system", "op": "wait", "ms": 100},
                {"type": "text", "value": "x"},
            ],
        }
        runner, state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.handle_key("f1")
        self.assertIn(("", "f1"), state.pending_steps)
        runner.cancel_pending_wait("f1")

        self.assertIn(("release", "f1"), gateway.events)

    def test_cancel_pending_wait_releases_owner_even_when_no_wait_exists(self):
        trigger = {"key": "f1", "actions": [self.down(), {"type": "text", "value": "x"}]}
        runner, _state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.cancel_pending_wait("f1")

        self.assertIn(("release", "f1"), gateway.events)

    def test_reset_loop_frames_releases_trigger_owner(self):
        trigger = {"key": "f1", "actions": [self.down(), {"type": "text", "value": "x"}]}
        runner, _state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.reset_loop_frames("f1")

        self.assertIn(("release", "f1"), gateway.events)

    def test_runtime_reset_releases_all_held_inputs(self):
        runner, _state, scheduler, gateway, _held = self.make_runner(
            [], release_all_errors=(RuntimeError("first"), RuntimeError("second")),
        )
        notifications = []
        runner._notify_error = lambda action, message: notifications.append((action, message))

        runner.on_runtime_reset()

        self.assertEqual(gateway.events, [("release_all",)])
        self.assertEqual(notifications, [])
        scheduler.run_pending()
        self.assertEqual(len(notifications), 1)

    def test_no_held_inputs_keeps_existing_runner_behavior(self):
        trigger = {"key": "f1", "actions": [self.down()]}
        runner, _state, _scheduler, gateway, _held = self.make_runner(
            [trigger], inject_held=False,
        )

        runner.handle_key("f1")
        runner.reset_loop_frames("f1")

        self.assertEqual([event[0] for event in gateway.events], ["send"])

    def test_release_errors_are_reported_once_after_release_attempt(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 20,
            "actions": [self.down(), {"type": "text", "value": "x"}],
        }
        notifications = []
        runner, _state, scheduler, gateway, _held = self.make_runner(
            [trigger], notify_error=lambda *args: notifications.append(args),
            release_errors=(RuntimeError("one"), RuntimeError("two")),
        )

        runner.handle_key("f1")
        runner.pause_run_to_end()

        self.assertEqual(gateway.events[-1], ("release", "f1"))
        self.assertEqual(notifications, [])
        scheduler.run_pending()
        self.assertEqual(len(notifications), 1)

    def test_explicit_continuous_stop_releases_owner(self):
        trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 100,
                   "actions": [self.down(), {"type": "text", "value": "after"}]}
        runner, _state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.stop_run_to_end()

        self.assertIn(("release", "f1"), gateway.events)

    def test_continuous_run_releases_owner_when_trigger_disappears(self):
        trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
                   "actions": [self.down(), {"type": "text", "value": "after"}]}
        triggers = [trigger]
        runner, state, scheduler, gateway, _held = self.make_runner(triggers)

        runner.handle_key("f1")
        triggers.clear()
        scheduler.run_pending()

        self.assertIsNone(state.run_to_end_key)
        self.assertIn(("release", "f1"), gateway.events)

    def test_starting_another_continuous_run_releases_previous_owner(self):
        first = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 100,
                 "actions": [self.down(), {"type": "text", "value": "first"}]}
        second = {"key": "f2", "run_to_end": True, "run_to_end_delay_ms": 100,
                  "actions": [self.down(), {"type": "text", "value": "second"}]}
        runner, state, _scheduler, gateway, _held = self.make_runner([first, second])

        runner.handle_key("f1")
        # 別の連続実行を受け入れた後に通る入口を直接確認する。
        runner._start_run_to_end("f2")

        self.assertEqual(state.run_to_end_key, "f2")
        self.assertIn(("release", "f1"), gateway.events)
        self.assertIn(("send", "f2", self.down()), gateway.events)

    def test_cancel_all_pending_waits_releases_each_waiting_owner(self):
        first = {"key": "f1", "actions": [
            self.down(), {"type": "system", "op": "wait", "ms": 100},
            {"type": "text", "value": "first"},
        ]}
        second = {"key": "f2", "actions": [
            self.down(), {"type": "system", "op": "wait", "ms": 100},
            {"type": "text", "value": "second"},
        ]}
        runner, state, _scheduler, gateway, _held = self.make_runner([first, second])

        for key in ("f1", "f2"):
            runner.handle_key(key)
            runner.handle_key(key)
        self.assertEqual(set(state.pending_steps), {("", "f1"), ("", "f2")})
        runner.cancel_pending_waits()

        self.assertIn(("release", "f1"), gateway.events)
        self.assertIn(("release", "f2"), gateway.events)

    def test_single_call_failure_releases_root_owner(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2", "all": True},
        ]}
        callee = {"key": "f2", "actions": [
            {"type": "system", "op": "unknown"},
        ]}
        runner, _state, scheduler, gateway, _held = self.make_runner([caller, callee])

        runner.handle_key("f1")
        scheduler.run_pending()

        self.assertIn(("release", "f1"), gateway.events)

    def test_tail_wait_releases_at_end_before_wait_callback(self):
        trigger = {"key": "f1", "actions": [
            {"type": "system", "op": "wait", "ms": 100},
            self.down(),
        ]}
        runner, state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")

        self.assertIn(("", "f1"), state.pending_steps)
        self.assertEqual(gateway.events[-1], ("release", "f1"))

    def test_call_stop_boundary_keeps_release_suppression_through_pause_stop(self):
        runner, state, _scheduler, gateway, _held = self.make_runner([])
        state.run_to_end_key = "f1"

        with (patch.object(runner, "_commit_run_to_end_call"),
              patch.object(runner, "_finish_run_to_end_wait", return_value=True),
              patch.object(runner, "stop_run_to_end", wraps=runner.stop_run_to_end) as stop):
            runner._handle_stopped_run_to_end_call(
                runner._run_to_end_generation, "f1", runner._run_to_end_call_token,
                object(), SimpleNamespace(call_done=False),
            )

        stop.assert_called_once_with(release_held=False)
        self.assertNotIn(("release", "f1"), gateway.events)

    def test_back_does_not_release_and_rewind_does(self):
        target = {"key": "f1", "actions": [self.down(), {"type": "text", "value": "x"}]}
        back = {"key": "f2", "actions": [{"type": "system", "op": "back"}]}
        rewind = {"key": "f3", "actions": [{"type": "system", "op": "rewind", "target": "f1"}]}
        runner, _state, _scheduler, gateway, _held = self.make_runner([target, back, rewind])

        runner.handle_key("f1")
        runner.handle_key("f2")
        self.assertNotIn(("release", "f1"), gateway.events)
        runner.handle_key("f3")

        self.assertIn(("release", "f1"), gateway.events)

    def test_run_to_end_pause_and_discard_releases_owner(self):
        trigger = {
            "key": "f1", "run_to_end": True, "run_to_end_delay_ms": 50,
            "actions": [self.down(), {"type": "text", "value": "x"}],
        }
        runner, _state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        runner.pause_run_to_end()
        runner.discard_paused()

        self.assertEqual(gateway.events.count(("release", "f1")), 2)

    def test_tail_wrap_releases_before_sending_wrapped_head(self):
        trigger = {
            "key": "f1",
            "actions": [
                self.down(),
                {"type": "text", "value": "middle"},
                {"type": "system", "op": "counter_inc", "counter": "n"},
            ],
        }
        runner, state, _scheduler, gateway, _held = self.make_runner([trigger])

        runner.handle_key("f1")
        state.indices_for("")["f1"] = 2
        gateway.events.clear()
        runner.handle_key("f1")

        self.assertEqual(gateway.events[0], ("release", "f1"))
        self.assertEqual(gateway.events[1][:2], ("send", "f1"))
        self.assertEqual(len(gateway.events), 2)

    def test_error_releases_before_notifying(self):
        notifications = []
        runner, _state, _scheduler, gateway, _held = self.make_runner(
            [{"key": "f1", "actions": [self.down(), {"type": "system", "op": "unknown"}]}],
            notify_error=lambda *_args: notifications.append(tuple(event[0] for event in gateway.events)),
        )

        runner.handle_key("f1")
        runner.handle_key("f1")

        self.assertEqual(notifications, [("send", "release")])

    def test_owner_is_inherited_by_callee_and_callee_end_does_not_release(self):
        caller = {
            "key": "f1", "actions": [
                {"type": "system", "op": "call", "target": "f2"},
                {"type": "text", "value": "caller"},
            ],
        }
        callee = {"key": "f2", "actions": [self.down()]}
        runner, _state, scheduler, gateway, _held = self.make_runner([caller, callee])

        runner.handle_key("f1")
        scheduler.run_pending()

        sends = [event for event in gateway.events if event[0] == "send"]
        self.assertEqual(sends, [("send", "f1", self.down())])
        self.assertFalse(any(event[0] == "release" for event in gateway.events))

    def test_nested_call_keeps_the_root_owner(self):
        root = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2", "all": True},
        ]}
        middle = {"key": "f2", "actions": [
            {"type": "system", "op": "call", "target": "f3", "all": True},
        ]}
        leaf = {"key": "f3", "actions": [self.down()]}
        runner, _state, scheduler, gateway, _held = self.make_runner([root, middle, leaf])

        runner.handle_key("f1")
        scheduler.run_pending()

        sends = [event for event in gateway.events if event[0] == "send"]
        self.assertEqual(sends, [("send", "f1", self.down())])

    def test_continuous_call_keeps_the_run_owner(self):
        runner_trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
                          "actions": [{"type": "system", "op": "call", "target": "f2", "all": True}]}
        callee = {"key": "f2", "actions": [self.down()]}
        runner, _state, scheduler, gateway, _held = self.make_runner([runner_trigger, callee])

        runner.handle_key("f1")
        scheduler.run_pending()

        sends = [event for event in gateway.events if event[0] == "send"]
        self.assertEqual(sends, [("send", "f1", self.down())])

    def test_direct_callee_completion_releases_linked_caller_owner(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2"},
        ]}
        callee = {"key": "f2", "actions": [self.down()]}
        runner, state, _scheduler, gateway, _held = self.make_runner([caller, callee])
        state.indices_for("")["f1"] = 0
        state.call_refs_for("").add("f1")

        runner.handle_key("f2")

        self.assertIn(("send", "f2", self.down()), gateway.events)
        self.assertIn(("release", "f1"), gateway.events)

    def test_file_line_begin_and_poll_run_under_the_top_level_owner(self):
        trigger = {"key": "f1", "actions": [
            self.down(), {"type": "file_line", "path": "unused"},
            {"type": "text", "value": "after"},
        ]}
        def begin(_action):
            return object()
        def poll(_handle):
            return True
        runner, _state, scheduler, _gateway, _held = self.make_runner(
            [trigger], begin_file_line=begin, poll_file_line=poll,
        )

        runner.handle_key("f1")
        runner.handle_key("f1")
        scheduler.run_one()

        self.assertEqual(_gateway.events[-2:], [
            ("begin_file_line", "f1"), ("poll_file_line", "f1"),
        ])

    def test_step_call_file_line_uses_the_callers_owner(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2"},
            {"type": "text", "value": "after"},
        ]}
        callee = {"key": "f2", "actions": [
            {"type": "file_line", "path": "unused"},
            {"type": "text", "value": "callee next"},
        ]}
        runner, _state, scheduler, gateway, _held = self.make_runner(
            [caller, callee], begin_file_line=lambda _action: object(),
            poll_file_line=lambda _handle: True,
        )

        runner.handle_key("f1")
        scheduler.run_one()
        scheduler.run_one()

        self.assertEqual(gateway.events[-2:], [
            ("begin_file_line", "f1"), ("poll_file_line", "f1"),
        ])

    def test_continuous_file_line_begin_and_poll_run_under_the_run_owner(self):
        trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
                   "actions": [self.down(), {"type": "file_line", "path": "unused"},
                               {"type": "text", "value": "after"}]}
        runner, _state, scheduler, gateway, _held = self.make_runner(
            [trigger], begin_file_line=lambda _action: object(),
            poll_file_line=lambda _handle: True,
        )

        runner.handle_key("f1")
        scheduler.run_pending()

        self.assertIn(("begin_file_line", "f1"), gateway.events)
        self.assertIn(("poll_file_line", "f1"), gateway.events)

    def test_executor_uses_scoped_owner_for_execute_begin_and_poll_errors(self):
        gateway = FakeGateway()
        held = HeldInputs(gateway)
        events = gateway.events
        action_errors = []

        class FailedLoader:
            def poll(self, _request):
                raise RuntimeError("poll failed")

        executor = ActionExecutor(
            input_gateway=gateway,
            validate_hotkey=lambda value: ("", value),
            on_action_error=lambda action, message: action_errors.append(
                (action, message, tuple(events))
            ),
            on_runtime_error=Mock(), on_stop_hook=Mock(), on_toggle_mode=Mock(),
            on_select_keymap=Mock(), on_trigger=Mock(),
            file_line_loader=FailedLoader(), held_inputs=held,
        )

        with held.owner_scope("f1"):
            self.assertTrue(executor.execute(self.down(), owner=None))
        held.release_owner("f1")
        self.assertEqual(events[-1], ("key_up", "shift"))

        with held.owner_scope("f1"):
            held.press_key(held.current_owner, "shift")
            self.assertFalse(executor.execute({"type": "unknown"}, owner=None))
        self.assertEqual(action_errors[-1][2][-2:], (("key_down", "shift"), ("key_up", "shift")))

        with held.owner_scope("f1"):
            held.press_key(held.current_owner, "shift")
            self.assertIsNone(executor.begin_file_line({"type": "file_line", "path": "x"}))
        self.assertEqual(action_errors[-1][2][-2:], (("key_down", "shift"), ("key_up", "shift")))

        handle = FileLineHandle(object(), 1, "error", "x", {"type": "file_line", "path": "x"})
        with held.owner_scope("f1"):
            held.press_key(held.current_owner, "shift")
            self.assertFalse(executor.poll_file_line(handle, owner=None))
        self.assertEqual(action_errors[-1][2][-2:], (("key_down", "shift"), ("key_up", "shift")))

    def test_held_input_owner_scope_restores_after_exception_and_nested_scope(self):
        held = HeldInputs(FakeGateway())

        with self.assertRaisesRegex(RuntimeError, "scope failed"):
            with held.owner_scope("root"):
                with held.owner_scope("callee"):
                    self.assertEqual(held.current_owner, "callee")
                    raise RuntimeError("scope failed")

        self.assertIsNone(held.current_owner)


if __name__ == "__main__":
    unittest.main()
