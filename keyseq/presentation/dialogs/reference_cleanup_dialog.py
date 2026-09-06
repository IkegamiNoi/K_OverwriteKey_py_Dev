from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class ReferenceCleanupDialog(tk.Toplevel):
    def __init__(
        self,
        parent: App,
        *,
        title: str,
        lines: tuple[str, ...],
        header: str = "除去する参照元を確認してください。",
        run_label: str = "実行",
    ):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(True, True)
        self.result = False

        self.parent.hook.suspend_hook_for_dialog()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ttk.Label(frame, text=header).grid(row=0, column=0, sticky="w")
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.text = tk.Text(list_frame, width=72, height=18, wrap="none")
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text=run_label, command=self._run).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="キャンセル", command=self.destroy).pack(side="left")

        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(parent)
        self.grab_set()

    def _run(self) -> None:
        self.result = True
        self.destroy()

    def destroy(self):
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()
