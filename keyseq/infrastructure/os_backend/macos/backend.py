from __future__ import annotations

from keyseq.domain.default_profile import MACOS_DEFAULT_PROFILE
from keyseq.infrastructure.os_backend.contracts import Capabilities, KeySend, OsBackend, ResolveLayoutScanCode


class MacKeyboardBackend:
    def register_global_hook(self, callback, *, suppress: bool = False) -> object:
        raise OSError("Global keyboard hooks will be implemented in task_08")

    def register_key_hook(self, key: str, callback, *, suppress: bool) -> object:
        raise OSError("Key hooks will be implemented in task_08")

    def unregister_hook(self, handle: object) -> None:
        pass

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
    )
