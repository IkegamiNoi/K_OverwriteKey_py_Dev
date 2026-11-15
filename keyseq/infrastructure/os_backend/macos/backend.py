from __future__ import annotations

from dataclasses import dataclass
import logging
import math
import os
import subprocess
from threading import Lock, RLock
from typing import Callable, Sequence

from keyseq.domain.default_profile import MACOS_DEFAULT_PROFILE
from keyseq.infrastructure.os_backend.contracts import Capabilities, KeySend, OsBackend, ResolveLayoutScanCode

from .event_tap import EventTap, KeyEvent, OWN_EVENT_MARK, load_quartz
from .key_table import (
    COMMON_FLAGS, KEY_TABLE, MODIFIERS, SHIFTED_JIS, SHIFTED_US,
    MacKey, is_jis_layout, key_for_vk, vk_for_name,
)
from .input_source import InputSourceAPI
from .modifier_state import modifier_flags


_LOG = logging.getLogger(__name__)
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


class MacMouseBackend:
    def capture_next_click(self, on_capture): raise NotImplementedError
    def cursor_position(self): raise NotImplementedError
    def move_cursor(self, x, y): raise NotImplementedError
    def scroll_mouse(self, *, vertical, deltas, position): raise NotImplementedError
    def click_at(self, x, y, button): raise NotImplementedError
    def click_mouse(self, x, y, button, clicks): raise NotImplementedError
    def mouse_down(self, button, x=None, y=None): raise NotImplementedError
    def mouse_up(self, button, x=None, y=None): raise NotImplementedError
    def drag_mouse(self, x, y, to_x, to_y, button, duration_sec): raise NotImplementedError


class MacWindowBackend:
    def __init__(self, *, quartz=None, appkit=None) -> None:
        self._quartz = quartz
        self._appkit = appkit
        self._foreground_failure_logged = False

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
    def foreground_own_window(self): return None
    def window_handle(self, window): return window.winfo_id()
    def place_window_below(self, window, above): return False
    def list_monitor_rects(self): return []
    def make_click_through_overlay(self, window): return False
    def is_mouse_button_down(self): return False
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
        Capabilities(False, False, False, False), MacImeBackend(), MacWindowBackend(),
        MacTkKeyTranslator(keyboard), MacAppIdentity(), keyboard, MacMouseBackend(),
        default_profile=MACOS_DEFAULT_PROFILE,
        queued_hook_dispatch=True,
    )
