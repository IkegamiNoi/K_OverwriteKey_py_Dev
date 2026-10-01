from __future__ import annotations

import ctypes
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable


IME_RESTORE_BASE_DELAY_MS = 200
IME_RESTORE_PER_CHARACTER_DELAY_MS = 40
WM_IME_CONTROL = 0x0283
IMC_GETOPENSTATUS = 0x0005
IMC_SETOPENSTATUS = 0x0006
SMTO_ABORTIFHUNG = 0x0002
IME_MESSAGE_TIMEOUT_MS = 200

_logger = logging.getLogger(__name__)


class _GuiThreadInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("hwndActive", ctypes.c_void_p),
        ("hwndFocus", ctypes.c_void_p),
        ("hwndCapture", ctypes.c_void_p),
        ("hwndMenuOwner", ctypes.c_void_p),
        ("hwndMoveSize", ctypes.c_void_p),
        ("hwndCaret", ctypes.c_void_p),
        ("rcCaret", ctypes.c_long * 4),
    ]


class _Win32ImeApi:
    def __init__(self) -> None:
        win_dll = getattr(ctypes, "WinDLL", None)
        if not sys.platform.startswith("win") or win_dll is None:
            raise OSError("Win32 IME APIs are unavailable")
        self._user32 = win_dll("user32", use_last_error=True)
        self._imm32 = win_dll("imm32", use_last_error=True)
        self._user32.GetForegroundWindow.restype = ctypes.c_void_p
        self._user32.GetWindowThreadProcessId.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)
        ]
        self._user32.GetWindowThreadProcessId.restype = ctypes.c_uint32
        self._user32.GetGUIThreadInfo.argtypes = [
            ctypes.c_uint32, ctypes.POINTER(_GuiThreadInfo)
        ]
        self._user32.GetGUIThreadInfo.restype = ctypes.c_int
        self._imm32.ImmGetDefaultIMEWnd.argtypes = [ctypes.c_void_p]
        self._imm32.ImmGetDefaultIMEWnd.restype = ctypes.c_void_p
        self._user32.SendMessageTimeoutW.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_size_t, ctypes.c_ssize_t,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_size_t),
        ]
        self._user32.SendMessageTimeoutW.restype = ctypes.c_void_p

    def get_ime_window(self) -> int | None:
        foreground = self._user32.GetForegroundWindow()
        if not foreground:
            return None
        process_id = ctypes.c_uint32()
        thread_id = self._user32.GetWindowThreadProcessId(
            foreground, ctypes.byref(process_id)
        )
        info = _GuiThreadInfo()
        info.cbSize = ctypes.sizeof(info)
        focus = None
        if thread_id and self._user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
            focus = info.hwndFocus
        target = focus or foreground
        ime_window = self._imm32.ImmGetDefaultIMEWnd(target)
        return int(ime_window) if ime_window else None

    def get_open_status(self, ime_window: int) -> int:
        return self._send(ime_window, IMC_GETOPENSTATUS, 0)

    def set_open_status(self, ime_window: int, is_open: bool) -> None:
        self._send(ime_window, IMC_SETOPENSTATUS, int(is_open))

    def _send(self, ime_window: int, command: int, value: int) -> int:
        result = ctypes.c_size_t()
        success = self._user32.SendMessageTimeoutW(
            ime_window, WM_IME_CONTROL, command, value,
            SMTO_ABORTIFHUNG, IME_MESSAGE_TIMEOUT_MS, ctypes.byref(result),
        )
        if not success:
            raise OSError(f"IME message {command} failed or timed out")
        return int(result.value)


@dataclass(frozen=True, slots=True)
class ImeReservation:
    ime_window: int
    generation: int


@dataclass(slots=True)
class _ImeState:
    generation: int
    timer: threading.Timer | None = None
    deadline: float = 0.0
    busy: bool = False
    owned: bool = False
    active: set[int] = field(default_factory=set)


