from __future__ import annotations

import tkinter as tk
from math import ceil
from tkinter import font as tkfont, ttk
from typing import TYPE_CHECKING

from keyseq.presentation.pane_width_rules import (
    MIN_LIST_CHARS, MinWidths, list_row_width, side_by_side_min_width, stacked_min_width,
)

if TYPE_CHECKING:
    from keyseq.presentation.app import App


def measure_window_min_height(app: App) -> int:
    """メイン領域の半分を下限にし、一時メッセージは 1 行分として測る。"""
    _sync_full_view_scroll_areas(app)
    app.update_idletasks()
    height = app.winfo_reqheight()
    label = _find_flash_message_label(app)
    other_heights = [] if label is None else [
        child.winfo_reqheight() for child in label.master.winfo_children()
        if isinstance(child, ttk.Label) and child is not label
    ]
    if other_heights:
        height -= max(0, label.winfo_reqheight() - max(other_heights))
    return height - app.full_view.panes.winfo_reqheight() + ceil(
        measure_main_area_basis_height(app) / 2
    )


def measure_main_area_basis_height(app: App) -> int:
    """3 枠の飾りと中身の要求高さからメイン領域の基準高さ H を測る。"""
    _sync_full_view_scroll_areas(app)
    app.update_idletasks()
    return max(
        box.winfo_reqheight() - box.scroll_area.winfo_reqheight()
        + box.scroll_area.content.winfo_reqheight()
        for box in _full_view_boxes(app)
    )


def _full_view_boxes(app: App) -> tuple[ttk.LabelFrame, ttk.LabelFrame, ttk.LabelFrame]:
    view = app.full_view
    return view.keymap_box, view.trigger_box, view.sequence_box


def _find_flash_message_label(app: App) -> ttk.Label | None:
    variable = str(app.ui_vars.flash_message_var)
    pending = list(app.winfo_children())
    while pending:
        widget = pending.pop()
        if isinstance(widget, ttk.Label) and str(widget.cget("textvariable")) == variable:
            return widget
        pending.extend(widget.winfo_children())
    return None


def measure_header_window_width(app: App) -> int:
    app.full_view.update_idletasks()
    header = app.full_view.header_area
    return header.winfo_reqwidth() + (app.winfo_width() - header.winfo_width())


def measure_min_widths(app: App) -> MinWidths:
    _sync_full_view_scroll_areas(app)
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
        keymap=(
            _stacked_width(app, view.keymap_box, view.keymap_box.keymap_listbox)
            + view.keymap_box.scroll_area.scrollbar.winfo_reqwidth()
        ),
        trigger=(
            _stacked_width(app, view.trigger_box, view.trigger_box.trigger_list)
            + view.trigger_box.scroll_area.scrollbar.winfo_reqwidth()
        ),
        sequence=side_by_side_min_width(
            _list_row(app, sequence.action_list), buttons.winfo_reqwidth(),
            gap, chrome, title,
        ) + sequence.scroll_area.scrollbar.winfo_reqwidth(),
    )


def _stacked_width(app: App, box: ttk.LabelFrame, listing: tk.Listbox) -> int:
    chrome, title = _frame_widths(app, box)
    others = [
        child.winfo_reqwidth() for child in box.scroll_area.content.winfo_children()
        if child is not listing.master
    ]
    return stacked_min_width(_list_row(app, listing), others, chrome, title)


def _sync_full_view_scroll_areas(app: App) -> None:
    for box in _full_view_boxes(app):
        box.scroll_area.sync()


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
