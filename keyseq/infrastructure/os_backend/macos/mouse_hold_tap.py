from __future__ import annotations

import logging
from threading import RLock, Thread, current_thread

from .event_tap import OWN_EVENT_MARK, load_quartz

_LOG = logging.getLogger(__name__)
MOUSE_BUTTON_EVENTS = {
    "left": ("kCGEventLeftMouseDown", "kCGEventLeftMouseUp", "kCGEventLeftMouseDragged", "kCGMouseButtonLeft"),
    "right": ("kCGEventRightMouseDown", "kCGEventRightMouseUp", "kCGEventRightMouseDragged", "kCGMouseButtonRight"),
    "middle": ("kCGEventOtherMouseDown", "kCGEventOtherMouseUp", "kCGEventOtherMouseDragged", "kCGMouseButtonCenter"),
}


class MouseHoldTap:
    def __init__(self, *, quartz=None):
        self._quartz = quartz
        self._lock = RLock()
        self._tap = self._loop = self._thread = None
        self._button = self._up = self._dragged = self._number = None
        self._failure_logged = False

    def start(self, button):
        self.stop()
        try:
            with self._lock:
                q = self._quartz if self._quartz is not None else load_quartz()
                self._quartz = q
                down, up, dragged, number = MOUSE_BUTTON_EVENTS[button]
                self._button, self._up = getattr(q, down), getattr(q, up)
                self._dragged, self._number = getattr(q, dragged), getattr(q, number)
                kinds = [q.kCGEventMouseMoved]
                for name in ("kCGEventLeftMouseDown", "kCGEventLeftMouseUp", "kCGEventRightMouseDown", "kCGEventRightMouseUp", "kCGEventOtherMouseDown", "kCGEventOtherMouseUp"):
                    kinds.append(getattr(q, name))
                mask = sum(1 << kind for kind in kinds)
                tap = q.CGEventTapCreate(q.kCGSessionEventTap, q.kCGHeadInsertEventTap, q.kCGEventTapOptionDefault, mask, self._callback, None)
                if not tap:
                    raise OSError("Could not create mouse hold tap")
                source = q.CFMachPortCreateRunLoopSource(None, tap, 0)
                if not source:
                    q.CFMachPortInvalidate(tap)
                    raise OSError("Could not create mouse tap run loop source")
                self._tap = tap
                self._thread = Thread(target=self._run, args=(tap, source), daemon=True, name="macos-mouse-hold-tap")
                self._thread.start()
        except Exception:
            self._tap = None
            self._button = None
            if not self._failure_logged:
                _LOG.exception("Could not start mouse hold tap; passing mouse movement through")
                self._failure_logged = True

    def _callback(self, _proxy, kind, event, _refcon):
        q = self._quartz
        try:
            if kind in (q.kCGEventTapDisabledByTimeout, q.kCGEventTapDisabledByUserInput):
                if self._tap is not None:
                    q.CGEventTapEnable(self._tap, True)
                return event
            if q.CGEventGetIntegerValueField(event, q.kCGEventSourceUserData) == OWN_EVENT_MARK:
                return event
            if kind == q.kCGEventMouseMoved and self._button is not None:
                q.CGEventSetType(event, self._dragged)
                q.CGEventSetIntegerValueField(event, q.kCGMouseEventButtonNumber, self._number)
            elif self._button is not None and kind in (self._button, self._up):
                Thread(target=self._stop_if_current, args=(self._tap,), daemon=True).start()
            return event
        except Exception:
            _LOG.exception("Mouse hold tap callback failed; passing event through")
            return event

    def _run(self, tap, source):
        q = self._quartz
        loop = None
        try:
            loop = q.CFRunLoopGetCurrent()
            q.CFRunLoopAddSource(loop, source, q.kCFRunLoopCommonModes)
            with self._lock:
                self._loop = loop
                q.CGEventTapEnable(tap, True)
            while self._tap is tap:
                q.CFRunLoopRunInMode(q.kCFRunLoopDefaultMode, 0.1, False)
        except Exception:
            _LOG.exception("Mouse hold tap run loop failed")
        finally:
            with self._lock:
                if self._tap is tap:
                    self._tap = None
                if self._loop is loop:
                    self._loop = None
            try:
                q.CFRunLoopRemoveSource(loop, source, q.kCFRunLoopCommonModes)
                q.CFMachPortInvalidate(tap)
            except Exception:
                _LOG.exception("Could not dispose mouse hold tap")

    def _stop_if_current(self, tap):
        # A later mouse_down may have started a new tap before this thread ran.
        with self._lock:
            if self._tap is not tap:
                return
        self.stop()

    def stop(self):
        with self._lock:
            tap, self._tap = self._tap, None
            loop, thread = self._loop, self._thread
            self._button = None
        q = self._quartz
        if q is not None:
            try:
                if tap is not None:
                    q.CGEventTapEnable(tap, False)
                if loop is not None:
                    q.CFRunLoopStop(loop)
            except Exception:
                _LOG.exception("Could not stop mouse hold tap")
        if thread is not None and thread is not current_thread():
            thread.join(timeout=1.0)
