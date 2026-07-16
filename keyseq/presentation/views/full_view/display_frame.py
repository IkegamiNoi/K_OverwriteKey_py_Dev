from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FullDisplayFrame(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text="表示", padding=(10, 6))

        self.topmost_chk = ttk.Checkbutton(
            self,
            text="常に手前",
            variable=app.ui_vars.always_on_top_var,
            command=app._apply_always_on_top,
        )
        self.topmost_chk.grid(row=0, column=0, sticky="w")
        # 省略表示へ
        self.compact_btn = ttk.Button(self, text="省略表示", command=app.show_compact_view)
        self.compact_btn.grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Button(self, text="キーボードUI", command=app.layout.open_keyboard_window).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.keyboard_layout_combo = ttk.Combobox(
            self,
            textvariable=app.ui_vars.keyboard_layout_var,
            state="readonly",
            width=18,
        )
        self.keyboard_layout_combo.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(10, 0))
        self.keyboard_layout_combo.bind("<<ComboboxSelected>>", app.layout.on_keyboard_layout_selected)
        app.layout.register_layout_combo(self.keyboard_layout_combo)
