import os
import tkinter as tk
from tkinter import filedialog, ttk

from keyseq.presentation.controllers.config_io import choice_dialog
from keyseq.presentation.modal import grab_modal
from keyseq.shared.i18n import tr


class IoDialogs:
    def __init__(self, app) -> None:
        self._app = app

    def choose_save_path_with_collision(self, *, title: str, suggested_path: str) -> str:
        path = suggested_path
        if os.path.exists(path):
            choice = choice_dialog.ask_choice(
                self._app,
                title=tr("config_io.io_dialogs.collision.title"),
                message=tr(
                    "config_io.io_dialogs.collision.message",
                    path=path,
                ),
                choices=[
                    ("overwrite", tr("config_io.io_dialogs.collision.overwrite")),
                    ("save_as", tr("common.save_as")),
                    ("cancel", tr("common.cancel")),
                ],
                default="overwrite",
                cancel="cancel",
            )
            if choice == "cancel":
                return ""
            if choice == "save_as":
                path = filedialog.asksaveasfilename(
                    title=title,
                    initialdir=os.path.dirname(os.path.abspath(suggested_path)),
                    initialfile=os.path.basename(suggested_path),
                    defaultextension=".json",
                    filetypes=[("JSON", "*.json"), ("All", "*.*")],
                )
        return path or ""

    def ask_link_label_to_filename(self, *, title: str, path: str) -> bool:
        dialog = tk.Toplevel(self._app)
        dialog.title(title)
        dialog.resizable(False, False)
        self._app.hook.suspend_hook_for_dialog()
        result = {"ok": False, "link": False}
        link_var = tk.BooleanVar(value=False)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        filename = self._app.paths.filename_stem(path)
        ttk.Label(
            frame,
            text=tr(
                "config_io.io_dialogs.link_label.filename",
                name=filename,
            ),
        ).pack(anchor="w")
        ttk.Checkbutton(
            frame,
            text=tr("config_io.io_dialogs.link_label.checkbox"),
            variable=link_var,
        ).pack(anchor="w", pady=(10, 0))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))

        def on_ok():
            result["ok"] = True
            result["link"] = bool(link_var.get())
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(buttons, text=tr("common.ok"), command=on_ok).pack(side="right")
        ttk.Button(buttons, text=tr("common.cancel"), command=on_cancel).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.bind("<Escape>", lambda _event: on_cancel())
        grab_modal(dialog, self._app)
        try:
            dialog.wait_window()
        finally:
            self._app.hook.resume_hook_after_dialog()
        if not result["ok"]:
            raise RuntimeError(tr("config_io.io_dialogs.link_label.cancelled"))
        return bool(result["link"])
