from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes
from functools import cache
from typing import Callable

import keyboard
import pyautogui

from keyseq.domain.key_identifiers import resolve_known_scan_code_from_key_name
from keyseq.domain.numpad_keys import (
    is_numpad_key_name,
    is_reserved_numpad_name,
    numpad_key_spec,
)
from keyseq.infrastructure import ime_control


_logger = logging.getLogger(__name__)


_EXTENDED_KEYS = {
    "up": (0x26, 0x48),
    "down": (0x28, 0x50),
    "left": (0x25, 0x4B),
    "right": (0x27, 0x4D),
    "home": (0x24, 0x47),
    "end": (0x23, 0x4F),
    "page up": (0x21, 0x49),
    "page down": (0x22, 0x51),
    "insert": (0x2D, 0x52),
    "delete": (0x2E, 0x53),
    "right ctrl": (0xA3, 0x1D),
    "right alt": (0xA5, 0x38),
    "windows": (0x5B, 0x5B),
    "left windows": (0x5B, 0x5B),
    "right windows": (0x5C, 0x5C),
    "menu": (0x5D, 0x5D),
    "print screen": (0x2C, 0x37),
    "num lock": (0x90, 0x45),
}
_KEYEVENTF_EXTENDEDKEY = 0x0001
_KEYEVENTF_KEYUP = 0x0002
_KEYEVENTF_SCANCODE = 0x0008
_INPUT_KEYBOARD = 1
_SPI_GETKEYBOARDSPEED = 0x000A
_SPI_GETKEYBOARDDELAY = 0x0016
_DEFAULT_REPEAT_DELAY_MS = 500
_DEFAULT_REPEAT_INTERVAL_MS = 33


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


def repeat_delay_ms(value: int) -> int | None:
    """Windows のキーボード待ち設定をミリ秒へ換算する。"""
    if not 0 <= value <= 3:
        return None
    return 250 * (value + 1)


def repeat_interval_ms(value: int) -> int | None:
    """Windows のキーボード間隔設定をミリ秒へ換算する。"""
    if not 0 <= value <= 31:
        return None
    return round(1000 / (2.5 + value * 27.5 / 31))


def _read_keyboard_setting(action: int, value_type) -> int | None:
    try:
        value = value_type()
        succeeded = ctypes.windll.user32.SystemParametersInfoW(
            action, 0, ctypes.byref(value), 0
        )
        return int(value.value) if succeeded else None
    except Exception:
        return None


def keyboard_repeat_timing() -> tuple[int, int]:
    """OS のキーリピート待ち時間と間隔をミリ秒で返す。"""
    if sys.platform != "win32":
        return _DEFAULT_REPEAT_DELAY_MS, _DEFAULT_REPEAT_INTERVAL_MS

    delay_value = _read_keyboard_setting(_SPI_GETKEYBOARDDELAY, wintypes.UINT)
    interval_value = _read_keyboard_setting(_SPI_GETKEYBOARDSPEED, wintypes.DWORD)
    delay = repeat_delay_ms(delay_value) if delay_value is not None else None
    interval = repeat_interval_ms(interval_value) if interval_value is not None else None
    return (
        delay if delay is not None else _DEFAULT_REPEAT_DELAY_MS,
        interval if interval is not None else _DEFAULT_REPEAT_INTERVAL_MS,
    )


def _resolve_extended_key(name: str) -> tuple[int, int] | None:
    try:
        normalized = keyboard.normalize_name(name.strip())
    except Exception:
        return None
    return _EXTENDED_KEYS.get(normalized)


def _send_extended_event(vk: int, scan: int, key_up: bool) -> None:
    flags = _KEYEVENTF_EXTENDEDKEY | (_KEYEVENTF_KEYUP if key_up else 0)
    try:
        listener = keyboard._listener
        previous_replaying = listener.is_replaying
    except AttributeError:
        ctypes.windll.user32.keybd_event(vk, scan, flags, 0)
        return

    listener.is_replaying = True
    try:
        ctypes.windll.user32.keybd_event(vk, scan, flags, 0)
    finally:
        listener.is_replaying = previous_replaying


@cache
def _send_input_api():
    """専用 user32 インスタンスから SendInput を取得する。"""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send_input = user32.SendInput
    send_input.argtypes = [
        wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int,
    ]
    send_input.restype = wintypes.UINT
    return send_input


def _send_numpad_event(scan: int, extended: bool, key_up: bool) -> None:
    flags = _KEYEVENTF_SCANCODE
    if extended:
        flags |= _KEYEVENTF_EXTENDEDKEY
    if key_up:
        flags |= _KEYEVENTF_KEYUP
    event = _INPUT(
        type=_INPUT_KEYBOARD,
        ki=_KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0),
    )

    def send() -> None:
        if _send_input_api()(1, ctypes.byref(event), ctypes.sizeof(_INPUT)) != 1:
            error_code = ctypes.get_last_error()
            raise OSError(error_code, "SendInput failed")

    try:
        listener = keyboard._listener
        previous_replaying = listener.is_replaying
    except AttributeError:
        send()
        return

    listener.is_replaying = True
    try:
        send()
    finally:
        listener.is_replaying = previous_replaying


