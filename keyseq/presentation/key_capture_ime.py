from __future__ import annotations

import tkinter
from dataclasses import dataclass
from typing import Callable

from keyseq.infrastructure import own_ime_status


GetOpen = Callable[[int], bool | None]
SetOpen = Callable[[int, bool], bool]


@dataclass
class _CaptureBinding:
    window: object
    funcid: str


class KeyCaptureImeTracker:
    def __init__(
        self,
        get_open: GetOpen = own_ime_status.get_open_status,
        set_open: SetOpen = own_ime_status.set_open_status,
    ) -> None:
        self._get_open = get_open
        self._set_open = set_open
        self._owners: dict[object, _CaptureBinding] = {}
        self._turned_off_by_app = False
        self._hwnd: int | None = None

    def begin(self, owner: object, window: object) -> None:
        if owner in self._owners:
            return
        root = window.nametowidget(".")
        hwnd = int(root.winfo_id())
        self._hwnd = hwnd
        if self._get_open(hwnd) is True and self._set_open(hwnd, False):
            self._turned_off_by_app = True

        def on_destroy(event: object) -> None:
            if getattr(event, "widget", None) is window:
                self.end(owner)

        funcid = window.bind("<Destroy>", on_destroy, "+")
        self._owners[owner] = _CaptureBinding(window, funcid)

    def end(self, owner: object) -> None:
        binding = self._owners.pop(owner, None)
        if binding is None:
            return
        try:
            binding.window.unbind("<Destroy>", binding.funcid)
        except tkinter.TclError:
            pass
        if self._owners or not self._turned_off_by_app:
            return
        if self._hwnd is not None and self._get_open(self._hwnd) is False:
            self._set_open(self._hwnd, True)
        self._turned_off_by_app = False

    def is_capturing(self, owner: object) -> bool:
        return owner in self._owners


_default_tracker: KeyCaptureImeTracker | None = None


def _get_tracker() -> KeyCaptureImeTracker:
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = KeyCaptureImeTracker()
    return _default_tracker


def begin_key_capture(owner: object, window: object) -> None:
    _get_tracker().begin(owner, window)


def end_key_capture(owner: object) -> None:
    _get_tracker().end(owner)
