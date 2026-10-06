from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from keyseq.presentation.listbox_utils import bind_listbox_click_selection_sync
from keyseq.presentation.views.full_view.call_view_frame import CallViewFrame
from keyseq.presentation.views.compact_view.sequence_frame import CompactSequenceFrame


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class CompactTriggerBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="トリガー一覧", padding=10)

        self._build_panes()
        tl_frame = self.trigger_frame
        self.trigger_list = tk.Listbox(tl_frame, height=16, width=26, exportselection=False)
        self.trigger_list.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tl_frame, orient="vertical", command=self.trigger_list.yview)
        sb.pack(side="left", fill="y")
        self.trigger_list.configure(yscrollcommand=sb.set)
        self.trigger_panes.add(tl_frame, stretch="always", padx=0, pady=0)
        self.trigger_panes.pack(side="top", fill="both", expand=True)
        self.call_view_frame = CallViewFrame(
            self.call_view_column, self.trigger_panes, lambda: app.call_view.on_heading_click(),
        )
        controller = app.compact_sequence
        self.sequence_frame = CompactSequenceFrame(
            self.call_view_column, self.trigger_panes, controller.on_heading_click,
            on_press=controller.on_press, on_release=controller.on_release,
            on_key=controller.on_key, on_ignore=controller.ignore,
        )
        self.sequence_frame.show_heading_at(tl_frame)
        controller.register_frame(self.sequence_frame)
        self.trigger_list.bind("<<ListboxSelect>>", app.trigger_panel.on_trigger_list_select)
        self.trigger_list.bind("<KeyRelease>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<Double-Button-1>", app.trigger_panel.on_trigger_double_click)
        bind_listbox_click_selection_sync(
            self.trigger_list, app.trigger_panel.on_trigger_list_mouse_release
        )
        app.trigger_panel.register_trigger_list(self.trigger_list)

    def _build_panes(self) -> None:
        self.call_view_column = ttk.Frame(self)
        self.call_view_column.pack(side="top", fill="both", expand=True)
        self.trigger_panes = tk.PanedWindow(
            self.call_view_column, orient="vertical", borderwidth=0, sashwidth=4,
            sashpad=0, showhandle=False, sashrelief="flat", background="#E8E8E8",
        )
        self.trigger_frame = ttk.Frame(self.trigger_panes)
