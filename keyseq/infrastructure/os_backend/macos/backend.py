from __future__ import annotations

from dataclasses import dataclass
import logging
import math
import os
import subprocess
import time
import tkinter
from threading import Lock, RLock
from typing import Callable, Sequence

from keyseq.domain.default_profile import MACOS_DEFAULT_PROFILE
from keyseq.infrastructure.os_backend.contracts import Capabilities, KeySend, OsBackend, ResolveLayoutScanCode
from keyseq.infrastructure.os_backend.pyautogui_mouse import PyAutoGuiMouseBackend

from .event_tap import EventTap, KeyEvent, OWN_EVENT_MARK, load_quartz
from .key_table import (
    COMMON_FLAGS, KEY_TABLE, MODIFIERS, SHIFTED_JIS, SHIFTED_US,
    MacKey, is_jis_layout, key_for_vk, vk_for_name,
)
from .input_source import InputSourceAPI
from .modifier_state import modifier_flags
from .mouse_hold_tap import MOUSE_BUTTON_EVENTS, MouseHoldTap
from .ns_window import ns_window_for


_LOG = logging.getLogger(__name__)
_OVERLAY_ALPHA = 0.5
_PHYSICAL_FLAGS_FAILURE_LOGGED = False
_EXTENDED_VKS = frozenset((54, 55, 61, 62, 75, 76, 114, 115, 116, 117,
                           119, 121, 123, 124, 125, 126))
_REJECTED_WINDOWS_MODIFIER_NAMES = frozenset({
    "windows", "left windows", "right windows", "win", "left win",
    "right win", "alt", "left alt", "right alt", "left menu",
})


def _normalize_key_name(name: str) -> str:
    return name.strip().lower().replace("_", " ")


def _physical_flags(quartz=None) -> int:
    global _PHYSICAL_FLAGS_FAILURE_LOGGED
    try:
        q = quartz if quartz is not None else load_quartz()
        return int(q.CGEventSourceFlagsState(q.kCGEventSourceStateHIDSystemState))
    except Exception:
        if not _PHYSICAL_FLAGS_FAILURE_LOGGED:
            _LOG.exception("Could not read physical keyboard modifiers")
            _PHYSICAL_FLAGS_FAILURE_LOGGED = True
        return 0


def _unicode_chunks(text: str) -> list[tuple[str, int]]:
    chunks = []
    current = []
    units = 0
    for character in text:
        character_units = 2 if ord(character) > 0xFFFF else 1
        if units + character_units > 20:
            chunks.append(("".join(current), units))
            current = []
            units = 0
        current.append(character)
        units += character_units
    if current:
        chunks.append(("".join(current), units))
    return chunks


@dataclass(frozen=True)
class _Hook:
    handle: object
    callback: Callable[[object], bool | None]
    suppress: bool
    vk: int | None


