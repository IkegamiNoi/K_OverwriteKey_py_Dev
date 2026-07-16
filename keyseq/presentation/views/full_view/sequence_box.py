from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class SequenceBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="出力シーケンス（選択中トリガーの内容）", padding=10)

        self.action_list = tk.Listbox(self, height=18, exportselection=False)
        self.action_list.pack(side="left", fill="both", expand=True)
        self.action_list.bind("<<ListboxSelect>>", app.trigger_panel.on_action_list_select)
        self.action_list.bind("<KeyRelease>", app.trigger_panel.on_action_list_focus_index_change)
        self.action_list.bind("<Double-Button-1>", app.trigger_panel.on_action_double_click)
        asb = ttk.Scrollbar(self, orient="vertical", command=self.action_list.yview)
        asb.pack(side="left", fill="y")
        self.action_list.configure(yscrollcommand=asb.set)

        abtns = ttk.Frame(self)
        abtns.pack(side="left", fill="y", padx=(12, 0))
        ttk.Button(abtns, text="追加", width=16, command=app.trigger_panel.add_action).pack(pady=(0, 6))
        ttk.Button(abtns, text="編集", width=16, command=app.trigger_panel.edit_action).pack(pady=6)
        ttk.Button(abtns, text="削除", width=16, command=app.trigger_panel.delete_action).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="上へ", width=16, command=lambda: app.trigger_panel.move_action(-1)).pack(pady=6)
        ttk.Button(abtns, text="下へ", width=16, command=lambda: app.trigger_panel.move_action(+1)).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="保存", width=16, command=app.config_io.save_selected_sequence).pack(pady=6)
        ttk.Button(abtns, text="別名で保存", width=16, command=app.config_io.save_selected_sequence_as).pack(pady=6)
        ttk.Button(abtns, text="読込", width=16, command=app.config_io.load_sequence_file).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        # 連続実行（run_to_end）
        self.run_to_end_chk = ttk.Checkbutton(
            abtns,
            text="連続実行",
            variable=app.ui_vars.run_to_end_var,
            command=app.trigger_panel.update_run_to_end,
        )
        self.run_to_end_chk.pack(anchor="w", pady=(8, 0))

        # 連続実行 間隔（ms） ※トリガーごと / デフォルト300
        delay_line = ttk.Frame(abtns)
        delay_line.pack(fill="x", pady=(6, 0))
        ttk.Label(delay_line, text="間隔(ms)").pack(side="left")
        self.run_to_end_delay_entry = ttk.Entry(delay_line, width=8, textvariable=app.ui_vars.run_to_end_delay_var)
        self.run_to_end_delay_entry.pack(side="left", padx=(8, 0))
        # Enter / フォーカスアウトで保存
        self.run_to_end_delay_entry.bind("<Return>", app.trigger_panel.update_run_to_end_delay)
        self.run_to_end_delay_entry.bind("<FocusOut>", app.trigger_panel.update_run_to_end_delay)
