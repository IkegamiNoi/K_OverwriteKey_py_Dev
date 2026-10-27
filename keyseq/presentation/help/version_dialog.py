"""バージョン情報のモーダルダイアログ。"""

import platform
import tkinter as tk
from tkinter import ttk

import keyseq
from keyseq.presentation.modal import grab_modal


def open_version_dialog(app: tk.Misc) -> tk.Toplevel:
    dialog = tk.Toplevel(app)
    dialog.title("バージョン情報")
    dialog.resizable(False, False)
    app.hook.suspend_hook_for_dialog(dialog)
    text = (
        "Key Replacer Sequencer\n"
        f"バージョン {keyseq.__version__}\n"
        "Copyright (C) 2026 池上ノイ (Ikegami Noi)\n"
        "ライセンス: GNU General Public License v3\n"
        f"実行環境: Python {platform.python_version()}・Tk {dialog.tk.call('info', 'patchlevel')}"
    )
    body = tk.Text(dialog, height=6, width=58, wrap="word", font="TkDefaultFont")
    body.pack(padx=14, pady=(14, 8), fill="both")
    body.insert("1.0", text)
    body.configure(state="disabled")
    close_button = ttk.Button(dialog, text="閉じる", command=dialog.destroy)
    close_button.pack(anchor="e", padx=14, pady=(0, 14))
    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    grab_modal(dialog, app, focus=close_button)
    return dialog
