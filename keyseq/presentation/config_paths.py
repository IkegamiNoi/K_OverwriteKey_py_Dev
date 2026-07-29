from __future__ import annotations

import os
import re


class ConfigPaths:
    """設定ファイル群の配置規約とパス解決。App の実行時状態には依存しない。"""

    def __init__(self, *, base_dir: str, config_root: str, user_root: str, config_service) -> None:
        self.base_dir = base_dir
        self.config_root = config_root
        self.user_root = user_root
        self._config_service = config_service

    def preferred_startup_path(self) -> str:
        return os.path.join(self.config_root, "config.json")

    def preferred_keymap_set_path(self) -> str:
        return os.path.join(self.config_root, "user", "keymap_sets", "default.json")

    def preferred_keymap_sets_dir(self) -> str:
        return os.path.dirname(self.preferred_keymap_set_path())

    def preferred_keymaps_dir(self) -> str:
        return os.path.join(self.config_root, "user", "keymaps")

    def preferred_trigger_sets_dir(self) -> str:
        return os.path.join(self.config_root, "user", "trigger_sets")

    def preferred_sequences_dir(self) -> str:
        return os.path.join(self.config_root, "user", "sequences")

    def legacy_settings_dir(self) -> str:
        return os.path.join(self.base_dir, "settings")

    def resolve_startup_path(self) -> str:
        new_path = self.preferred_startup_path()
        old_path = os.path.join(self.legacy_settings_dir(), "startup.json")
        return new_path if os.path.exists(new_path) else old_path

    def resolve_keymap_set_path(self, path: str = "") -> str:
        if path:
            return path if os.path.isabs(path) else os.path.normpath(os.path.join(self.config_root, path))
        new_path = self.preferred_keymap_set_path()
        old_path = os.path.join(self.legacy_settings_dir(), "config.json")
        return new_path if os.path.exists(new_path) else old_path

    def resolve_keylayout_dir(self) -> str:
        new_path = os.path.join(self.user_root, "keylayout")
        old_path = os.path.join(self.base_dir, "keylayout")
        return new_path if os.path.exists(new_path) else old_path

    def is_within_legacy_settings(self, path: str) -> bool:
        if not path:
            return False
        return self._config_service.is_path_within(
            path,
            self.legacy_settings_dir(),
        )

    def normalize_keymap_set_save_path(self, path: str) -> str:
        if not path:
            return self.preferred_keymap_set_path()
        normalized = os.path.normpath(str(path).strip())
        if not os.path.isabs(normalized):
            parts = re.split(r"[\\/]+", normalized)
            if parts and parts[0] == "config":
                normalized = os.path.normpath(os.path.join(self.base_dir, normalized))
            else:
                normalized = os.path.normpath(os.path.join(self.config_root, normalized))
        if self.is_within_legacy_settings(normalized):
            return self.preferred_keymap_set_path()
        return normalized

    def suggest_keymap_set_dialog_path(self, current_keymap_set_path: str) -> str:
        current = str(current_keymap_set_path or "").strip()
        if current:
            return self.normalize_keymap_set_save_path(current)
        return self.preferred_keymap_set_path()

    def suggest_keymap_set_dialog_dir(self, current_keymap_set_path: str) -> str:
        current = str(current_keymap_set_path or "").strip()
        if current:
            current_dir = os.path.dirname(os.path.abspath(current))
            if os.path.isdir(current_dir):
                return current_dir

        preferred_dir = self.preferred_keymap_sets_dir()
        if os.path.isdir(preferred_dir):
            return preferred_dir
        return self.config_root

    def to_config_relative_or_absolute(self, path: str) -> str:
        return self._config_service.to_config_relative_or_absolute(path, self.config_root)

    def is_within_config_root(self, path: str) -> bool:
        return self._config_service.is_path_within(path, self.config_root)

    def json_dialog_initial_dir(self, preferred_dir: str, source_path: str = "") -> str:
        if source_path:
            directory = os.path.dirname(os.path.abspath(source_path))
            if os.path.isdir(directory):
                return directory
        if os.path.isdir(preferred_dir):
            return preferred_dir
        return self.user_root if os.path.isdir(self.user_root) else self.base_dir

    def filename_stem(self, path: str) -> str:
        return os.path.splitext(os.path.basename(str(path or "")))[0]

    def suggest_json_path(self, directory: str, label: str, fallback: str) -> str:
        stem = self._config_service.slugify_file_stem(label) or fallback
        return os.path.join(directory, f"{stem}.json")

    def keymap_set_file_stem(self, current_keymap_set_path: str) -> str:
        stem = self.filename_stem(str(current_keymap_set_path or ""))
        return self._config_service.slugify_file_stem(stem) or "trigger_set"

    def to_rel_if_possible(self, path: str) -> str:
        return self._config_service.resolve_startup_relative_path(path, self.base_dir)
