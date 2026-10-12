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
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
MONITORINFOF_PRIMARY = 0x00000001
MAPVK_VK_TO_VSC = 0
MAPVK_VK_TO_CHAR = 2

_T = TypeVar("_T")


@cache
def _user32(name: str, argtypes: tuple, restype):
    """Return a typed function from a dedicated user32 instance."""
    function = getattr(ctypes.WinDLL("user32", use_last_error=True), name)
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
    "monitor_rects": "モニター領域の列挙に失敗しました",
    "scan_code": "仮想キーコードからスキャンコードへの変換に失敗しました",
    "vk_char": "仮想キーコードから文字への変換に失敗しました",
    "click_through_overlay": "クリック透過ウィンドウの設定に失敗しました",
}


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def list_monitor_rects() -> list[tuple[tuple[int, int, int, int], bool]]:
    """Return monitor bounds in enumeration order with primary flags."""
    def enumerate_monitors() -> list[tuple[tuple[int, int, int, int], bool]]:
        monitor_rects: list[tuple[tuple[int, int, int, int], bool]] = []
        failed = False
        callback_type = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
            wintypes.BOOL,
            wintypes.HANDLE,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_ssize_t,
        )

        def collect(monitor, _dc, _rect, _data):
            nonlocal failed
            try:
                info = _MONITORINFO()
                info.cbSize = ctypes.sizeof(_MONITORINFO)
                get_monitor_info = _user32(
                    "GetMonitorInfoW",
                    (wintypes.HANDLE, ctypes.POINTER(_MONITORINFO)),
                    wintypes.BOOL,
                )
                if not get_monitor_info(monitor, ctypes.byref(info)):
                    failed = True
                    return False
                rect = info.rcMonitor
                monitor_rects.append(
                    (
                        (rect.left, rect.top, rect.right, rect.bottom),
                        bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    )
                )
                return True
            except Exception:
                failed = True
                _log_once("monitor_rects", _ERROR_MESSAGES["monitor_rects"])
                return False

        callback = callback_type(collect)
        enum_display_monitors = _user32(
            "EnumDisplayMonitors",
            (
                wintypes.HDC,
                ctypes.POINTER(wintypes.RECT),
                callback_type,
                ctypes.c_ssize_t,
            ),
            wintypes.BOOL,
        )
        if not enum_display_monitors(None, None, callback, 0) or failed:
            return []
        return monitor_rects

    return _guarded("monitor_rects", [], enumerate_monitors)


def vk_to_scan_code(vk: int) -> int | None:
    """Convert a Win32 virtual-key code to its scan code."""
    def convert() -> int | None:
        map_virtual_key = _user32(
            "MapVirtualKeyW", (wintypes.UINT, wintypes.UINT), wintypes.UINT
        )
        scan_code = int(map_virtual_key(int(vk), MAPVK_VK_TO_VSC))
        return scan_code or None

    return _guarded("scan_code", None, convert)


def vk_to_char(vk: int) -> str:
    """Return the unshifted character of a Win32 virtual-key code, or ""."""
    def convert() -> str:
        map_virtual_key = _user32(
            "MapVirtualKeyW", (wintypes.UINT, wintypes.UINT), wintypes.UINT
        )
        # 最上位ビットはデッドキーの印なので落とす。
        code = int(map_virtual_key(int(vk), MAPVK_VK_TO_CHAR)) & 0x7FFFFFFF
        return chr(code) if 0x20 < code < 0x110000 else ""

    return _guarded("vk_char", "", convert)


def make_click_through_overlay(widget_id: int) -> bool:
    """Make a Tk child window click-through and non-activating."""
    def update_extended_style() -> bool:
        get_parent = _user32("GetParent", (wintypes.HWND,), wintypes.HWND)
        hwnd = get_parent(widget_id)
        if not hwnd:
            return False

        long_ptr = ctypes.c_ssize_t
        get_window_long = _user32(
            "GetWindowLongPtrW",
            (wintypes.HWND, ctypes.c_int),
            long_ptr,
        )
        set_window_long = _user32(
            "SetWindowLongPtrW",
            (wintypes.HWND, ctypes.c_int, long_ptr),
            long_ptr,
        )
        ctypes.set_last_error(0)
        style = get_window_long(hwnd, GWL_EXSTYLE)
        if not style and ctypes.get_last_error():
            return False

        new_style = style | (
            WS_EX_LAYERED
            | WS_EX_TRANSPARENT
            | WS_EX_NOACTIVATE
            | WS_EX_TOOLWINDOW
        )
        ctypes.set_last_error(0)
        previous_style = set_window_long(hwnd, GWL_EXSTYLE, new_style)
        return bool(previous_style or not ctypes.get_last_error())

    return _guarded("click_through_overlay", False, update_extended_style)


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
