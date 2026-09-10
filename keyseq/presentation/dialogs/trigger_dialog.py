from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from keyseq.domain.config import normalize_key_name
from keyseq.presentation.modal import grab_modal
from keyseq.presentation.tk_keys import normalize_tk_keysym

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class TriggerDialog(tk.Toplevel):
    """トリガーキー + ラベル を入力するダイアログ（追加/変更で共通）"""
    def __init__(self, parent: App, title: str, initial_key: str = "", initial_label: str = ""):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._capturing = False
        
        # 編集中の誤爆防止
        self.parent.hook.suspend_hook_for_dialog()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="トリガー").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar(value=initial_key or "")
        self.key_entry = ttk.Entry(frm, textvariable=self.key_var, width=28)
        self.key_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))
        self.capture_btn = ttk.Button(frm, text="キー入力で取得", command=self._toggle_capture)
        self.capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="ラベル").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.label_var = tk.StringVar(value=initial_label or "")
        self.label_entry = ttk.Entry(frm, textvariable=self.label_var, width=42)
        self.label_entry.grid(row=1, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=(10, 0))

        self.hint = ttk.Label(frm, text="例）トリガー: f1 \n   ラベル: コピー→ウィンドウ切替→貼り付け")
        self.hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=3, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        self.key_entry.focus_set()
        grab_modal(self, parent)

    def _ok(self):
        key = normalize_key_name(self.key_var.get())
        label = (self.label_var.get() or "").strip()
        if not key:
            messagebox.showerror("入力エラー", "トリガーが空です。")
            return
        self.result = {"key": key, "label": label}
        self.destroy()
        
    def destroy(self):
        self._stop_capture()
        # ダイアログ終了でフックを必要なら再開
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()

    def _toggle_capture(self):
        if self._capturing:
            self._stop_capture()
        else:
            self._start_capture()

    def _start_capture(self):
        # 単キーの取得（F1等）を想定。Escでキャンセル。
        self._capturing = True
        self.capture_btn.configure(text="取得中…（Escで停止）")
        self.hint.configure(text="取得中：トリガーにしたいキーを1回押してください（Escでキャンセル）")
        self.key_entry.focus_set()
        # ダイアログ全体で拾う（Entryにフォーカスが無くてもOK）
        self.bind("<KeyPress>", self._on_capture_keypress, add="+")

    def _stop_capture(self):
        if not getattr(self, "_capturing", False):
            return
        self._capturing = False
        self.capture_btn.configure(text="キー入力で取得")
        self.hint.configure(text="例）トリガー: f1 / ラベル: コピー→ウィンドウ切替→貼り")
        try:
            self.unbind("<KeyPress>")
        except Exception:
            pass

    def _on_capture_keypress(self, event):
        if not self._capturing:
            return
        k = self._normalize_tk_key(event.keysym)
        # Escはキャンセル
        if k == "esc":
            self._stop_capture()
            return "break"
        # 修飾キー単体は無視（ctrl/shift/alt/windows）
        if k in ("ctrl", "shift", "alt", "windows"):
            return "break"
        # 取得して終了
        self.key_var.set(k)
        self.key_entry.icursor(tk.END)
        self._stop_capture()
        return "break"

    def _normalize_tk_key(self, keysym: str) -> str:
        # Tkのkeysymを keyboard ライブラリの表記に寄せる（トリガー用）
        return normalize_tk_keysym(keysym)
