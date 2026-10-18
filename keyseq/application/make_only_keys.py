"""押下だけのキーを、押下・リピート・離しに組み直す。"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from keyseq.application.input_router import InputRoute
from keyseq.domain.make_only_keys import is_make_only_scan_code


PAIR_WINDOW_S = 0.016


@dataclass(frozen=True)
class SyntheticKeyEvent:
    event_type: str
    scan_code: int
    name: str | None
    is_keypad: bool = False


@dataclass(frozen=True)
class MakeOnlyResult:
    accept: bool
    routes: tuple[InputRoute, ...]
    generation: int


@dataclass
class _KeyState:
    pressed: bool = False
    accept: bool = True
    has_actions: bool = False
    last_down_at: float = 0.0
    pending_at: float | None = None
    stale: bool = False
    released_at: float | None = None
    released_accept: bool = True
    name: str | None = None


class MakeOnlyKeyFilter:
    def __init__(
        self, *, route: Callable[[object], InputRoute],
        release_state: Callable[[object], None], clock: Callable[[], float],
        schedule: Callable[[float, Callable[[], None]], None],
        get_hook_pause_count: Callable[[], int],
        get_repeat_delay_ms: Callable[[], int],
        on_routes: Callable[[tuple[InputRoute, ...], int], None],
    ) -> None:
        self._route = route
        self._release_state = release_state
        self._clock = clock
        self._schedule = schedule
        self._get_hook_pause_count = get_hook_pause_count
        self._get_repeat_delay_ms = get_repeat_delay_ms
        self._on_routes = on_routes
        self._lock = threading.Lock()
        self._states: dict[int, _KeyState] = {}
        self._generation = 0

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    def clear(self) -> None:
        with self._lock:
            self._states.clear()
            self._generation += 1

    def handle(self, event: object) -> MakeOnlyResult | None:
        scan_code = getattr(event, "scan_code", None)
        if not is_make_only_scan_code(scan_code):
            return None
        event_type = getattr(event, "event_type", None)
        if event_type not in ("down", "up"):
            return None
        scan_code = int(scan_code)
        with self._lock:
            now = self._clock()
            state = self._states.setdefault(scan_code, _KeyState())
            if event_type == "up":
                state.pending_at = None
                state.pressed = False
                self._release_state(event)
                route = self._route(event)
                return MakeOnlyResult(route.accept, (route,), self._generation)
            return self._handle_down(event, scan_code, state, now)

    def _handle_down(
        self, event: object, scan_code: int, state: _KeyState, now: float,
    ) -> MakeOnlyResult:
        if not state.pressed:
            if state.released_at is not None and now <= state.released_at + PAIR_WINDOW_S:
                return self._result(state.released_accept)
            route = self._route(event)
            self._remember_press(state, route)
            state.last_down_at = now
            return MakeOnlyResult(route.accept, (route,), self._generation)

        routes: tuple[InputRoute, ...] = ()
        if state.pending_at is not None:
            if now <= state.pending_at + PAIR_WINDOW_S:
                state.pending_at = None
                self._release_state(SyntheticKeyEvent("up", scan_code, getattr(event, "name", None)))
                state.pressed = False
                state.released_at = now
                state.released_accept = state.accept
                return self._result(state.accept)
            routes = self._confirm_pending(scan_code, state)
        self._start_pending(event, scan_code, state, now)
        return self._result(state.accept, routes)

    def _result(
        self, accept: bool, routes: tuple[InputRoute, ...] = (),
    ) -> MakeOnlyResult:
        return MakeOnlyResult(
            True if self._get_hook_pause_count() > 0 else accept,
            routes, self._generation,
        )

    @staticmethod
    def _remember_press(state: _KeyState, route: InputRoute) -> None:
        state.pressed = True
        state.accept = route.accept
        state.has_actions = bool(route.actions)

    def _start_pending(
        self, event: object, scan_code: int, state: _KeyState, now: float,
    ) -> None:
        stale_after = self._get_repeat_delay_ms() / 1000 + 0.3
        state.stale = now > state.last_down_at + stale_after
        state.pending_at = now
        state.name = getattr(event, "name", None)
        state.last_down_at = now
        generation = self._generation
        self._schedule(
            PAIR_WINDOW_S, lambda: self._expire(scan_code, now, generation),
        )

    def _confirm_pending(self, scan_code: int, state: _KeyState) -> tuple[InputRoute, ...]:
        routes: tuple[InputRoute, ...] = ()
        if state.stale:
            self._release_state(SyntheticKeyEvent("up", scan_code, state.name))
            route = self._route(SyntheticKeyEvent("down", scan_code, state.name))
            self._remember_press(state, route)
            routes = (route,)
        elif state.has_actions:
            routes = (self._route(SyntheticKeyEvent("down", scan_code, state.name)),)
        state.pending_at = None
        return routes

    def _expire(self, scan_code: int, pending_at: float, generation: int) -> None:
        with self._lock:
            if generation != self._generation:
                return
            state = self._states.get(scan_code)
            if state is None or state.pending_at != pending_at:
                return
            now = self._clock()
            # 差の丸めで「16 ms ちょうど」を超過扱いしないよう期限と比較する。
            deadline = pending_at + PAIR_WINDOW_S
            if now <= deadline:
                self._schedule(
                    deadline - now,
                    lambda: self._expire(scan_code, pending_at, generation),
                )
                return
            routes = self._confirm_pending(scan_code, state)
        if routes:
            self._on_routes(routes, generation)
