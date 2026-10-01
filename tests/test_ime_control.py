from __future__ import annotations

import unittest

from keyseq.infrastructure.ime_control import ImeController


class FakeTimer:
    def __init__(self, delay: float, callback) -> None:
        self.delay = delay
        self.callback = callback
        self.daemon = None
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        self.callback()


class FakeImeApi:
    def __init__(self) -> None:
        self.window: int | None = 10
        self.open_status: dict[int, bool] = {10: True, 20: True}
        self.events: list[tuple[object, ...]] = []
        self.get_window_error: Exception | None = None
        self.get_status_error: Exception | None = None
        self.set_status_error: Exception | None = None

    def get_ime_window(self) -> int | None:
        self.events.append(("window", self.window))
        if self.get_window_error is not None:
            raise self.get_window_error
        return self.window

    def get_open_status(self, window: int) -> int:
        self.events.append(("get", window))
        if self.get_status_error is not None:
            raise self.get_status_error
        return int(self.open_status[window])

    def set_open_status(self, window: int, is_open: bool) -> None:
        self.events.append(("set", window, is_open))
        if self.set_status_error is not None:
            raise self.set_status_error
        self.open_status[window] = is_open


class ImeControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeImeApi()
        self.timers: list[FakeTimer] = []

        def timer_factory(delay: float, callback) -> FakeTimer:
            timer = FakeTimer(delay, callback)
            self.timers.append(timer)
            return timer

        self.controller = ImeController(self.api, timer_factory=timer_factory)

    def test_turns_off_then_restores_after_character_based_delay(self) -> None:
        reservation = self.controller.before_send()
        self.assertEqual(self.api.events, [
            ("window", 10), ("get", 10), ("set", 10, False),
        ])
        self.controller.after_send(reservation, 3)
        self.assertEqual(self.api.events[-1], ("set", 10, False))
        timer = self.timers[0]
        self.assertEqual(timer.delay, 0.32)
        self.assertTrue(timer.started)
        self.assertFalse(timer.daemon)
        timer.fire()
        self.assertEqual(self.api.events[-1], ("set", 10, True))
        self.assertTrue(self.api.open_status[10])

    def test_already_off_ime_is_not_touched_or_scheduled(self) -> None:
        self.api.open_status[10] = False
        reservation = self.controller.before_send()
        self.controller.after_send(reservation, 5)
        self.assertIsNone(reservation)
        self.assertEqual(self.api.events, [("window", 10), ("get", 10)])
        self.assertEqual(self.timers, [])

    def test_missing_window_and_api_failures_fall_back_without_reservation(self) -> None:
        self.api.window = None
        self.assertIsNone(self.controller.before_send())
        self.api.window = 10
        self.api.get_window_error = RuntimeError("window lookup failed")
        self.assertIsNone(self.controller.before_send())
        self.api.get_window_error = None
        self.api.get_status_error = RuntimeError("status failed")
        self.assertIsNone(self.controller.before_send())
        self.assertEqual(self.api.events[-1], ("get", 10))
        self.assertEqual(self.timers, [])

    def test_missing_win32_api_is_a_no_op(self) -> None:
        controller = ImeController(None, timer_factory=lambda *_: self.fail("timer created"))
        self.assertIsNone(controller.before_send())
        controller.after_send(None, 3)

    def test_same_window_resend_cancels_and_replaces_timer_without_requery(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 2)
        second = self.controller.before_send()
        self.controller.after_send(second, 4)
        self.assertEqual(self.api.events.count(("get", 10)), 1)
        self.assertTrue(self.timers[0].cancelled)
        self.assertEqual(self.timers[1].delay, 0.36)
        self.timers[0].fire()
        self.assertFalse(self.api.open_status[10])
        self.timers[1].fire()
        self.assertTrue(self.api.open_status[10])

    def test_timer_creation_and_start_failures_restore_and_allow_requery(self) -> None:
        class StartFailTimer(FakeTimer):
            def start(self) -> None:
                raise RuntimeError("timer start failed")

        def fail_creation(*_args):
            raise RuntimeError("timer creation failed")

        failing_factories = (
            fail_creation,
            lambda delay, callback: StartFailTimer(delay, callback),
        )
        for factory in failing_factories:
            with self.subTest(factory=factory):
                api = FakeImeApi()
                controller = ImeController(api, timer_factory=factory)
                reservation = controller.before_send()
                with self.assertLogs(
                    "keyseq.infrastructure.ime_control", level="ERROR"
                ):
                    controller.after_send(reservation, 1)
                self.assertTrue(api.open_status[10])

                next_reservation = controller.before_send()
                self.assertIsNotNone(next_reservation)
                self.assertEqual(api.events.count(("get", 10)), 2)
                self.assertFalse(api.open_status[10])

    def test_zero_character_reservation_restores_immediately_and_clears_state(self) -> None:
        reservation = self.controller.before_send()
        self.controller.after_send(reservation, 0)
        self.assertTrue(self.api.open_status[10])
        self.assertEqual(self.api.events[-1], ("set", 10, True))
        self.assertEqual(self.timers, [])

        next_reservation = self.controller.before_send()
        self.assertIsNotNone(next_reservation)
        self.assertEqual(self.api.events.count(("get", 10)), 2)
        self.assertFalse(self.api.open_status[10])

    def test_resend_after_timer_fires_queries_ime_and_turns_it_off_again(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.timers[0].fire()
        self.assertTrue(self.api.open_status[10])

        second = self.controller.before_send()
        self.assertIsNotNone(second)
        self.assertEqual(self.api.events.count(("get", 10)), 2)
        self.assertEqual(self.api.events[-1], ("set", 10, False))
        self.assertFalse(self.api.open_status[10])

    def test_different_windows_have_independent_restore_timers(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.api.window = 20
        second = self.controller.before_send()
        self.controller.after_send(second, 2)
        self.assertEqual(len(self.timers), 2)
        self.timers[0].fire()
        self.assertTrue(self.api.open_status[10])
        self.assertFalse(self.api.open_status[20])
        self.timers[1].fire()
        self.assertTrue(self.api.open_status[20])

    def test_restore_failure_is_logged_and_does_not_escape_timer(self) -> None:
        reservation = self.controller.before_send()
        self.controller.after_send(reservation, 1)
        self.api.set_status_error = RuntimeError("restore failed")
        with self.assertLogs("keyseq.infrastructure.ime_control", level="ERROR"):
            self.timers[0].fire()


if __name__ == "__main__":
    unittest.main()
