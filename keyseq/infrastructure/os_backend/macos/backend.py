from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable

from keyseq.domain.default_profile import MACOS_DEFAULT_PROFILE
from keyseq.infrastructure.os_backend.contracts import Capabilities, KeySend, OsBackend, ResolveLayoutScanCode

from .event_tap import EventTap, KeyEvent
from .key_table import vk_for_name


@dataclass(frozen=True)
class _Hook:
    handle: object
    callback: Callable[[object], bool | None]
    suppress: bool
    vk: int | None


class MacKeyboardBackend:
    def __init__(self) -> None:
        self._hooks: list[_Hook] = []
        self._lock = RLock()
        self._lifecycle = RLock()
        self._tap: EventTap | None = None

    def register_global_hook(self, callback, *, suppress: bool = False) -> object:
        return self._register(callback, suppress, None)

    def register_key_hook(self, key: str, callback, *, suppress: bool) -> object:
        vk = vk_for_name(key)
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
                    self._tap = EventTap(self._dispatch)
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
        raise NotImplementedError

    def press_send(self, send: KeySend) -> None: raise NotImplementedError
    def release_send(self, send: KeySend) -> None: raise NotImplementedError
    def identity_of(self, send: KeySend) -> tuple[int, bool]: raise NotImplementedError
    def needs_shift(self, send: KeySend) -> bool: raise NotImplementedError
    def press_shift(self) -> None: raise NotImplementedError
    def release_shift(self) -> None: raise NotImplementedError
    def send_native_hotkey(self, hotkey: str, keys, resolve_layout_scan_code: ResolveLayoutScanCode) -> bool: raise NotImplementedError
    def write_text(self, text: str) -> None: raise NotImplementedError
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
    def is_own_process_foreground(self) -> bool: return False
    def foreground_own_window(self): return None
    def window_handle(self, window): return window.winfo_id()
    def place_window_below(self, window, above): return False
    def list_monitor_rects(self): return []
    def make_click_through_overlay(self, window): return False
    def is_mouse_button_down(self): return False
    def is_shift_down(self): return False
    def is_ctrl_alt_win_down(self): return False


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
