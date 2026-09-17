from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import TYPE_CHECKING

from keyseq.presentation.pane_width_rules import (
    MIN_LIST_CHARS, MinWidths, list_row_width, side_by_side_min_width, stacked_min_width,
)

if TYPE_CHECKING:
    from keyseq.presentation.app import App


def measure_window_min_height(app: App) -> int:
    """呼び出し側で paneconfigure を適用した後のウィンドウ要求高さを測る。"""
    app.update_idletasks()
    return app.winfo_reqheight()


def measure_header_window_width(app: App) -> int:
    app.full_view.update_idletasks()
    header = app.full_view.header_area
    return header.winfo_reqwidth() + (app.winfo_width() - header.winfo_width())


def measure_min_widths(app: App) -> MinWidths:
    view = app.full_view
    view.update_idletasks()
    sequence = view.sequence_box
    buttons = sequence.run_to_end_chk.master
    chrome, title = _frame_widths(app, sequence)
    gap_parts = sequence.tk.splitlist(buttons.pack_info()["padx"])
    gap = sum(sequence.winfo_pixels(str(part)) for part in gap_parts)
    if len(gap_parts) == 1:
        gap *= 2
    return MinWidths(
        keymap=_stacked_width(app, view.keymap_box, view.keymap_box.keymap_listbox),
        trigger=_stacked_width(app, view.trigger_box, view.trigger_box.trigger_list),
        sequence=side_by_side_min_width(
            _list_row(app, sequence.action_list), buttons.winfo_reqwidth(),
            gap, chrome, title,
        ),
    )


def _stacked_width(app: App, box: ttk.LabelFrame, listing: tk.Listbox) -> int:
    chrome, title = _frame_widths(app, box)
    others = [
        child.winfo_reqwidth() for child in box.winfo_children()
        if child is not listing.master
    ]
    return stacked_min_width(_list_row(app, listing), others, chrome, title)


def _list_row(app: App, listing: tk.Listbox) -> int:
    font = tkfont.Font(root=app, font=listing.cget("font"))
    char_width = font.measure("0")
    chrome = listing.winfo_reqwidth() - char_width * int(listing.cget("width"))
    scrollbar = next(
        child for child in listing.master.winfo_children()
        if isinstance(child, ttk.Scrollbar)
    )
    return list_row_width(char_width, MIN_LIST_CHARS, chrome, scrollbar.winfo_reqwidth())


def _frame_widths(app: App, box: ttk.LabelFrame) -> tuple[int, int]:
    # 未配置の同一テーマの枠で、native theme の枠線も含めて測る。
    probe = ttk.LabelFrame(
        app, padding=box.cget("padding"), style=box.cget("style"),
    )
    try:
        # 空見出しの領域が要求幅を決めないよう、中身を十分広くして枠の分を測る。
        content = ttk.Frame(probe, width=500, height=1)
        content.pack()
        probe.update_idletasks()
        chrome = probe.winfo_reqwidth() - 500
        font = tkfont.nametofont("TkDefaultFont", root=app)
        sample = "0" * 100  # 内側余白より見出しが必ず広い状態で測定。
        content.configure(width=1)
        probe.configure(text=sample)
        probe.update_idletasks()
        # タイトル要求幅に既に含まれる枠の分は二重加算しない。
        inset = max(0, probe.winfo_reqwidth() - font.measure(sample) - chrome)
        title = font.measure(str(box.cget("text"))) + chrome + inset
        return chrome, title
    finally:
        probe.destroy()