class MacKeyboardBackend:
    def __init__(self, *, quartz=None, foundation=None) -> None:
        self._hooks: list[_Hook] = []
        self._lock = RLock()
        self._lifecycle = RLock()
        self._tap: EventTap | None = None
        self._quartz = quartz
        self._foundation = foundation
        self._repeat_timing_failure_logged = False
        self._hook_failure_listener: Callable[[], None] | None = None
        self._jis = False
        self._send_lock = RLock()
        self._sent_modifiers: set[int] = set()
        self._sent_modifiers_lock = Lock()

    def accepts_key_name(self, name: str) -> bool:
        return _normalize_key_name(name) not in _REJECTED_WINDOWS_MODIFIER_NAMES

    def set_layout_key_ids(self, key_ids: frozenset[str]) -> None:
        self._jis = is_jis_layout(key_ids)

    def input_permission_granted(self) -> bool:
        try:
            from ApplicationServices import AXIsProcessTrusted
            return bool(AXIsProcessTrusted())
        except Exception:
            _LOG.exception("Could not check Accessibility permission")
            return True

    def open_input_permission_settings(self) -> bool:
        try:
            subprocess.run(
                ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
                check=True, capture_output=True, timeout=5,
            )
            return True
        except Exception:
            _LOG.exception("Could not open Accessibility settings")
            return False

    def set_hook_failure_listener(self, callback: Callable[[], None] | None) -> None:
        with self._lock:
            self._hook_failure_listener = callback
            tap = self._tap
        if tap is not None:
            tap.set_failure_listener(self._notify_hook_failure)

    def _notify_hook_failure(self) -> None:
        with self._lock:
            listener = self._hook_failure_listener
        if listener is not None:
            listener()

    def register_global_hook(self, callback, *, suppress: bool = False) -> object:
        return self._register(callback, suppress, None)

    def register_key_hook(self, key: str, callback, *, suppress: bool) -> object:
        vk = vk_for_name(key, jis=self._jis)
        if vk is None:
            raise ValueError(f"Unknown or ambiguous Mac key name: {key!r}")
        return self._register(callback, suppress, vk)

    def _register(self, callback, suppress: bool, vk: int | None) -> object:
        hook = _Hook(object(), callback, suppress, vk)
        with self._lifecycle:
            with self._lock:
                first = not self._hooks
                self._hooks.append(hook)
                if self._tap is None:
                    self._tap = EventTap(
                        self._dispatch, quartz=self._quartz,
                        sent_modifiers=self._sent_modifier_snapshot,
                        is_jis_layout=lambda: self._jis,
                        input_permission_granted=self.input_permission_granted,
                        failure_listener=self._notify_hook_failure,
                    )
            if first:
                try:
                    self._tap.start()
                except Exception:
                    with self._lock:
                        self._hooks.remove(hook)
                    raise
        return hook.handle

    def unregister_hook(self, handle: object) -> None:
        with self._lifecycle:
            with self._lock:
                found = next((h for h in self._hooks if h.handle is handle), None)
                if found is None:
                    return
                self._hooks.remove(found)
                stop = not self._hooks
            if stop and self._tap is not None:
                self._tap.stop()

    def _dispatch(self, vk: int, event: KeyEvent) -> bool:
        with self._lock:
            hooks = tuple(self._hooks)
        for hook in hooks:
            if hook.suppress and hook.vk is None and not hook.callback(event):
                return False
        for hook in hooks:
            if hook.suppress and hook.vk == vk:
                if event.event_type == "down":
                    hook.callback(event)
                return False
        for hook in hooks:
            if not hook.suppress and (hook.vk is None or hook.vk == vk):
                if hook.vk is None or event.event_type == "down":
                    hook.callback(event)
        return True

    def resolve_send(self, key: str, resolve_layout_scan_code: ResolveLayoutScanCode) -> KeySend:
        if not self.accepts_key_name(key):
            raise ValueError(f"Unknown key name: {key!r}")
        jis = self._jis
        shifted = SHIFTED_JIS if jis else SHIFTED_US
        if key in shifted:
            vk = vk_for_name(shifted[key], jis=jis)
            if vk is not None:
                return KeySend("mac_shift", (vk,), key)
        vk = vk_for_name(key, jis=jis)
        if vk is not None:
            return KeySend("mac", (vk,), key)
        if resolve_layout_scan_code is not None:
            try:
                scan = resolve_layout_scan_code(key)
            except Exception:
                _LOG.exception("Could not resolve layout scan code for %r", key)
                scan = None
            if isinstance(scan, int) and not isinstance(scan, bool) and 1 <= scan <= 255:
                matches = [vk for vk, spec in KEY_TABLE.items() if spec.scan_code == scan]
                if len(matches) == 1:
                    return KeySend("mac", (matches[0],), key)
        raise ValueError(f"Unknown key name: {key!r}")

    def _native_api(self):
        if self._quartz is None:
            self._quartz = load_quartz()
        return self._quartz

    def _send_flags(self) -> int:
        return modifier_flags(self._sent_modifiers)

    def _sent_modifier_snapshot(self) -> frozenset[int]:
        with self._sent_modifiers_lock:
            return frozenset(self._sent_modifiers)

    def _post_event(self, q, event, flags: int) -> None:
        if event is None:
            raise OSError("Could not create keyboard event")
        q.CGEventSetIntegerValueField(event, q.kCGEventSourceUserData, OWN_EVENT_MARK)
        q.CGEventSetFlags(event, flags)
        q.CGEventPost(q.kCGHIDEventTap, event)

    def _send(self, send: KeySend, down: bool) -> None:
        tap = self._tap
        physical = tap.physical_modifiers() if tap is not None else frozenset()
        with self._send_lock:
            q = self._native_api()
            vk = send.values[0]
            event = q.CGEventCreateKeyboardEvent(None, vk, down)
            if event is None:
                raise OSError("Could not create keyboard event")
            with self._sent_modifiers_lock:
                previous = self._sent_modifiers.copy()
                if vk in MODIFIERS:
                    if down:
                        self._sent_modifiers.add(vk)
                    else:
                        self._sent_modifiers.discard(vk)
                sent_modifiers = frozenset(self._sent_modifiers)
            flags = modifier_flags(physical | sent_modifiers)
            if send.kind == "mac_shift":
                flags |= _physical_flags(q) & COMMON_FLAGS["shift"]
            try:
                self._post_event(q, event, flags)
            except Exception:
                with self._sent_modifiers_lock:
                    self._sent_modifiers = previous
                raise

    def press_send(self, send: KeySend) -> None:
        self._send(send, True)

    def release_send(self, send: KeySend) -> None:
        self._send(send, False)

    def identity_of(self, send: KeySend) -> tuple[int, bool]:
        vk = send.values[0]
        return KEY_TABLE[vk].scan_code, vk in _EXTENDED_VKS

    def needs_shift(self, send: KeySend) -> bool:
        return send.kind == "mac_shift"

    def press_shift(self) -> None:
        self.press_send(KeySend("mac", (56,), "shift"))

    def release_shift(self) -> None:
        self.release_send(KeySend("mac", (56,), "shift"))

    def send_native_hotkey(
        self, hotkey: str, keys: Sequence[str], resolve_layout_scan_code: ResolveLayoutScanCode
    ) -> bool:
        return False

    def write_text(self, text: str) -> None:
        with self._send_lock:
            if not text:
                return
            q = self._native_api()
            for chunk, length in _unicode_chunks(text):
                for down in (True, False):
                    event = q.CGEventCreateKeyboardEvent(None, 0, down)
                    if event is None:
                        raise OSError("Could not create Unicode keyboard event")
                    q.CGEventKeyboardSetUnicodeString(event, length, chunk)
                    self._post_event(q, event, self._send_flags())

    def repeat_timing(self) -> tuple[int, int]:
        try:
            foundation = self._foundation
            if foundation is None:
                from Foundation import CFPreferencesAppSynchronize, CFPreferencesCopyAppValue
            else:
                CFPreferencesAppSynchronize = foundation.CFPreferencesAppSynchronize
                CFPreferencesCopyAppValue = foundation.CFPreferencesCopyAppValue
            domain = ".GlobalPreferences"
            CFPreferencesAppSynchronize(domain)
        except Exception:
            if not self._repeat_timing_failure_logged:
                _LOG.exception("Could not read keyboard repeat timing")
                self._repeat_timing_failure_logged = True
            return (500, 33)
        return (self._read_repeat_value(CFPreferencesCopyAppValue, "InitialKeyRepeat", domain, 500),
                self._read_repeat_value(CFPreferencesCopyAppValue, "KeyRepeat", domain, 33))

    def _read_repeat_value(self, getter, key: str, domain: str, default: int) -> int:
        try:
            return self._repeat_milliseconds(getter(key, domain), default)
        except Exception:
            if not self._repeat_timing_failure_logged:
                _LOG.exception("Could not read keyboard repeat timing")
                self._repeat_timing_failure_logged = True
            return default

    @staticmethod
    def _repeat_milliseconds(value: object, default: int) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return default
        if not math.isfinite(value) or value <= 0:
            return default
        return max(1, round(value * 15))


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


