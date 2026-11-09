from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable, Sequence

import keyboard

from keyseq.domain.numpad_keys import numpad_key_spec
from keyseq.infrastructure.os_backend.contracts import KeySend, ResolveLayoutScanCode
from .send_input import _INPUT, _INPUT_KEYBOARD, _KEYBDINPUT, _send_input_api


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
_SPI_GETKEYBOARDSPEED = 0x000A
_SPI_GETKEYBOARDDELAY = 0x0016
_DEFAULT_REPEAT_DELAY_MS = 500
_DEFAULT_REPEAT_INTERVAL_MS = 33


def _needs_shift(key: str) -> bool:
    try:
        name = keyboard.normalize_name(key)
        _scan_code, modifiers = next(iter(keyboard._os_keyboard.map_name(name)))
        return tuple(modifiers) == ("shift",)
    except Exception:
        return False


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


class WindowsKeyboardBackend:
    def register_global_hook(
        self,
        callback: Callable[[object], bool | None],
        *,
        suppress: bool = False,
    ) -> object:
        return keyboard.hook(callback, suppress=suppress)

    def register_key_hook(
        self,
        key: str,
        callback: Callable[[object], None],
        *,
        suppress: bool,
    ) -> object:
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

    def unregister_hook(self, handle: object) -> None:
        keyboard.unhook(handle)

    def resolve_send(
        self, key: str, resolve_layout_scan_code: ResolveLayoutScanCode
    ) -> KeySend:
        numpad = numpad_key_spec(key)
        if numpad is not None:
            return KeySend("numpad", (numpad[0], int(numpad[1])), key)
        extended = _resolve_extended_key(key)
        if extended is not None:
            return KeySend("extended", extended, key)
        try:
            scan_codes = tuple(keyboard.key_to_scan_codes(key))
        except Exception:
            scan_codes = ()
        if scan_codes:
            return KeySend("keyboard", scan_codes, key)
        if resolve_layout_scan_code is not None:
            try:
                scan_code = resolve_layout_scan_code(key)
            except Exception:
                scan_code = None
            if (
                isinstance(scan_code, int)
                and not isinstance(scan_code, bool)
                and 1 <= scan_code <= 255
            ):
                return KeySend("layout", (scan_code,), key)
        raise ValueError(f"Unknown key name: {key!r}")

    def press_send(self, send: KeySend) -> None:
        kind, values = send.kind, send.values
        if kind == "numpad":
            _send_numpad_event(values[0], bool(values[1]), key_up=False)
            return
        if kind == "extended":
            _send_extended_event(values[0], values[1], key_up=False)
        elif kind == "layout":
            _send_numpad_event(values[0], False, key_up=False)
        else:
            keyboard.press(send.key)

    def release_send(self, send: KeySend) -> None:
        kind, values = send.kind, send.values
        if kind == "numpad":
            _send_numpad_event(values[0], bool(values[1]), key_up=True)
            return
        if kind == "extended":
            _send_extended_event(values[0], values[1], key_up=True)
        elif kind == "layout":
            _send_numpad_event(values[0], False, key_up=True)
        else:
            keyboard.release(send.key)

    def identity_of(self, send: KeySend) -> tuple[int, bool]:
        kind, values = send.kind, send.values
        if kind == "numpad":
            return values[0], bool(values[1])
        if kind == "extended":
            return values[1], True
        if kind == "layout":
            return values[0], False
        if kind == "keyboard":
            scan_code = values[0]
            if (scan_code & 0xFF00) == 0xE000:
                return scan_code & 0xFF, True
            return scan_code, False
        raise ValueError(f"Unknown key name: {send.key!r}")

    def needs_shift(self, send: KeySend) -> bool:
        return send.kind == "keyboard" and _needs_shift(send.key)

    def press_shift(self) -> None:
        keyboard.press("shift")

    def release_shift(self) -> None:
        keyboard.release("shift")

    def send_native_hotkey(
        self, hotkey: str, keys: Sequence[str],
        resolve_layout_scan_code: ResolveLayoutScanCode,
    ) -> bool:
        all_keyboard = True
        for key in keys:
            try:
                send = self.resolve_send(key, resolve_layout_scan_code)
            except ValueError:
                all_keyboard = False
                break
            if send.kind != "keyboard":
                all_keyboard = False
                break
        if all_keyboard:
            keyboard.send(hotkey)
            return True

        return False

    def write_text(self, text: str) -> None:
        keyboard.write(text, restore_state_after=False)

    def repeat_timing(self) -> tuple[int, int]:
        """OS のキーリピート待ち時間と間隔をミリ秒で返す。"""
        delay_value = _read_keyboard_setting(_SPI_GETKEYBOARDDELAY, wintypes.UINT)
        interval_value = _read_keyboard_setting(_SPI_GETKEYBOARDSPEED, wintypes.DWORD)
        delay = repeat_delay_ms(delay_value) if delay_value is not None else None
        interval = repeat_interval_ms(interval_value) if interval_value is not None else None
        return (
            delay if delay is not None else _DEFAULT_REPEAT_DELAY_MS,
            interval if interval is not None else _DEFAULT_REPEAT_INTERVAL_MS,
        )
