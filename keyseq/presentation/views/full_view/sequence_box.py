from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from keyseq.presentation.listbox_range_drag import bind_listbox_range_drag
from keyseq.presentation.pane_width_rules import MIN_LIST_CHARS
from keyseq.presentation.views.full_view.call_view_frame import CallViewFrame


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class SequenceBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="出力シーケンス（選択中トリガーの内容）", padding=10)

        # 既定18行の半分をフル表示の最小高さの基準にする（表示行数は伸びた分で決まる）。
        self.action_column = ttk.Frame(self)
        self.action_column.pack(side="left", fill="both", expand=True)
        self.action_panes = tk.PanedWindow(
            self.action_column, orient="vertical", borderwidth=0, sashwidth=4,
            sashpad=0, showhandle=False, sashrelief="flat", background="#E8E8E8",
        )
        self.action_frame = ttk.Frame(self.action_panes)
        # 包む PanedWindow の要求幅も、幅計測の 10 文字 + スクロールバーに揃える。
        self.action_list = tk.Listbox(
            self.action_frame, height=9, width=MIN_LIST_CHARS, exportselection=False,
        )
        self.action_list.bind("<<ListboxSelect>>", app.trigger_panel.on_action_list_select)
        self.action_list.bind("<KeyRelease>", app.trigger_panel.on_action_list_focus_index_change)
        self.action_list.bind("<Double-Button-1>", app.trigger_panel.on_action_double_click)
        self.action_list.bind("<Control-c>", app.trigger_panel.copy_actions)
        self.action_list.bind("<Control-C>", app.trigger_panel.copy_actions)
        self.action_list.bind("<Control-v>", app.trigger_panel.paste_actions)
        self.action_list.bind("<Control-V>", app.trigger_panel.paste_actions)
        self.action_range_drag = bind_listbox_range_drag(
            self.action_list,
            on_move=app.trigger_panel.on_action_list_move,
            on_commit=app.trigger_panel.on_action_list_mouse_release,
        )
        asb = ttk.Scrollbar(self.action_frame, orient="vertical", command=self.action_list.yview)
        self.action_list.configure(yscrollcommand=asb.set)

        abtns = ttk.Frame(self)
        abtns.pack(side="right", fill="y", padx=(12, 0))
        asb.pack(side="right", fill="y")
        self.action_list.pack(side="left", fill="both", expand=True)
        self.action_panes.add(self.action_frame, stretch="always", padx=0, pady=0)
        self.action_panes.pack(side="top", fill="both", expand=True)
        self.call_view_frame = CallViewFrame(
            self.action_column, self.action_panes, lambda: app.call_view.on_heading_click(),
        )
        ttk.Button(abtns, text="追加", width=16, command=app.trigger_panel.add_action).pack(pady=(0, 6))
        ttk.Button(abtns, text="編集", width=16, command=app.trigger_panel.edit_action).pack(pady=6)
        ttk.Button(abtns, text="削除", width=16, command=app.trigger_panel.delete_action).pack(pady=6)
        ttk.Button(abtns, text="複製", width=16, command=app.trigger_panel.duplicate_action).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="上へ", width=16, command=lambda: app.trigger_panel.move_action(-1)).pack(pady=6)
        ttk.Button(abtns, text="下へ", width=16, command=lambda: app.trigger_panel.move_action(+1)).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="保存", width=16, command=app.sequence_io.save_selected_sequence).pack(pady=6)
        ttk.Button(abtns, text="別名で保存", width=16, command=app.sequence_io.save_selected_sequence_as).pack(pady=6)
        ttk.Button(abtns, text="読込", width=16, command=app.sequence_io.load_sequence_file).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        # 連続実行（run_to_end）
        self.run_to_end_chk = ttk.Checkbutton(
            abtns,
            text="連続実行",
            variable=app.ui_vars.run_to_end_var,
            command=app.trigger_panel.update_run_to_end,
        )
        self.run_to_end_chk.pack(anchor="w", pady=(8, 0))
        self.select_before_run_chk = ttk.Checkbutton(
            abtns, text="確認して実行",
            variable=app.ui_vars.sequence_select_before_run_var,
            command=app.trigger_panel.update_select_before_run,
        )

        # 連続実行 間隔（ms） ※トリガーごと / デフォルト300
        delay_line = ttk.Frame(abtns)
        delay_line.pack(fill="x", pady=(6, 0))
        ttk.Label(delay_line, text="間隔(ms)").pack(side="left")
        self.run_to_end_delay_entry = ttk.Entry(delay_line, width=8, textvariable=app.ui_vars.run_to_end_delay_var)
        self.run_to_end_delay_entry.pack(side="left", padx=(8, 0))
        # Enter / フォーカスアウトで保存
        self.run_to_end_delay_entry.bind("<Return>", app.trigger_panel.update_run_to_end_delay)
        self.run_to_end_delay_entry.bind("<FocusOut>", app.trigger_panel.update_run_to_end_delay)
        self.select_before_run_chk.pack(anchor="w", pady=(6, 0))
