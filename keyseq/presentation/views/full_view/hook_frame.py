from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FullHookFrame(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="フック", padding=10)

        # フックラベルフレーム1行目
        self.full_hook_line1 = ttk.Frame(self)
        self.full_hook_line1.pack(side="top", fill="x")
        self.hook_toggle_btn = ttk.Button(self.full_hook_line1, text="開始（フックON）", command=app.hook.toggle_hook)
        self.trigger_toggle_btn = ttk.Button(self.full_hook_line1, text="通常トリガー無効化", command=app.hook.toggle_triggers_enabled, state="disabled")
        self.hook_toggle_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.trigger_toggle_btn.grid(row=0, column=1, padx=(8, 0), sticky="w")

        # フックラベルフレーム2行目
        self.full_hook_line2 = ttk.Frame(self)
        self.full_hook_line2.pack(side="top", fill="x")
        # フック停止トリガー（フル：取得/クリアあり）
        ttk.Label(self.full_hook_line2, text="フック停止トリガー: ").grid(row=0, column=0, sticky="w")
        self.stop_key_entry = ttk.Entry(self.full_hook_line2, textvariable=app.ui_vars.stop_key_var, width=8, state="readonly")
        self.stop_key_entry.grid(row=0, column=1, sticky="w", padx=(0, 0))
        self.stop_key_capture_btn = ttk.Button(self.full_hook_line2, text="キー入力で取得", command=app.toggle_stop_key_capture)
        self.stop_key_capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.stop_key_clear_btn = ttk.Button(self.full_hook_line2, text="クリア", command=app.stop_key_capture.clear)
        self.stop_key_clear_btn.grid(row=0, column=3, sticky="w", padx=(8, 0))

        # 通常トリガー有効/無効トグルキー（フル：取得/クリアあり）
        ttk.Label(self.full_hook_line2, text="有効/無効トグルキー: ").grid(row=1, column=0, sticky="w")
        self.toggle_key_entry = ttk.Entry(self.full_hook_line2, textvariable=app.ui_vars.toggle_key_var, width=8, state="readonly")
        self.toggle_key_entry.grid(row=1, column=1, sticky="w", padx=(0, 0))
        self.toggle_key_capture_btn = ttk.Button(self.full_hook_line2, text="キー入力で取得", command=app.toggle_toggle_key_capture)
        self.toggle_key_capture_btn.grid(row=1, column=2, sticky="w", padx=(8, 0))
        self.toggle_key_clear_btn = ttk.Button(self.full_hook_line2, text="クリア", command=app.toggle_key_capture.clear)
        self.toggle_key_clear_btn.grid(row=1, column=3, sticky="w", padx=(8, 0))

        app.hook.register_hook_buttons(self.hook_toggle_btn, self.trigger_toggle_btn)
        app.stop_key_capture.register_widgets(self.stop_key_entry, self.stop_key_capture_btn, self.stop_key_clear_btn)
        app.toggle_key_capture.register_widgets(self.toggle_key_entry, self.toggle_key_capture_btn, self.toggle_key_clear_btn)
