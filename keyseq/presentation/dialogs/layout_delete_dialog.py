from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class LayoutDeleteDialog(tk.Toplevel):
    def __init__(self, parent: App, title: str, items: list[tuple[str, str]]):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._items = list(items)

        self.parent.hook.suspend_hook_for_dialog()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(0, weight=1)

        ttk.Label(frm, text="削除する外部レイアウトを選択してください。").grid(row=0, column=0, sticky="w")

        list_frame = ttk.Frame(frm)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.listbox = tk.Listbox(list_frame, height=8, width=36, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<Double-Button-1>", lambda _event: self._ok())

        for layout_id, display_name in self._items:
            self.listbox.insert(tk.END, f"{display_name} [{layout_id}]")

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="削除", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        if self._items:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        self.grab_set()
        self.transient(parent)

    def _ok(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("レイアウト削除", "削除するレイアウトを選択してください。")
            return
        index = int(selection[0])
        self.result = self._items[index][0]
        self.destroy()

    def destroy(self):
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()
