from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from keyseq.domain.key_hold import is_modifier_key
from keyseq.domain.numpad_keys import is_numpad_key_name


HookCallback = Callable[[object], bool]


class KeyCaptureHook:
    """Temporarily suppresses layout-mapped keys while a capture is active."""

    def __init__(
        self,
        register_hook: Callable[[HookCallback], object],
        unregister_hook: Callable[[object], None],
        resolve_name: Callable[[object], str],
        numpad_name: Callable[[object, bool], str | None],
        is_foreground: Callable[[], bool],
        after: Callable[[int, Callable[[], None]], object],
        repeat_delay_ms: Callable[[], int],
        deliver: Callable[[str, int], None],
        get_generation: Callable[[], int],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._register_hook = register_hook
        self._unregister_hook = unregister_hook
        self._resolve_name = resolve_name
        self._numpad_name = numpad_name
        self._is_foreground = is_foreground
        self._after = after
        self._repeat_delay_ms = repeat_delay_ms
        self._deliver = deliver
        self._get_generation = get_generation
        self._clock = clock
        self._logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._handle: object | None = None
        self._owners = 0
        self._pressed: dict[object, float] = {}
        self._idle_token = 0
        self._idle_started: float | None = None

    def activate(self) -> None:
        with self._lock:
            self._owners += 1
            self._idle_token += 1
            self._idle_started = None
            if self._handle is None:
                self._handle = self._register_hook(self._callback)

    def deactivate(self) -> None:
        with self._lock:
            if self._owners == 0:
                return
            self._owners -= 1
            if self._owners:
                return
            self._idle_started = self._clock()
            self._idle_token += 1
            token = self._idle_token
            if not self._has_pressed_locked():
                self._unregister_locked()
                return
        self._schedule_idle_check(token)

    def shutdown(self) -> None:
        with self._lock:
            self._owners = 0
            self._idle_token += 1
            self._idle_started = None
            self._pressed.clear()
            self._unregister_locked()

    def _unregister_locked(self) -> None:
        handle = self._handle
        if handle is None:
            return
        self._handle = None
        self._unregister_hook(handle)

    def _timeout_seconds(self) -> float:
        return (self._repeat_delay_ms() + 200) / 1000

    def _has_pressed_locked(self) -> bool:
        cutoff = self._clock() - self._timeout_seconds()
        stale = [scan_code for scan_code, pressed_at in self._pressed.items() if pressed_at < cutoff]
        for scan_code in stale:
            del self._pressed[scan_code]
        return bool(self._pressed)

    def _schedule_idle_check(self, token: int) -> None:
        try:
            self._after(100, lambda: self._check_idle(token))
        except Exception:
            self._logger.exception("Could not schedule capture hook idle check")

    def _check_idle(self, token: int) -> None:
        with self._lock:
            if token != self._idle_token or self._owners:
                return
            started = self._idle_started
            if started is None:
                return
            if self._clock() - started >= 5 or not self._has_pressed_locked():
                self._unregister_locked()
                self._idle_started = None
                return
        self._schedule_idle_check(token)

    def _callback(self, event: object) -> bool:
        try:
            return self._handle_event(event)
        except Exception:
            self._logger.exception("Capture hook callback failed")
            return True

    def _handle_event(self, event: object) -> bool:
        event_type = event.event_type
        if event_type not in ("down", "up"):
            return True
        generation = self._get_generation()
        scan_code = event.scan_code
        name = self._target_name(scan_code, event.is_keypad)
        if name is None:
            return True
        now = self._clock()
        with self._lock:
            if self._owners == 0:
                self._has_pressed_locked()
                if scan_code not in self._pressed:
                    return True
                if event_type == "down":
                    self._pressed[scan_code] = now
                return False
            is_new = scan_code not in self._pressed
            if not is_new:
                is_new = now - self._pressed[scan_code] > self._timeout_seconds()
            if event_type == "down":
                self._pressed[scan_code] = now
            should_deliver = event_type == "down" and is_new
        if should_deliver:
            self._queue_delivery(name, generation)
        return False

    def _target_name(self, scan_code: object, is_keypad: bool) -> str | None:
        if not self._is_foreground():
            return None
        if self._numpad_name(scan_code, is_keypad):
            return None
        name = self._resolve_name(scan_code)
        if (
            not name
            or name.strip().lower() == "esc"
            or is_modifier_key(name)
            or is_numpad_key_name(name)
        ):
            return None
        return name

    def _queue_delivery(self, name: str, generation: int) -> None:
        try:
            self._after(0, lambda: self._deliver(name, generation))
        except Exception:
            self._logger.exception("Could not queue captured key")
