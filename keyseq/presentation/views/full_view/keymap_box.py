from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from keyseq.presentation.listbox_range_drag import bind_listbox_range_drag


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class KeymapBox(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="キーマップ管理", padding=10)

        keymap_list_frame = ttk.Frame(self)
        keymap_list_frame.pack(side="top", fill="both", expand=True)
        # 既定12行の半分をフル表示の最小高さの基準にする（表示行数は伸びた分で決まる）。
        self.keymap_listbox = tk.Listbox(keymap_list_frame, height=6, width=26, exportselection=False)
        self.keymap_listbox.bind("<<ListboxSelect>>", app.keymap_panel.on_keymap_list_select)
        self.keymap_listbox.bind("<KeyRelease>", app.keymap_panel.on_keymap_list_focus_index_change)
        self.keymap_listbox.bind("<Double-Button-1>", app.keymap_panel.on_keymap_list_double_click)
        self.keymap_range_drag = bind_listbox_range_drag(
            self.keymap_listbox,
            on_move=app.keymap_panel.on_keymap_list_move,
            on_commit=app.keymap_panel.on_keymap_list_mouse_release,
            can_start_drag=app.keymap_panel.can_start_keymap_drag,
        )
        for sequence in ("<Control-c>", "<Control-C>"):
            self.keymap_listbox.bind(sequence, app.keymap_panel.copy_keymaps)
        for sequence in ("<Control-v>", "<Control-V>"):
            self.keymap_listbox.bind(sequence, app.keymap_panel.paste_keymaps)
        keymap_list_scrollbar = ttk.Scrollbar(keymap_list_frame, orient="vertical", command=self.keymap_listbox.yview)
        keymap_list_scrollbar.pack(side="right", fill="y")
        self.keymap_listbox.pack(side="left", fill="both", expand=True)
        self.keymap_listbox.configure(yscrollcommand=keymap_list_scrollbar.set)

        keymap_btns = ttk.Frame(self)
        keymap_btns.pack(fill="x", pady=(6, 0))
        self.keymap_add_btn = ttk.Button(keymap_btns, text="追加", command=app.keymap_panel.add_keymap)
        self.keymap_add_btn.pack(fill="x", pady=(0, 3))
        self.keymap_edit_btn = ttk.Button(keymap_btns, text="キーマップ変更", command=app.keymap_panel.edit_selected_keymap)
        self.keymap_edit_btn.pack(fill="x", pady=3)
        self.keymap_delete_btn = ttk.Button(keymap_btns, text="削除", command=app.keymap_panel.delete_keymap)
        self.keymap_delete_btn.pack(fill="x", pady=3)
        ttk.Separator(keymap_btns).pack(fill="x", pady=6)
        ttk.Button(keymap_btns, text="保存", command=app.keymap_io.save_selected_keymap).pack(fill="x", pady=3)
        ttk.Button(keymap_btns, text="別名で保存", command=app.keymap_io.save_selected_keymap_as).pack(fill="x", pady=3)
        ttk.Button(keymap_btns, text="読込", command=app.keymap_io.load_keymap_file).pack(fill="x", pady=3)