class MacWindowBackend:
    def __init__(self, *, quartz=None, appkit=None, notification_center=None) -> None:
        self._quartz = quartz
        self._appkit = appkit
        self._notification_center = notification_center
        self._minimize_observers: dict[object, object] = {}
        self._minimize_preparation_failure_logged = False
        self._foreground_failure_logged = False
        self._mouse_button_failure_logged = False
        self._window_failure_logged = False
        self._key_window_failure_logged = False
        self._overlay_reapply_failure_logged = False
        self._minimize_button_failure_logged = False
        self._order_out_failure_logged = False

    def releases_topmost_during_modal(self) -> bool:
        return True

    def install_minimize_preparation(self, window: tkinter.Misc) -> bool:
        try:
            from keyseq.infrastructure.os_backend.macos.minimize_observer import create_minimize_observer

            native = ns_window_for(window)
            if native is None:
                raise RuntimeError("Could not resolve native window")
            key = native  # NSWindow identity (windowNumber is -1 before first show and can be reused)
            if key in self._minimize_observers:
                return True
            center = self._notification_center
            if center is None:
                from Foundation import NSNotificationCenter
                center = NSNotificationCenter.defaultCenter()
                self._notification_center = center
            appkit = self._get_appkit()
            observer = create_minimize_observer()
            center.addObserver_selector_name_object_(
                observer, "willMiniaturize:", appkit.NSWindowWillMiniaturizeNotification, native
            )
            self._minimize_observers[key] = observer
            return True
        except Exception:
            if not self._minimize_preparation_failure_logged:
                _LOG.exception("Could not install minimize preparation")
                self._minimize_preparation_failure_logged = True
            return False

    def order_out(self, window: tkinter.Misc) -> bool:
        try:
            native = ns_window_for(window)
            if native is None:
                return False
            native.orderOut_(None)
            return True
        except Exception:
            if not self._order_out_failure_logged:
                _LOG.exception("Could not order window out")
                self._order_out_failure_logged = True
            return False

    def disable_minimize_button(self, window: tkinter.Misc) -> bool:
        try:
            stylemask = window.attributes("-stylemask")
            window.attributes(
                "-stylemask", tuple(item for item in stylemask if item != "miniaturizable")
            )
            return True
        except Exception:
            if not self._minimize_button_failure_logged:
                _LOG.exception("Could not disable minimize button")
                self._minimize_button_failure_logged = True
            return False

    def _log_overlay_reapply_failure(self) -> None:
        if not self._overlay_reapply_failure_logged:
            _LOG.exception("Could not reapply click-through overlay")
            self._overlay_reapply_failure_logged = True

    def _reapply_overlay_click_through(self, window) -> None:
        try:
            native = ns_window_for(window)
            if native is not None:
                native.setIgnoresMouseEvents_(True)
                native.setLevel_(self._get_appkit().NSStatusWindowLevel)
        except Exception:
            self._log_overlay_reapply_failure()

    def _overlay_mapped(self, window, event) -> None:
        try:
            if event.widget is window:
                window.after(0, lambda: self._reapply_overlay_click_through(window))
        except Exception:
            self._log_overlay_reapply_failure()

    def is_own_process_foreground(self) -> bool:
        try:
            appkit = self._appkit
            if appkit is None:
                from AppKit import NSWorkspace
            else:
                NSWorkspace = appkit.NSWorkspace
            application = NSWorkspace.sharedWorkspace().frontmostApplication()
            return application is None or application.processIdentifier() == os.getpid()
        except Exception:
            if not self._foreground_failure_logged:
                _LOG.exception("Could not determine frontmost application")
                self._foreground_failure_logged = True
            return False
    def _get_appkit(self):
        if self._appkit is None:
            import AppKit
            return AppKit
        return self._appkit

    def window_handle(self, window):
        native = ns_window_for(window)
        return self._window_number(native)

    @staticmethod
    def _window_number(native):
        try:
            number = int(native.windowNumber()) if native is not None else 0
            return number if number > 0 else None
        except Exception:
            return None

    def foreground_own_window(self):
        try:
            app = self._get_appkit().NSApplication.sharedApplication()
            native = app.keyWindow()
            return self._window_number(native) if app.isActive() and native is not None else None
        except Exception:
            if not self._key_window_failure_logged:
                _LOG.exception("Could not determine foreground window")
                self._key_window_failure_logged = True
            return None

    def place_window_below(self, window, above):
        if not isinstance(above, int):
            return False
        try:
            native = ns_window_for(window)
            if native is None:
                return False
            native.orderWindow_relativeTo_(self._get_appkit().NSWindowBelow, above)
            return True
        except Exception:
            return False

    def list_monitor_rects(self):
        try:
            screens = list(self._get_appkit().NSScreen.screens())
            if not screens:
                return []
            height = screens[0].frame().size.height
            result = []
            for index, screen in enumerate(screens):
                frame = screen.frame()
                x, y = frame.origin.x, frame.origin.y
                w, h = frame.size.width, frame.size.height
                result.append(((round(x), round(height-y-h), round(x+w), round(height-y)), index == 0))
            return result
        except Exception:
            if not self._window_failure_logged:
                _LOG.exception("Could not list monitors")
                self._window_failure_logged = True
            return []

    def make_click_through_overlay(self, window, transparent_color):
        try:
            pending = [window]
            while pending:
                widget = pending.pop()
                try:
                    if str(widget.cget("background")).lower() == transparent_color.lower():
                        widget.configure(background="#000000")
                except tkinter.TclError:
                    continue
                pending.extend(widget.winfo_children())
            window.attributes("-alpha", _OVERLAY_ALPHA)
            native = ns_window_for(window)
            if native is None:
                return False
            native.setIgnoresMouseEvents_(True)
            native.setLevel_(self._get_appkit().NSStatusWindowLevel)
            window.bind("<Map>", lambda event: self._overlay_mapped(window, event), add="+")
            return True
        except Exception:
            return False
    def is_mouse_button_down(self):
        try:
            q = self._quartz if self._quartz is not None else load_quartz()
            return bool(q.CGEventSourceButtonState(q.kCGEventSourceStateHIDSystemState, q.kCGMouseButtonLeft) or
                        q.CGEventSourceButtonState(q.kCGEventSourceStateHIDSystemState, q.kCGMouseButtonRight))
        except Exception:
            if not self._mouse_button_failure_logged:
                _LOG.exception("Could not read physical mouse buttons")
                self._mouse_button_failure_logged = True
            return False
    def is_shift_down(self) -> bool:
        return bool(_physical_flags(self._quartz) & COMMON_FLAGS["shift"])

    def is_ctrl_alt_win_down(self) -> bool:
        mask = COMMON_FLAGS["control"] | COMMON_FLAGS["option"] | COMMON_FLAGS["command"]
        return bool(_physical_flags(self._quartz) & mask)


