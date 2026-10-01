from __future__ import annotations

import unittest
import ctypes
import threading
from unittest.mock import Mock, patch

from keyseq.infrastructure import ime_control
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
        self.now = 10.0

        def timer_factory(delay: float, callback) -> FakeTimer:
            timer = FakeTimer(delay, callback)
            self.timers.append(timer)
            return timer

        self.controller = ImeController(
            self.api, timer_factory=timer_factory, clock=lambda: self.now,
        )

    def test_turns_off_then_restores_after_character_based_delay(self) -> None:
        reservation = self.controller.before_send()
        self.assertEqual(self.api.events, [
            ("window", 10), ("get", 10), ("set", 10, False),
        ])
        self.controller.after_send(reservation, 3)
        self.assertEqual(self.api.events[-1], ("set", 10, False))
        timer = self.timers[0]
        self.assertAlmostEqual(timer.delay, 0.32)
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

    def test_same_window_resend_requeries_and_preserves_later_deadline(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 20)
        self.now += 0.1
        second = self.controller.before_send()
        self.controller.after_send(second, 1)
        self.assertEqual(self.api.events.count(("get", 10)), 2)
        self.assertTrue(self.timers[0].cancelled)
        self.assertAlmostEqual(self.timers[1].delay, 0.9)
        self.timers[0].fire()
        self.assertFalse(self.api.open_status[10])
        self.timers[1].fire()
        self.assertTrue(self.api.open_status[10])

    def test_short_then_long_resend_extends_deadline(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.now += 0.1
        second = self.controller.before_send()
        self.controller.after_send(second, 20)
        self.assertAlmostEqual(self.timers[1].delay, 1.0)

    def test_overlapping_sends_restore_only_after_both_finish(self) -> None:
        first = self.controller.before_send()
        second = self.controller.before_send()
        self.controller.after_send(second, 1)
        self.assertEqual(self.timers, [])
        self.controller.after_send(first, 20)
        self.assertEqual(len(self.timers), 1)
        self.assertAlmostEqual(self.timers[0].delay, 1.0)
        self.timers[0].fire()
        self.assertTrue(self.api.open_status[10])

    def test_resend_turns_ime_off_again_if_user_enabled_it(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.api.open_status[10] = True
        second = self.controller.before_send()
        self.assertIsNotNone(second)
        self.assertEqual(self.api.events[-2:], [("get", 10), ("set", 10, False)])

    def test_resend_query_failure_keeps_reservation(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.api.get_status_error = OSError("timed out")
        with self.assertLogs("keyseq.infrastructure.ime_control", level="ERROR"):
            second = self.controller.before_send()
        self.assertIsNotNone(second)
        self.assertTrue(self.timers[0].cancelled)
        self.api.get_status_error = None
        self.controller.after_send(second, 2)
        self.timers[1].fire()
        self.assertTrue(self.api.open_status[10])

    def test_restore_leaves_already_on_ime_untouched(self) -> None:
        reservation = self.controller.before_send()
        self.controller.after_send(reservation, 1)
        self.api.open_status[10] = True
        self.timers[0].fire()
        self.assertEqual(self.api.events[-1], ("get", 10))

    def test_restore_query_failure_does_not_set_status(self) -> None:
        reservation = self.controller.before_send()
        self.controller.after_send(reservation, 1)
        self.api.get_status_error = OSError("timed out")
        with self.assertLogs("keyseq.infrastructure.ime_control", level="ERROR"):
            self.timers[0].fire()
        self.assertEqual(self.api.events[-1], ("get", 10))

    def test_generation_change_during_query_discards_old_result(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        original = self.api.get_open_status
        triggered = False

        def query(window):
            nonlocal triggered
            if not triggered:
                triggered = True
                self.controller._states[window].generation += 1
            return original(window)

        self.api.get_open_status = query
        self.timers[0].fire()
        self.assertFalse(self.api.open_status[10])
        self.assertNotIn(("set", 10, True), self.api.events)

    def test_generation_change_during_disable_rechecks_status_and_restores(self) -> None:
        original = self.api.set_open_status
        changed = False

        def set_status(window, is_open):
            nonlocal changed
            self.assertTrue(self.controller._lock.acquire(blocking=False))
            self.controller._lock.release()
            original(window, is_open)
            if not changed:
                changed = True
                self.controller._states[window].generation += 1

        self.api.set_open_status = set_status
        reservation = self.controller.before_send()
        self.assertIsNotNone(reservation)
        self.assertEqual(self.api.events.count(("get", 10)), 2)
        self.controller.after_send(reservation, 1)
        self.timers[0].fire()
        self.assertTrue(self.api.open_status[10])

    def test_query_timeout_still_allows_no_ime_reservation(self) -> None:
        self.api.get_status_error = OSError("timed out")
        with self.assertLogs("keyseq.infrastructure.ime_control", level="ERROR"):
            reservation = self.controller.before_send()
        self.assertIsNone(reservation)
        self.assertEqual(self.timers, [])

    def test_shutdown_cancels_all_and_prevents_new_reservations(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.api.window = 20
        second = self.controller.before_send()
        self.controller.after_send(second, 1)
        self.controller.restore_all_now()
        self.assertTrue(all(timer.cancelled for timer in self.timers))
        self.assertTrue(self.api.open_status[10])
        self.assertTrue(self.api.open_status[20])
        self.timers[0].fire()
        self.assertEqual(self.api.events.count(("set", 10, True)), 1)
        self.assertIsNone(self.controller.before_send())

    def test_shutdown_waits_for_active_text_before_restoring(self) -> None:
        reservation = self.controller.before_send()
        finished = threading.Event()

        def close():
            self.controller.restore_all_now()
            finished.set()

        worker = threading.Thread(target=close)
        worker.start()
        try:
            self.assertFalse(finished.wait(0.01))
            self.assertFalse(self.api.open_status[10])
            self.controller.after_send(reservation, 3)
            self.assertTrue(finished.wait(1))
            self.assertTrue(self.api.open_status[10])
        finally:
            self.controller.after_send(reservation, 3)
            worker.join(1)

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
                self.assertEqual(api.events.count(("get", 10)), 3)
                self.assertFalse(api.open_status[10])

    def test_zero_character_reservation_restores_immediately_and_clears_state(self) -> None:
        reservation = self.controller.before_send()
        self.controller.after_send(reservation, 0)
        self.assertTrue(self.api.open_status[10])
        self.assertEqual(self.api.events[-1], ("set", 10, True))
        self.assertEqual(self.timers, [])

        next_reservation = self.controller.before_send()
        self.assertIsNotNone(next_reservation)
        self.assertEqual(self.api.events.count(("get", 10)), 3)
        self.assertFalse(self.api.open_status[10])

    def test_resend_after_timer_fires_queries_ime_and_turns_it_off_again(self) -> None:
        first = self.controller.before_send()
        self.controller.after_send(first, 1)
        self.timers[0].fire()
        self.assertTrue(self.api.open_status[10])

        second = self.controller.before_send()
        self.assertIsNotNone(second)
        self.assertEqual(self.api.events.count(("get", 10)), 3)
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


class Win32ImeApiTests(unittest.TestCase):
    def test_timeout_is_failure_and_result_uses_pointer_sized_storage(self) -> None:
        user32 = Mock()
        imm32 = Mock()
        user32.SendMessageTimeoutW.return_value = 0
        with patch.object(ime_control.sys, "platform", "win32"), patch.object(
            ime_control.ctypes, "WinDLL", side_effect=[user32, imm32], create=True,
        ):
            api = ime_control._Win32ImeApi()
        self.assertEqual(
            user32.SendMessageTimeoutW.argtypes[-1],
            ctypes.POINTER(ctypes.c_size_t),
        )
        with self.assertRaises(OSError):
            api.get_open_status(10)
        self.assertEqual(user32.SendMessageTimeoutW.call_args.args[4:6], (0x0002, 200))

    def test_non_windows_unavailable_api_warns_without_traceback(self) -> None:
        with patch.object(ime_control.sys, "platform", "linux"), self.assertLogs(
            "keyseq.infrastructure.ime_control", level="WARNING",
        ) as logs:
            controller = ime_control._create_default_controller()
        self.assertIsNone(controller.before_send())
        self.assertEqual(len(logs.records), 1)
        self.assertIsNone(logs.records[0].exc_info)


if __name__ == "__main__":
    unittest.main()
