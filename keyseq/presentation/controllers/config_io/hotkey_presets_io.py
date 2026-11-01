import tkinter as tk
from tkinter import messagebox, ttk

from keyseq.presentation.modal import grab_modal
from keyseq.shared.i18n import tr


class HotkeyPresetsIo:
    def __init__(self, app) -> None:
        self._app = app

    def write_presets(self, presets: list, *, stored_path: str) -> bool:
        """指定された保存先、またはグローバルプリセットへ即時保存する。"""
        try:
            if stored_path:
                self._app.config_service.save_hotkey_presets(
                    presets,
                    config_root=self._app.config_root,
                    stored_path=stored_path,
                )
            else:
                self._app.config_service.save_global_hotkey_presets(
                    presets,
                    config_root=self._app.config_root,
                )
            return True
        except Exception as e:
            messagebox.showerror(tr("config_io.hotkey_presets.save_failed_title"), str(e))
            return False

    def show_save_path_rejection(self, reason: str, *, stored_path: str) -> None:
        if reason == "reserved_dir":
            message = tr("config_io.hotkey_presets.reserved_dir", path=stored_path)
        else:
            message = tr("config_io.hotkey_presets.same_file", path=stored_path)
        messagebox.showerror(tr("config_io.hotkey_presets.rejection_title"), message)

    def confirm_overwrite(self, *, stored_path: str, existing: list | None,
                          transient_parent: tk.Misc) -> str:
        """個別プリセットの上書き確認を 3 択で表示する。

        `transient_parent` には**生存中の呼び出し元ウィンドウ**を渡す（ネストして開くため必須）。
        破棄済みのウィジェットを渡すと初期化が `TclError` で中断し、grab 未取得のまま窓が残る。
        """
        result = {"choice": "cancel"}
        dialog = tk.Toplevel(self._app)
        dialog.title(tr("config_io.hotkey_presets.overwrite_title"))
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        if existing is None:
            description = tr("config_io.hotkey_presets.unreadable_existing", path=stored_path)
        else:
            description = tr("config_io.hotkey_presets.different_existing", path=stored_path)
        ttk.Label(
            frame,
            text=description,
            justify="left",
            wraplength=560,
        ).pack(fill="both", expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="e", pady=(12, 0))

        def choose(choice: str) -> None:
            result["choice"] = choice
            dialog.destroy()

        ttk.Button(buttons, text=tr("common.cancel"), command=dialog.destroy).pack(side="right")
        if existing is not None:
            ttk.Button(
                buttons,
                text=tr("config_io.hotkey_presets.adopt_existing"),
                command=lambda: choose("adopt"),
            ).pack(side="right", padx=(0, 8))
        ttk.Button(
            buttons,
            text=tr("config_io.hotkey_presets.overwrite"),
            command=lambda: choose("overwrite"),
        ).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        grab_modal(dialog, transient_parent)
        dialog.wait_window()
        return result["choice"]
