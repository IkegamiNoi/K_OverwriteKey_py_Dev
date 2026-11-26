"""前面のヘルプと親ダイアログの間でローカル grab を受け渡す。"""

from functools import partial
import tkinter as tk

from keyseq.infrastructure.os_backend import get_backend


def install_grab_handoff(help_window: tk.Toplevel, dialog: tk.Toplevel) -> None:
    if not get_backend().window.hands_grab_to_active_child_window():
        return
    help_window.bind("<Activate>", partial(_activate, help_window, dialog), add="+")
    help_window.bind("<Deactivate>", partial(_deactivate, help_window, dialog), add="+")
    help_window.bind("<Destroy>", partial(_destroy, help_window, dialog), add="+")


def _activate(help_window: tk.Toplevel, dialog: tk.Toplevel, event: tk.Event) -> None:
    if event.widget is not help_window:
        return
    try:
        if help_window.grab_current() is dialog:
            help_window.grab_set()
    except tk.TclError:
        pass


def _deactivate(help_window: tk.Toplevel, dialog: tk.Toplevel, event: tk.Event) -> None:
    if event.widget is not help_window:
        return
    try:
        if help_window.grab_current() is help_window:
            dialog.grab_set()
    except tk.TclError:
        pass


def _destroy(help_window: tk.Toplevel, dialog: tk.Toplevel, event: tk.Event) -> None:
    if event.widget is not help_window:
        return
    try:
        holder = help_window.grab_current()
        if (holder is help_window or holder is None) and dialog.winfo_exists() and dialog.winfo_viewable():
            dialog.grab_set()
    except tk.TclError:
        pass
