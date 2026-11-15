from __future__ import annotations

import ctypes
from typing import Sequence

from keyseq.infrastructure.os_backend.pyautogui_mouse import PyAutoGuiMouseBackend

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


class WindowsMouseBackend(PyAutoGuiMouseBackend):
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
