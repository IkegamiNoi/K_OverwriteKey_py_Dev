from __future__ import annotations

import os
from typing import Any

from keyseq.domain.config import (
    DEFAULT_RUN_TO_END_DELAY_MS,
    HOOK_KEY_FIELDS,
    HOOK_STOP_KEY,
    HOOK_TOGGLE_KEY,
    ensure_config_compatibility,
    normalize_hotkey_presets,
    normalize_hook_key_pair,
    normalize_key_name,
    resolve_hook_keys_individual,
    safe_deepcopy,
)


def load_split_config(service, *, config_root: str, keymap_set_path: str) -> dict[str, Any]:
    keymap_set = service._load_optional_json(keymap_set_path)
    if not isinstance(keymap_set, dict):
        raise ValueError("keymap_set.json の読込に失敗しました。")
    return build_runtime_data_from_split(service, keymap_set, config_root=config_root)


def load_global_hook_keys(service, *, config_root: str) -> tuple[str, str]:
    """config/config.json（起動エントリ）の hook キー全体デフォルトを (stop, toggle) で返す。

    読めない / 未設定なら ("", "")。
    """
    if not config_root:
        return "", ""

    startup = service._load_optional_json(service._startup_entry_path(config_root))
    if not isinstance(startup, dict):
        return "", ""
    return normalize_hook_key_pair(
        startup.get(HOOK_STOP_KEY),
        startup.get(HOOK_TOGGLE_KEY),
    )


def load_global_hotkey_presets_path(service, *, config_root: str) -> str:
    """config/config.json（起動エントリ）のグローバルプリセットパスを返す。

    返すのは保存されている表記のまま。未設定・空・非文字列・読込失敗・config_root 空
    のときは既定へ縮退する。
    """
    default_path = service.HOTKEY_PRESETS_RELATIVE_PATH
    if not config_root:
        return default_path

    startup = service._load_optional_json(service._startup_entry_path(config_root))
    if not isinstance(startup, dict):
        return default_path

    raw_hotkey_presets_path = startup.get("hotkey_presets_path")
    if not isinstance(raw_hotkey_presets_path, str):
        return default_path

    return raw_hotkey_presets_path.strip() or default_path


def load_global_hotkey_presets(service, *, config_root: str) -> list[Any] | None:
    """config.json が指すグローバルプリセットを、読めた場合だけ返す。"""
    try:
        stored_path = load_global_hotkey_presets_path(service, config_root=config_root)
        resolved_path = service._resolve_config_relative_path(stored_path, config_root)
        loaded = service._load_optional_json(resolved_path)
    except Exception:
        return None

    if not isinstance(loaded, dict):
        return None
    items = loaded.get("hotkey_presets")
    if not isinstance(items, list):
        return None
    return normalize_hotkey_presets(items)


