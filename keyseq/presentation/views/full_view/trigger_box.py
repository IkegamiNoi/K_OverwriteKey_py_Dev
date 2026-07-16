from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FullTriggerBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="トリガー一覧（選択して編集）", padding=10)

        # トリガー一覧（スクロール）
        tl_frame = ttk.Frame(self)
        tl_frame.pack(side="top", fill="y", expand=False)
        self.trigger_list = tk.Listbox(tl_frame, height=12, width=26, exportselection=False)
        self.trigger_list.pack(side="left", fill="y", expand=False)
        sb = ttk.Scrollbar(tl_frame, orient="vertical", command=self.trigger_list.yview)
        sb.pack(side="left", fill="y")
        self.trigger_list.configure(yscrollcommand=sb.set)
        self.trigger_list.bind("<<ListboxSelect>>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<KeyRelease>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<Double-Button-1>", app.trigger_panel.on_trigger_double_click)

        tbtns = ttk.Frame(self)
        tbtns.pack(fill="x", pady=(6, 0))
        ttk.Button(tbtns, text="追加", command=app.trigger_panel.add_trigger).pack(fill="x", pady=(0, 3))
        ttk.Button(tbtns, text="トリガー変更", command=app.trigger_panel.rename_trigger).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="削除", command=app.trigger_panel.delete_trigger).pack(fill="x", pady=3)
        ttk.Separator(tbtns).pack(fill="x", pady=6)
        ttk.Button(tbtns, text="保存", command=app.config_io.save_trigger_set_file).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="別名で保存", command=app.config_io.save_trigger_set_file_as).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="読込", command=app.config_io.load_trigger_set_file).pack(fill="x", pady=3)

        app.suppress_chk = ttk.Checkbutton(
            self,
            text="トリガーキーを抑止（suppress）",
            variable=app.ui_vars.suppress_var,
            command=app.trigger_panel.update_suppress,
        )
        app.suppress_chk.pack(anchor="w", pady=(6, 0))
