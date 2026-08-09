from tkinter import messagebox


class HotkeyPresetsIo:
    def __init__(self, app) -> None:
        self._app = app

    def write_global_presets(self, presets: list) -> bool:
        """グローバルプリセットへ即時保存する（成否を返す）。"""
        try:
            self._app.config_service.save_global_hotkey_presets(
                presets,
                config_root=self._app.config_root,
            )
            return True
        except Exception as e:
            messagebox.showerror("プリセット保存失敗", str(e))
            return False
