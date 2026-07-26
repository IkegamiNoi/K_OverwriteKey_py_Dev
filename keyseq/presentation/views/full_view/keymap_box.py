from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class KeymapBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="キーマップ管理", padding=10)

        keymap_list_frame = ttk.Frame(self)
        keymap_list_frame.pack(side="top", fill="y", expand=False)
        self.keymap_listbox = tk.Listbox(keymap_list_frame, height=12, width=26, exportselection=False)
        self.keymap_listbox.pack(side="left", fill="y", expand=False)
        self.keymap_listbox.bind("<<ListboxSelect>>", app.keymap_panel.on_keymap_list_select)
        self.keymap_listbox.bind("<KeyRelease>", app.keymap_panel.on_keymap_list_focus_index_change)
        self.keymap_listbox.bind("<Double-Button-1>", app.keymap_panel.on_keymap_list_double_click)
        keymap_list_scrollbar = ttk.Scrollbar(keymap_list_frame, orient="vertical", command=self.keymap_listbox.yview)
        keymap_list_scrollbar.pack(side="left", fill="y")
        self.keymap_listbox.configure(yscrollcommand=keymap_list_scrollbar.set)

        keymap_btns = ttk.Frame(self)
        keymap_btns.pack(fill="x", pady=(6, 0))
        self.keymap_add_btn = ttk.Button(keymap_btns, text="追加", command=app.keymap_panel.add_keymap)
        self.keymap_add_btn.pack(fill="x", pady=(0, 3))
        self.keymap_edit_btn = ttk.Button(keymap_btns, text="キーマップ変更", command=app.keymap_panel.edit_selected_keymap)
        self.keymap_edit_btn.pack(fill="x", pady=3)
        self.keymap_delete_btn = ttk.Button(keymap_btns, text="削除", command=app.keymap_panel.delete_keymap)
        self.keymap_delete_btn.pack(fill="x", pady=3)
        self.keymap_select_btn = ttk.Button(keymap_btns, text="選択", command=app.keymap_panel.select_keymap)
        self.keymap_select_btn.pack(fill="x", pady=3)
        ttk.Separator(keymap_btns).pack(fill="x", pady=6)
        ttk.Button(keymap_btns, text="保存", command=app.keymap_io.save_selected_keymap).pack(fill="x", pady=3)
        ttk.Button(keymap_btns, text="別名で保存", command=app.keymap_io.save_selected_keymap_as).pack(fill="x", pady=3)
        ttk.Button(keymap_btns, text="読込", command=app.keymap_io.load_keymap_file).pack(fill="x", pady=3)
