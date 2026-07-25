import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class IoDialogs:
    def __init__(self, app) -> None:
        self._app = app

    def choose_save_path_with_collision(self, *, title: str, suggested_path: str) -> str:
        path = suggested_path
        if os.path.exists(path):
            result = messagebox.askyesnocancel(
                "保存先の確認",
                f"同名ファイルが既にあります。\n\n{path}\n\n上書きしますか？\n「いいえ」で別名保存します。",
            )
            if result is None:
                return ""
            if result is False:
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
        ttk.Label(frame, text=f"保存名: {self._app.paths.filename_stem(path)}").pack(anchor="w")
        ttk.Checkbutton(frame, text="ラベル名も保存名に合わせる", variable=link_var).pack(anchor="w", pady=(10, 0))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))

        def on_ok():
            result["ok"] = True
            result["link"] = bool(link_var.get())
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(buttons, text="OK", command=on_ok).pack(side="right")
        ttk.Button(buttons, text="キャンセル", command=on_cancel).pack(side="right", padx=(0, 8))
        dialog.transient(self._app)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        try:
            dialog.wait_window()
        finally:
            self._app.hook.resume_hook_after_dialog()
        if not result["ok"]:
            raise RuntimeError("キャンセルされました。")
        return bool(result["link"])
