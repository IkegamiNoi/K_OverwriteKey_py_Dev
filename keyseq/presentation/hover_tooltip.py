"""Shared hover tooltip for presentation widgets."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class HoverTooltip:
    """Show and refresh a tooltip while the pointer is over a widget."""

    def __init__(
        self,
        widget: tk.Widget,
        text: Callable[[], str],
        should_show: Callable[[], bool],
    ) -> None:
        self._widget = widget
        self._text = text
        self._should_show = should_show
        self._window: tk.Toplevel | None = None
        self._label: ttk.Label | None = None
        self._hovered = False
        self._last_mouse_position: tuple[int, int] | None = None

    def show(self, event) -> None:
        self._hovered = True
        self._remember_mouse_position(event)
        self._show_at_last_position()

    def _remember_mouse_position(self, event) -> None:
        self._last_mouse_position = (event.x_root, event.y_root)

    def _show_at_last_position(self) -> None:
        self.close()
        if self._last_mouse_position is None or not self._should_show():
            return
        text = self._text()
        if not text:
            return
        try:
            window = tk.Toplevel(self._widget)
            self._window = window
            window.overrideredirect(True)
            x, y = self._last_mouse_position
            window.geometry(f"+{x + 12}+{y + 12}")
            try:
                window.wm_attributes("-topmost", True)
            except Exception:
                pass
            label = ttk.Label(window, text=text, padding=4, justify="left")
            self._label = label
            label.pack()
        except Exception:
            self.close()

    def motion(self, event) -> None:
        # 位置は覚えるだけ（出している窓は動かさない）。乗せたまま後から出すときに使う。
        if self._hovered:
            self._remember_mouse_position(event)

    def leave(self, _event=None) -> None:
        self._hovered = False
        self.close()

    def button(self, _event=None) -> None:
        self._hovered = False
        self.close()

    def destroy(self, _event=None) -> None:
        self._hovered = False
        self.close()

    def close(self, _event=None) -> None:
        window = self._window
        self._window = None
        self._label = None
        if window is None:
            return
        try:
            window.destroy()
        except Exception:
            pass

    def refresh(self) -> None:
        """Update a visible tooltip or show one when truncation starts on hover."""
        if self._window is None and not self._hovered:
            return
        if not self._should_show():
            self.close()
            return
        text = self._text()
        if not text:
            self.close()
            return
        if self._window is None:
            self._show_at_last_position()
            return
        try:
            if self._label is not None:
                self._label.configure(text=text)
        except Exception:
            self.close()


def bind_hover_tooltip(
    widget: tk.Widget,
    text: Callable[[], str],
    should_show: Callable[[], bool],
) -> HoverTooltip:
    """Bind a dynamic tooltip to a widget and return its refresh handle."""
    tooltip = HoverTooltip(widget, text, should_show)
    try:
        widget.bind("<Enter>", tooltip.show)
        widget.bind("<Motion>", tooltip.motion, add="+")
        widget.bind("<Leave>", tooltip.leave)
        widget.bind("<Button>", tooltip.button)
        widget.bind("<Destroy>", tooltip.destroy, add="+")
    except Exception:
        tooltip.close()
    return tooltip
