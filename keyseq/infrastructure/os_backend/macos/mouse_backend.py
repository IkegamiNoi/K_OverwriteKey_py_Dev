from __future__ import annotations

import logging
import math
import time

from keyseq.infrastructure.os_backend.pyautogui_mouse import PyAutoGuiMouseBackend

from .event_tap import OWN_EVENT_MARK, load_quartz
from .mouse_hold_tap import MOUSE_BUTTON_EVENTS, MouseHoldTap


_LOG = logging.getLogger(__name__)


PIXELS_PER_NOTCH = 10


class MacMouseBackend(PyAutoGuiMouseBackend):
    def __init__(self, *, quartz=None, sleep=time.sleep) -> None:
        self._quartz = quartz
        self._sleep = sleep
        self._hold_tap = MouseHoldTap(quartz=quartz)

    def _button(self, button):
        try:
            down, up, dragged, number = MOUSE_BUTTON_EVENTS[button]
        except KeyError as exc:
            raise ValueError(f"Unsupported mouse button: {button}") from exc
        q = self._quartz if self._quartz is not None else load_quartz()
        return q, getattr(q, down), getattr(q, up), getattr(q, dragged), getattr(q, number)

    def _post_mouse(self, q, event_type, x, y, button_number, click_state=None):
        event = q.CGEventCreateMouseEvent(None, event_type, (x, y), button_number)
        if event is None:
            raise OSError("Could not create mouse event")
        q.CGEventSetIntegerValueField(event, q.kCGEventSourceUserData, OWN_EVENT_MARK)
        if click_state is not None:
            q.CGEventSetIntegerValueField(event, q.kCGMouseEventClickState, click_state)
        q.CGEventPost(q.kCGHIDEventTap, event)

    def scroll_mouse(self, *, vertical, deltas, position):
        if position is not None:
            self.move_cursor(*position)
        if not deltas:
            return
        q = self._quartz if self._quartz is not None else load_quartz()
        for delta in deltas:
            if delta == 0:
                continue
            pixels = max(1, math.floor(abs(delta) * PIXELS_PER_NOTCH / 120 + 0.5))
            amount = int(math.copysign(pixels, delta))
            event = q.CGEventCreateScrollWheelEvent(None, q.kCGScrollEventUnitPixel, 2,
                                                    amount if vertical else 0,
                                                    0 if vertical else -amount)
            if event is None:
                raise OSError("Could not create scroll event")
            q.CGEventSetIntegerValueField(event, q.kCGEventSourceUserData, OWN_EVENT_MARK)
            q.CGEventPost(q.kCGHIDEventTap, event)

    def click_mouse(self, x, y, button, clicks):
        q, down, up, _, number = self._button(button)
        self.move_cursor(x, y)
        for index in range(1, clicks + 1):
            self._post_mouse(q, down, x, y, number, index)
            self._post_mouse(q, up, x, y, number, index)

    def mouse_down(self, button, x=None, y=None):
        q, down, _, _, number = self._button(button)
        if x is not None and y is not None:
            self.move_cursor(x, y)
        px, py = self.cursor_position()
        self._post_mouse(q, down, px, py, number)
        self._hold_tap.start(button)

    def mouse_up(self, button, x=None, y=None):
        q, _, up, _, number = self._button(button)
        if x is not None and y is not None:
            self.move_cursor(x, y)
        px, py = self.cursor_position()
        self._post_mouse(q, up, px, py, number)
        self._hold_tap.stop()

    def drag_mouse(self, x, y, to_x, to_y, button, duration_sec):
        q, down, up, dragged, number = self._button(button)
        self.move_cursor(x, y)
        count = max(1, round(duration_sec / 0.01))
        try:
            self._post_mouse(q, down, x, y, number)
            for step in range(1, count + 1):
                px = round(x + (to_x - x) * step / count)
                py = round(y + (to_y - y) * step / count)
                self._post_mouse(q, dragged, px, py, number)
                self._sleep(duration_sec / count)
        finally:
            self._post_mouse(q, up, to_x, to_y, number)
