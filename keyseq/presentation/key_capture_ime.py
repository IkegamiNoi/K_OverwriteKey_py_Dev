from __future__ import annotations

import logging
import tkinter
from dataclasses import dataclass
from typing import Callable, Protocol

from keyseq.infrastructure import own_ime_status


GetOpen = Callable[[int], bool | None]
SetOpen = Callable[[int, bool], bool]


class CaptureHook(Protocol):
    def activate(self) -> None:
        ...

    def deactivate(self) -> None:
        ...

    def shutdown(self) -> None:
        ...


@dataclass
class _CaptureBinding:
    window: object
    funcid: str
    on_hook_key: Callable[[str], None] | None


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
        self._generation = 0
        self._capture_hook: CaptureHook | None = None
        self._logger = logging.getLogger(__name__)

    def begin(
        self,
        owner: object,
        window: object,
        on_hook_key: Callable[[str], None] | None = None,
    ) -> None:
        self._generation += 1
        if owner in self._owners:
            binding = self._owners.pop(owner)
            binding.on_hook_key = on_hook_key if on_hook_key is not None else binding.on_hook_key
            self._owners[owner] = binding
            return
        was_empty = not self._owners
        root = window.nametowidget(".")
        hwnd = int(root.winfo_id())
        self._hwnd = hwnd
        if self._get_open(hwnd) is True and self._set_open(hwnd, False):
            self._turned_off_by_app = True

        def on_destroy(event: object) -> None:
            if getattr(event, "widget", None) is window:
                self.end(owner)

        funcid = window.bind("<Destroy>", on_destroy, "+")
        self._owners[owner] = _CaptureBinding(window, funcid, on_hook_key)
        if was_empty and self._capture_hook is not None:
            try:
                self._capture_hook.activate()
            except Exception:
                self._logger.exception("Could not activate key capture hook")

    def end(self, owner: object) -> None:
        binding = self._owners.pop(owner, None)
        if binding is None:
            return
        self._generation += 1
        try:
            binding.window.unbind("<Destroy>", binding.funcid)
        except tkinter.TclError:
            pass
        if self._owners:
            return
        if self._capture_hook is not None:
            try:
                self._capture_hook.deactivate()
            except Exception:
                self._logger.exception("Could not deactivate key capture hook")
        if not self._turned_off_by_app:
            return
        if self._hwnd is not None and self._get_open(self._hwnd) is False:
            self._set_open(self._hwnd, True)
        self._turned_off_by_app = False

    def is_capturing(self, owner: object) -> bool:
        return owner in self._owners

    @property
    def generation(self) -> int:
        return self._generation

    def set_capture_hook(self, hook: CaptureHook | None) -> None:
        self._capture_hook = hook

    def shutdown_capture_hook(self) -> None:
        if self._capture_hook is not None:
            self._capture_hook.shutdown()

    def deliver(self, name: str, generation: int) -> None:
        if generation != self._generation:
            return
        focused_toplevel = self._focused_toplevel()
        if focused_toplevel is None:
            return
        self._deliver_to_matching_owner(name, focused_toplevel)

    def _focused_toplevel(self) -> object | None:
        focused_window = None
        for binding in self._owners.values():
            try:
                focused_window = binding.window.focus_get()
            except Exception:
                self._logger.exception("Could not get focused capture widget")
                return
            if focused_window is not None:
                break
        if focused_window is None:
            return
        try:
            return focused_window.winfo_toplevel()
        except Exception:
            self._logger.exception("Could not resolve focused capture window")
            return None

    def _deliver_to_matching_owner(self, name: str, focused_toplevel: object) -> None:
        for binding in reversed(tuple(self._owners.values())):
            try:
                matches = binding.window.winfo_toplevel() is focused_toplevel
            except Exception:
                self._logger.exception("Could not resolve capture owner window")
                continue
            if matches and binding.on_hook_key is not None:
                try:
                    binding.on_hook_key(name)
                except Exception:
                    self._logger.exception("Capture key handler failed")
                return


_default_tracker: KeyCaptureImeTracker | None = None


def _get_tracker() -> KeyCaptureImeTracker:
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = KeyCaptureImeTracker()
    return _default_tracker


def begin_key_capture(
    owner: object,
    window: object,
    on_hook_key: Callable[[str], None] | None = None,
) -> None:
    _get_tracker().begin(owner, window, on_hook_key)


def end_key_capture(owner: object) -> None:
    _get_tracker().end(owner)


def configure_capture_hook(hook: CaptureHook | None) -> None:
    _get_tracker().set_capture_hook(hook)


def capture_key_generation() -> int:
    return _get_tracker().generation


def deliver_captured_key(name: str, generation: int) -> None:
    _get_tracker().deliver(name, generation)


def shutdown_capture_hook() -> None:
    _get_tracker().shutdown_capture_hook()
