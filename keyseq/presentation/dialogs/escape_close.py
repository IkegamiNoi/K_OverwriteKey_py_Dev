from __future__ import annotations

import tkinter as tk
from typing import Callable


def bind_escape_close(
    window: tk.Toplevel, *, is_busy: Callable[[], bool], stop: Callable[[], None]
) -> None:
    """Escape で閉じる。is_busy() の間は stop() を優先し、その Esc を離すまでは閉じない。"""
    held = False

    def on_escape(_event):
        nonlocal held
        if is_busy():
            stop()
            held = True
            return "break"
        if held:
            return "break"
        window.destroy()

    def on_release(_event):
        nonlocal held
        held = False

    window.bind("<Escape>", on_escape)
    window.bind("<KeyRelease-Escape>", on_release)
