from __future__ import annotations

import unittest
from collections.abc import Callable

from keyseq.application.held_inputs import HeldInputs
from keyseq.application.key_repeat import KeyRepeater


class ManualAfter:
    """予約だけを記録し、必要なときに callback を発火する。"""

    def __init__(self) -> None:
        self.next_id = 0
        self.calls: list[tuple[str, int]] = []
        self.callbacks: dict[str, Callable[[], None]] = {}
        self.cancelled: set[str] = set()

    def after(self, delay: int, callback) -> str:
        timer_id = f"after-{self.next_id}"
        self.next_id += 1
        self.calls.append((timer_id, delay))
        self.callbacks[timer_id] = callback
        return timer_id

    def after_cancel(self, timer_id: str) -> None:
        self.cancelled.add(timer_id)

    def fire(self, timer_id: str) -> None:
        self.callbacks[timer_id]()


class FakeInputGateway:
    """記録だけを行い、実際のキー入力は送らない gateway。"""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.failures: dict[tuple, Exception] = {}

    def key_identity(self, key: str) -> tuple[int, bool]:
        if key in {"", "unknown"}:
            raise ValueError(f"unknown key: {key!r}")
        return (30 if key in {"a", "a alias"} else 31, False)

    def press_key(self, key: str) -> None:
        call = ("press_key", key)
        self.calls.append(call)
        error = self.failures.get(call)
        if error is not None:
            raise error

    def release_key(self, key: str) -> None:
        call = ("release_key", key)
        self.calls.append(call)
        error = self.failures.get(call)
        if error is not None:
            raise error


class HeldInputsRepeatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = FakeInputGateway()
        self.timer = ManualAfter()
        self.guards: list[str] = []
        self.changes: list[tuple[str, ...]] = []
        self.repeat_errors: list[tuple[dict, str]] = []
        self.repeater = KeyRepeater(
            after=self.timer.after,
            after_cancel=self.timer.after_cancel,
            get_timing=lambda: (300, 40),
        )
        self.held = HeldInputs(
            self.gateway,
            enter_send_guard=lambda: self.guards.append("enter"),
            exit_send_guard=lambda: self.guards.append("exit"),
            on_change=self.changes.append,
            repeater=self.repeater,
            on_repeat_error=lambda action, message: self.repeat_errors.append(
                (action, message)
            ),
        )
        self.action = {
            "type": "key_hold", "edge": "down", "value": "a", "repeat": True,
        }

    def test_repeat_action_starts_only_after_successful_press_and_sends_under_guard(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        self.assertEqual(self.timer.calls, [("after-0", 300)])
        self.assertEqual(self.gateway.calls, [("press_key", "a")])
        self.assertEqual(self.changes, [("a",)])

        self.timer.fire("after-0")

        self.assertEqual(self.gateway.calls, [("press_key", "a"), ("press_key", "a")])
        self.assertEqual(self.guards, ["enter", "exit", "enter", "exit"])
        self.assertEqual(self.changes, [("a",)])

    def test_stop_repeat_for_keys_skips_unresolvable_names_and_still_stops_target(self) -> None:
        self.held.press_key("f1", "a", repeat_action=self.action)
        self.held.stop_repeat_for_keys(["unknown", "", "b"])
        self.assertTrue(self.repeater.has_target)
        self.held.stop_repeat_for_keys(["unknown", "a"])
        self.assertFalse(self.repeater.has_target)

    def test_no_repeat_action_does_not_start_timer(self) -> None:
        self.held.press_key("owner", "a")

        self.assertEqual(self.timer.calls, [])

    def test_press_failure_does_not_start_repeat_and_preserves_compensation(self) -> None:
        error = RuntimeError("press failed")
        self.gateway.failures[("press_key", "a")] = error

        with self.assertRaises(RuntimeError) as caught:
            self.held.press_key("owner", "a", repeat_action=self.action)

        self.assertIs(caught.exception, error)
        self.assertEqual(self.timer.calls, [])
        self.assertEqual(self.gateway.calls, [("press_key", "a"), ("release_key", "a")])
        self.assertEqual(self.held.display_names, ())

    def test_targeted_release_stops_before_sending_and_stale_callback_is_ignored(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        target_states: list[bool] = []
        release_key = self.gateway.release_key

        def observe_release(key: str) -> None:
            target_states.append(self.repeater.is_target(("key", 30, False)))
            release_key(key)

        self.gateway.release_key = observe_release

        self.held.release_key("a")
        self.timer.fire("after-0")

        self.assertEqual(self.timer.cancelled, {"after-0"})
        self.assertEqual(self.gateway.calls, [("press_key", "a"), ("release_key", "a")])
        self.assertEqual(target_states, [False])
        self.assertFalse(self.repeater.is_target(("key", 30, False)))

    def test_repeat_send_failure_releases_key_and_reports_without_raising_into_caller(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        repeat_error = RuntimeError("repeat failed")
        self.gateway.failures[("press_key", "a")] = repeat_error

        self.timer.fire("after-0")

        self.assertEqual(
            self.gateway.calls,
            [("press_key", "a"), ("press_key", "a"), ("release_key", "a")],
        )
        self.assertEqual(self.held.display_names, ())
        self.assertEqual(
            self.repeat_errors,
            [(self.action, "キーのリピート送信に失敗しました: repeat failed")],
        )
        self.assertFalse(self.repeater.is_target(("key", 30, False)))

    def test_repeat_send_failure_keeps_record_when_cleanup_release_fails(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        self.gateway.failures[("press_key", "a")] = RuntimeError("repeat failed")
        release_error = RuntimeError("release failed")
        self.gateway.failures[("release_key", "a")] = release_error

        self.timer.fire("after-0")

        self.assertEqual(self.held.display_names, ("a",))
        self.assertEqual(len(self.repeat_errors), 1)
        self.assertIn("解放エラー: release failed", self.repeat_errors[0][1])
        self.assertFalse(self.repeater.is_target(("key", 30, False)))

    def test_alias_with_same_identity_stops_repeat_before_release_send(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        self.gateway.failures[("release_key", "a alias")] = RuntimeError("stop after")

        with self.assertRaises(RuntimeError):
            self.held.release_key("a alias")

        self.assertFalse(self.repeater.is_target(("key", 30, False)))
        self.assertEqual(self.timer.cancelled, {"after-0"})
        self.assertEqual(self.gateway.calls[-1], ("release_key", "a alias"))

    def test_release_owner_all_and_keyboard_stop_even_when_release_fails(self) -> None:
        for release in (
            lambda held: held.release_owner("owner"),
            lambda held: held.release_all(),
            lambda held: held.release_keyboard(),
        ):
            with self.subTest(release=release):
                self.setUp()
                self.held.press_key("owner", "a", repeat_action=self.action)
                self.gateway.failures[("release_key", "a")] = RuntimeError("release failed")

                errors = release(self.held)

                self.assertEqual(len(errors), 1)
                self.assertFalse(self.repeater.is_target(("key", 30, False)))
                self.assertEqual(self.timer.cancelled, {"after-0"})

    def test_suspend_release_failure_discards_saved_repeat(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        self.gateway.failures[("release_key", "a")] = RuntimeError("release failed")

        with self.assertRaises(RuntimeError):
            self.held.suspend_keyboard()

        self.held.resume_keyboard()
        self.assertEqual(self.timer.calls, [("after-0", 300)])
        self.assertFalse(self.repeater.is_target(("key", 30, False)))

    def test_suspend_and_resume_restarts_only_the_previously_repeating_key(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        self.held.press_key("owner", "b")

        self.held.suspend_keyboard()
        self.held.resume_keyboard()

        self.assertEqual(self.timer.cancelled, {"after-0"})
        self.assertEqual(self.timer.calls[-1], ("after-1", 300))
        self.assertTrue(self.repeater.is_target(("key", 30, False)))
        self.assertFalse(self.repeater.is_target(("key", 31, False)))
        self.assertEqual(self.gateway.calls, [
            ("press_key", "a"), ("press_key", "b"),
            ("release_key", "a"), ("release_key", "b"),
            ("press_key", "a"), ("press_key", "b"),
        ])

    def test_failed_resume_does_not_restart_saved_repeat(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)
        self.held.press_key("owner", "b")
        self.held.suspend_keyboard()
        self.gateway.failures[("press_key", "b")] = RuntimeError("resume failed")

        with self.assertRaises(RuntimeError):
            self.held.resume_keyboard()

        self.assertEqual(self.timer.calls, [("after-0", 300)])
        self.assertFalse(self.repeater.is_target(("key", 30, False)))

    def test_stop_repeat_for_keys_matches_gateway_identity(self) -> None:
        self.held.press_key("owner", "a", repeat_action=self.action)

        self.held.stop_repeat_for_keys(["b"])
        self.assertTrue(self.repeater.is_target(("key", 30, False)))
        self.held.stop_repeat_for_keys(["a"])

        self.assertFalse(self.repeater.is_target(("key", 30, False)))
        self.assertEqual(self.timer.cancelled, {"after-0"})


if __name__ == "__main__":
    unittest.main()