class MacTkKeyTranslator:
    def __init__(self, keyboard: MacKeyboardBackend) -> None:
        self._keyboard = keyboard

    def _key(self, keycode: object) -> MacKey | None:
        if not isinstance(keycode, int) or isinstance(keycode, bool):
            return None
        vk = (keycode >> 24) & 0xFF
        if vk == 0xFF:
            return None
        return key_for_vk(vk, jis=self._keyboard._jis)

    def numpad_name(self, keycode: object, state: object) -> str:
        key = self._key(keycode)
        return key.name if key is not None and key.is_keypad else ""

    def vk_to_scan_code(self, vk: int) -> int | None:
        key = self._key(vk)
        return key.scan_code if key is not None else None

    def vk_to_char(self, vk: int) -> str:
        key = self._key(vk)
        return key.name if key is not None and len(key.name) == 1 else ""

    def modifier_name(self, keysym: str, *, sided: bool) -> str | None:
        key = (keysym or "").lower()
        if key in {"super_l", "super_r"}:
            return "??"
        names = {
            "control_l": ("ctrl", "left ctrl"),
            "control_r": ("ctrl", "right ctrl"),
            "shift_l": ("shift", "left shift"),
            "shift_r": ("shift", "right shift"),
            "meta_l": ("command", "left command"),
            "meta_r": ("command", "right command"),
            "alt_l": ("option", "left option"),
            "alt_r": ("option", "right option"),
        }
        result = names.get(key)
        return result[1 if sided else 0] if result is not None else None


