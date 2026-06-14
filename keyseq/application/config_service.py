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
    SEQUENCES_RELATIVE_DIR = os.path.join("user", "sequences")
    LEGACY_CONFIG_RELATIVE_PATH = os.path.join("user", "config.json")
    INTERNAL_KEYMAP_SOURCE_PATH = "_keymap_source_path"
    INTERNAL_KEYMAP_IMPORTED = "_keymap_imported"
    INTERNAL_KEYMAP_DIRTY = "_keymap_dirty"
    INTERNAL_SEQUENCE_SOURCE_PATH = "_sequence_source_path"
    INTERNAL_SEQUENCE_IMPORTED = "_sequence_imported"
    INTERNAL_SEQUENCE_DIRTY = "_sequence_dirty"

    def __init__(self, repository: JsonRepository):
        self.repository = repository

    def new_default_data(self) -> dict[str, Any]:
        return safe_deepcopy(DEFAULT_CONFIG)

    def new_empty_data(self) -> dict[str, Any]:
        data = self.new_default_data()
        data["triggers"] = []
        data["hotkey_presets"] = []
        data["keymaps"] = []
        data["active_keymap_id"] = ""
        data["keymap_switch_keys"] = {}
        return ensure_config_compatibility(data)

    def normalize_runtime_data(self, data: Any) -> dict[str, Any]:
        return ensure_config_compatibility(data)

    def load_if_exists(self, path: str) -> tuple[dict[str, Any], bool]:
        if not os.path.exists(path):
            return self.new_default_data(), False
        return self.load(path), True

    def load(self, path: str) -> dict[str, Any]:
        loaded = self.repository.load_json(path)
        return ensure_config_compatibility(loaded)

    def load_legacy_runtime_data(self, path: str) -> dict[str, Any]:
        return self.load(path)

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

    def load_runtime_data_from_keymap_set_path(
        self,
        keymap_set_path: str,
        *,
        config_root: str | None = None,
    ) -> dict[str, Any]:
        resolved_keymap_set_path = os.path.abspath(keymap_set_path)
        resolved_config_root = os.path.abspath(config_root) if config_root else self._infer_config_root_from_keymap_set_path(resolved_keymap_set_path)
        if not os.path.exists(resolved_keymap_set_path):
            raise FileNotFoundError(resolved_keymap_set_path)
        return self._load_split_config(
            config_root=resolved_config_root,
            keymap_set_path=resolved_keymap_set_path,
        )

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

    def export_runtime_data(self, path: str, data: Any) -> dict[str, Any]:
        normalized = ensure_config_compatibility(data)
        self.repository.save_json(path, self._sanitize_runtime_for_storage(normalized))
        return normalized

    def load_keymap_file(
        self,
        path: str,
        *,
        used_keymap_ids: set[str] | None = None,
        imported: bool = True,
    ) -> dict[str, Any]:
        raw_keymap = self.repository.load_json(path)
        if not isinstance(raw_keymap, dict):
            raise ValueError("keymap JSON の形式が不正です。")
        used_ids = used_keymap_ids if used_keymap_ids is not None else set()
        keymap_id = self._generate_keymap_id(path, raw_keymap, used_ids)
        mappings = raw_keymap.get("mappings")
        if not isinstance(mappings, dict):
            mappings = {}
        keymap = {
            "id": keymap_id,
            "label": str(raw_keymap.get("label") or "").strip(),
            "mappings": safe_deepcopy(mappings),
            self.INTERNAL_KEYMAP_SOURCE_PATH: path,
            self.INTERNAL_KEYMAP_IMPORTED: bool(imported),
            self.INTERNAL_KEYMAP_DIRTY: False,
        }
        return ensure_config_compatibility({"keymaps": [keymap]}).get("keymaps", [keymap])[0]

    def save_keymap_file(self, path: str, keymap: dict[str, Any]) -> dict[str, Any]:
        normalized = ensure_config_compatibility({"keymaps": [keymap]}).get("keymaps", [])
        if not normalized:
            raise ValueError("保存できる keymap がありません。")
        item = normalized[0]
        payload = self._build_keymap_file_payload(item)
        self.repository.save_json(path, payload)
        saved = safe_deepcopy(item)
        saved[self.INTERNAL_KEYMAP_SOURCE_PATH] = path
        saved[self.INTERNAL_KEYMAP_IMPORTED] = False
        saved[self.INTERNAL_KEYMAP_DIRTY] = False
        return saved

    def load_sequence_file(self, path: str, *, imported: bool = True) -> dict[str, Any]:
        raw_sequence = self.repository.load_json(path)
        if not isinstance(raw_sequence, dict):
            raise ValueError("sequence JSON の形式が不正です。")
        sequence = self._normalize_sequence_payload(raw_sequence)
        sequence[self.INTERNAL_SEQUENCE_SOURCE_PATH] = path
        sequence[self.INTERNAL_SEQUENCE_IMPORTED] = bool(imported)
        sequence[self.INTERNAL_SEQUENCE_DIRTY] = False
        return sequence

    def save_sequence_file(self, path: str, trigger: dict[str, Any]) -> dict[str, Any]:
        payload = self._build_sequence_payload(trigger)
        self.repository.save_json(path, payload)
        sequence = self._normalize_sequence_payload(payload)
        sequence[self.INTERNAL_SEQUENCE_SOURCE_PATH] = path
        sequence[self.INTERNAL_SEQUENCE_IMPORTED] = False
        sequence[self.INTERNAL_SEQUENCE_DIRTY] = False
        return sequence

    def load_trigger_set_file(
        self,
        path: str,
        *,
        config_root: str,
        imported: bool = True,
    ) -> list[dict[str, Any]]:
        payload = self.repository.load_json(path)
        if not isinstance(payload, dict):
            raise ValueError("trigger_set JSON の形式が不正です。")
        return self._load_triggers_from_trigger_set(payload, config_root=config_root, imported=imported)

    def save_trigger_set_file(
        self,
        path: str,
        data: dict[str, Any],
        *,
        config_root: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        normalized = ensure_config_compatibility(data)
        trigger_payload, sequence_items = self._build_trigger_set_payloads(
            normalized,
            config_root=os.path.abspath(config_root),
            trigger_set_path=os.path.abspath(path),
        )
        for item in sequence_items:
            self.repository.save_json(str(item["resolved_path"]), item["payload"])
        self.repository.save_json(path, trigger_payload)

        triggers = safe_deepcopy(normalized.get("triggers", [])) if isinstance(normalized.get("triggers"), list) else []
        by_key = {
            normalize_key_name(str(item.get("key") or "")): str(item.get("resolved_path") or "")
            for item in sequence_items
            if isinstance(item, dict)
        }
        for trigger in triggers:
            key = normalize_key_name(str(trigger.get("key") or ""))
            if key in by_key:
                trigger[self.INTERNAL_SEQUENCE_SOURCE_PATH] = by_key[key]
            trigger[self.INTERNAL_SEQUENCE_IMPORTED] = False
            trigger[self.INTERNAL_SEQUENCE_DIRTY] = False
        return triggers, trigger_payload

    def save_runtime_data(
        self,
        keymap_set_path: str,
        data: Any,
        *,
        config_root: str,
        startup_data: Any = None,
        keep_legacy_copy: bool = False,
        legacy_path: str = "",
        split_base_dir: str = "",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        normalized = ensure_config_compatibility(data)
        sanitized_legacy = self._sanitize_runtime_for_storage(normalized)
        resolved_config_root = os.path.abspath(config_root)
        resolved_keymap_set_path = os.path.abspath(keymap_set_path) if keymap_set_path else self._default_keymap_set_path(resolved_config_root)
        resolved_split_base_dir = os.path.abspath(split_base_dir) if split_base_dir else ""

        payloads = self._build_split_save_payloads(
            normalized,
            config_root=resolved_config_root,
            startup_data=startup_data,
            keymap_set_path=resolved_keymap_set_path,
            legacy_path=legacy_path if keep_legacy_copy else "",
            split_base_dir=resolved_split_base_dir,
        )

        self._ensure_split_config_dirs(resolved_config_root)
        self.repository.save_json(self._startup_entry_path(resolved_config_root), payloads["startup"])
        self.repository.save_json(resolved_keymap_set_path, payloads["keymap_set"])
        self.repository.save_json(
            str(payloads["trigger_set_path"]),
            payloads["trigger_set"],
        )
        self.repository.save_json(
            str(payloads["hotkey_presets_path"]),
            payloads["hotkey_presets"],
        )
        for item in payloads["keymaps"]:
            self.repository.save_json(
                self._resolve_config_relative_path(str(item["path"]), resolved_config_root),
                item["payload"],
            )
        for item in payloads["sequences"]:
            self.repository.save_json(
                str(item["resolved_path"]),
                item["payload"],
            )

        if keep_legacy_copy:
            target_legacy_path = legacy_path or self._default_legacy_config_path(resolved_config_root)
            self.repository.save_json(target_legacy_path, sanitized_legacy)

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
        runtime["triggers"] = self._load_trigger_set(
            keymap_set.get("trigger_set_path"),
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
                self.INTERNAL_KEYMAP_IMPORTED: False,
                self.INTERNAL_KEYMAP_DIRTY: False,
            },
        }

    def _load_trigger_set(self, path_value: Any, *, config_root: str) -> list[dict[str, Any]]:
        stored_path = str(path_value or "").strip()
        if not stored_path:
            return []

        resolved_path = self._resolve_config_relative_path(stored_path, config_root)
        loaded = self._load_optional_json(resolved_path)
        if not isinstance(loaded, dict):
            return []
        return self._load_triggers_from_trigger_set(loaded, config_root=config_root, imported=False)

    def _load_triggers_from_trigger_set(
        self,
        trigger_set: dict[str, Any],
        *,
        config_root: str,
        imported: bool,
    ) -> list[dict[str, Any]]:
        raw_triggers = trigger_set.get("triggers")
        if not isinstance(raw_triggers, list):
            return []

        triggers: list[dict[str, Any]] = []
        for raw_trigger in raw_triggers:
            if not isinstance(raw_trigger, dict):
                continue

            trigger = {
                "key": normalize_key_name(str(raw_trigger.get("key") or "")),
                "suppress": bool(raw_trigger.get("suppress", True)),
                "label": str(raw_trigger.get("label") or "").strip(),
                "run_to_end": bool(raw_trigger.get("run_to_end", False)),
                "run_to_end_delay_ms": self._coerce_nonnegative_int(raw_trigger.get("run_to_end_delay_ms", 300), 300),
                "actions": safe_deepcopy(raw_trigger.get("actions", []))
                if isinstance(raw_trigger.get("actions"), list)
                else [],
            }
            sequence_path = str(raw_trigger.get("sequence_path") or "").strip()
            if sequence_path:
                resolved_sequence_path = self._resolve_config_relative_path(sequence_path, config_root)
                sequence = self._load_optional_json(resolved_sequence_path)
                if isinstance(sequence, dict):
                    normalized_sequence = self._normalize_sequence_payload(sequence)
                    trigger.update(normalized_sequence)
                    trigger[self.INTERNAL_SEQUENCE_SOURCE_PATH] = sequence_path
                    trigger[self.INTERNAL_SEQUENCE_IMPORTED] = bool(imported)
                    trigger[self.INTERNAL_SEQUENCE_DIRTY] = False
            triggers.append(trigger)

        return ensure_config_compatibility({"triggers": triggers}).get("triggers", [])

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
        keymap_set_path: str,
        legacy_path: str,
        split_base_dir: str,
    ) -> dict[str, Any]:
        keymaps_dir = os.path.join(split_base_dir, "keymaps") if split_base_dir else ""
        sequences_dir = os.path.join(split_base_dir, "sequences") if split_base_dir else ""
        trigger_set_path = (
            os.path.join(split_base_dir, "trigger_sets", "default.json")
            if split_base_dir
            else self._resolve_config_relative_path(self.TRIGGER_SET_RELATIVE_PATH, config_root)
        )
        hotkey_presets_path = (
            os.path.join(split_base_dir, "hotkey_presets", "default.json")
            if split_base_dir
            else self._resolve_config_relative_path(self.HOTKEY_PRESETS_RELATIVE_PATH, config_root)
        )
        keymap_payloads = self._build_keymap_payloads(runtime, config_root=config_root, keymaps_dir=keymaps_dir)
        keymap_paths_by_id = {
            str(item["id"]): str(item["path"])
            for item in keymap_payloads
            if str(item.get("id") or "").strip()
        }
        startup_payload = self._build_startup_payload(
            startup_data,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
            legacy_path=legacy_path,
        )
        keymap_set_payload = self._build_keymap_set_payload(
            runtime,
            keymap_paths_by_id,
            config_root=config_root,
            trigger_set_path=trigger_set_path,
            hotkey_presets_path=hotkey_presets_path,
        )
        trigger_payload, sequence_payloads = self._build_trigger_set_payloads(
            runtime,
            config_root=config_root,
            trigger_set_path=trigger_set_path,
            sequences_dir=sequences_dir,
        )
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
            "trigger_set_path": trigger_set_path,
            "trigger_set": trigger_payload,
            "hotkey_presets_path": hotkey_presets_path,
            "hotkey_presets": hotkey_presets_payload,
            "keymaps": serialized_keymaps,
            "sequences": sequence_payloads,
        }

    def _build_startup_payload(
        self,
        startup_data: Any,
        *,
        config_root: str,
        keymap_set_path: str,
        legacy_path: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if isinstance(startup_data, dict):
            payload.update(safe_deepcopy(startup_data))

        payload.pop("config_path", None)
        payload["keymap_set_path"] = self._to_config_relative_or_absolute(keymap_set_path, config_root)
        try:
            payload["ui_font_delta_pt"] = int(payload.get("ui_font_delta_pt", 0) or 0)
        except Exception:
            payload["ui_font_delta_pt"] = 0
        payload["last_used_directory"] = str(payload.get("last_used_directory") or "")
        payload["prompt_if_missing"] = bool(payload.get("prompt_if_missing", True))
        if legacy_path:
            payload["config_path"] = self.resolve_startup_relative_path(legacy_path, os.path.dirname(config_root))
        return payload

    def _build_keymap_set_payload(
        self,
        runtime: dict[str, Any],
        keymap_paths_by_id: dict[str, str],
        *,
        config_root: str,
        trigger_set_path: str,
        hotkey_presets_path: str,
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
            "trigger_set_path": self._to_config_relative_or_absolute(trigger_set_path, config_root),
            "hotkey_presets_path": self._to_config_relative_or_absolute(hotkey_presets_path, config_root),
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

    def _build_keymap_payloads(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
        keymaps_dir: str = "",
    ) -> list[dict[str, Any]]:
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

            stored_path = str(keymap.get(self.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
            if stored_path:
                resolved_path = self._resolve_config_relative_path(stored_path, config_root)
                relative_path = self._to_config_relative_or_absolute(resolved_path, config_root)
                normalized_for_collision = self._normalize_path_separators(relative_path)
                if normalized_for_collision in used_relative_paths:
                    base_name = self._resolve_keymap_file_base_name(keymap)
                    relative_path = self._allocate_unique_keymap_path(base_name, used_relative_paths)
                else:
                    used_relative_paths.add(normalized_for_collision)
            else:
                base_name = self._resolve_keymap_file_base_name(keymap)
                if keymaps_dir:
                    relative_path = self._allocate_unique_absolute_path(
                        keymaps_dir,
                        base_name,
                        "keymap",
                        used_relative_paths,
                        config_root,
                    )
                else:
                    relative_path = self._allocate_unique_keymap_path(base_name, used_relative_paths)
            resolved_paths.append(
                {
                    "id": keymap_id,
                    "path": relative_path,
                    "payload": self._build_keymap_file_payload(keymap),
                }
            )
        return resolved_paths

    def _build_keymap_file_payload(self, keymap: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": str(keymap.get("label") or "").strip(),
            "mappings": safe_deepcopy(keymap.get("mappings", {}))
            if isinstance(keymap.get("mappings"), dict)
            else {},
        }

    def _build_trigger_set_payloads(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
        trigger_set_path: str,
        sequences_dir: str = "",
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        triggers = runtime.get("triggers", [])
        if not isinstance(triggers, list):
            return {"triggers": []}, []

        used_paths: set[str] = set()
        trigger_entries: list[dict[str, Any]] = []
        sequence_payloads: list[dict[str, Any]] = []
        for trigger in triggers:
            if not isinstance(trigger, dict):
                continue

            key = normalize_key_name(str(trigger.get("key") or ""))
            if not key:
                continue

            sequence_path = self._resolve_sequence_save_path(
                trigger,
                config_root=config_root,
                trigger_set_path=trigger_set_path,
                sequences_dir=sequences_dir,
                used_paths=used_paths,
            )
            resolved_sequence_path = self._resolve_config_relative_path(sequence_path, config_root)
            stored_sequence_path = self._to_config_relative_or_absolute(resolved_sequence_path, config_root)
            trigger_entries.append(
                {
                    "key": key,
                    "suppress": bool(trigger.get("suppress", True)),
                    "sequence_path": stored_sequence_path,
                }
            )
            sequence_payloads.append(
                {
                    "key": key,
                    "path": stored_sequence_path,
                    "resolved_path": resolved_sequence_path,
                    "payload": self._build_sequence_payload(trigger),
                }
            )

        return {"triggers": trigger_entries}, sequence_payloads

    def _resolve_sequence_save_path(
        self,
        trigger: dict[str, Any],
        *,
        config_root: str,
        trigger_set_path: str,
        sequences_dir: str,
        used_paths: set[str],
    ) -> str:
        source_path = str(trigger.get(self.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        if source_path:
            resolved_source_path = self._resolve_config_relative_path(source_path, config_root)
            stored_source_path = self._to_config_relative_or_absolute(resolved_source_path, config_root)
            normalized_source_path = self._normalize_path_separators(stored_source_path)
            if normalized_source_path not in used_paths:
                used_paths.add(normalized_source_path)
                return stored_source_path

        base_name = self._resolve_sequence_file_base_name(trigger)
        if self._is_default_trigger_set_area(trigger_set_path, config_root):
            return self._allocate_unique_relative_path(self.SEQUENCES_RELATIVE_DIR, base_name, "sequence", used_paths)

        sequence_dir = sequences_dir or os.path.join(os.path.dirname(os.path.abspath(trigger_set_path)), "sequences")
        return self._allocate_unique_absolute_path(sequence_dir, base_name, "sequence", used_paths, config_root)

    def _build_sequence_payload(self, trigger: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": str(trigger.get("label") or "").strip(),
            "run_to_end": bool(trigger.get("run_to_end", False)),
            "run_to_end_delay_ms": self._coerce_nonnegative_int(trigger.get("run_to_end_delay_ms", 300), 300),
            "actions": safe_deepcopy(trigger.get("actions", []))
            if isinstance(trigger.get("actions"), list)
            else [],
        }

    def _normalize_sequence_payload(self, sequence: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": str(sequence.get("label") or "").strip(),
            "run_to_end": bool(sequence.get("run_to_end", False)),
            "run_to_end_delay_ms": self._coerce_nonnegative_int(sequence.get("run_to_end_delay_ms", 300), 300),
            "actions": safe_deepcopy(sequence.get("actions", []))
            if isinstance(sequence.get("actions"), list)
            else [],
        }

    def _resolve_sequence_file_base_name(self, trigger: dict[str, Any]) -> str:
        for candidate in (trigger.get("label"), trigger.get("key"), "sequence"):
            slug = self._slugify_file_stem(candidate)
            if slug:
                return slug
        return "sequence"

    def _is_default_trigger_set_area(self, trigger_set_path: str, config_root: str) -> bool:
        try:
            trigger_sets_dir = os.path.join(os.path.abspath(config_root), "user", "trigger_sets")
            return os.path.commonpath([os.path.abspath(trigger_set_path), trigger_sets_dir]) == trigger_sets_dir
        except Exception:
            return False

    def _allocate_unique_relative_path(
        self,
        relative_dir: str,
        base_name: str,
        fallback: str,
        used_paths: set[str],
    ) -> str:
        stem = self._slugify_file_stem(base_name) or fallback
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            candidate = os.path.join(relative_dir, f"{stem}{suffix}.json")
            normalized_candidate = self._normalize_path_separators(candidate)
            if normalized_candidate not in used_paths:
                used_paths.add(normalized_candidate)
                return normalized_candidate
            index += 1

    def _allocate_unique_absolute_path(
        self,
        directory: str,
        base_name: str,
        fallback: str,
        used_paths: set[str],
        config_root: str,
    ) -> str:
        stem = self._slugify_file_stem(base_name) or fallback
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            candidate = os.path.join(directory, f"{stem}{suffix}.json")
            stored = self._to_config_relative_or_absolute(candidate, config_root)
            normalized_candidate = self._normalize_path_separators(stored)
            if normalized_candidate not in used_paths:
                used_paths.add(normalized_candidate)
                return stored
            index += 1

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
        raw_triggers = sanitized.get("triggers")
        if isinstance(raw_triggers, list):
            cleaned_triggers: list[dict[str, Any]] = []
            for trigger in raw_triggers:
                if not isinstance(trigger, dict):
                    continue
                cleaned = safe_deepcopy(trigger)
                cleaned.pop(self.INTERNAL_SEQUENCE_SOURCE_PATH, None)
                cleaned.pop(self.INTERNAL_SEQUENCE_IMPORTED, None)
                cleaned.pop(self.INTERNAL_SEQUENCE_DIRTY, None)
                cleaned_triggers.append(cleaned)
            sanitized["triggers"] = cleaned_triggers

        raw_keymaps = sanitized.get("keymaps")
        if isinstance(raw_keymaps, list):
            cleaned_keymaps: list[dict[str, Any]] = []
            for keymap in raw_keymaps:
                if not isinstance(keymap, dict):
                    continue
                cleaned = safe_deepcopy(keymap)
                cleaned.pop(self.INTERNAL_KEYMAP_SOURCE_PATH, None)
                cleaned.pop(self.INTERNAL_KEYMAP_IMPORTED, None)
                cleaned.pop(self.INTERNAL_KEYMAP_DIRTY, None)
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
        os.makedirs(os.path.join(config_root, "user", "sequences"), exist_ok=True)

    def _startup_entry_path(self, config_root: str) -> str:
        return os.path.join(config_root, "config.json")

    def _default_keymap_set_path(self, config_root: str) -> str:
        return self._resolve_config_relative_path(self.KEYMAP_SET_RELATIVE_PATH, config_root)

    def _default_legacy_config_path(self, config_root: str) -> str:
        return self._resolve_config_relative_path(self.LEGACY_CONFIG_RELATIVE_PATH, config_root)

    def _infer_config_root_from_keymap_set_path(self, keymap_set_path: str) -> str:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(keymap_set_path))))

    def _to_config_relative_or_absolute(self, path: str, config_root: str) -> str:
        absolute_path = os.path.abspath(path)
        absolute_config_root = os.path.abspath(config_root)
        try:
            if os.path.commonpath([absolute_path, absolute_config_root]) == absolute_config_root:
                relative_path = os.path.relpath(absolute_path, absolute_config_root)
                return self._normalize_path_separators(relative_path)
        except Exception:
            pass
        return self._normalize_path_separators(absolute_path)

    def _to_config_relative_path(self, path: str, config_root: str) -> str:
        return self._to_config_relative_or_absolute(path, config_root)

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
        return self._slugify_file_stem(value)

    def _slugify_file_stem(self, value: Any) -> str:
        normalized = str(value or "").strip()
        normalized = re.sub(r'[\\/:*?"<>|]+', "_", normalized)
        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip(" ._")
        if not normalized:
            return ""
        reserved_names = {
            "con",
            "prn",
            "aux",
            "nul",
            "com1",
            "com2",
            "com3",
            "com4",
            "com5",
            "com6",
            "com7",
            "com8",
            "com9",
            "lpt1",
            "lpt2",
            "lpt3",
            "lpt4",
            "lpt5",
            "lpt6",
            "lpt7",
            "lpt8",
            "lpt9",
        }
        if normalized.lower() in reserved_names:
            normalized = f"{normalized}_"
        return normalized

    def _coerce_nonnegative_int(self, value: Any, default: int) -> int:
        try:
            number = int(value)
        except Exception:
            number = int(default)
        if number < 0:
            number = 0
        return number

    def _load_optional_json(self, path: str) -> Any:
        if not path or not os.path.exists(path):
            return None
        try:
            return self.repository.load_json(path)
        except Exception:
            return None
