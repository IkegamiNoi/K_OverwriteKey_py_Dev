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

    def show(self, event) -> None:
        self.close()
        if not self._should_show():
            return
        text = self._text()
        if not text:
            return
        try:
            window = tk.Toplevel(self._widget)
            self._window = window
            window.overrideredirect(True)
            window.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
            label = ttk.Label(window, text=text, padding=4, justify="left")
            self._label = label
            label.pack()
        except Exception:
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
        """Update a visible tooltip or close it when it no longer applies."""
        if self._window is None:
            return
        if not self._should_show():
            self.close()
            return
        text = self._text()
        if not text:
            self.close()
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
        widget.bind("<Leave>", tooltip.close)
        widget.bind("<Button>", tooltip.close)
        widget.bind("<Destroy>", tooltip.close, add="+")
    except Exception:
        tooltip.close()
    return tooltip
