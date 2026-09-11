import tkinter as tk
from tkinter import messagebox, ttk

from keyseq.presentation.modal import grab_modal


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
            messagebox.showerror("プリセット保存失敗", str(e))
            return False

    def show_save_path_rejection(self, reason: str, *, stored_path: str) -> None:
        if reason == "reserved_dir":
            message = (
                "global/ はグローバル用のため、専用プリセットの保存先にできません。\n"
                f"現在の保存先: {stored_path}"
            )
        else:
            message = (
                "保存先がグローバルライブラリと同じファイルです。\n"
                "config.json の hotkey_presets_path を global/ 配下へ直してください。\n"
                f"現在の保存先: {stored_path}"
            )
        messagebox.showerror("専用プリセットを保存できません", message)

    def confirm_overwrite(self, *, stored_path: str, existing: list | None) -> str:
        """個別プリセットの上書き確認を 3 択で表示する。"""
        result = {"choice": "cancel"}
        dialog = tk.Toplevel(self._app)
        dialog.title("専用プリセットの上書き確認")
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        if existing is None:
            description = "保存先には既にファイルがありますが、プリセットとして読み込めません。"
        else:
            description = "保存先には既にプリセットファイルがあり、表示中の一覧と内容が異なります。"
        ttk.Label(
            frame,
            text=f"{description}\n保存先: {stored_path}",
            justify="left",
            wraplength=560,
        ).pack(fill="both", expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="e", pady=(12, 0))

        def choose(choice: str) -> None:
            result["choice"] = choice
            dialog.destroy()

        ttk.Button(buttons, text="キャンセル", command=dialog.destroy).pack(side="right")
        if existing is not None:
            ttk.Button(
                buttons,
                text="既存を読み込む",
                command=lambda: choose("adopt"),
            ).pack(side="right", padx=(0, 8))
        ttk.Button(
            buttons,
            text="上書きする",
            command=lambda: choose("overwrite"),
        ).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        grab_modal(dialog, self._app)
        dialog.wait_window()
        return result["choice"]
