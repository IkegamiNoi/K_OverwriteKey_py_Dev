from __future__ import annotations

from typing import Any

from keyseq.domain.config import normalize_key_name

DEFAULT_KEYMAP_ID = "default"
DEFAULT_KEYMAP_LABEL = "Default"


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
    def set_active_keymap_id(data: dict[str, Any], keymap_id: str) -> bool:
        normalized = normalize_key_name(keymap_id)
        if not normalized:
            changed = bool(normalize_key_name(data.get("active_keymap_id", "")))
            data["active_keymap_id"] = ""
            return changed

        if not KeymapService.find_keymap(data, normalized):
            return False

        current = KeymapService.get_active_keymap_id(data)
        data["active_keymap_id"] = normalized
        return current != normalized

    @staticmethod
    def create_keymap(data: dict[str, Any]) -> dict[str, Any]:
        keymaps = data.get("keymaps")
        if not isinstance(keymaps, list):
            keymaps = []
            data["keymaps"] = keymaps
        had_keymaps = bool(keymaps)

        existing_ids = {
            normalize_key_name(item.get("id", ""))
            for item in keymaps
            if isinstance(item, dict)
        }
        index = 1
        while True:
            keymap_id = f"keymap_{index}"
            if keymap_id not in existing_ids:
                break
            index += 1

        created = {
            "id": keymap_id,
            "label": "",
            "mappings": {},
        }
        keymaps.append(created)

        if not had_keymaps:
            data["active_keymap_id"] = keymap_id

        return created

    @staticmethod
    def delete_keymap(data: dict[str, Any], keymap_id: str) -> tuple[bool, str]:
        keymaps = data.get("keymaps")
        if not isinstance(keymaps, list):
            data["keymaps"] = []
            data["active_keymap_id"] = ""
            return False, ""

        target = normalize_key_name(keymap_id)
        if not target:
            return False, KeymapService.get_active_keymap_id(data)

        target_index = None
        for index, keymap in enumerate(keymaps):
            if normalize_key_name(keymap.get("id", "")) == target:
                target_index = index
                break
        if target_index is None:
            return False, KeymapService.get_active_keymap_id(data)

        was_active = KeymapService.get_active_keymap_id(data) == target
        del keymaps[target_index]

        if not keymaps:
            data["active_keymap_id"] = ""
            return True, ""

        remaining_ids = [normalize_key_name(item.get("id", "")) for item in keymaps]
        current_active = normalize_key_name(data.get("active_keymap_id", ""))
        if was_active or current_active not in remaining_ids:
            fallback_index = min(target_index, len(keymaps) - 1)
            data["active_keymap_id"] = remaining_ids[fallback_index]

        return True, KeymapService.get_active_keymap_id(data)

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

    @staticmethod
    def ensure_active_keymap(data: dict[str, Any]) -> dict[str, Any]:
        current = KeymapService.get_active_keymap(data)
        if isinstance(current, dict):
            mappings = current.get("mappings")
            if not isinstance(mappings, dict):
                current["mappings"] = {}
            current.setdefault("label", "")
            return current

        keymaps = KeymapService.get_keymaps(data)
        if not keymaps:
            created = {
                "id": DEFAULT_KEYMAP_ID,
                "label": DEFAULT_KEYMAP_LABEL,
                "mappings": {},
            }
            data["keymaps"] = [created]
            data["active_keymap_id"] = DEFAULT_KEYMAP_ID
            return created

        fallback = keymaps[0]
        fallback.setdefault("label", "")
        mappings = fallback.get("mappings")
        if not isinstance(mappings, dict):
            fallback["mappings"] = {}
        data["active_keymap_id"] = normalize_key_name(fallback.get("id", ""))
        return fallback

    @staticmethod
    def set_mapping(data: dict[str, Any], source_key: str, target_key: str) -> tuple[str, bool]:
        keymap = KeymapService.ensure_active_keymap(data)
        keymap_id = normalize_key_name(keymap.get("id", ""))
        source = normalize_key_name(source_key)
        target = normalize_key_name(target_key)
        mappings = keymap.setdefault("mappings", {})
        if not isinstance(mappings, dict):
            mappings = {}
            keymap["mappings"] = mappings
        previous = normalize_key_name(mappings.get(source, ""))
        mappings[source] = target
        data["active_keymap_id"] = keymap_id
        return keymap_id, previous != target

    @staticmethod
    def clear_mapping(data: dict[str, Any], source_key: str) -> tuple[str, bool]:
        keymap = KeymapService.get_active_keymap(data)
        if not isinstance(keymap, dict):
            return "", False

        mappings = keymap.get("mappings", {})
        if not isinstance(mappings, dict):
            keymap["mappings"] = {}
            return normalize_key_name(keymap.get("id", "")), False

        source = normalize_key_name(source_key)
        if source not in mappings:
            return normalize_key_name(keymap.get("id", "")), False

        del mappings[source]
        return normalize_key_name(keymap.get("id", "")), True
