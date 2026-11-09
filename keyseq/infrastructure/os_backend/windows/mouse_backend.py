from __future__ import annotations

import ctypes
from typing import Callable, Sequence

import pyautogui
from pynput import mouse

from .send_input import _INPUT, _INPUT_MOUSE, _MOUSEINPUT, _send_input_api


_MOUSEEVENTF_WHEEL = 0x0800
_MOUSEEVENTF_HWHEEL = 0x1000


def _build_wheel_inputs(vertical: bool, deltas: Sequence[int]) -> tuple[_INPUT, ...]:
    flags = _MOUSEEVENTF_WHEEL if vertical else _MOUSEEVENTF_HWHEEL
    return tuple(
        _INPUT(
            type=_INPUT_MOUSE,
            mi=_MOUSEINPUT(
                dx=0, dy=0, mouseData=delta & 0xFFFFFFFF,
                dwFlags=flags, time=0, dwExtraInfo=0,
            ),
        )
        for delta in deltas
    )


class WindowsMouseBackend:
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
        """Return the current cursor position in screen coordinates."""
        position = pyautogui.position()
        return int(position.x), int(position.y)

    def move_cursor(self, x: int, y: int) -> None:
        """Move the cursor without pyautogui's default post-call pause."""
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            pyautogui.moveTo(x, y, _pause=False)
        finally:
            pyautogui.FAILSAFE = failsafe

    def scroll_mouse(
        self,
        *,
        vertical: bool,
        deltas: Sequence[int],
        position: tuple[int, int] | None,
    ) -> None:
        if position is not None:
            self.move_cursor(*position)
        if not deltas:
            return
        events = _build_wheel_inputs(vertical, deltas)
        inputs = (_INPUT * len(events))(*events)
        sent = _send_input_api()(
            len(events), inputs, ctypes.sizeof(_INPUT),
        )
        if sent != len(events):
            raise OSError(ctypes.get_last_error(), "SendInput failed")

    def click_at(self, x: int, y: int, button: str) -> None:
        """Move and click without blocking the UI for pyautogui's default pause."""
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            pyautogui.moveTo(x, y, _pause=False)
            pyautogui.click(button=button, _pause=False)
        finally:
            pyautogui.FAILSAFE = failsafe

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
