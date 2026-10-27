"""ダイアログの下端に置くヘルプボタン。"""

import tkinter as tk
from tkinter import ttk

from keyseq.presentation.hover_tooltip import bind_hover_tooltip


def add_help_button(
    row: tk.Misc, dialog: tk.Toplevel, target_id: str, *, tab: str = "guide",
) -> ttk.Button:
    def open_help() -> None:
        controller = getattr(dialog.nametowidget("."), "help", None)
        if controller is not None:
            controller.open_for_dialog(dialog, tab, target_id)

    children = row.pack_slaves()
    button = ttk.Button(row, text="?", width=1, command=open_help)
    if children:
        button.pack(side="left", before=children[0])
    else:
        button.pack(side="left")
    bind_hover_tooltip(button, lambda: "ヘルプ", lambda: True)
    return button
