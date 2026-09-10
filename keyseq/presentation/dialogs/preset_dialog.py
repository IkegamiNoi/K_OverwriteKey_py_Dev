from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from keyseq.presentation.modal import grab_modal


class PresetDialog(tk.Toplevel):
    """プリセット（value=hotkey内容, label=表示名）を入力するダイアログ（追加/編集で共通）"""
    def __init__(self, parent, title: str, initial_value: str = "", initial_label: str = ""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="内容（hotkey）").grid(row=0, column=0, sticky="w")
        self.value_var = tk.StringVar(value=initial_value or "")
        self.value_entry = ttk.Entry(frm, textvariable=self.value_var, width=34)
        self.value_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))

        ttk.Label(frm, text="ラベル").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.label_var = tk.StringVar(value=initial_label or "")
        self.label_entry = ttk.Entry(frm, textvariable=self.label_var, width=34)
        self.label_entry.grid(row=1, column=1, sticky="we", padx=(8, 0), pady=(10, 0))

        hint = ttk.Label(frm, text="例）内容: windows+d / ラベル: Win+D（ラベルは重複禁止）")
        hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        self.value_entry.focus_set()
        grab_modal(self, parent)

    def _ok(self):
        value = (self.value_var.get() or "").strip()
        label = (self.label_var.get() or "").strip()
        if not value:
            messagebox.showerror("入力エラー", "内容（hotkey）が空です。")
            return
        if not label:
            messagebox.showerror("入力エラー", "ラベルが空です。")
            return
        self.result = {"value": value, "label": label}
        self.destroy()
