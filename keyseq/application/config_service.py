from __future__ import annotations

import os
from typing import Any

from keyseq.domain.config import DEFAULT_CONFIG, ensure_config_compatibility, normalize_key_name, safe_deepcopy
from keyseq.infrastructure.json_repository import JsonRepository


class ConfigService:
    def __init__(self, repository: JsonRepository):
        self.repository = repository

    def new_default_data(self) -> dict[str, Any]:
        return safe_deepcopy(DEFAULT_CONFIG)

    def normalize_runtime_data(self, data: Any) -> dict[str, Any]:
        return ensure_config_compatibility(data)

    def load_if_exists(self, path: str) -> tuple[dict[str, Any], bool]:
        if not os.path.exists(path):
            return self.new_default_data(), False
        return self.load(path), True

    def load_runtime_data(
        self,
        startup: Any,
        *,
        config_root: str,
        fallback_path: str,
    ) -> tuple[dict[str, Any], bool]:
        split_data = self.try_load_split_runtime_data(startup, config_root=config_root)
        if split_data is not None:
            return split_data, True
        return self.load_if_exists(fallback_path)

    def load(self, path: str) -> dict[str, Any]:
        loaded = self.repository.load_json(path)
        return ensure_config_compatibility(loaded)

    def try_load_split_runtime_data(
        self,
        startup: Any,
        *,
        config_root: str,
    ) -> dict[str, Any] | None:
        if not isinstance(startup, dict):
            return None

        keymap_set_path = str(startup.get("keymap_set_path") or "").strip()
        if not keymap_set_path:
            return None

        resolved_keymap_set_path = self._resolve_config_relative_path(keymap_set_path, config_root)
        if not os.path.exists(resolved_keymap_set_path):
            return None

        try:
            return self._load_split_config(config_root=config_root, keymap_set_path=resolved_keymap_set_path)
        except Exception:
            return None

    def load_startup(self, startup_path: str) -> dict[str, Any]:
        if not os.path.exists(startup_path):
            return {}
        return self.repository.load_json(startup_path)

    def save_startup(self, path: str, data: Any) -> None:
        self.repository.save_json(path, data)

    def resolve_startup_config_path(self, startup: dict[str, Any], base_dir: str, default_path: str) -> str:
        config_path = default_path
        if not isinstance(startup, dict):
            return config_path
        cfg = startup.get("config_path")
        if not cfg:
            return config_path
        cfg_path = cfg if os.path.isabs(cfg) else os.path.join(base_dir, cfg)
        if os.path.exists(cfg_path):
            return cfg_path
        return config_path

    def resolve_startup_relative_path(self, path: str, base_dir: str) -> str:
        try:
            rel = os.path.relpath(path, base_dir)
            if rel.startswith(".."):
                return path
            return rel
        except Exception:
            return path

    def save(self, path: str, data: Any) -> dict[str, Any]:
        normalized = ensure_config_compatibility(data)
        self.repository.save_json(path, normalized)
        return normalized

    def _load_split_config(self, *, config_root: str, keymap_set_path: str) -> dict[str, Any]:
        keymap_set = self._load_optional_json(keymap_set_path)
        if not isinstance(keymap_set, dict):
            raise ValueError("keymap_set.json の読込に失敗しました。")
        return self._build_runtime_data_from_split(keymap_set, config_root=config_root)

    def _build_runtime_data_from_split(
        self,
        keymap_set: dict[str, Any],
        *,
        config_root: str,
    ) -> dict[str, Any]:
        runtime = self.new_default_data()

        for key in (
            "hook_stop_key",
            "hook_toggle_key",
            "keyboard_layout",
            "keyboard_show_physical_key_labels",
            "debug_jis_special_key_events",
        ):
            if key in keymap_set:
                runtime[key] = safe_deepcopy(keymap_set.get(key))

        runtime["external_keyboard_layouts"] = self._normalize_external_keyboard_layouts(
            keymap_set.get("external_keyboard_layouts"),
            config_root=config_root,
        )
        runtime["triggers"] = self._load_named_list(
            keymap_set.get("trigger_set_path"),
            root_key="triggers",
            config_root=config_root,
        )
        runtime["hotkey_presets"] = self._load_named_list(
            keymap_set.get("hotkey_presets_path"),
            root_key="hotkey_presets",
            config_root=config_root,
        )

        keymaps: list[dict[str, Any]] = []
        keymap_switch_keys: dict[str, str] = {}
        loaded_keymap_ids_by_path: dict[str, str] = {}
        used_keymap_ids: set[str] = set()

        active_keymap_path = str(keymap_set.get("active_keymap_path") or "").strip()
        active_keymap_resolved_path = (
            self._resolve_config_relative_path(active_keymap_path, config_root)
            if active_keymap_path
            else ""
        )

        raw_keymaps = keymap_set.get("keymaps")
        if isinstance(raw_keymaps, list):
            for entry in raw_keymaps:
                loaded_entry = self._load_keymap_entry(
                    entry,
                    config_root=config_root,
                    used_keymap_ids=used_keymap_ids,
                )
                if loaded_entry is None:
                    continue

                keymap = loaded_entry["keymap"]
                keymaps.append(keymap)
                loaded_keymap_ids_by_path[loaded_entry["resolved_path"]] = str(keymap.get("id") or "")

                switch_key = normalize_key_name(loaded_entry["switch_key"])
                if switch_key:
                    keymap_switch_keys[switch_key] = str(keymap.get("id") or "")

        active_keymap_id = loaded_keymap_ids_by_path.get(active_keymap_resolved_path, "")
        if not active_keymap_id and active_keymap_resolved_path and os.path.exists(active_keymap_resolved_path):
            active_keymap = self._load_keymap_entry(
                {"path": active_keymap_path},
                config_root=config_root,
                used_keymap_ids=used_keymap_ids,
            )
            if active_keymap is not None:
                keymaps.append(active_keymap["keymap"])
                active_keymap_id = str(active_keymap["keymap"].get("id") or "")

        runtime["keymaps"] = keymaps
        runtime["active_keymap_id"] = active_keymap_id
        runtime["keymap_switch_keys"] = keymap_switch_keys
        return ensure_config_compatibility(runtime)

    def _load_keymap_entry(
        self,
        entry: Any,
        *,
        config_root: str,
        used_keymap_ids: set[str],
    ) -> dict[str, Any] | None:
        if isinstance(entry, dict):
            stored_path = str(entry.get("path") or "").strip()
            switch_key = str(entry.get("switch_key") or "").strip()
        else:
            stored_path = str(entry or "").strip()
            switch_key = ""

        if not stored_path:
            return None

        resolved_path = self._resolve_config_relative_path(stored_path, config_root)
        raw_keymap = self._load_optional_json(resolved_path)
        if not isinstance(raw_keymap, dict):
            return None

        keymap_id = self._generate_keymap_id(stored_path, raw_keymap, used_keymap_ids)
        used_keymap_ids.add(keymap_id)

        mappings = raw_keymap.get("mappings")
        if not isinstance(mappings, dict):
            mappings = {}

        return {
            "resolved_path": resolved_path,
            "switch_key": switch_key,
            "keymap": {
                "id": keymap_id,
                "label": str(raw_keymap.get("label") or "").strip(),
                "mappings": safe_deepcopy(mappings),
            },
        }

    def _load_named_list(
        self,
        path_value: Any,
        *,
        root_key: str,
        config_root: str,
    ) -> list[Any]:
        stored_path = str(path_value or "").strip()
        if not stored_path:
            return []

        resolved_path = self._resolve_config_relative_path(stored_path, config_root)
        loaded = self._load_optional_json(resolved_path)
        if not isinstance(loaded, dict):
            return []

        items = loaded.get(root_key)
        if not isinstance(items, list):
            return []
        return safe_deepcopy(items)

    def _normalize_external_keyboard_layouts(
        self,
        registrations: Any,
        *,
        config_root: str,
    ) -> list[dict[str, str]]:
        if not isinstance(registrations, list):
            return []

        base_dir = os.path.dirname(config_root)
        normalized: list[dict[str, str]] = []
        for item in registrations:
            if isinstance(item, dict):
                stored_path = str(item.get("path") or "").strip()
            else:
                stored_path = str(item or "").strip()
            if not stored_path:
                continue

            resolved_path = self._resolve_config_relative_path(stored_path, config_root)
            runtime_path = resolved_path
            try:
                relative_path = os.path.relpath(runtime_path, base_dir)
                if not relative_path.startswith(".."):
                    runtime_path = relative_path
            except Exception:
                pass
            normalized.append({"path": runtime_path})
        return normalized

    def _generate_keymap_id(
        self,
        stored_path: str,
        raw_keymap: dict[str, Any],
        used_keymap_ids: set[str],
    ) -> str:
        preferred = normalize_key_name(raw_keymap.get("id", ""))
        if not preferred:
            preferred = normalize_key_name(os.path.splitext(os.path.basename(stored_path))[0])
        if not preferred:
            preferred = "keymap"

        candidate = preferred
        suffix = 2
        while candidate in used_keymap_ids:
            candidate = f"{preferred}_{suffix}"
            suffix += 1
        return candidate

    def _resolve_config_relative_path(self, path: str, config_root: str) -> str:
        normalized = str(path or "").strip()
        if not normalized:
            return ""
        if os.path.isabs(normalized):
            return normalized
        return os.path.normpath(os.path.join(config_root, normalized))

    def _load_optional_json(self, path: str) -> Any:
        if not path or not os.path.exists(path):
            return None
        try:
            return self.repository.load_json(path)
        except Exception:
            return None
