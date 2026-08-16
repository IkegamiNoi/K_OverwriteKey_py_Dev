from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from keyseq.domain.config import normalize_key_name
from keyseq.presentation.tk_keys import normalize_tk_keysym

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class KeymapEditDialog(tk.Toplevel):
    """keymap の切替キー + ラベルを編集するダイアログ。"""
    def __init__(self, parent: App, title: str, initial_key: str = "", initial_label: str = ""):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._capturing = False

        self.parent.hook.suspend_hook_for_dialog()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="切替キー").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar(value=initial_key or "")
        self.key_entry = ttk.Entry(frm, textvariable=self.key_var, width=24, state="readonly")
        self.key_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))
        self.capture_btn = ttk.Button(frm, text="キー入力で取得", command=self._toggle_capture)
        self.capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.clear_btn = ttk.Button(frm, text="クリア", command=self._clear_key)
        self.clear_btn.grid(row=0, column=3, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="ラベル").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.label_var = tk.StringVar(value=initial_label or "")
        self.label_entry = ttk.Entry(frm, textvariable=self.label_var, width=42)
        self.label_entry.grid(row=1, column=1, columnspan=3, sticky="we", padx=(8, 0), pady=(10, 0))

        self.hint = ttk.Label(frm, text="例) 切替キー: 1\nラベル: numpad")
        self.hint.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=4, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        self.label_entry.focus_set()
        self.grab_set()
        self.transient(parent)

    def _ok(self):
        self.result = {
            "key": normalize_key_name(self.key_var.get()),
            "label": (self.label_var.get() or "").strip(),
        }
        self.destroy()

    def destroy(self):
        self._stop_capture()
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()

    def _clear_key(self):
        self.key_var.set("")
        self.key_entry.icursor(tk.END)

    def _toggle_capture(self):
        if self._capturing:
            self._stop_capture()
        else:
            self._start_capture()

    def _start_capture(self):
        self._capturing = True
        self.capture_btn.configure(text="取得中…（Escで停止）")
        self.label_entry.configure(state="disabled")
        self.hint.configure(text="取得中：切替キーにしたいキーを1回押してください（Escでキャンセル）")
        self.capture_btn.focus_set()
        self.bind("<KeyPress>", self._on_capture_keypress, add="+")

    def _stop_capture(self):
        if not getattr(self, "_capturing", False):
            return
        self._capturing = False
        self.capture_btn.configure(text="キー入力で取得")
        self.label_entry.configure(state="normal")
        self.hint.configure(text="例) 切替キー: 1\nラベル: numpad")
        try:
            self.unbind("<KeyPress>")
        except Exception:
            pass

    def _on_capture_keypress(self, event):
        if not self._capturing:
            return
        key = self._normalize_tk_key(event.keysym)
        if key == "esc":
            self._stop_capture()
            return "break"
        if key in ("ctrl", "shift", "alt", "windows"):
            return "break"
        self.key_var.set(key)
        self.key_entry.icursor(tk.END)
        self._stop_capture()
        return "break"

    def _normalize_tk_key(self, keysym: str) -> str:
        return normalize_tk_keysym(keysym)
