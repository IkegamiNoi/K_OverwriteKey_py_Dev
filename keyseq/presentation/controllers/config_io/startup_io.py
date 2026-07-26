import os
from tkinter import messagebox

from keyseq.presentation.theme import coerce_font_delta


class StartupIo:
    def __init__(self, app) -> None:
        self._app = app

    def load_startup_and_config(self):
        """
        起動設定JSON があれば split 構成の keymap_set を読み込む。
        無い場合や split 構成が読めない場合は空データで起動する。
        """
        startup = dict(getattr(self._app, "_startup_settings", {}) or {})
        stored_keymap_set_path = str(startup.get("keymap_set_path") or "").strip()
        self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()

        if stored_keymap_set_path:
            resolved_keymap_set_path = self._app.paths.resolve_keymap_set_path(stored_keymap_set_path)
            if os.path.exists(resolved_keymap_set_path):
                try:
                    self._app.data = self._app.config_service.load_runtime_data_from_keymap_set_path(
                        resolved_keymap_set_path,
                        config_root=self._app.config_root,
                    )
                    self._app.keymap_set_path = resolved_keymap_set_path
                    self._app.keymap_set_io.apply_loaded_data_to_ui()
                    return
                except Exception:
                    pass

        self._app.data = self._app.config_service.new_empty_data()
        self._app.keymap_set_io.apply_loaded_data_to_ui()

    def write_startup(self, data: dict[str, any]):
        base = {
            "prompt_if_missing": True,
            "ui_font_delta_pt": 0,
            "last_used_directory": "",
        }
        current = getattr(self._app, "_startup_settings", {})
        if isinstance(current, dict):
            base.update(current)
        if isinstance(data, dict):
            base.update(data)
        base.pop("config_path", None)
        base["ui_font_delta_pt"] = coerce_font_delta(base.get("ui_font_delta_pt", 0))

        try:
            self._app.startup_path = self._app.paths.preferred_startup_path()
            self._app.config_service.save_startup(self._app.startup_path, base)
            self._app._startup_settings = base
        except Exception as e:
            messagebox.showerror("startup.json 保存失敗", str(e))
