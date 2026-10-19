from __future__ import annotations

import threading
import unittest
from collections.abc import Callable
from types import SimpleNamespace

from keyseq.application.input_router import InputRoute
from keyseq.application.make_only_keys import (
    MakeOnlyKeyFilter,
    MakeOnlyResult,
    SyntheticKeyEvent,
)
from keyseq.domain.make_only_keys import (
    MAKE_ONLY_SCAN_CODES,
    is_make_only_scan_code,
)


class FakeClockAndScheduler:
    """A manually advanced clock and a scheduler whose callbacks tests fire."""

    def __init__(self) -> None:
        self.now = 0.0
        self.scheduled: list[tuple[float, Callable[[], None]]] = []

    def clock(self) -> float:
        return self.now

    def schedule(self, delay: float, callback: Callable[[], None]) -> None:
        self.scheduled.append((delay, callback))

    def fire(self, index: int = -1) -> None:
        callback = self.scheduled[index][1]
        callback()


class MakeOnlyKeyFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.time = FakeClockAndScheduler()
        self.routed: list[object] = []
        self.released: list[object] = []
        self.timer_routes: list[tuple[tuple[InputRoute, ...], int]] = []
        self.pause_count = 0
        self.repeat_delay_ms = 500
        self.next_route = InputRoute(actions=(object(),), accept=False)
        self.filter = self.make_filter()

    def make_filter(
        self,
        *,
        on_routes: Callable[[tuple[InputRoute, ...], int], None] | None = None,
        trace: Callable[[str], None] | None = None,
    ) -> MakeOnlyKeyFilter:
        def route(event: object) -> InputRoute:
            self.routed.append(event)
            return self.next_route

        def timer_routes(routes: tuple[InputRoute, ...], generation: int) -> None:
            self.timer_routes.append((routes, generation))
            if on_routes is not None:
                on_routes(routes, generation)

        return MakeOnlyKeyFilter(
            route=route,
            release_state=self.released.append,
            clock=self.time.clock,
            schedule=self.time.schedule,
            get_hook_pause_count=lambda: self.pause_count,
            get_repeat_delay_ms=lambda: self.repeat_delay_ms,
            on_routes=timer_routes,
            trace=trace,
        )

    def test_trace_reports_press_release_and_pending_discard(self) -> None:
        trace: list[str] = []
        self.filter = self.make_filter(trace=trace.append)

        self.send_down(0.0)
        self.send_up(0.005)
        self.send_down(0.100)
        self.send_down(0.150)
        self.send_down(0.163)
        self.send_down(0.300)
        self.send_down(0.400)
        self.time.now = 0.4161
        self.time.fire()
        self.send_down(1.0)
        self.send_down(1.500)
        self.time.now = 1.5161
        self.time.fire()

        self.assertTrue(any("down accept=False" in line for line in trace))
        self.assertTrue(any("up accept=False actions=1" in line for line in trace))
        self.assertTrue(any("kind=half-pair-release" in line for line in trace))
        self.assertTrue(any("continuable=False" in line for line in trace))
        self.assertTrue(any("pending confirmed kind=discarded-hold" in line for line in trace))
        self.assertTrue(all("t=" in line and "scan=241" in line and "generation=" in line for line in trace))

    def test_trace_is_optional(self) -> None:
        self.filter = self.make_filter()
        self.assertIsNotNone(self.send_down(0.0))

    def send_down(
        self, at: float, scan_code: int = 241, name: str | None = None
    ) -> MakeOnlyResult | None:
        self.time.now = at
        return self.filter.handle(
            SimpleNamespace(event_type="down", scan_code=scan_code, name=name)
        )

    def send_up(
        self, at: float, scan_code: int = 241, name: str | None = None
    ) -> MakeOnlyResult | None:
        self.time.now = at
        return self.filter.handle(
            SimpleNamespace(event_type="up", scan_code=scan_code, name=name)
        )

    def test_one_press_and_release_pair(self) -> None:
        first = self.send_down(0.0, name="muhenkan")
        self.send_down(0.045, name="muhenkan")
        self.send_down(0.056, name="muhenkan")

        self.assertEqual(len(first.routes), 1)
        self.assertEqual([e.event_type for e in self.routed], ["down"])
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 0)
        self.assertEqual(self.released[0], SyntheticKeyEvent("up", 241, "muhenkan"))

    def test_hold_does_not_repeat_then_releases(self) -> None:
        self.send_down(0.0)
        for repeat_time in (0.500, 0.533, 0.566):
            self.send_down(repeat_time)
            self.time.now = repeat_time + 0.0161
            self.time.fire()
        self.send_down(0.588)  # +22 ms after the last physical repeat
        self.send_down(0.601)  # +13 ms: the release pair

        self.assertEqual([e.event_type for e in self.routed], ["down"])
        self.assertEqual(len(self.timer_routes), 0)
        self.assertEqual(len(self.released), 1)

    def test_single_missed_release_allows_next_press_and_pair(self) -> None:
        self.send_down(0.000)
        self.send_down(0.045)
        self.send_down(0.120)
        self.send_down(0.165)
        self.send_down(0.176)

        self.assertEqual([e.event_type for e in self.routed], ["down", "down"])
        self.assertEqual(len(self.released), 2)
        self.assertEqual(len(self.timer_routes), 0)

    def test_half_release_threshold_uses_repeat_delay(self) -> None:
        self.repeat_delay_ms = 500
        self.send_down(0.000, scan_code=241)
        self.send_down(0.399, scan_code=241)
        self.time.now = 0.4151
        self.time.fire(index=0)
        self.send_down(0.500, scan_code=242)
        self.send_down(0.901, scan_code=242)
        self.time.now = 0.9171
        self.time.fire(index=1)

        self.assertEqual([e.scan_code for e in self.released], [241])
        self.filter.clear()
        self.repeat_delay_ms = 250
        self.send_down(1.000, scan_code=241)
        self.send_down(1.149, scan_code=241)
        self.time.now = 1.1651
        self.time.fire(index=2)
        self.send_down(1.300, scan_code=241)
        self.send_down(1.451, scan_code=241)
        self.time.now = 1.4671
        self.time.fire(index=3)
        self.assertEqual([e.scan_code for e in self.released], [241, 241])

    def test_three_quick_taps_each_produce_one_press_and_release(self) -> None:
        for first, second, third in (
            (0.000, 0.045, 0.056),
            (0.120, 0.165, 0.176),
            (0.240, 0.285, 0.296),
        ):
            self.send_down(first)
            self.send_down(second)
            self.send_down(third)

        self.assertEqual(len(self.routed), 3)
        self.assertEqual(len(self.released), 3)
        self.assertEqual(len(self.timer_routes), 0)

    def test_stale_press_followed_by_pair_does_not_repeat(self) -> None:
        self.send_down(0.0)
        self.send_down(1.000)
        self.send_down(1.011)

        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_stale_press_followed_by_single_press_releases_then_represses(self) -> None:
        self.send_down(0.0)
        self.send_down(1.000)
        self.time.now = 1.0161
        self.time.fire()

        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.routed), 2)
        self.assertEqual(len(self.timer_routes), 1)
        self.assertEqual(len(self.timer_routes[0][0]), 1)

    def test_pair_after_discarded_hold_releases_and_second_is_dropped(self) -> None:
        self.send_down(0.0)
        self.send_down(0.500)
        self.time.now = 0.5161
        self.time.fire()
        self.send_down(0.533)
        self.send_down(0.544)
        dropped = self.send_down(0.550)

        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.released), 1)
        self.assertEqual(dropped.routes, ())
        self.assertEqual(len(self.timer_routes), 0)

    def test_late_old_hold_is_discarded_then_new_pending_is_created(self) -> None:
        self.send_down(0.0)
        self.send_down(0.500)
        result = self.send_down(0.521)

        self.assertEqual(len(self.routed), 1)
        self.assertEqual(result.routes, ())
        self.assertEqual(len(self.time.scheduled), 2)
        self.assertEqual(len(self.timer_routes), 0)

    def test_late_pending_half_release_reprocesses_next_down_as_continuation(self) -> None:
        self.send_down(0.0)
        self.send_down(0.100)
        result = self.send_down(0.120)

        self.assertEqual([e.event_type for e in self.routed], ["down"])
        self.assertEqual(result.routes, ())
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_continuation_after_late_half_release_does_not_route(self) -> None:
        self.send_down(0.0)
        self.send_down(0.100)
        self.send_down(0.130)

        self.assertEqual([e.event_type for e in self.routed], ["down"])
        self.assertEqual(len(self.released), 1)
        self.assertTrue(self.filter._states[241].pressed)
        self.assertEqual(self.filter._states[241].pressed_at, 0.130)

    def test_repeat_misclassified_pair_does_not_start_output_chain(self) -> None:
        trace: list[str] = []
        self.filter = self.make_filter(trace=trace.append)
        self.send_down(0.0)
        for index in range(6):
            at = 0.500 + index * 0.033
            self.send_down(at)
            if index < 5:
                self.time.now = at + 0.0161
                self.time.fire()
        self.send_down(0.500 + 5 * 0.033 + 0.015)
        for index in range(6):
            at = 0.710 + index * 0.030
            self.send_down(at)
            if index < 5:
                self.time.now = at + 0.0161
                self.time.fire()
        self.send_down(0.710 + 5 * 0.030 + 0.022)
        self.send_down(0.710 + 5 * 0.030 + 0.035)

        self.assertEqual([event.event_type for event in self.routed], ["down"])
        self.assertEqual(self.filter._states[241].pressed, False)
        self.assertTrue(any("continuation since_release_ms=" in line for line in trace))

    def test_long_release_continuation_boundaries(self) -> None:
        trace: list[str] = []
        self.filter = self.make_filter(trace=trace.append)
        self.send_down(0.0)
        self.send_down(0.500)
        self.send_down(0.516)
        continuation = self.send_down(0.516 + 0.060)
        self.assertEqual(len(self.routed), 1)
        self.assertFalse(continuation.accept)
        self.assertTrue(any("continuable=True" in line for line in trace))

        self.filter.clear()
        self.routed.clear()
        self.send_down(1.0)
        self.send_down(1.500)
        self.send_down(1.516)
        self.send_down(1.516 + 0.061)
        self.assertEqual(len(self.routed), 2)

        self.filter.clear()
        self.routed.clear()
        self.send_down(2.0)
        self.send_down(2.500)
        self.send_down(2.516)
        dropped = self.send_down(2.516 + 0.016)
        self.assertEqual(len(self.routed), 1)
        self.assertEqual(dropped.routes, ())

    def test_two_pair_spans_half_pair_release_threshold(self) -> None:
        self.send_down(0.0)
        self.send_down(0.390)
        self.send_down(0.420)
        self.send_down(0.509)

        self.assertEqual(len(self.routed), 2)
        self.assertEqual(len(self.released), 2)

    def test_short_release_pairs_do_not_make_continuations(self) -> None:
        for press, release, second in (
            (0.0, 0.050, 0.063),
            (0.100, 0.150, 0.163),
            (0.200, 0.250, 0.263),
        ):
            self.send_down(press)
            self.send_down(release)
            self.send_down(second)

        self.assertEqual(len(self.routed), 3)
        self.assertEqual(len(self.released), 3)

    def test_long_hold_continuation_rebases_press_time_for_later_taps(self) -> None:
        self.send_down(0.0, name="0.000")
        repeat_times = [0.500 + index * 0.033 for index in range(16)]
        for at in repeat_times:
            self.send_down(at, name=f"{at:.3f}")
            if at != repeat_times[-1]:
                self.time.now = at + 0.0161
                self.time.fire()
        for at in (1.050, 1.063, 1.100, 1.150, 1.163, 1.200,
                   1.250, 1.263, 1.300, 1.350, 1.363):
            self.send_down(at, name=f"{at:.3f}")

        self.assertEqual(
            [event.name for event in self.routed], ["0.000", "1.200", "1.300"]
        )
        self.assertEqual(self.filter._states[241].pressed, False)

    def test_continuation_preserves_saved_decision_and_pause_passes_through(self) -> None:
        first = self.send_down(0.0)
        self.send_down(0.500)
        self.send_down(0.516)
        continued = self.send_down(0.550)
        self.assertFalse(first.accept)
        self.assertFalse(continued.accept)
        self.assertEqual(len(self.routed), 1)

        self.filter.clear()
        self.routed.clear()
        self.send_down(1.0)
        self.send_down(1.500)
        self.send_down(1.516)
        self.pause_count = 1
        paused = self.send_down(1.550)
        self.assertTrue(paused.accept)
        self.assertEqual(len(self.routed), 1)

    def test_real_up_clears_continuation_window(self) -> None:
        self.send_down(0.0)
        self.send_down(0.500)
        self.send_down(0.516)
        self.send_up(0.520)
        self.send_down(0.550)

        self.assertEqual(len(self.routed), 3)

    def test_push_80ms_after_continuation_pair_is_a_new_press(self) -> None:
        self.send_down(0.0)
        self.send_down(0.500)
        self.send_down(0.516)
        self.send_down(0.550)
        self.send_down(0.600)
        self.send_down(0.613)
        self.send_down(0.693)

        self.assertEqual(len(self.routed), 2)

    def test_held_single_release_is_discarded_then_stale_represses(self) -> None:
        self.send_down(0.000)
        for at in (0.500, 0.533, 0.566, 0.599, 0.621, 0.654):
            self.send_down(at)
        self.time.now = 0.6701
        self.time.fire()
        self.send_down(1.554)
        self.time.now = 1.5701
        self.time.fire()

        self.assertEqual([e.event_type for e in self.routed], ["down", "down"])
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 1)

    def test_early_timer_reschedules_without_confirming(self) -> None:
        self.send_down(0.0)
        self.send_down(0.020)
        self.time.now = 0.030
        self.time.fire()

        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.timer_routes), 0)
        self.assertAlmostEqual(self.time.scheduled[-1][0], 0.006)

        self.time.now = 0.0361
        self.time.fire()
        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_exact_window_input_first_then_timer_releases(self) -> None:
        # If input wins at the boundary, it consumes the pending pair before
        # the timer runs. The timer must then be harmless.
        self.send_down(0.0)
        self.send_down(0.020)
        boundary = 0.020 + 0.016
        self.send_down(boundary)
        self.time.now = boundary
        self.time.fire()
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_exact_window_timer_first_then_input_releases(self) -> None:
        # If the timer wins at exactly 16 ms, it must wait and let the next
        # event at that same boundary classify the pair as a release.
        self.send_down(0.0)
        self.send_down(0.020)
        boundary = 0.020 + 0.016
        self.time.now = boundary
        self.time.fire()
        self.send_down(boundary)
        self.assertEqual(len(self.released), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_saved_accept_is_used_while_route_is_not_called_again(self) -> None:
        self.next_route = InputRoute(actions=(), accept=False)
        initial = self.send_down(0.0)
        followup = self.send_down(0.020)

        self.assertFalse(initial.accept)
        self.assertFalse(followup.accept)
        self.assertEqual(len(self.routed), 1)

    def test_pause_request_overrides_saved_accept_to_passthrough(self) -> None:
        self.next_route = InputRoute(actions=(), accept=False)
        self.send_down(0.0)
        self.pause_count = 1
        followup = self.send_down(0.020)

        self.assertTrue(followup.accept)
        self.assertEqual(len(self.routed), 1)

    def test_passthrough_without_actions_does_not_route_repeats(self) -> None:
        self.next_route = InputRoute(actions=(), accept=True)
        self.send_down(0.0)
        repeated = self.send_down(0.500)
        self.time.now = 0.5161
        self.time.fire()

        self.assertTrue(repeated.accept)
        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_passthrough_with_actions_does_not_route_repeats(self) -> None:
        self.next_route = InputRoute(actions=(object(),), accept=True)
        self.send_down(0.0)
        repeated = self.send_down(0.500)
        self.time.now = 0.5161
        self.time.fire()

        self.assertTrue(repeated.accept)
        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_real_up_cancels_pending_and_updates_release_state_and_route(self) -> None:
        self.send_down(0.0)
        self.send_down(0.020)
        self.pause_count = 1  # a real up still clears pressed state while paused
        result = self.send_up(0.025, name="henkan")
        self.time.now = 0.040
        self.time.fire()

        self.assertEqual(len(self.released), 1)
        self.assertIs(self.released[0], self.routed[-1])
        self.assertEqual(self.released[0].event_type, "up")
        self.assertEqual(self.released[0].name, "henkan")
        self.assertEqual(self.routed[-1].event_type, "up")
        self.assertEqual(len(result.routes), 1)
        self.assertEqual(len(self.timer_routes), 0)

    def test_clear_invalidates_old_timer_generation(self) -> None:
        self.send_down(0.0)
        self.send_down(0.020)
        old_generation = self.filter.generation
        self.filter.clear()
        self.time.now = 0.100
        self.time.fire()

        self.assertGreater(self.filter.generation, old_generation)
        self.assertEqual(len(self.timer_routes), 0)
        self.assertEqual(len(self.routed), 1)
        self.assertEqual(len(self.released), 0)

    def test_non_make_only_scan_codes_return_none(self) -> None:
        for scan_code in (40, 41, 112, 240, 243):
            with self.subTest(scan_code=scan_code):
                self.assertIsNone(self.send_down(0.0, scan_code=scan_code))
        self.assertEqual(self.routed, [])

    def test_domain_scan_code_table_and_conversion(self) -> None:
        self.assertEqual(MAKE_ONLY_SCAN_CODES, frozenset({241, 242}))
        for value in (241, 242, "241", 242.9):
            with self.subTest(value=value):
                self.assertTrue(is_make_only_scan_code(value))
        for value in (None, "muhenkan", object()):
            with self.subTest(value=value):
                self.assertFalse(is_make_only_scan_code(value))

    def test_two_scan_codes_keep_independent_state(self) -> None:
        self.send_down(0.000, scan_code=241)
        self.send_down(0.010, scan_code=242)
        self.send_down(0.045, scan_code=241)
        self.send_down(0.055, scan_code=242)
        self.send_down(0.056, scan_code=241)
        self.send_down(0.066, scan_code=242)

        self.assertEqual([event.scan_code for event in self.routed], [241, 242])
        self.assertEqual(
            [event.scan_code for event in self.released], [241, 242]
        )

    def test_missing_name_is_preserved_on_synthetic_release(self) -> None:
        self.send_down(0.0, name=None)
        self.send_down(0.020, name=None)
        self.send_down(0.031, name=None)

        self.assertEqual(self.released, [SyntheticKeyEvent("up", 241, None)])

    def test_stale_repress_remembers_new_accept_only(self) -> None:
        self.next_route = InputRoute(actions=(object(),), accept=False)
        self.send_down(0.0)
        self.send_down(1.000)  # old press: mark pending as stale
        self.next_route = InputRoute(actions=(), accept=True)
        self.time.now = 1.0161
        self.time.fire()  # stale release then fresh routed press

        self.time.now = 1.050
        followup = self.filter.handle(
            SimpleNamespace(event_type="down", scan_code=241, name=None)
        )
        self.time.now = 1.0661
        self.time.fire()

        self.assertTrue(followup.accept)
        self.assertEqual(len(self.routed), 2)
        self.assertEqual(len(self.released), 2)
        self.assertEqual(len(self.timer_routes), 1)  # only the stale re-press

    def test_on_routes_runs_outside_lock_and_can_reenter_filter(self) -> None:
        callback_completed: list[bool] = []

        def reenter(_routes, _generation) -> None:
            self.filter.handle(
                SimpleNamespace(event_type="up", scan_code=242, name=None)
            )
            callback_completed.append(True)

        self.filter = self.make_filter(on_routes=reenter)
        self.send_down(0.0)
        self.send_down(1.000)
        self.time.now = 1.0161
        timer_thread = threading.Thread(target=self.time.fire, daemon=True)
        timer_thread.start()
        timer_thread.join(timeout=1.0)

        self.assertFalse(timer_thread.is_alive())
        self.assertEqual(callback_completed, [True])


if __name__ == "__main__":
    unittest.main()
