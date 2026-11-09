from __future__ import annotations

import logging
from typing import Callable, Sequence

from keyseq.domain.numpad_keys import is_numpad_key_name, is_reserved_numpad_name
from keyseq.infrastructure.os_backend import KeySend, get_backend
from keyseq.shared.i18n import tr


_logger = logging.getLogger(__name__)


def keyboard_repeat_timing() -> tuple[int, int]:
    """OS のキーリピート待ち時間と間隔をミリ秒で返す。"""
    return get_backend().keyboard.repeat_timing()


class InputGateway:
    def __init__(
        self,
        *,
        resolve_layout_scan_code: Callable[[str], int | None] | None = None,
    ) -> None:
        self._resolve_layout_scan_code = resolve_layout_scan_code

    def cursor_position(self) -> tuple[int, int]:
        """Return the current cursor position in screen coordinates."""
        return get_backend().mouse.cursor_position()

    def move_cursor(self, x: int, y: int) -> None:
        """Move the cursor without pyautogui's default post-call pause."""
        get_backend().mouse.move_cursor(x, y)

    def scroll_mouse(
        self,
        *,
        vertical: bool,
        deltas: Sequence[int],
        position: tuple[int, int] | None,
    ) -> None:
        get_backend().mouse.scroll_mouse(vertical=vertical, deltas=deltas, position=position)

    def click_at(self, x: int, y: int, button: str) -> None:
        """Move and click without blocking the UI for pyautogui's default pause."""
        get_backend().mouse.click_at(x, y, button)

    def register_global_hook(
        self,
        callback: Callable[[object], bool | None],
        *,
        suppress: bool = False,
    ):
        return get_backend().keyboard.register_global_hook(callback, suppress=suppress)

    def register_key_hook(
        self,
        key: str,
        callback: Callable[[object], None],
        *,
        suppress: bool,
    ):
        return get_backend().keyboard.register_key_hook(key, callback, suppress=suppress)

    def unregister_hook(self, handle) -> None:
        get_backend().keyboard.unregister_hook(handle)

    def press_key(self, key: str) -> None:
        self.press_send(self.resolve_send(key))

    def send_mapped_key(self, key: str) -> None:
        send = self.resolve_send(key)
        kb = get_backend().keyboard
        window = get_backend().window
        if (
            kb.needs_shift(send)
            and not window.is_shift_down()
            and not window.is_ctrl_alt_win_down()
        ):
            kb.press_shift()
            try:
                self.press_send(send)
                self.release_send(send)
            finally:
                kb.release_shift()
            return
        self.press_send(send)
        self.release_send(send)

    def resolve_send(self, key: str) -> KeySend:
        return get_backend().keyboard.resolve_send(key, self._resolve_layout_scan_code)

    def press_send(self, send: KeySend) -> None:
        get_backend().keyboard.press_send(send)

    def release_key(self, key: str) -> None:
        self.release_send(self.resolve_send(key))

    def release_send(self, send: KeySend) -> None:
        get_backend().keyboard.release_send(send)

    def send_hotkey(self, hotkey: str) -> None:
        keys = [key.strip() for key in hotkey.split("+")]
        kb = get_backend().keyboard
        if kb.send_native_hotkey(hotkey, keys, self._resolve_layout_scan_code):
            return

        pressed: list[str] = []
        first_error: BaseException | None = None
        try:
            for key in keys:
                self.press_key(key)
                pressed.append(key)
        except BaseException as exc:
            first_error = exc
        finally:
            for key in reversed(pressed):
                try:
                    self.release_key(key)
                except BaseException as exc:
                    if first_error is None:
                        first_error = exc
        if first_error is not None:
            raise first_error

    def write_text(self, text: str) -> None:
        kb = get_backend().keyboard
        if not text:
            kb.write_text(text)
            return
        ime = get_backend().ime
        reservation = ime.disable_for_text()
        try:
            kb.write_text(text)
        finally:
            ime.restore_after_text(reservation, len(text))

    def key_identity(self, key: str) -> tuple[int, bool]:
        return self.identity_of(self.resolve_send(key))

    def identity_of(self, send: KeySend) -> tuple[int, bool]:
        return get_backend().keyboard.identity_of(send)

    def restore_ime_now(self) -> None:
        try:
            get_backend().ime.restore_ime_now()
        except Exception:
            _logger.exception("Failed to restore destination IME during shutdown")

    def validate_key_name(self, key_name: str) -> None:
        if is_numpad_key_name(key_name):
            return
        if is_reserved_numpad_name(key_name):
            raise ValueError(
                tr("infrastructure.input_gateway.reserved_numpad_name")
            )
        self.resolve_send(key_name)

    def click_mouse(self, x: int, y: int, button: str, clicks: int) -> None:
        get_backend().mouse.click_mouse(x, y, button, clicks)

    def mouse_down(
        self, button: str, x: int | None = None, y: int | None = None
    ) -> None:
        get_backend().mouse.mouse_down(button, x, y)

    def mouse_up(
        self, button: str, x: int | None = None, y: int | None = None
    ) -> None:
        get_backend().mouse.mouse_up(button, x, y)

    def drag_mouse(
        self, x: int, y: int, to_x: int, to_y: int, button: str, duration_sec: float
    ) -> None:
        get_backend().mouse.drag_mouse(x, y, to_x, to_y, button, duration_sec)
