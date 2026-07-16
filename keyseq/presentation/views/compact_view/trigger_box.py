from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class CompactTriggerBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="トリガー一覧", padding=10)

        tl_frame = ttk.Frame(self)
        tl_frame.pack(side="top", fill="both", expand=True)
        self.trigger_list = tk.Listbox(tl_frame, height=16, width=26, exportselection=False)
        self.trigger_list.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tl_frame, orient="vertical", command=self.trigger_list.yview)
        sb.pack(side="left", fill="y")
        self.trigger_list.configure(yscrollcommand=sb.set)
        self.trigger_list.bind("<<ListboxSelect>>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<KeyRelease>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<Double-Button-1>", app.trigger_panel.on_trigger_double_click)
