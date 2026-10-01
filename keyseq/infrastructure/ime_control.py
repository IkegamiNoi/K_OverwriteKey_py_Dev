from __future__ import annotations

import ctypes
import logging
import sys
import threading
from dataclasses import dataclass
from typing import Callable


IME_RESTORE_BASE_DELAY_MS = 200
IME_RESTORE_PER_CHARACTER_DELAY_MS = 40
WM_IME_CONTROL = 0x0283
IMC_GETOPENSTATUS = 0x0005
IMC_SETOPENSTATUS = 0x0006

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
        self._user32.SendMessageW.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_size_t, ctypes.c_ssize_t
        ]
        self._user32.SendMessageW.restype = ctypes.c_ssize_t

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
        return int(self._user32.SendMessageW(
            ime_window, WM_IME_CONTROL, IMC_GETOPENSTATUS, 0
        ))

    def set_open_status(self, ime_window: int, is_open: bool) -> None:
        self._user32.SendMessageW(
            ime_window, WM_IME_CONTROL, IMC_SETOPENSTATUS, int(is_open)
        )


@dataclass(frozen=True, slots=True)
class ImeReservation:
    ime_window: int
    generation: int


@dataclass(slots=True)
class _ImeState:
    generation: int
    timer: threading.Timer | None = None


class ImeController:
    def __init__(
        self,
        api: _Win32ImeApi | None,
        *,
        timer_factory: Callable[[float, Callable[[], None]], threading.Timer] = threading.Timer,
    ) -> None:
        self._api = api
        self._timer_factory = timer_factory
        self._lock = threading.Lock()
        self._states: dict[int, _ImeState] = {}

    def before_send(self) -> ImeReservation | None:
        if self._api is None:
            return None
        try:
            ime_window = self._api.get_ime_window()
            if not ime_window:
                return None
            with self._lock:
                state = self._states.get(ime_window)
                if state is not None:
                    self._cancel_timer(state)
                    state.generation += 1
                    return ImeReservation(ime_window, state.generation)
                if not self._api.get_open_status(ime_window):
                    return None
                self._api.set_open_status(ime_window, False)
                self._states[ime_window] = _ImeState(generation=1)
                return ImeReservation(ime_window, 1)
        except Exception:
            _logger.exception("Failed to turn off the destination IME")
            return None

    def after_send(self, reservation: ImeReservation | None, character_count: int) -> None:
        if reservation is None:
            return
        delay = (
            IME_RESTORE_BASE_DELAY_MS
            + IME_RESTORE_PER_CHARACTER_DELAY_MS * character_count
        ) / 1000
        with self._lock:
            state = self._states.get(reservation.ime_window)
            if state is None or state.generation != reservation.generation:
                return
            self._cancel_timer(state)
            if character_count <= 0:
                self._restore_locked(reservation.ime_window, reservation.generation)
                return
            try:
                timer = self._timer_factory(
                    delay,
                    lambda: self._restore(
                        reservation.ime_window, reservation.generation
                    ),
                )
                timer.daemon = False
                state.timer = timer
                timer.start()
            except Exception:
                _logger.exception("Failed to schedule destination IME restoration")
                self._restore_locked(reservation.ime_window, reservation.generation)

    def _restore(self, ime_window: int, generation: int) -> None:
        with self._lock:
            self._restore_locked(ime_window, generation)

    def _restore_locked(self, ime_window: int, generation: int) -> None:
        state = self._states.get(ime_window)
        if state is None or state.generation != generation:
            return
        try:
            if self._api is not None:
                self._api.set_open_status(ime_window, True)
        except Exception:
            _logger.exception("Failed to restore the destination IME")
        finally:
            self._states.pop(ime_window, None)

    @staticmethod
    def _cancel_timer(state: _ImeState) -> None:
        if state.timer is not None:
            state.timer.cancel()
            state.timer = None


def _create_default_controller() -> ImeController:
    try:
        api = _Win32ImeApi()
    except Exception:
        _logger.exception("Win32 IME APIs are unavailable")
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
