from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class QuarantineManageDialog(tk.Toplevel):
    def __init__(self, parent: App, *, lines: tuple[str, ...], unit_ids: tuple[str, ...]):
        super().__init__(parent)
        self.parent = parent
        self.parent.hook.suspend_hook_for_dialog()
        self.selected_unit_id: str = ""
        self.action: str = ""
        self._unit_ids = unit_ids
        self.title("隔離の管理")
        self.resizable(False, False)
        self._build_widgets(lines)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(parent)
        self.grab_set()

    def _build_widgets(self, lines: tuple[str, ...]) -> None:
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="実行単位を選択してください。").pack(anchor="w")
        list_frame = ttk.Frame(frm)
        list_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.listbox = tk.Listbox(list_frame, height=8, width=85, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        for line in lines:
            self.listbox.insert(tk.END, line)
        actions = ttk.Frame(frm)
        actions.pack(anchor="e", pady=(14, 0))
        ttk.Button(actions, text="復元する…", command=self._restore).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="削除する…", command=self._delete).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="閉じる", command=self.destroy).pack(side="left")

    def _restore(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self.selected_unit_id = self._unit_ids[int(selection[0])]
        self.action = "restore"
        self.destroy()

    def _delete(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self.selected_unit_id = self._unit_ids[int(selection[0])]
        self.action = "delete"
        self.destroy()

    def destroy(self) -> None:
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()
