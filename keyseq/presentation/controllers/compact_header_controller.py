"""Controls the expandable sections above the compact trigger list."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from keyseq.presentation.compact_header_view import (
    COMPACT_HEADER_VIEW_KEY, parse_compact_header_view,
)

if TYPE_CHECKING:
    from tkinter import ttk
    from keyseq.presentation.app import App


class CompactHeaderController:
    def __init__(self, app: App):
        self.app = app
        self.open = parse_compact_header_view(
            app._startup_settings.get(COMPACT_HEADER_VIEW_KEY),
        )
        self._sections: dict[str, tuple[ttk.LabelFrame, ttk.Label, ttk.Label]] = {}

    def register_section(
        self, name: str, frame: ttk.LabelFrame, heading: ttk.Label,
        collapsed_heading: ttk.Label,
    ) -> None:
        self._sections[name] = (frame, heading, collapsed_heading)
        heading.configure(takefocus=True)
        heading.configure(text=f"▾ {self._title(name)}")
        heading.bind("<Button-1>", lambda _event, section=name: self.toggle(section))
        for sequence in ("<Return>", "<space>", "<KP_Enter>"):
            heading.bind(
                sequence,
                lambda event, section=name: self._toggle_from_keyboard(event, section),
            )
        collapsed_heading.configure(takefocus=True)
        collapsed_heading.configure(cursor="hand2")
        collapsed_heading.bind("<Button-1>", lambda _event, section=name: self.toggle(section))
        for sequence in ("<Return>", "<space>", "<KP_Enter>"):
            collapsed_heading.bind(
                sequence,
                lambda event, section=name: self._toggle_from_keyboard(event, section),
            )
        collapsed_heading.configure(
            text=f"▾ {self._title(name)}" if self.open[name]
            else f"▸ {self._title(name)}",
        )

    def _toggle_from_keyboard(self, _event: tk.Event, name: str) -> str:
        self.toggle(name, from_keyboard=True)
        return "break"

    def apply_initial_state(self) -> None:
        for name in ("hook", "display"):
            if not self.open[name]:
                self._show_collapsed(name)

    @staticmethod
    def _title(name: str) -> str:
        return "フック" if name == "hook" else "表示"

    def _show_collapsed(self, name: str) -> None:
        frame, _heading, collapsed = self._sections[name]
        next_sibling = self._next_sibling(frame, collapsed)
        frame.pack_forget()
        options = {"before": next_sibling} if next_sibling is not None else {}
        collapsed.pack(side="top", fill="x", expand=False, **options)
        if name == "display":
            collapsed.pack_configure(pady=(8, 0))

    def _show_expanded(self, name: str) -> None:
        frame, _heading, collapsed = self._sections[name]
        next_sibling = self._next_sibling(frame, collapsed)
        collapsed.pack_forget()
        options = {"before": next_sibling} if next_sibling is not None else {}
        pack_options = {"side": "top", "fill": "x", "expand": False, **options}
        if name == "display":
            pack_options["pady"] = (8, 0)
        frame.pack(**pack_options)

    def _next_sibling(
        self, frame: ttk.LabelFrame, collapsed: ttk.Label,
    ) -> ttk.Widget | None:
        siblings = [
            widget for widget in frame.master.pack_slaves()
            if widget not in (frame, collapsed)
        ]
        return next(
            (widget for widget in siblings if self._section_order(widget) > self._section_order(frame)),
            None,
        )

    def _section_order(self, widget) -> int:
        for order, name in enumerate(("hook", "display")):
            frame, _heading, collapsed = self._sections[name]
            if widget in (frame, collapsed):
                return order
        return 2

    def toggle(self, name: str, *, from_keyboard: bool = False) -> None:
        frame, heading, collapsed = self._sections[name]
        self.open[name] = not self.open[name]
        heading.configure(text=f"▾ {self._title(name)}")
        collapsed.configure(
            text=f"▾ {self._title(name)}" if self.open[name]
            else f"▸ {self._title(name)}",
        )
        if self.open[name]:
            self._show_expanded(name)
        else:
            try:
                focus = frame.focus_get()
            except (tk.TclError, KeyError):
                focus = None
            if focus is frame or (focus is not None and str(focus).startswith(f"{frame}.")):
                self.app.compact_view.trigger_box.trigger_list.focus_set()
            self._show_collapsed(name)
        if from_keyboard:
            (heading if self.open[name] else collapsed).focus_set()
        self.app.compact_window.refresh_minimum_height()
        self.app.startup_io.write_startup({
            COMPACT_HEADER_VIEW_KEY: dict(self.open),
        })
