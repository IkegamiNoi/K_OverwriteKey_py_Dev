from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import TYPE_CHECKING

from keyseq.presentation.pane_width_rules import (
    MIN_LIST_CHARS, SASH_WIDTH, MinWidths, default_pane_widths, list_row_width,
    side_by_side_min_width, stacked_min_width,
)

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class PaneLayoutController:
    """フル表示の最小幅を測定し、初回表示の既定幅を設定する。"""

    def __init__(self, app: App) -> None:
        self.app = app
        self._installed = False
        self._applied = False

    def install(self) -> None:
        if not self._installed:
            self.app.full_view.panes.bind("<Configure>", self._on_configure, add="+")
            self._installed = True

    def _on_configure(self, event: tk.Event) -> None:
        if event.width > 1 and not self._applied:
            # 測定中の update_idletasks による Configure の再入も防ぐ。
            self._applied = True
            self.apply_default_widths()

    def measure_min_widths(self) -> MinWidths:
        view = self.app.full_view
        view.update_idletasks()
        sequence = view.sequence_box
        buttons = sequence.run_to_end_chk.master
        chrome, title = self._frame_widths(sequence)
        gap_parts = sequence.tk.splitlist(buttons.pack_info()["padx"])
        gap = sum(sequence.winfo_pixels(str(part)) for part in gap_parts)
        if len(gap_parts) == 1:
            gap *= 2
        return MinWidths(
            keymap=self._stacked_width(view.keymap_box, view.keymap_box.keymap_listbox),
            trigger=self._stacked_width(view.trigger_box, view.trigger_box.trigger_list),
            sequence=side_by_side_min_width(
                self._list_row(sequence.action_list), buttons.winfo_reqwidth(),
                gap, chrome, title,
            ),
        )

    def _stacked_width(self, box: ttk.LabelFrame, listing: tk.Listbox) -> int:
        chrome, title = self._frame_widths(box)
        others = [
            child.winfo_reqwidth() for child in box.winfo_children()
            if child is not listing.master
        ]
        return stacked_min_width(self._list_row(listing), others, chrome, title)

    def _list_row(self, listing: tk.Listbox) -> int:
        font = tkfont.Font(root=self.app, font=listing.cget("font"))
        char_width = font.measure("0")
        chrome = listing.winfo_reqwidth() - char_width * int(listing.cget("width"))
        scrollbar = next(
            child for child in listing.master.winfo_children()
            if isinstance(child, ttk.Scrollbar)
        )
        return list_row_width(char_width, MIN_LIST_CHARS, chrome, scrollbar.winfo_reqwidth())

    def _frame_widths(self, box: ttk.LabelFrame) -> tuple[int, int]:
        # 未配置の同一テーマの枠で、native theme の枠線も含めて測る。
        probe = ttk.LabelFrame(
            self.app, padding=box.cget("padding"), style=box.cget("style"),
        )
        try:
            # 空見出しの領域が要求幅を決めないよう、中身を十分広くして枠の分を測る。
            content = ttk.Frame(probe, width=500, height=1)
            content.pack()
            probe.update_idletasks()
            chrome = probe.winfo_reqwidth() - 500
            font = tkfont.nametofont("TkDefaultFont", root=self.app)
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

    def apply_default_widths(self) -> None:
        view = self.app.full_view
        panes = view.panes
        mins = self.measure_min_widths()
        widths = default_pane_widths(
            main_width=panes.winfo_width(), keymap_req=view.keymap_box.winfo_reqwidth(),
            trigger_req=view.trigger_box.winfo_reqwidth(), sash_total=2 * SASH_WIDTH,
            mins=mins,
        )
        panes.paneconfigure(view.keymap_box, minsize=mins.keymap, width=widths.keymap)
        panes.paneconfigure(view.trigger_box, minsize=mins.trigger)
        panes.paneconfigure(view.sequence_box, minsize=mins.sequence, width=widths.sequence)
