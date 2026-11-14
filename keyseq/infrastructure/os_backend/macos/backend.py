from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import RLock
from typing import Callable, Sequence

from keyseq.domain.default_profile import MACOS_DEFAULT_PROFILE
from keyseq.infrastructure.os_backend.contracts import Capabilities, KeySend, OsBackend, ResolveLayoutScanCode

from .event_tap import EventTap, KeyEvent, OWN_EVENT_MARK, load_quartz
from .key_table import (
    COMMON_FLAGS, KEY_TABLE, MODIFIERS, SHIFTED_JIS, SHIFTED_US,
    is_jis_layout, vk_for_name,
)


_LOG = logging.getLogger(__name__)
_PHYSICAL_FLAGS_FAILURE_LOGGED = False
_EXTENDED_VKS = frozenset((54, 55, 61, 62, 75, 76, 114, 115, 116, 117,
                           119, 121, 123, 124, 125, 126))


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
    def __init__(self, *, quartz=None) -> None:
        self._hooks: list[_Hook] = []
        self._lock = RLock()
        self._lifecycle = RLock()
        self._tap: EventTap | None = None
        self._quartz = quartz
        self._jis = False
        self._send_lock = RLock()
        self._sent_modifiers: set[int] = set()

    def set_layout_key_ids(self, key_ids: frozenset[str]) -> None:
        self._jis = is_jis_layout(key_ids)

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
                        is_jis_layout=lambda: self._jis,
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
        flags = 0
        for vk in self._sent_modifiers:
            kind, _side, bit = MODIFIERS[vk]
            flags |= COMMON_FLAGS[kind] | bit
        return flags

    def _post_event(self, q, event, flags: int) -> None:
        if event is None:
            raise OSError("Could not create keyboard event")
        q.CGEventSetIntegerValueField(event, q.kCGEventSourceUserData, OWN_EVENT_MARK)
        q.CGEventSetFlags(event, flags)
        q.CGEventPost(q.kCGHIDEventTap, event)

    def _send(self, send: KeySend, down: bool) -> None:
        with self._send_lock:
            q = self._native_api()
            vk = send.values[0]
            event = q.CGEventCreateKeyboardEvent(None, vk, down)
            if event is None:
                raise OSError("Could not create keyboard event")
            previous = self._sent_modifiers.copy()
            if vk in MODIFIERS:
                if down:
                    self._sent_modifiers.add(vk)
                else:
                    self._sent_modifiers.discard(vk)
            flags = self._send_flags()
            if send.kind == "mac_shift":
                flags |= _physical_flags(q) & COMMON_FLAGS["shift"]
            try:
                self._post_event(q, event, flags)
            except Exception:
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

    def repeat_timing(self) -> tuple[int, int]: return (500, 33)


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
    def __init__(self, *, quartz=None) -> None:
        self._quartz = quartz

    def is_own_process_foreground(self) -> bool: return False
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
    def numpad_name(self, keycode, state) -> str: return ""
    def vk_to_scan_code(self, vk: int): return None
    def vk_to_char(self, vk: int) -> str: return ""


class MacImeBackend:
    def disable_for_text(self): return None
    def restore_after_text(self, reservation, character_count): pass
    def restore_ime_now(self): pass
    def get_own_open_status(self, window): return None
    def set_own_open_status(self, window, is_open): return False


class MacAppIdentity:
    def apply_process_identity(self, app_id: str) -> bool: return True
    def relaunch(self, startup_cwd: str) -> OSError | None: return OSError("Application relaunch is not implemented")


def create_backend() -> OsBackend:
    return OsBackend(
        Capabilities(False, False, False, False), MacImeBackend(), MacWindowBackend(),
        MacTkKeyTranslator(), MacAppIdentity(), MacKeyboardBackend(), MacMouseBackend(),
        default_profile=MACOS_DEFAULT_PROFILE,
        queued_hook_dispatch=True,
    )
