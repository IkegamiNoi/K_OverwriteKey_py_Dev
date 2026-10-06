"""省略表示のシーケンス欄の Widget。"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height


class CompactSequenceFrame:
    def __init__(self, parent, pane_parent, on_heading_click, *, on_press,
                 on_release, on_key, on_ignore):
        self.heading = ttk.Label(parent, text="", anchor="w", cursor="hand2")
        self.heading.bind("<Button-1>", lambda _event: on_heading_click())
        self.set_heading(False)
        self.body = ttk.Frame(pane_parent)
        self.content = ttk.Frame(self.body)
        self.content.pack(fill="both", expand=True)
        self.action_list = tk.Listbox(
            self.content, height=3, width=1, exportselection=False, selectmode="browse",
        )
        self.scrollbar = ttk.Scrollbar(
            self.content, orient="vertical", command=self.action_list.yview,
        )
        self.action_list.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.action_list.pack(side="left", fill="both", expand=True)
        self.action_list.bind("<Button-1>", on_press)
        self.action_list.bind("<ButtonRelease-1>", on_release)
        for key in ("Up", "Down", "Prior", "Next", "Home", "End"):
            self.action_list.bind(f"<KeyPress-{key}>", on_key)
        for event in (
            "<B1-Motion>", "<Double-Button-1>", "<Control-c>", "<Control-C>",
            "<Control-v>", "<Control-V>", "<Delete>",
        ):
            self.action_list.bind(event, on_ignore)

    def set_heading(self, is_open: bool) -> None:
        self.heading.configure(text="▾ シーケンス" if is_open else "▸ シーケンス")

    def show_heading_in_body(self) -> None:
        self.heading.pack(in_=self.body, side="top", fill="x", before=self.content)
        self.heading.lift()

    def show_heading_at(self, parent) -> None:
        siblings = [widget for widget in parent.pack_slaves() if widget != self.heading]
        options = {"before": siblings[0]} if siblings else {}
        self.heading.pack(in_=parent, side="bottom", fill="x", **options)
        self.heading.lift()

    def minimum_body_height(self) -> int:
        return list_minimum_height(self.action_list)
