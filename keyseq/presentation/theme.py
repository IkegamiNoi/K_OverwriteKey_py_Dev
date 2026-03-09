import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


def _smaller_size(size: int, delta_pt: int) -> int:
    """Return one-step smaller size for both point-size and pixel-size fonts."""
    if size == 0:
        return size
    if size > 0:
        return max(1, size + delta_pt)
    # Negative means pixel-based size in Tk.
    return min(-1, size - delta_pt)


def _shrink_named_font(name: str, delta_pt: int) -> None:
    try:
        f = tkfont.nametofont(name)
    except tk.TclError:
        return
    size = int(f.cget("size"))
    f.configure(size=_smaller_size(size, delta_pt))


def apply_global_theme(root: tk.Misc, *, font_delta_pt: int = -1) -> None:
    """Apply shared UI theme across the app."""
    if font_delta_pt == 0:
        return

    for name in (
        "TkDefaultFont",
        "TkTextFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    ):
        _shrink_named_font(name, font_delta_pt)

    # Explicitly bind common ttk styles to default named fonts.
    default_font = tkfont.nametofont("TkDefaultFont")
    text_font = tkfont.nametofont("TkTextFont")
    style = ttk.Style(root)
    style.configure(".", font=default_font)
    style.configure("TLabel", font=default_font)
    style.configure("TButton", font=default_font)
    style.configure("TCheckbutton", font=default_font)
    style.configure("TRadiobutton", font=default_font)
    style.configure("TEntry", font=text_font)
    style.configure("TCombobox", font=text_font)
    style.configure("TMenubutton", font=default_font)