def build_runtime_data_from_split(
    service,
    keymap_set: dict[str, Any],
    *,
    config_root: str,
) -> dict[str, Any]:
    runtime = service.new_default_data()

    for key in (
        *HOOK_KEY_FIELDS,
        "keyboard_layout",
        "keyboard_show_physical_key_labels",
        "debug_jis_special_key_events",
    ):
        if key in keymap_set:
            runtime[key] = safe_deepcopy(keymap_set.get(key))

    runtime["hook_keys_individual"] = resolve_hook_keys_individual(keymap_set)
    if not runtime["hook_keys_individual"]:
        runtime[HOOK_STOP_KEY], runtime[HOOK_TOGGLE_KEY] = load_global_hook_keys(
            service, config_root=config_root
        )

    runtime["external_keyboard_layouts"] = normalize_external_keyboard_layouts(
        service,
        keymap_set.get("external_keyboard_layouts"),
        config_root=config_root,
    )
    triggers, trigger_set_parent_refs = load_trigger_set(
        service,
        keymap_set.get("trigger_set_path"),
        config_root=config_root,
    )
    runtime["triggers"] = triggers
    trigger_set_path = str(keymap_set.get("trigger_set_path") or "").strip()
    if trigger_set_path:
        runtime[service.INTERNAL_TRIGGER_SET_SOURCE_PATH] = trigger_set_path
    if trigger_set_parent_refs is not None:
        runtime[service.INTERNAL_TRIGGER_SET_PARENT_REFS] = trigger_set_parent_refs
    hotkey_presets = load_global_hotkey_presets(service, config_root=config_root)
    if hotkey_presets is not None:
        runtime["hotkey_presets"] = hotkey_presets

    keymaps: list[dict[str, Any]] = []
    keymap_switch_keys: dict[str, str] = {}
    loaded_keymap_ids_by_path: dict[str, str] = {}
    used_keymap_ids: set[str] = set()

    active_keymap_path = str(keymap_set.get("active_keymap_path") or "").strip()
    active_keymap_resolved_path = (
        service._resolve_config_relative_path(active_keymap_path, config_root)
        if active_keymap_path
        else ""
    )

    raw_keymaps = keymap_set.get("keymaps")
    if isinstance(raw_keymaps, list):
        for entry in raw_keymaps:
            loaded_entry = load_keymap_entry(
                service,
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
        active_keymap = load_keymap_entry(
            service,
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
    normalized = ensure_config_compatibility(runtime)
    normalized_keymaps = normalized.get("keymaps", [])
    for keymap, normalized_keymap in zip(keymaps, normalized_keymaps):
        parent_refs = service._normalize_parent_refs(keymap.get(service.INTERNAL_KEYMAP_PARENT_REFS))
        if parent_refs is not None:
            normalized_keymap[service.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
    return normalized


def load_keymap_entry(
    service,
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

    resolved_path = service._resolve_config_relative_path(stored_path, config_root)
    raw_keymap = service._load_optional_json(resolved_path)
    if not isinstance(raw_keymap, dict):
        return None

    keymap_id = service._generate_keymap_id(stored_path, raw_keymap, used_keymap_ids)
    used_keymap_ids.add(keymap_id)

    mappings = raw_keymap.get("mappings")
    if not isinstance(mappings, dict):
        mappings = {}

    loaded_entry = {
        "resolved_path": resolved_path,
        "switch_key": switch_key,
        "keymap": {
            "id": keymap_id,
            "label": str(raw_keymap.get("label") or "").strip(),
            "mappings": safe_deepcopy(mappings),
            service.INTERNAL_KEYMAP_SOURCE_PATH: stored_path,
            service.INTERNAL_KEYMAP_IMPORTED: False,
            service.INTERNAL_KEYMAP_DIRTY: False,
        },
    }
    parent_refs = service._normalize_parent_refs(raw_keymap.get(service.PARENT_REFS_KEY))
    if parent_refs is not None:
        loaded_entry["keymap"][service.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
    return loaded_entry


def load_trigger_set(
    service,
    path_value: Any,
    *,
    config_root: str,
) -> tuple[list[dict[str, Any]], list[str] | None]:
    stored_path = str(path_value or "").strip()
    if not stored_path:
        return [], None

    resolved_path = service._resolve_config_relative_path(stored_path, config_root)
    loaded = service._load_optional_json(resolved_path)
    if not isinstance(loaded, dict):
        return [], None
    return load_triggers_from_trigger_set(service, loaded, config_root=config_root, imported=False)


def load_triggers_from_trigger_set(
    service,
    trigger_set: dict[str, Any],
    *,
    config_root: str,
    imported: bool,
) -> tuple[list[dict[str, Any]], list[str] | None]:
    trigger_set_parent_refs = service._normalize_parent_refs(trigger_set.get(service.PARENT_REFS_KEY))
    raw_triggers = trigger_set.get("triggers")
    if not isinstance(raw_triggers, list):
        return [], trigger_set_parent_refs

    triggers: list[dict[str, Any]] = []
    for raw_trigger in raw_triggers:
        if not isinstance(raw_trigger, dict):
            continue

        trigger = {
            "key": normalize_key_name(str(raw_trigger.get("key") or "")),
            "suppress": bool(raw_trigger.get("suppress", True)),
            "label": str(raw_trigger.get("label") or "").strip(),
            "run_to_end": bool(raw_trigger.get("run_to_end", False)),
            "run_to_end_delay_ms": service._coerce_nonnegative_int(
                raw_trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                DEFAULT_RUN_TO_END_DELAY_MS,
            ),
            "actions": safe_deepcopy(raw_trigger.get("actions", []))
            if isinstance(raw_trigger.get("actions"), list)
            else [],
        }
        sequence_path = str(raw_trigger.get("sequence_path") or "").strip()
        if sequence_path:
            resolved_sequence_path = service._resolve_config_relative_path(sequence_path, config_root)
            sequence = service._load_optional_json(resolved_sequence_path)
            if isinstance(sequence, dict):
                normalized_sequence = service._normalize_sequence_payload(sequence)
                trigger.update(normalized_sequence)
                parent_refs = service._normalize_parent_refs(sequence.get(service.PARENT_REFS_KEY))
                if parent_refs is not None:
                    trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
                trigger[service.INTERNAL_SEQUENCE_SOURCE_PATH] = (
                    service.to_config_relative_or_absolute(sequence_path, config_root)
                    if config_root
                    else sequence_path
                )
                trigger[service.INTERNAL_SEQUENCE_IMPORTED] = bool(imported)
                trigger[service.INTERNAL_SEQUENCE_DIRTY] = False
        triggers.append(trigger)

    normalized = ensure_config_compatibility({"triggers": triggers}).get("triggers", [])
    for trigger, normalized_trigger in zip(triggers, normalized):
        parent_refs = service._normalize_parent_refs(trigger.get(service.INTERNAL_SEQUENCE_PARENT_REFS))
        if parent_refs is not None:
            normalized_trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
    return normalized, trigger_set_parent_refs


def normalize_external_keyboard_layouts(
    service,
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

        resolved_path = service._resolve_config_relative_path(stored_path, config_root)
        runtime_path = resolved_path
        try:
            relative_path = os.path.relpath(runtime_path, base_dir)
            if not relative_path.startswith(".."):
                runtime_path = service._normalize_path_separators(relative_path)
        except Exception:
            runtime_path = service._normalize_path_separators(runtime_path)
        normalized.append({"path": runtime_path})
    return normalized
