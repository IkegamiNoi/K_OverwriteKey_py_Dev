"""呼び出し先の読み取り専用 Widget。"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class CallViewFrame:
    def __init__(self, parent, pane_parent, on_heading_click):
        self.heading = ttk.Label(parent, text="", anchor="w", cursor="hand2")
        self.heading.pack(fill="x")
        self.heading.bind("<Button-1>", lambda _event: on_heading_click())
        self.set_heading(False)
        self.body = ttk.Frame(pane_parent)
        self.content = ttk.Frame(self.body)
        self.content.pack(fill="both", expand=True)
        self.action_list = tk.Listbox(
            self.content, height=3, width=1, exportselection=False, takefocus=False,
            activestyle="none", selectborderwidth=0,
        )
        self.action_list.configure(
            selectbackground=self.action_list.cget("background"),
            selectforeground=self.action_list.cget("foreground"),
        )
        self.scrollbar = ttk.Scrollbar(
            self.content, orient="vertical", command=self.action_list.yview,
        )
        self.action_list.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.action_list.pack(side="left", fill="both", expand=True)
        self.set_empty_state()
        for event in (
            "<Button-1>", "<Double-Button-1>", "<B1-Motion>",
            "<ButtonRelease-1>", "<Button-2>", "<B2-Motion>",
            "<ButtonRelease-2>", "<Button-3>", "<KeyPress>", "<KeyRelease>",
        ):
            self.action_list.bind(event, self._ignore)

    @staticmethod
    def _ignore(_event):
        return "break"

    def minimum_body_height(self) -> int:
        return list_minimum_height(self.action_list)

    def show_heading_in_body(self) -> None:
        self.heading.pack(
            in_=self.body, side="top", fill="x", before=self.content,
        )
        self.heading.lift()

    def show_heading_below_list(self, parent) -> None:
        # 一覧より先に pack して下端に置き、窓が低くても見出しの高さを先に確保する。
        others = [slave for slave in parent.pack_slaves() if slave is not self.heading]
        before = {"before": others[0]} if others else {}
        self.heading.pack(in_=parent, side="bottom", fill="x", **before)

    def set_heading(self, is_open: bool, path: tuple[str, ...] = ()) -> None:
        if not is_open:
            text = "▸ 呼び出し先"
        else:
            text = "▾ 呼び出し先" + (f"　{' › '.join(path)}" if path else "")
        self.heading.configure(text=text)

    def set_empty_state(self) -> None:
        self.action_list.delete(0, tk.END)
        self.action_list.insert(tk.END, "呼び出し中ではありません")


def list_minimum_height(listing: tk.Listbox) -> int:
    """現在のフォントで 3 行と Listbox の枠線分を測る。"""
    chrome = 2 * sum(
        listing.winfo_pixels(str(listing.cget(option)))
        for option in ("borderwidth", "highlightthickness")
    )
    rows = max(1, int(listing.cget("height")))
    row_height = (listing.winfo_reqheight() - chrome) // rows
    return 3 * row_height + chrome
