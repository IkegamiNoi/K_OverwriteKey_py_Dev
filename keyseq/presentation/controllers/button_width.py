"""TButton のフォントで文言の最大幅を固定する。"""

import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import Sequence

from keyseq.presentation.button_width_rules import fixed_button_width_chars


def apply_fixed_button_width(button: ttk.Button, texts: Sequence[str]) -> None:
    try:
        font_spec = ttk.Style(button).lookup("TButton", "font")
        font = tkfont.Font(root=button, font=font_spec or "TkDefaultFont")
    except tk.TclError:
        font = tkfont.Font(root=button, font="TkDefaultFont")
    width = fixed_button_width_chars(
        [font.measure(text) for text in texts], font.measure("0")
    )
    button.configure(width=width)
