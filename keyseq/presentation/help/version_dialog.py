"""バージョン情報のモーダルダイアログ。"""

import platform
import tkinter as tk
from tkinter import ttk

import keyseq
from keyseq.presentation.modal import grab_modal
from keyseq.shared.i18n import tr


def open_version_dialog(app: tk.Misc) -> tk.Toplevel:
    dialog = tk.Toplevel(app)
    dialog.title(tr("help.version.title"))
    dialog.resizable(False, False)
    app.hook.suspend_hook_for_dialog(dialog)
    text = tr(
        "help.version.content",
        version=keyseq.__version__,
        python_version=platform.python_version(),
        tk_version=dialog.tk.call("info", "patchlevel"),
    )
    body = tk.Text(dialog, height=6, width=58, wrap="word", font="TkDefaultFont")
    body.pack(padx=14, pady=(14, 8), fill="both")
    body.insert("1.0", text)
    body.configure(state="disabled")
    close_button = ttk.Button(dialog, text=tr("help.version.close"), command=dialog.destroy)
    close_button.pack(anchor="e", padx=14, pady=(0, 14))
    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    grab_modal(dialog, app, focus=close_button)
    return dialog
