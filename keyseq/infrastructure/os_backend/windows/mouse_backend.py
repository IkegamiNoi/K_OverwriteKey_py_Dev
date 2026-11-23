from __future__ import annotations

import ctypes
from typing import Sequence

from keyseq.infrastructure.os_backend.pyautogui_mouse import PyAutoGuiMouseBackend

from .send_input import _INPUT, _INPUT_MOUSE, _MOUSEINPUT, _send_input_api


_MOUSEEVENTF_WHEEL = 0x0800
_MOUSEEVENTF_HWHEEL = 0x1000
_MOUSEEVENTF_MOVE = 0x0001
_MOUSEEVENTF_ABSOLUTE = 0x8000
_MOUSEEVENTF_VIRTUALDESK = 0x4000
_CLICK_FLAGS = {
    "left": (0x0002, 0x0004),
    "right": (0x0008, 0x0010),
    "middle": (0x0020, 0x0040),
}


def _virtual_screen() -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    return tuple(user32.GetSystemMetrics(index) for index in (76, 77, 78, 79))


def _build_click_inputs(
    x: int, y: int, button: str, clicks: int,
    virtual_screen: tuple[int, int, int, int],
) -> tuple[_INPUT, ...]:
    if button not in _CLICK_FLAGS:
        raise ValueError(f"Unsupported mouse button: {button}")
    vx, vy, vw, vh = virtual_screen
    dx = round((x - vx) * 65535 / max(vw - 1, 1))
    dy = round((y - vy) * 65535 / max(vh - 1, 1))
    events = [_INPUT(type=_INPUT_MOUSE, mi=_MOUSEINPUT(
        dx=dx, dy=dy, mouseData=0,
        dwFlags=_MOUSEEVENTF_MOVE | _MOUSEEVENTF_ABSOLUTE | _MOUSEEVENTF_VIRTUALDESK,
        time=0, dwExtraInfo=0,
    ))]
    down, up = _CLICK_FLAGS[button]
    for _ in range(clicks):
        for flags in (down, up):
            events.append(_INPUT(type=_INPUT_MOUSE, mi=_MOUSEINPUT(
                dx=0, dy=0, mouseData=0, dwFlags=flags, time=0, dwExtraInfo=0,
            )))
    return tuple(events)


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


class WindowsMouseBackend(PyAutoGuiMouseBackend):
    def click_mouse(self, x: int, y: int, button: str, clicks: int) -> None:
        events = _build_click_inputs(x, y, button, clicks, _virtual_screen())
        inputs = (_INPUT * len(events))(*events)
        sent = _send_input_api()(len(events), inputs, ctypes.sizeof(_INPUT))
        if sent != len(events):
            raise OSError(ctypes.get_last_error(), "SendInput failed")

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
