from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable


class VerticalScrollArea(ttk.Frame):
    """A vertically scrollable content frame whose requested size follows its content."""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._measure_pending = False
        self._measuring = False
        self._remeasure_requested = False
        self.scrollbar_shown = False
        self._last_window_size: tuple[int, int] | None = None
        self._last_scrollregion: tuple[int, int, int, int] | None = None
        self._last_measured_size: tuple[int, int, int, int] | None = None

        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.scrollbar.grid_remove()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content = ttk.Frame(self.canvas)
        self._content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw",
        )
        self.canvas.bind("<Configure>", self._on_canvas_configure, add="+")
        self.content.bind("<Configure>", self._on_content_configure, add="+")
        self.bind("<<ThemeChanged>>", self._on_theme_changed, add="+")

    def bind_wheel(self, skip: Iterable[tk.Widget] = ()) -> None:
        skipped = {str(widget) for widget in skip}

        def bind_tree(widget: tk.Widget) -> None:
            if str(widget) in skipped:
                return
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
            for child in widget.winfo_children():
                bind_tree(child)

        bind_tree(self)

    def sync(self) -> None:
        """Synchronize requested dimensions and the canvas window immediately."""
        self._measure_scroll_area()

    def _on_mousewheel(self, event: tk.Event) -> str:
        if self.scrollbar_shown:
            units = int(-event.delta / 120) or (-1 if event.delta > 0 else 1)
            self.canvas.yview_scroll(units, "units")
        return "break"

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        self._request_measurement()

    def _on_content_configure(self, _event: tk.Event) -> None:
        self._request_measurement()

    def _request_measurement(self) -> None:
        if self._measuring:
            self._remeasure_requested = True
        else:
            self._schedule_measurement()

    def _on_theme_changed(self, _event: tk.Event) -> None:
        self._schedule_measurement()

    def _schedule_measurement(self) -> None:
        if self._measure_pending or self._measuring:
            return
        self._measure_pending = True
        self.after_idle(self._measure_scroll_area)

    def _measure_scroll_area(self) -> None:
        self._measure_pending = False
        if self._measuring or not self.winfo_exists():
            return
        self._measuring = True
        self._remeasure_requested = False
        previous_size = self._last_measured_size
        try:
            self.content.update_idletasks()
            content_width = self.content.winfo_reqwidth()
            content_height = self.content.winfo_reqheight()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if int(self.canvas.cget("width")) != content_width:
                self.canvas.configure(width=content_width)
            if int(self.canvas.cget("height")) != content_height:
                self.canvas.configure(height=content_height)

            # The content request can be measured before the pane is placed. In
            # that state the Canvas's default actual height is not usable.
            self.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            show_scrollbar = (
                self.canvas.winfo_ismapped()
                and canvas_height > 1
                and content_height > canvas_height
            )
            if self.scrollbar_shown != show_scrollbar:
                self.scrollbar_shown = show_scrollbar
                if show_scrollbar:
                    self.scrollbar.grid()
                else:
                    self.canvas.yview_moveto(0)
                    self.scrollbar.grid_remove()
                self.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

            window_size = (canvas_width, max(canvas_height, content_height))
            if window_size != self._last_window_size:
                self.canvas.itemconfigure(
                    self._content_window, width=window_size[0], height=window_size[1],
                )
                self._last_window_size = window_size
            scrollregion = (0, 0, window_size[0], window_size[1])
            if scrollregion != self._last_scrollregion:
                self.canvas.configure(scrollregion=scrollregion)
                self._last_scrollregion = scrollregion
            # pane_layout reads the LabelFrame request immediately after sync().
            self.master.update_idletasks()
            measured_size = (
                self.canvas.winfo_width(),
                self.canvas.winfo_height(),
                self.content.winfo_reqwidth(),
                self.content.winfo_reqheight(),
            )
            self._last_measured_size = measured_size
        finally:
            self._measuring = False
        if (
            self._remeasure_requested
            and measured_size != previous_size
            and self.winfo_exists()
        ):
            self._schedule_measurement()
