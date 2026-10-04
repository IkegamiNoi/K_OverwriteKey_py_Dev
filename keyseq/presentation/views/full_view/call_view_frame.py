"""呼び出し先の読み取り専用 Widget。"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class CallViewFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.heading = ttk.Label(self, text="", anchor="w")
        self.heading.pack(fill="x")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.action_list = tk.Listbox(
            body, height=3, width=1, exportselection=False, takefocus=False,
            activestyle="none", selectborderwidth=0,
        )
        self.action_list.configure(
            selectbackground=self.action_list.cget("background"),
            selectforeground=self.action_list.cget("foreground"),
        )
        self.scrollbar = ttk.Scrollbar(
            body, orient="vertical", command=self.action_list.yview,
        )
        self.action_list.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.action_list.pack(side="left", fill="both", expand=True)
        for event in (
            "<Button-1>", "<Double-Button-1>", "<B1-Motion>",
            "<ButtonRelease-1>", "<Button-2>", "<B2-Motion>",
            "<ButtonRelease-2>", "<Button-3>", "<KeyPress>", "<KeyRelease>",
        ):
            self.action_list.bind(event, self._ignore)

    @staticmethod
    def _ignore(_event):
        return "break"

    def minimum_height(self) -> int:
        return self.heading.winfo_reqheight() + list_minimum_height(self.action_list)


def list_minimum_height(listing: tk.Listbox) -> int:
    """現在のフォントで 3 行と Listbox の枠線分を測る。"""
    chrome = 2 * sum(
        listing.winfo_pixels(str(listing.cget(option)))
        for option in ("borderwidth", "highlightthickness")
    )
    rows = max(1, int(listing.cget("height")))
    row_height = (listing.winfo_reqheight() - chrome) // rows
    return 3 * row_height + chrome
