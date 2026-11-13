"""One active Quartz event tap, with all OS imports delayed until start."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import RLock, Thread, current_thread
from typing import Callable

from .key_table import KEY_TABLE, MODIFIERS, MacKey
from .modifier_state import ModifierState


OWN_EVENT_MARK = 0x4B535145
CAPS_LOCK_VK = 57
FN_VK = 63
_UNKNOWN = MacKey(0, False, "")
_LOG = logging.getLogger(__name__)


def load_quartz():
    """Load the native API only when a tap (or standalone probe) needs it."""
    import Quartz
    return Quartz


@dataclass(frozen=True)
class KeyEvent:
    event_type: str
    scan_code: int
    name: str
    is_keypad: bool


class EventTap:
    def __init__(self, callback: Callable[[int, KeyEvent], bool], *, quartz=None) -> None:
        self._callback = callback
        self._quartz = quartz
        self._lock = RLock()
        self._tap = None
        self._run_loop = None
        self._thread: Thread | None = None
        self._modifiers = ModifierState()

    def start(self) -> None:
        with self._lock:
            if self._tap is not None:
                return
            if self._thread is not None and self._thread.is_alive():
                raise OSError("Previous keyboard tap is still stopping")
            if self._quartz is None:
                self._quartz = load_quartz()
            q = self._quartz
            mask = sum(1 << kind for kind in (
                q.kCGEventKeyDown, q.kCGEventKeyUp, q.kCGEventFlagsChanged,
            ))
            tap = q.CGEventTapCreate(q.kCGSessionEventTap, q.kCGHeadInsertEventTap,
                                     q.kCGEventTapOptionDefault, mask, self._handle_event, None)
            if not tap:
                raise OSError("Could not create keyboard event tap")
            self._start_thread(tap)

    def _start_thread(self, tap) -> None:
        q = self._quartz
        try:
            source = q.CFMachPortCreateRunLoopSource(None, tap, 0)
            if not source:
                raise OSError("Could not create keyboard tap run loop source")
            self._tap = tap
            self._thread = Thread(target=self._run, args=(tap, source), name="macos-keyboard-tap", daemon=True)
            self._thread.start()
        except Exception:
            self._tap = None
            self._thread = None
            q.CFMachPortInvalidate(tap)
            raise

    def _run(self, tap, source) -> None:
        q = self._quartz
        run_loop = None
        try:
            run_loop = q.CFRunLoopGetCurrent()
            q.CFRunLoopAddSource(run_loop, source, q.kCFRunLoopCommonModes)
            with self._lock:
                if self._tap is not tap:
                    return
                self._run_loop = run_loop
                q.CGEventTapEnable(tap, True)
            # Bounded iterations also handle stop before CFRunLoopRunInMode enters.
            while self._tap is tap:
                q.CFRunLoopRunInMode(q.kCFRunLoopDefaultMode, 0.1, False)
        except Exception:
            _LOG.exception("Keyboard tap run loop failed")
        finally:
            self._finish_run(tap, run_loop, source)

    def _finish_run(self, tap, run_loop, source) -> None:
        q = self._quartz
        with self._lock:
            if self._tap is tap:
                self._tap = None
            if self._run_loop is run_loop:
                self._run_loop = None
            self._clear_state()
        try:
            if source is not None and run_loop is not None:
                q.CFRunLoopRemoveSource(run_loop, source, q.kCFRunLoopCommonModes)
            q.CFMachPortInvalidate(tap)
        except Exception:
            _LOG.exception("Could not dispose keyboard tap")

    def stop(self) -> None:
        with self._lock:
            tap, self._tap = self._tap, None
            run_loop = self._run_loop
            thread = self._thread
            self._clear_state()
        q = self._quartz
        try:
            if tap is not None:
                q.CGEventTapEnable(tap, False)
        except Exception:
            _LOG.exception("Could not disable keyboard tap")
        finally:
            if run_loop is not None:
                try:
                    q.CFRunLoopStop(run_loop)
                except Exception:
                    _LOG.exception("Could not stop keyboard tap run loop")
            if thread is not None and thread is not current_thread():
                thread.join(timeout=1.0)

    def _clear_state(self) -> None:
        self._modifiers.clear()

    def _handle_event(self, _proxy, event_type, event, _refcon):
        try:
            with self._lock:
                tap = self._tap
                if tap is None:
                    return event
                q = self._quartz
                if event_type in (q.kCGEventTapDisabledByTimeout, q.kCGEventTapDisabledByUserInput):
                    self._clear_state()
                    q.CGEventTapEnable(tap, True)
                    return event
                if q.CGEventGetIntegerValueField(event, q.kCGEventSourceUserData) == OWN_EVENT_MARK:
                    return event
            return self._dispatch(tap, event_type, event)
        except Exception:
            _LOG.exception("Keyboard tap callback failed; passing event through")
            return event

    def _dispatch(self, tap, event_type, event):
        q = self._quartz
        vk = int(q.CGEventGetIntegerValueField(event, q.kCGKeyboardEventKeycode))
        flags = int(q.CGEventGetFlags(event))
        with self._lock:
            if self._tap is not tap:
                return event
            kind = self._event_kind(event_type, vk, flags)
            if kind is None:
                return event
        key = KEY_TABLE.get(vk, _UNKNOWN)
        translated = KeyEvent(kind, key.scan_code, key.name, key.is_keypad)
        suppressed = self._call_backend(tap, vk, translated)
        with self._lock:
            if self._tap is not tap:
                return event
            if vk in MODIFIERS:
                suppressed = self._modifiers.mark_suppressed(vk, suppressed)
            if suppressed and vk not in (CAPS_LOCK_VK, FN_VK):
                return None
            q.CGEventSetFlags(event, self._modifiers.rewrite_flags(flags))
        return event

    def _call_backend(self, tap, vk: int, event: KeyEvent) -> bool:
        try:
            return not self._callback(vk, event)
        except Exception:
            # Only this event passed on failure; keep other held suppression pairs.
            with self._lock:
                if self._tap is tap and vk in MODIFIERS:
                    self._modifiers.mark_suppressed(vk, False)
            raise

    def _event_kind(self, event_type: int, vk: int, flags: int) -> str | None:
        q = self._quartz
        if event_type == q.kCGEventKeyDown:
            return "down"
        if event_type == q.kCGEventKeyUp:
            return "up"
        if event_type != q.kCGEventFlagsChanged:
            return None
        change = self._modifiers.on_flags_changed(vk, flags)
        if change is not None:
            return change[0]
        # CapsLock follows alphaShift; fn follows SecondaryFn, never suppression.
        if vk == CAPS_LOCK_VK:
            bit = 0x10000
        elif vk == FN_VK:
            bit = 0x800000
        else:
            return None
        return "down" if flags & bit else "up"
