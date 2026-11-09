from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from keyseq.infrastructure.os_backend.contracts import Capabilities, OsBackend
from keyseq.infrastructure.os_backend.windows import app_relaunch, ime_control, own_ime_status, tk_key_translator, win32_window
from keyseq.infrastructure.os_backend.windows.keyboard_backend import WindowsKeyboardBackend
from keyseq.infrastructure.os_backend.windows.mouse_backend import WindowsMouseBackend

if TYPE_CHECKING:
    import tkinter

_logger = logging.getLogger(__name__)


class WindowsImeBackend:
    def disable_for_text(self) -> object | None:
        return ime_control.disable_for_text()

    def restore_after_text(self, reservation: object | None, character_count: int) -> None:
        ime_control.restore_after_text(reservation, character_count)

    def restore_ime_now(self) -> None:
        ime_control.restore_ime_now()

    def get_own_open_status(self, window) -> bool | None:
        try:
            return own_ime_status.get_open_status(int(window.winfo_id()))
        except Exception:
            _logger.warning("Could not get IME status for the application window", exc_info=True)
            return None

    def set_own_open_status(self, window, is_open: bool) -> bool:
        try:
            return own_ime_status.set_open_status(int(window.winfo_id()), is_open)
        except Exception:
            _logger.warning("Could not set IME status for the application window", exc_info=True)
            return False


class WindowsWindowBackend:
    def is_own_process_foreground(self) -> bool:
        return win32_window.is_own_process_foreground()

    def foreground_own_window(self) -> object | None:
        return win32_window.foreground_own_window()

    def window_handle(self, window: tkinter.Misc) -> object:
        return int(window.wm_frame(), 16)

    def place_window_below(self, window: tkinter.Misc, above: object) -> bool:
        return win32_window.place_window_below(int(window.wm_frame(), 16), above)

    def list_monitor_rects(self) -> list[tuple[tuple[int, int, int, int], bool]]:
        return win32_window.list_monitor_rects()

    def make_click_through_overlay(self, window: tkinter.Misc) -> bool:
        return win32_window.make_click_through_overlay(window.winfo_id())

    def is_mouse_button_down(self) -> bool:
        return win32_window.is_mouse_button_down()

    def is_shift_down(self) -> bool:
        return win32_window.is_shift_down()

    def is_ctrl_alt_win_down(self) -> bool:
        return win32_window.is_ctrl_alt_win_down()


class WindowsTkKeyTranslator:
    def numpad_name(self, keycode: object, state: object) -> str:
        return tk_key_translator.numpad_name_from_tk_event(keycode, state)

    def vk_to_scan_code(self, vk: int) -> int | None:
        return win32_window.vk_to_scan_code(vk)

    def vk_to_char(self, vk: int) -> str:
        return win32_window.vk_to_char(vk)


class WindowsAppIdentity:
    def apply_process_identity(self, app_id: str) -> bool:
        return win32_window.set_app_user_model_id(app_id)

    def relaunch(self, startup_cwd: str) -> OSError | None:
        return app_relaunch.relaunch_app(startup_cwd)


def create_backend() -> OsBackend:
    return OsBackend(
        Capabilities(True, True, True, True), WindowsImeBackend(),
        WindowsWindowBackend(), WindowsTkKeyTranslator(), WindowsAppIdentity(),
        WindowsKeyboardBackend(), WindowsMouseBackend(),
    )
