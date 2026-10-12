"""Win32 window and mouse state queries."""

from __future__ import annotations

import ctypes
import logging
import os
import sys
from ctypes import wintypes
from functools import cache
from typing import Callable, TypeVar


_logger = logging.getLogger(__name__)
_logged_errors: set[str] = set()

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
_KEY_DOWN = 0x8000

_T = TypeVar("_T")


@cache
def _user32(name: str, argtypes: tuple, restype):
    """Return a typed function from a dedicated user32 instance."""
    function = getattr(ctypes.WinDLL("user32"), name)
    function.argtypes = list(argtypes)
    function.restype = restype
    return function


def _log_once(key: str, message: str) -> None:
    if key not in _logged_errors:
        _logger.exception(message)
        _logged_errors.add(key)


def _guarded(name: str, default: _T, call: Callable[[], _T]) -> _T:
    if sys.platform != "win32":
        return default
    try:
        return call()
    except Exception:
        _log_once(name, _ERROR_MESSAGES[name])
        return default


_ERROR_MESSAGES = {
    "foreground": "前面ウィンドウのプロセス判定に失敗しました",
    "foreground_window": "前面ウィンドウ HWND の取得に失敗しました",
    "place_window_below": "ウィンドウ位置の変更に失敗しました",
    "mouse_button": "マウスボタン状態の取得に失敗しました",
}


def _foreground_process_id(foreground) -> int:
    get_process_id = _user32(
        "GetWindowThreadProcessId",
        (wintypes.HWND, ctypes.POINTER(wintypes.DWORD)),
        wintypes.DWORD,
    )
    process_id = wintypes.DWORD()
    get_process_id(foreground, ctypes.byref(process_id))
    return process_id.value


def is_own_process_foreground() -> bool:
    """Return whether the foreground window belongs to this process."""
    def check() -> bool:
        foreground = _user32("GetForegroundWindow", (), wintypes.HWND)()
        if foreground is None or not foreground:
            return True
        process_id = _foreground_process_id(foreground)
        return bool(process_id and process_id == os.getpid())

    return _guarded("foreground", False, check)


def foreground_own_window() -> int | None:
    """Return this process's foreground HWND, if one is available."""
    def check() -> int | None:
        foreground = _user32("GetForegroundWindow", (), wintypes.HWND)()
        if foreground is None or not foreground:
            return None
        process_id = _foreground_process_id(foreground)
        if not process_id or process_id != os.getpid():
            return None
        return int(foreground)

    return _guarded("foreground_window", None, check)


def place_window_below(hwnd: int, above_hwnd: int) -> bool:
    """Place hwnd immediately below above_hwnd without moving or activating it."""
    def place() -> bool:
        set_window_pos = _user32(
            "SetWindowPos",
            (
                wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                ctypes.c_int, ctypes.c_int, ctypes.c_uint,
            ),
            wintypes.BOOL,
        )
        flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
        return bool(set_window_pos(hwnd, above_hwnd, 0, 0, 0, 0, flags))

    return _guarded("place_window_below", False, place)


def is_mouse_button_down() -> bool:
    """Return whether either physical mouse button is held down."""
    def check() -> bool:
        get_async_key_state = _user32(
            "GetAsyncKeyState", (ctypes.c_int,), ctypes.c_short
        )
        return any(
            get_async_key_state(button) & _KEY_DOWN
            for button in (VK_LBUTTON, VK_RBUTTON)
        )

    return _guarded("mouse_button", False, check)
