from __future__ import annotations

import unittest
from collections.abc import Callable

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


class KeyRepeaterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timer = ManualAfter()
        self.sent: list[str] = []
        self.failures: list[tuple] = []
        self.timing_calls = 0
        self.action = {"type": "key_hold", "edge": "down", "value": "a", "repeat": True}
        self.identity = ("key", 30, False)

        def get_timing() -> tuple[int, int]:
            self.timing_calls += 1
            return (350, 45)

        self.repeater = KeyRepeater(
            after=self.timer.after,
            after_cancel=self.timer.after_cancel,
            get_timing=get_timing,
            send=self.sent.append,
            on_failure=lambda *args: self.failures.append(args),
        )

    def test_wait_then_repeats_at_interval_after_each_send(self) -> None:
        self.repeater.start(self.identity, "a", self.action)

        self.assertEqual(self.timer.calls, [("after-0", 350)])
        self.assertEqual(self.sent, [])
        self.timer.fire("after-0")
        self.assertEqual(self.sent, ["a"])
        self.assertEqual(self.timer.calls[-1], ("after-1", 45))
        self.timer.fire("after-1")
        self.assertEqual(self.sent, ["a", "a"])
        self.assertEqual(self.timer.calls[-1], ("after-2", 45))
        self.assertEqual(self.timing_calls, 1)

    def test_reschedule_failure_stops_without_leaving_target(self) -> None:
        self.repeater.start(self.identity, "a", self.action)
        original_after = self.timer.after

        def failing_after(delay, callback):
            raise RuntimeError("after failed")

        self.repeater._after = failing_after
        with self.assertLogs("keyseq.application.key_repeat", level="ERROR"):
            self.timer.fire("after-0")
        self.assertEqual(self.sent, ["a"])
        self.assertFalse(self.repeater.has_target)
        self.repeater._after = original_after

    def test_restart_of_same_target_invalidates_previous_reservation(self) -> None:
        self.repeater.start(self.identity, "a", self.action)

        self.repeater.start(self.identity, "a", self.action)
        self.timer.fire("after-0")
        self.timer.fire("after-1")

        self.assertEqual(self.timer.cancelled, {"after-0"})
        self.assertEqual(self.sent, ["a"])
        self.assertEqual(self.timer.calls, [("after-0", 350), ("after-1", 350), ("after-2", 45)])
        self.assertEqual(self.timing_calls, 2)

    def test_start_replaces_target_and_stale_timer_does_not_send(self) -> None:
        self.repeater.start(self.identity, "a", self.action)
        self.repeater.start(("key", 31, False), "b", {"value": "b"})

        self.assertEqual(self.timer.cancelled, {"after-0"})
        self.timer.fire("after-0")
        self.assertEqual(self.sent, [])
        self.assertTrue(self.repeater.is_target(("key", 31, False)))
        self.assertFalse(self.repeater.is_target(self.identity))
        self.assertEqual(self.timer.calls[-1], ("after-1", 350))

    def test_stop_cancels_reservation_and_clears_target(self) -> None:
        self.repeater.start(self.identity, "a", self.action)

        self.repeater.stop()
        self.timer.fire("after-0")

        self.assertEqual(self.timer.cancelled, {"after-0"})
        self.assertEqual(self.sent, [])
        self.assertFalse(self.repeater.is_target(self.identity))

    def test_each_missing_timer_callback_disables_repeating(self) -> None:
        for after, after_cancel in ((None, self.timer.after_cancel), (self.timer.after, None)):
            repeater = KeyRepeater(
                after=after,
                after_cancel=after_cancel,
                get_timing=lambda: (350, 45),
                send=self.sent.append,
            )

            repeater.start(self.identity, "a", self.action)

        self.assertEqual(self.timer.calls, [])
        self.assertEqual(self.sent, [])

    def test_pause_returns_target_and_resume_starts_a_fresh_wait(self) -> None:
        self.repeater.start(self.identity, "a", self.action)

        saved = self.repeater.pause_for_text()
        self.assertEqual(saved, (self.identity, "a", self.action))
        self.assertFalse(self.repeater.is_target(self.identity))
        self.repeater.resume_after_text(saved)

        self.assertEqual(self.timer.calls[-1], ("after-1", 350))
        self.assertTrue(self.repeater.is_target(self.identity))

    def test_suppression_blocks_start_resume_and_firing_until_ended(self) -> None:
        self.repeater.start(self.identity, "a", self.action)
        self.repeater.begin_suppress()
        self.repeater.begin_suppress()
        self.timer.fire("after-0")
        self.assertEqual(self.sent, [])
        self.assertEqual(len(self.timer.calls), 1)

        self.repeater.end_suppress()
        self.repeater.start(self.identity, "a", self.action)
        self.assertEqual(len(self.timer.calls), 1)
        self.repeater.end_suppress()
        self.repeater.start(self.identity, "a", self.action)
        self.assertEqual(self.timer.calls[-1], ("after-1", 350))
        self.repeater.begin_suppress()
        self.timer.fire("after-1")
        self.assertEqual(self.sent, [])
        self.assertEqual(len(self.timer.calls), 2)
        self.assertFalse(self.repeater.is_target(self.identity))

    def test_send_failure_stops_and_reports_original_target_and_exception(self) -> None:
        error = RuntimeError("repeat failed")
        self.repeater.set_callbacks(
            lambda _key: (_ for _ in ()).throw(error),
            lambda identity, key, action, exc: self.failures.append(
                (identity, key, action, exc)
            ),
        )
        self.repeater.start(self.identity, "a", self.action)

        self.timer.fire("after-0")

        self.assertFalse(self.repeater.is_target(self.identity))
        self.assertEqual(self.failures, [(self.identity, "a", self.action, error)])
        self.assertEqual(len(self.timer.calls), 1)

    def test_resume_is_refused_while_suppressed_and_does_not_resume_later(self) -> None:
        self.repeater.start(self.identity, "a", self.action)
        saved = self.repeater.pause_for_text()
        self.repeater.begin_suppress()

        self.repeater.resume_after_text(saved)
        self.repeater.end_suppress()

        self.assertEqual(self.timer.calls, [("after-0", 350)])
        self.assertFalse(self.repeater.is_target(self.identity))


if __name__ == "__main__":
    unittest.main()
