from __future__ import annotations

from typing import Any

from keyseq.domain.config import normalize_key_name


class KeymapService:
    @staticmethod
    def get_keymaps(data: dict[str, Any]) -> list[dict[str, Any]]:
        keymaps = data.get("keymaps", [])
        if isinstance(keymaps, list):
            return keymaps
        return []

    @staticmethod
    def find_keymap(data: dict[str, Any], keymap_id: str) -> dict[str, Any] | None:
        normalized = normalize_key_name(keymap_id)
        if not normalized:
            return None
        for keymap in KeymapService.get_keymaps(data):
            if normalize_key_name(keymap.get("id", "")) == normalized:
                return keymap
        return None

    @staticmethod
    def get_active_keymap_id(data: dict[str, Any]) -> str:
        keymaps = KeymapService.get_keymaps(data)
        configured = normalize_key_name(data.get("active_keymap_id", ""))
        if configured and KeymapService.find_keymap(data, configured):
            return configured
        if keymaps:
            return normalize_key_name(keymaps[0].get("id", ""))
        return ""

    @staticmethod
    def get_active_keymap(data: dict[str, Any]) -> dict[str, Any] | None:
        return KeymapService.find_keymap(data, KeymapService.get_active_keymap_id(data))

    @staticmethod
    def get_active_keymap_label(data: dict[str, Any]) -> str:
        keymap = KeymapService.get_active_keymap(data)
        if not keymap:
            return ""
        label = str(keymap.get("label") or "").strip()
        if label:
            return label
        return normalize_key_name(keymap.get("id", ""))

    @staticmethod
    def find_mapping_target(data: dict[str, Any], source_key: str) -> str:
        keymap = KeymapService.get_active_keymap(data)
        if not isinstance(keymap, dict):
            return ""
        mappings = keymap.get("mappings", {})
        if not isinstance(mappings, dict):
            return ""
        return normalize_key_name(mappings.get(normalize_key_name(source_key), ""))

    @staticmethod
    def has_any_mapping(data: dict[str, Any]) -> bool:
        return bool(KeymapService.collect_source_keys(data))

    @staticmethod
    def collect_source_keys(data: dict[str, Any]) -> set[str]:
        keys: set[str] = set()
        for keymap in KeymapService.get_keymaps(data):
            mappings = keymap.get("mappings", {})
            if not isinstance(mappings, dict):
                continue
            for source in mappings.keys():
                normalized = normalize_key_name(str(source or ""))
                if normalized:
                    keys.add(normalized)
        return keys

    @staticmethod
    def source_key_exists(data: dict[str, Any], key: str) -> bool:
        normalized = normalize_key_name(key)
        if not normalized:
            return False
        return normalized in KeymapService.collect_source_keys(data)

    @staticmethod
    def cycle_active_keymap(data: dict[str, Any]) -> str:
        keymaps = KeymapService.get_keymaps(data)
        if not keymaps:
            data["active_keymap_id"] = ""
            return ""

        keymap_ids = [normalize_key_name(item.get("id", "")) for item in keymaps]
        keymap_ids = [item for item in keymap_ids if item]
        if not keymap_ids:
            data["active_keymap_id"] = ""
            return ""

        current = KeymapService.get_active_keymap_id(data)
        if current not in keymap_ids:
            next_id = keymap_ids[0]
        else:
            index = keymap_ids.index(current)
            next_id = keymap_ids[(index + 1) % len(keymap_ids)]

        data["active_keymap_id"] = next_id
        return next_id
