import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


_NAMED_FONTS = (
    "TkDefaultFont",
    "TkTextFont",
    "TkMenuFont",
    "TkHeadingFont",
    "TkCaptionFont",
    "TkSmallCaptionFont",
    "TkIconFont",
    "TkTooltipFont",
)

# Captured once from the runtime default so re-apply does not accumulate.
_BASE_FONT_SIZES: dict[str, int] = {}


def _apply_delta(size: int, delta_pt: int) -> int:
    if size == 0:
        return size
    if size > 0:
        return max(1, size + delta_pt)
    # Negative means pixel-based size in Tk.
    return min(-1, size - delta_pt)


def _get_named_font(name: str):
    try:
        return tkfont.nametofont(name)
    except tk.TclError:
        return None


def _capture_base_sizes() -> None:
    if _BASE_FONT_SIZES:
        return
    for name in _NAMED_FONTS:
        f = _get_named_font(name)
        if f is None:
            continue
        _BASE_FONT_SIZES[name] = int(f.cget("size"))


def apply_global_theme(root: tk.Misc, *, font_delta_pt: int = 0) -> None:
    """Apply shared UI theme across the app with absolute delta from default."""
    _capture_base_sizes()

    for name in _NAMED_FONTS:
        f = _get_named_font(name)
        if f is None:
            continue
        base = _BASE_FONT_SIZES.get(name, int(f.cget("size")))
        f.configure(size=_apply_delta(base, int(font_delta_pt)))

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
