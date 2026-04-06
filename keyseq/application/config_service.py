from __future__ import annotations

import os
import re
from typing import Any

from keyseq.domain.config import DEFAULT_CONFIG, ensure_config_compatibility, normalize_key_name, safe_deepcopy
from keyseq.infrastructure.json_repository import JsonRepository


class ConfigService:
    KEYMAP_SET_RELATIVE_PATH = os.path.join("user", "keymap_sets", "default.json")
    TRIGGER_SET_RELATIVE_PATH = os.path.join("user", "trigger_sets", "default.json")
    HOTKEY_PRESETS_RELATIVE_PATH = os.path.join("user", "hotkey_presets", "default.json")
    KEYMAPS_RELATIVE_DIR = os.path.join("user", "keymaps")
    LEGACY_CONFIG_RELATIVE_PATH = os.path.join("user", "config.json")
    INTERNAL_KEYMAP_SOURCE_PATH = "_keymap_source_path"

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
        self.repository.save_json(path, self._sanitize_runtime_for_storage(normalized))
        return normalized

    def save_runtime_data(
        self,
        path: str,
        data: Any,
        *,
        config_root: str,
        startup_data: Any = None,
        keep_legacy_copy: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        normalized = ensure_config_compatibility(data)
        sanitized_legacy = self._sanitize_runtime_for_storage(normalized)
        payloads = self._build_split_save_payloads(
            normalized,
            config_root=config_root,
            startup_data=startup_data,
            legacy_path=path if keep_legacy_copy else "",
        )

        self._ensure_split_config_dirs(config_root)
        self.repository.save_json(self._startup_entry_path(config_root), payloads["startup"])
        self.repository.save_json(
            self._resolve_config_relative_path(self.KEYMAP_SET_RELATIVE_PATH, config_root),
            payloads["keymap_set"],
        )
        self.repository.save_json(
            self._resolve_config_relative_path(self.TRIGGER_SET_RELATIVE_PATH, config_root),
            payloads["trigger_set"],
        )
        self.repository.save_json(
            self._resolve_config_relative_path(self.HOTKEY_PRESETS_RELATIVE_PATH, config_root),
            payloads["hotkey_presets"],
        )
        for item in payloads["keymaps"]:
            self.repository.save_json(
                self._resolve_config_relative_path(str(item["path"]), config_root),
                item["payload"],
            )

        if keep_legacy_copy and path:
            self.repository.save_json(path, sanitized_legacy)

        return normalized, payloads["startup"]

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
                self.INTERNAL_KEYMAP_SOURCE_PATH: stored_path,
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

    def _build_split_save_payloads(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
        startup_data: Any,
        legacy_path: str,
    ) -> dict[str, Any]:
        keymap_payloads = self._build_keymap_payloads(runtime)
        keymap_paths_by_id = {
            str(item["id"]): str(item["path"])
            for item in keymap_payloads
            if str(item.get("id") or "").strip()
        }
        startup_payload = self._build_startup_payload(
            startup_data,
            config_root=config_root,
            legacy_path=legacy_path,
        )
        keymap_set_payload = self._build_keymap_set_payload(runtime, keymap_paths_by_id)
        trigger_payload = {
            "triggers": safe_deepcopy(runtime.get("triggers", []))
            if isinstance(runtime.get("triggers"), list)
            else []
        }
        hotkey_presets_payload = {
            "hotkey_presets": safe_deepcopy(runtime.get("hotkey_presets", []))
            if isinstance(runtime.get("hotkey_presets"), list)
            else []
        }
        serialized_keymaps = [
            {
                "path": str(item["path"]),
                "payload": item["payload"],
            }
            for item in keymap_payloads
        ]
        return {
            "startup": startup_payload,
            "keymap_set": keymap_set_payload,
            "trigger_set": trigger_payload,
            "hotkey_presets": hotkey_presets_payload,
            "keymaps": serialized_keymaps,
        }

    def _build_startup_payload(
        self,
        startup_data: Any,
        *,
        config_root: str,
        legacy_path: str,
    ) -> dict[str, Any]:
        payload = {}
        if isinstance(startup_data, dict):
            payload.update(safe_deepcopy(startup_data))

        base_dir = os.path.dirname(config_root)
        payload["keymap_set_path"] = self._to_config_relative_path(
            self._resolve_config_relative_path(self.KEYMAP_SET_RELATIVE_PATH, config_root),
            config_root,
        )
        payload["ui_font_delta_pt"] = int(payload.get("ui_font_delta_pt", 0) or 0)
        payload["last_used_directory"] = str(payload.get("last_used_directory") or "")
        payload["prompt_if_missing"] = bool(payload.get("prompt_if_missing", True))
        if legacy_path:
            payload["config_path"] = self.resolve_startup_relative_path(legacy_path, base_dir)
        return payload

    def _build_keymap_set_payload(
        self,
        runtime: dict[str, Any],
        keymap_paths_by_id: dict[str, str],
    ) -> dict[str, Any]:
        keymap_entries: list[dict[str, Any]] = []
        switch_keys = runtime.get("keymap_switch_keys", {})
        switch_keys_by_id: dict[str, str] = {}
        if isinstance(switch_keys, dict):
            for raw_key, raw_keymap_id in switch_keys.items():
                switch_key = normalize_key_name(str(raw_key or ""))
                keymap_id = normalize_key_name(str(raw_keymap_id or ""))
                if switch_key and keymap_id and keymap_id not in switch_keys_by_id:
                    switch_keys_by_id[keymap_id] = switch_key

        keymaps = runtime.get("keymaps", [])
        if isinstance(keymaps, list):
            for keymap in keymaps:
                if not isinstance(keymap, dict):
                    continue
                keymap_id = normalize_key_name(keymap.get("id", ""))
                keymap_path = keymap_paths_by_id.get(keymap_id, "")
                if not keymap_path:
                    continue
                keymap_entries.append(
                    {
                        "path": keymap_path,
                        "switch_key": switch_keys_by_id.get(keymap_id, ""),
                    }
                )

        active_keymap_id = normalize_key_name(runtime.get("active_keymap_id", ""))
        active_keymap_path = keymap_paths_by_id.get(active_keymap_id, "")
        if not active_keymap_path and keymap_entries:
            active_keymap_path = str(keymap_entries[0].get("path") or "")

        return {
            "trigger_set_path": self._normalize_path_separators(self.TRIGGER_SET_RELATIVE_PATH),
            "hotkey_presets_path": self._normalize_path_separators(self.HOTKEY_PRESETS_RELATIVE_PATH),
            "active_keymap_path": active_keymap_path,
            "keymaps": keymap_entries,
            "hook_stop_key": normalize_key_name(runtime.get("hook_stop_key", "")),
            "hook_toggle_key": normalize_key_name(runtime.get("hook_toggle_key", "")),
            "keyboard_layout": str(runtime.get("keyboard_layout") or "us_tkl").strip() or "us_tkl",
            "keyboard_show_physical_key_labels": bool(runtime.get("keyboard_show_physical_key_labels", False)),
            "debug_jis_special_key_events": bool(runtime.get("debug_jis_special_key_events", False)),
            "external_keyboard_layouts": safe_deepcopy(runtime.get("external_keyboard_layouts", []))
            if isinstance(runtime.get("external_keyboard_layouts"), list)
            else [],
        }

    def _build_keymap_payloads(self, runtime: dict[str, Any]) -> list[dict[str, Any]]:
        keymaps = runtime.get("keymaps", [])
        if not isinstance(keymaps, list):
            return []

        resolved_paths: list[dict[str, Any]] = []
        used_relative_paths: set[str] = set()
        for keymap in keymaps:
            if not isinstance(keymap, dict):
                continue

            keymap_id = normalize_key_name(keymap.get("id", ""))
            if not keymap_id:
                continue

            base_name = self._resolve_keymap_file_base_name(keymap)
            relative_path = self._allocate_unique_keymap_path(base_name, used_relative_paths)
            resolved_paths.append(
                {
                    "id": keymap_id,
                    "path": relative_path,
                    "payload": {
                        "label": str(keymap.get("label") or "").strip(),
                        "mappings": safe_deepcopy(keymap.get("mappings", {}))
                        if isinstance(keymap.get("mappings"), dict)
                        else {},
                    },
                }
            )
        return resolved_paths

    def _resolve_keymap_file_base_name(self, keymap: dict[str, Any]) -> str:
        source_path = str(keymap.get(self.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        if source_path:
            normalized_source = self._normalize_path_separators(source_path)
            source_prefix = self._normalize_path_separators(self.KEYMAPS_RELATIVE_DIR) + "/"
            if normalized_source.startswith(source_prefix):
                filename = os.path.splitext(os.path.basename(normalized_source))[0]
                slug = self._slugify_keymap_file_stem(filename)
                if slug:
                    return slug

        for candidate in (keymap.get("id"), keymap.get("label"), "keymap"):
            slug = self._slugify_keymap_file_stem(candidate)
            if slug:
                return slug
        return "keymap"

    def _allocate_unique_keymap_path(self, base_name: str, used_relative_paths: set[str]) -> str:
        stem = self._slugify_keymap_file_stem(base_name) or "keymap"
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            candidate = os.path.join(self.KEYMAPS_RELATIVE_DIR, f"{stem}{suffix}.json")
            normalized_candidate = self._normalize_path_separators(candidate)
            if normalized_candidate not in used_relative_paths:
                used_relative_paths.add(normalized_candidate)
                return normalized_candidate
            index += 1

    def _sanitize_runtime_for_storage(self, data: dict[str, Any]) -> dict[str, Any]:
        sanitized = safe_deepcopy(data)
        raw_keymaps = sanitized.get("keymaps")
        if isinstance(raw_keymaps, list):
            cleaned_keymaps: list[dict[str, Any]] = []
            for keymap in raw_keymaps:
                if not isinstance(keymap, dict):
                    continue
                cleaned = safe_deepcopy(keymap)
                cleaned.pop(self.INTERNAL_KEYMAP_SOURCE_PATH, None)
                cleaned_keymaps.append(cleaned)
            sanitized["keymaps"] = cleaned_keymaps
        return sanitized

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
                    runtime_path = self._normalize_path_separators(relative_path)
            except Exception:
                runtime_path = self._normalize_path_separators(runtime_path)
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

    def _ensure_split_config_dirs(self, config_root: str) -> None:
        os.makedirs(config_root, exist_ok=True)
        os.makedirs(os.path.join(config_root, "user"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "keymap_sets"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "keymaps"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "trigger_sets"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "hotkey_presets"), exist_ok=True)

    def _startup_entry_path(self, config_root: str) -> str:
        return os.path.join(config_root, "config.json")

    def _to_config_relative_path(self, path: str, config_root: str) -> str:
        try:
            relative_path = os.path.relpath(path, config_root)
            if relative_path.startswith(".."):
                return self._normalize_path_separators(path)
            return self._normalize_path_separators(relative_path)
        except Exception:
            return self._normalize_path_separators(path)

    def _resolve_config_relative_path(self, path: str, config_root: str) -> str:
        normalized = str(path or "").strip()
        if not normalized:
            return ""
        if os.path.isabs(normalized):
            return normalized
        return os.path.normpath(os.path.join(config_root, normalized))

    def _normalize_path_separators(self, path: str) -> str:
        return str(path or "").replace("\\", "/")

    def _slugify_keymap_file_stem(self, value: Any) -> str:
        normalized = normalize_key_name(str(value or ""))
        normalized = normalized.replace("\\", "_").replace("/", "_")
        normalized = re.sub(r"[^a-z0-9_-]+", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized

    def _load_optional_json(self, path: str) -> Any:
        if not path or not os.path.exists(path):
            return None
        try:
            return self.repository.load_json(path)
        except Exception:
            return None