class ImeController:
    def __init__(
        self,
        api: _Win32ImeApi | None,
        *,
        timer_factory: Callable[[float, Callable[[], None]], threading.Timer] = threading.Timer,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._api = api
        self._timer_factory = timer_factory
        self._clock = clock
        self._lock = threading.Lock()
        self._changed = threading.Condition(self._lock)
        self._states: dict[int, _ImeState] = {}
        self._next_generation = 0
        self._closed = False

    def before_send(self) -> ImeReservation | None:
        if self._api is None:
            return None
        try:
            ime_window = self._api.get_ime_window()
            if not ime_window:
                return None
        except Exception:
            _logger.exception("Failed to locate the destination IME")
            return None
        while True:
            with self._changed:
                if self._closed:
                    return None
                state = self._states.get(ime_window)
                if state is None:
                    state = _ImeState(generation=0)
                    self._states[ime_window] = state
                self._next_generation += 1
                state.generation = self._next_generation
                generation = state.generation
                self._cancel_timer(state)
                while state.busy:
                    self._changed.wait()
                    if self._closed:
                        return None
                state.busy = True
            result = self._turn_off(ime_window, state, generation)
            with self._lock:
                current = (not self._closed and self._states.get(ime_window) is state
                           and state.generation == generation)
                if result == "ready" and current:
                    state.active.add(generation)
            if result == "stale" or (result == "ready" and not current):
                continue
            return ImeReservation(ime_window, generation) if result == "ready" else None

    def _current(self, ime_window: int, state: _ImeState, generation: int) -> bool:
        with self._lock:
            return (not self._closed and self._states.get(ime_window) is state
                    and state.generation == generation)

    def _finish(self, ime_window: int, state: _ImeState, generation: int,
                *, discard: bool = False) -> bool:
        with self._changed:
            current = (not self._closed and self._states.get(ime_window) is state
                       and state.generation == generation)
            if current and discard:
                self._states.pop(ime_window)
            state.busy = False
            self._changed.notify_all()
            return current

    def _turn_off(self, window: int, state: _ImeState, generation: int) -> str:
        try:
            is_open = self._api.get_open_status(window)
            if not self._current(window, state, generation):
                return "stale"
            if is_open:
                self._api.set_open_status(window, False)
                state.owned = True
                if not self._current(window, state, generation):
                    return "stale"
            elif not state.owned:
                return "skip"
            return "ready"
        except Exception:
            _logger.exception("Failed to turn off the destination IME")
            return "ready" if state.owned else "skip"
        finally:
            # A superseding sender retries only after this operation has finished.
            self._finish(window, state, generation, discard=not state.owned)

    def after_send(self, reservation: ImeReservation | None, character_count: int) -> None:
        if reservation is None:
            return
        delay = (
            IME_RESTORE_BASE_DELAY_MS
            + IME_RESTORE_PER_CHARACTER_DELAY_MS * character_count
        ) / 1000
        restore_now = character_count <= 0
        with self._changed:
            state = self._states.get(reservation.ime_window)
            if state is None or reservation.generation not in state.active:
                return
            state.active.remove(reservation.generation)
            self._changed.notify_all()
            if self._closed:
                return
            state.deadline = max(state.deadline, self._clock() + delay)
            if state.active:
                return
            self._cancel_timer(state)
            generation = state.generation
            if not restore_now:
                try:
                    timer = self._timer_factory(
                        max(0.0, state.deadline - self._clock()),
                        lambda: self._restore(reservation.ime_window, generation),
                    )
                    timer.daemon = False
                    state.timer = timer
                    timer.start()
                except Exception:
                    _logger.exception("Failed to schedule destination IME restoration")
                    restore_now = True
        if restore_now:
            self._restore(reservation.ime_window, generation)

    def _restore(self, ime_window: int, generation: int) -> None:
        with self._changed:
            state = self._states.get(ime_window)
            if state is None or state.generation != generation or state.active:
                return
            while state.busy:
                self._changed.wait()
                if (self._states.get(ime_window) is not state
                        or state.generation != generation or state.active):
                    return
            state.busy = True
        try:
            is_open = self._api.get_open_status(ime_window)
            if self._current(ime_window, state, generation) and not is_open:
                self._api.set_open_status(ime_window, True)
                self._current(ime_window, state, generation)
        except Exception:
            _logger.exception("Failed to restore the destination IME")
        finally:
            self._finish(ime_window, state, generation, discard=True)

    def restore_all_now(self) -> None:
        with self._changed:
            self._closed = True
            reservations = []
            for window, state in self._states.items():
                self._cancel_timer(state)
                reservations.append((window, state))
        for window, state in reservations:
            with self._changed:
                while state.busy or state.active:
                    self._changed.wait()
                if self._states.get(window) is not state:
                    continue
                if not state.owned:
                    self._states.pop(window)
                    continue
                state.busy = True
                generation = state.generation
            try:
                is_open = self._api.get_open_status(window)
                with self._lock:
                    current = (self._states.get(window) is state
                               and state.generation == generation)
                if current and not is_open:
                    self._api.set_open_status(window, True)
                    with self._lock:
                        current = (self._states.get(window) is state
                                   and state.generation == generation)
                    if not current:
                        continue
            except Exception:
                _logger.exception("Failed to restore the destination IME at shutdown")
            finally:
                with self._changed:
                    self._states.pop(window, None)
                    state.busy = False
                    self._changed.notify_all()

    @staticmethod
    def _cancel_timer(state: _ImeState) -> None:
        if state.timer is not None:
            state.timer.cancel()
            state.timer = None


def _create_default_controller() -> ImeController:
    try:
        api = _Win32ImeApi()
    except OSError as exc:
        _logger.warning("Win32 IME APIs are unavailable: %s", exc)
        api = None
    except Exception:
        _logger.exception("Failed to initialize Win32 IME APIs")
        api = None
    return ImeController(api)


_controller: ImeController | None = None
_controller_lock = threading.Lock()


def _get_controller() -> ImeController:
    global _controller
    with _controller_lock:
        if _controller is None:
            _controller = _create_default_controller()
        return _controller


def disable_for_text() -> ImeReservation | None:
    return _get_controller().before_send()


def restore_after_text(
    reservation: ImeReservation | None, character_count: int
) -> None:
    _get_controller().after_send(reservation, character_count)


def restore_ime_now() -> None:
    _get_controller().restore_all_now()