class MacImeBackend:
    def __init__(self, *, tis=None) -> None:
        self._tis = tis
        self._load_failure_logged = False
        self._capture_sources: tuple[object, object] | None = None

    def _native_api(self):
        if self._tis is None:
            try:
                self._tis = InputSourceAPI()
            except Exception:
                if not self._load_failure_logged:
                    _LOG.exception("Could not load keyboard input source API")
                    self._load_failure_logged = True
                return None
        return self._tis

    def disable_for_text(self): return None
    def restore_after_text(self, reservation, character_count): pass
    def restore_ime_now(self): pass

    def get_own_open_status(self, window) -> bool | None:
        try:
            tis = self._native_api()
            if tis is None: return None
            source = tis.current()
            if source is None:
                return None
            try:
                ascii_capable = tis.is_ascii_capable(source)
                return None if ascii_capable is None else not ascii_capable
            finally:
                tis.release(source)
        except Exception:
            _LOG.exception("Could not read keyboard input source")
            return None

    def set_own_open_status(self, window, is_open: bool) -> bool:
        sources = self._capture_sources
        try:
            tis = self._native_api()
            if tis is None: return False
            if is_open:
                self._capture_sources = None
                try:
                    return self._restore_capture_source(tis, sources)
                finally:
                    if sources is not None:
                        tis.release(sources[0]); tis.release(sources[1])
            self._release_capture(tis)
            original = tis.current()
            target = tis.ascii_source()
            if original is None or target is None:
                if original: tis.release(original)
                if target: tis.release(target)
                return False
            status = tis.select(target)
            current = tis.current()
            matches = current is not None and tis.source_id(current) == tis.source_id(target)
            if current: tis.release(current)
            if status != 0 or not matches:
                tis.release(original); tis.release(target)
                return False
            self._capture_sources = (original, target)
            return True
        except Exception:
            _LOG.exception("Could not switch keyboard input source")
            return False

    def _restore_capture_source(self, tis, sources: tuple[object, object] | None) -> bool:
        if sources is None:
            return False
        original, target = sources
        current = tis.current()
        if current is None: return False
        try:
            matches = tis.source_id(current) == tis.source_id(target)
        finally:
            tis.release(current)
        if not matches:
            return False
        status = tis.select(original)
        return status == 0

    def _release_capture(self, tis) -> None:
        sources, self._capture_sources = self._capture_sources, None
        if sources is not None:
            tis.release(sources[0]); tis.release(sources[1])


class MacAppIdentity:
    def apply_process_identity(self, app_id: str) -> bool: return True
    def relaunch(self, startup_cwd: str) -> OSError | None: return OSError("Application relaunch is not implemented")


def create_backend() -> OsBackend:
    keyboard = MacKeyboardBackend()
    return OsBackend(
        Capabilities(True, True, False, False), MacImeBackend(), MacWindowBackend(),
        MacTkKeyTranslator(keyboard), MacAppIdentity(), keyboard, MacMouseBackend(),
        default_profile=MACOS_DEFAULT_PROFILE,
        queued_hook_dispatch=True,
    )
