"""Message box entry points with modal parenting and presence tracking."""

import tkinter
from tkinter import messagebox as _messagebox

from keyseq.infrastructure.os_backend import get_backend
from keyseq.presentation import modal


def _default_parent():
    """Innermost viewable modal, else the viewable root, else None (any failure means None)."""
    try:
        for window in reversed(modal._active_modals):
            if window.winfo_exists() and window.winfo_viewable():
                return window
        root = tkinter._default_root
        if root is not None and root.winfo_viewable():
            return root
    except Exception:
        return None
    return None


def _show(name: str, title=None, message=None, **options):
    if options.get("parent") is None:
        parent = _default_parent()
        if parent is None:
            options.pop("parent", None)
        else:
            options["parent"] = parent
    modal.enter_message_box()
    try:
        if name in {"showerror", "showwarning"}:
            get_backend().window.bring_app_to_front()
        return getattr(_messagebox, name)(title, message, **options)
    finally:
        modal.leave_message_box()


def showerror(title=None, message=None, **options): return _show("showerror", title, message, **options)
def showwarning(title=None, message=None, **options): return _show("showwarning", title, message, **options)
def showinfo(title=None, message=None, **options): return _show("showinfo", title, message, **options)
def askyesno(title=None, message=None, **options): return _show("askyesno", title, message, **options)
def askyesnocancel(title=None, message=None, **options): return _show("askyesnocancel", title, message, **options)
def askokcancel(title=None, message=None, **options): return _show("askokcancel", title, message, **options)
def askquestion(title=None, message=None, **options): return _show("askquestion", title, message, **options)
def askretrycancel(title=None, message=None, **options): return _show("askretrycancel", title, message, **options)
