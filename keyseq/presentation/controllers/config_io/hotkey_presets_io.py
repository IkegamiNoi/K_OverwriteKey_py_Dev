from tkinter import messagebox


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

    def confirm_overwrite(self, *, stored_path: str) -> bool:
        return messagebox.askyesno(
            "専用プリセットの上書き確認",
            "保存先には既にプリセットファイルがあり、内容が異なります。\n"
            "上書きしますか？\n"
            f"保存先: {stored_path}",
            parent=self._app,
        )
