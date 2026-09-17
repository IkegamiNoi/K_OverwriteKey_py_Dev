from __future__ import annotations

import ctypes
from typing import Callable

import keyboard
import pyautogui
from keyboard._canonical_names import normalize_name

from keyseq.domain.key_identifiers import resolve_known_scan_code_from_key_name


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


def _resolve_extended_key(name: str) -> tuple[int, int] | None:
    try:
        normalized = normalize_name(name.strip())
    except Exception:
        return None
    return _EXTENDED_KEYS.get(normalized)


def _send_extended_event(vk: int, scan: int, key_up: bool) -> None:
    flags = _KEYEVENTF_EXTENDEDKEY | (_KEYEVENTF_KEYUP if key_up else 0)
    ctypes.windll.user32.keybd_event(vk, scan, flags, 0)


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
        extended = _resolve_extended_key(key)
        if extended is not None:
            _send_extended_event(*extended, key_up=False)
        else:
            keyboard.press(key)

    def release_key(self, key: str) -> None:
        extended = _resolve_extended_key(key)
        if extended is not None:
            _send_extended_event(*extended, key_up=True)
        else:
            keyboard.release(key)

    def send_hotkey(self, hotkey: str) -> None:
        keys = [key.strip() for key in hotkey.split("+")]
        if not any(_resolve_extended_key(key) is not None for key in keys):
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
        keyboard.write(text)

    def validate_key_name(self, key_name: str) -> None:
        try:
            keyboard.key_to_scan_codes(key_name)
        except Exception:
            scan_code = resolve_known_scan_code_from_key_name(str(key_name or ""))
            if scan_code is None:
                raise

    def click_mouse(self, x: int, y: int, button: str, clicks: int) -> None:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
