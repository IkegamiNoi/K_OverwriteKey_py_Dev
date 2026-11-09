from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter


class ImeBackend(Protocol):
    def disable_for_text(self) -> object | None: ...
    def restore_after_text(self, reservation: object | None, character_count: int) -> None: ...
    def restore_ime_now(self) -> None: ...
    def get_own_open_status(self, window: tkinter.Misc) -> bool | None: ...
    def set_own_open_status(self, window: tkinter.Misc, is_open: bool) -> bool: ...


@dataclass(frozen=True)
class Capabilities:
    click_through_window: bool
    window_stacking: bool
    status_icon: bool
    ime_control: bool


@dataclass(frozen=True)
class OsBackend:
    capabilities: Capabilities
    ime: ImeBackend
