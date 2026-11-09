from __future__ import annotations

import logging

from keyseq.infrastructure.os_backend.contracts import Capabilities, ImeBackend, OsBackend
from keyseq.infrastructure.os_backend.windows import ime_control, own_ime_status

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


def create_backend() -> OsBackend:
    return OsBackend(Capabilities(True, True, True, True), WindowsImeBackend())
