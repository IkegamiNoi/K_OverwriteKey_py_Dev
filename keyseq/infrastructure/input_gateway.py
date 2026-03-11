from __future__ import annotations

from typing import Callable

import keyboard
import pyautogui


class InputGateway:
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

    def send_hotkey(self, hotkey: str) -> None:
        keyboard.send(hotkey)

    def write_text(self, text: str) -> None:
        keyboard.write(text)

    def validate_key_name(self, key_name: str) -> None:
        keyboard.key_to_scan_codes(key_name)

    def click_mouse(self, x: int, y: int, button: str, clicks: int) -> None:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
