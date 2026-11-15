from __future__ import annotations

from typing import Callable

import pyautogui
from pynput import mouse


class PyAutoGuiMouseBackend:
    def capture_next_click(self, on_capture: Callable[[float, float], None]) -> None:
        def on_click(x: float, y: float, button: mouse.Button, pressed: bool) -> bool:
            if pressed:
                on_capture(x, y)
                return False
            return True

        listener = mouse.Listener(on_click=on_click)
        listener.daemon = True
        listener.start()

    def cursor_position(self) -> tuple[int, int]:
        position = pyautogui.position()
        return int(position.x), int(position.y)

    def move_cursor(self, x: int, y: int) -> None:
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            pyautogui.moveTo(x, y, _pause=False)
        finally:
            pyautogui.FAILSAFE = failsafe

    def click_at(self, x: int, y: int, button: str) -> None:
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            pyautogui.moveTo(x, y, _pause=False)
            pyautogui.click(button=button, _pause=False)
        finally:
            pyautogui.FAILSAFE = failsafe

    def click_mouse(self, x: int, y: int, button: str, clicks: int) -> None:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)

    def mouse_down(self, button: str, x: int | None = None, y: int | None = None) -> None:
        self._send_mouse_button(button, x, y, is_down=True)

    def mouse_up(self, button: str, x: int | None = None, y: int | None = None) -> None:
        self._send_mouse_button(button, x, y, is_down=False)

    @staticmethod
    def _send_mouse_button(button: str, x: int | None, y: int | None, *, is_down: bool) -> None:
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

    def drag_mouse(self, x: int, y: int, to_x: int, to_y: int, button: str, duration_sec: float) -> None:
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
