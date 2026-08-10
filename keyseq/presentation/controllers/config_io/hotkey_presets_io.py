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
