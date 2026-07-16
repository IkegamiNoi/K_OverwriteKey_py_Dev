from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class CompactHookFrame(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="フック", padding=10)

        # フックラベルフレーム1行目
        self.compact_hook_line1 = ttk.Frame(self)
        self.compact_hook_line1.pack(side="top", fill="x")
        # 開始/停止（Appの同名メソッドを呼ぶ。ウィジェットは別物でOK）
        self.hook_toggle_btn = ttk.Button(self.compact_hook_line1, text="開始（フックON）", command=app.hook.toggle_hook)
        self.trigger_toggle_btn = ttk.Button(self.compact_hook_line1, text="通常トリガー無効化", command=app.hook.toggle_triggers_enabled, state="disabled")
        self.hook_toggle_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.trigger_toggle_btn.grid(row=0, column=1, padx=(8, 0), sticky="w")
        # App側でも参照できるように保持（フック開始/停止時のstate同期用）
        app.compact_hook_toggle_btn = self.hook_toggle_btn
        app.compact_trigger_toggle_btn = self.trigger_toggle_btn
        
        # フックラベルフレーム2行目
        self.compact_hook_line2 = ttk.Frame(self)
        self.compact_hook_line2.pack(side="top", fill="x")
        # 停止トリガー表示のみ（Entryだけ）
        ttk.Label(self.compact_hook_line2, text="フック停止トリガー: ").grid(row=0, column=0, sticky="w")
        self.stop_key_entry = ttk.Entry(self.compact_hook_line2, textvariable=app.ui_vars.stop_key_var, width=8, state="readonly")
        self.stop_key_entry.grid(row=0, column=1, sticky="w")

        # トグルキー表示のみ（Entryだけ）
        ttk.Label(self.compact_hook_line2, text="有効/無効トグルキー: ").grid(row=1, column=0, sticky="w")
        self.toggle_key_entry = ttk.Entry(self.compact_hook_line2, textvariable=app.ui_vars.toggle_key_var, width=8, state="readonly")
        self.toggle_key_entry.grid(row=1, column=1, sticky="w")
