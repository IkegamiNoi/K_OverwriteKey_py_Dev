from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk
from typing import TYPE_CHECKING

from keyseq.presentation.modal import grab_modal

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class OrphanSweepDialog(tk.Toplevel):
    def __init__(self, parent: App, *, scan_dirs: tuple[str, ...], initial_dir: str):
        super().__init__(parent)
        self.parent = parent
        self.parent.hook.suspend_hook_for_dialog()
        self.result: bool = False
        self.scan_dirs: tuple[str, ...] = scan_dirs
        self._initial_dir = initial_dir
        self.title("孤児ファイルの棚卸し")
        self.resizable(False, False)
        self._build_widgets()
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        grab_modal(self, parent)

    def _build_widgets(self) -> None:
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="追加で走査するディレクトリを指定してください。\n"
                  "一覧の変更は「閉じる」でも保存されます。").pack(anchor="w")
        list_frame = ttk.Frame(frm)
        list_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.listbox = tk.Listbox(list_frame, height=8, width=60, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        for directory in self.scan_dirs:
            self.listbox.insert(tk.END, directory)
        edits = ttk.Frame(frm)
        edits.pack(anchor="e", pady=(8, 0))
        ttk.Button(edits, text="追加…", command=self._add).pack(side="left", padx=(0, 8))
        ttk.Button(edits, text="削除", command=self._remove).pack(side="left")
        actions = ttk.Frame(frm)
        actions.pack(anchor="e", pady=(14, 0))
        ttk.Button(actions, text="棚卸しを実行", command=self._run).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="閉じる", command=self.destroy).pack(side="left")

    def _add(self) -> None:
        directory = filedialog.askdirectory(parent=self, initialdir=self._initial_dir)
        if directory and directory not in self.listbox.get(0, tk.END):
            self.listbox.insert(tk.END, directory)
            self.scan_dirs = tuple(self.listbox.get(0, tk.END))

    def _remove(self) -> None:
        for index in reversed(self.listbox.curselection()):
            self.listbox.delete(index)
        self.scan_dirs = tuple(self.listbox.get(0, tk.END))

    def _run(self) -> None:
        self.result = True
        self.destroy()

    def destroy(self) -> None:
        self.scan_dirs = tuple(self.listbox.get(0, tk.END))
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()
