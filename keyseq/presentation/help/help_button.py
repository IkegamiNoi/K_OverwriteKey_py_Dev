"""ダイアログの下端に置くヘルプボタン。"""

import tkinter as tk
from tkinter import ttk

from keyseq.presentation.hover_tooltip import bind_hover_tooltip


def add_help_button(
    row: tk.Misc, dialog: tk.Toplevel, target_id: str, *, tab: str = "guide",
) -> ttk.Button:
    """行の左端に「?」を置き、続けて横へ伸びる空きを 1 つ置く。

    後から pack したボタンは右寄せになる。row は横幅いっぱいに置くこと（fill="x" / sticky="ew"）。
    """
    def open_help() -> None:
        controller = getattr(dialog.nametowidget("."), "help", None)
        if controller is not None:
            controller.open_for_dialog(dialog, tab, target_id)

    button = ttk.Button(row, text="?", width=1, command=open_help)
    button.pack(side="left")
    ttk.Frame(row).pack(side="left", fill="x", expand=True)
    bind_hover_tooltip(button, lambda: "ヘルプ", lambda: True)
    return button