class InputGateway:
    def register_global_hook(
        self,
        callback: Callable[[object], bool | None],
        *,
        suppress: bool = False,
    ):
        return keyboard.hook(callback, suppress=suppress)

    def register_key_hook(
        self,
        key: str,
        callback: Callable[[object], None],
        *,
        suppress: bool,
    ):
        # hook_key+suppress を使い、押下(down)のみを上位へ渡す。
        # これにより制御キー（停止/トグル）の抑止を安定させる。
        def _wrapped(event):
            try:
                if getattr(event, "event_type", None) != "down":
                    return
            except Exception:
                pass
            callback(event)

        return keyboard.hook_key(key, _wrapped, suppress=suppress)

    def unregister_hook(self, handle) -> None:
        keyboard.unhook(handle)

    def press_key(self, key: str) -> None:
        numpad = numpad_key_spec(key)
        if numpad is not None:
            _send_numpad_event(*numpad, key_up=False)
            return
        extended = _resolve_extended_key(key)
        if extended is not None:
            _send_extended_event(*extended, key_up=False)
        else:
            keyboard.press(key)

    def release_key(self, key: str) -> None:
        numpad = numpad_key_spec(key)
        if numpad is not None:
            _send_numpad_event(*numpad, key_up=True)
            return
        extended = _resolve_extended_key(key)
        if extended is not None:
            _send_extended_event(*extended, key_up=True)
        else:
            keyboard.release(key)

    def send_hotkey(self, hotkey: str) -> None:
        keys = [key.strip() for key in hotkey.split("+")]
        if not any(
            _resolve_extended_key(key) is not None or numpad_key_spec(key) is not None
            for key in keys
        ):
            keyboard.send(hotkey)
            return

        pressed: list[str] = []
        first_error: BaseException | None = None
        try:
            for key in keys:
                self.press_key(key)
                pressed.append(key)
        except BaseException as exc:
            first_error = exc
        finally:
            for key in reversed(pressed):
                try:
                    self.release_key(key)
                except BaseException as exc:
                    if first_error is None:
                        first_error = exc
        if first_error is not None:
            raise first_error

    def write_text(self, text: str) -> None:
        if not text:
            keyboard.write(text, restore_state_after=False)
            return
        reservation = ime_control.disable_for_text()
        try:
            keyboard.write(text, restore_state_after=False)
        finally:
            ime_control.restore_after_text(reservation, len(text))

    def key_identity(self, key: str) -> tuple[int, bool]:
        numpad = numpad_key_spec(key)
        if numpad is not None:
            return numpad
        extended = _resolve_extended_key(key)
        if extended is not None:
            return extended[1], True

        scan_codes: tuple[int, ...] = ()
        try:
            scan_codes = tuple(keyboard.key_to_scan_codes(key))
        except Exception:
            scan_code = resolve_known_scan_code_from_key_name(str(key or ""))
            if scan_code is None:
                raise
            return scan_code, False

        if scan_codes:
            scan_code = scan_codes[0]
            if (scan_code & 0xFF00) == 0xE000:
                return scan_code & 0xFF, True
            return scan_code, False
        scan_code = resolve_known_scan_code_from_key_name(str(key or ""))
        if scan_code is None:
            raise ValueError(f"Unknown key name: {key!r}")
        return scan_code, False

    def restore_ime_now(self) -> None:
        try:
            ime_control.restore_ime_now()
        except Exception:
            _logger.exception("Failed to restore destination IME during shutdown")

    def validate_key_name(self, key_name: str) -> None:
        if is_numpad_key_name(key_name):
            return
        if is_reserved_numpad_name(key_name):
            raise ValueError(
                "テンキーのキー名は num 0〜num 9 / num add / num subtract / "
                "num multiply / num divide / num decimal / num enter のいずれかで指定してください。"
            )
        try:
            keyboard.key_to_scan_codes(key_name)
        except Exception:
            scan_code = resolve_known_scan_code_from_key_name(str(key_name or ""))
            if scan_code is None:
                raise

    def click_mouse(self, x: int, y: int, button: str, clicks: int) -> None:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)

    def mouse_down(
        self, button: str, x: int | None = None, y: int | None = None
    ) -> None:
        self._send_mouse_button(button, x, y, is_down=True)

    def mouse_up(
        self, button: str, x: int | None = None, y: int | None = None
    ) -> None:
        self._send_mouse_button(button, x, y, is_down=False)

    @staticmethod
    def _send_mouse_button(
        button: str, x: int | None, y: int | None, *, is_down: bool
    ) -> None:
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            if is_down:
                pyautogui.mouseDown(button=button)
            else:
                pyautogui.mouseUp(button=button)
        finally:
            pyautogui.FAILSAFE = failsafe

    def drag_mouse(
        self, x: int, y: int, to_x: int, to_y: int, button: str, duration_sec: float
    ) -> None:
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            pyautogui.moveTo(x, y)
            try:
                pyautogui.mouseDown(button=button)
                pyautogui.moveTo(to_x, to_y, duration=duration_sec)
            finally:
                pyautogui.mouseUp(button=button)
        finally:
            pyautogui.FAILSAFE = failsafe
