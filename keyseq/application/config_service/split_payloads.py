from __future__ import annotations

import os
from typing import Any

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP, CHILD_KEYMAP, CHILD_SEQUENCE, CHILD_TRIGGER_SET, SavePlan
from keyseq.domain.config import DEFAULT_KEYBOARD_LAYOUT_ID, DEFAULT_RUN_TO_END_DELAY_MS, normalize_key_name, safe_deepcopy


def build_split_save_payloads(service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    startup_data: Any,
    keymap_set_path: str,
    legacy_path: str,
    split_base_dir: str,
    save_plan: SavePlan,
) -> dict[str, Any]:
    keymaps_dir = os.path.join(split_base_dir, "keymaps") if split_base_dir else ""
    sequences_dir = os.path.join(split_base_dir, "sequences") if split_base_dir else ""
    trigger_set_path = service._resolve_trigger_set_save_path(
        runtime,
        config_root=config_root,
        keymap_set_path=keymap_set_path,
        split_base_dir=split_base_dir,
        save_plan=save_plan,
    )
    hotkey_presets_path = (
        os.path.join(split_base_dir, "hotkey_presets", "default.json")
        if split_base_dir
        else service._resolve_config_relative_path(service.HOTKEY_PRESETS_RELATIVE_PATH, config_root)
    )
    keymap_payloads = build_keymap_payloads(service,
        runtime,
        config_root=config_root,
        keymaps_dir=keymaps_dir,
        parent_ref=keymap_set_path,
        save_plan=save_plan,
    )
    keymap_paths_by_id = {
        str(item["id"]): str(item["path"])
        for item in keymap_payloads
        if str(item.get("id") or "").strip() and str(item.get("path") or "").strip()
    }
    startup_payload = build_startup_payload(service,
        startup_data,
        config_root=config_root,
        keymap_set_path=keymap_set_path,
        legacy_path=legacy_path,
    )
    trigger_payload, sequence_payloads = build_trigger_set_payloads(service,
        runtime,
        config_root=config_root,
        trigger_set_path=trigger_set_path,
        sequences_dir=sequences_dir,
        parent_ref=keymap_set_path,
        save_plan=save_plan,
    )
    trigger_set_entry = save_plan.entry_for(CHILD_TRIGGER_SET)
    trigger_set_skip = bool(trigger_set_entry and trigger_set_entry.action == ACTION_SKIP)
    trigger_set_exists = os.path.exists(trigger_set_path)
    indexed_trigger_set_path = trigger_set_path if not trigger_set_skip or trigger_set_exists else ""
    keymap_set_payload = build_keymap_set_payload(service,
        runtime,
        keymap_paths_by_id,
        config_root=config_root,
        trigger_set_path=indexed_trigger_set_path,
        hotkey_presets_path=hotkey_presets_path,
    )
    hotkey_presets_payload = {
        "hotkey_presets": safe_deepcopy(runtime.get("hotkey_presets", []))
        if isinstance(runtime.get("hotkey_presets"), list)
        else []
    }
    serialized_keymaps = [
        {
            "path": str(item["path"]),
            "resolved_path": str(item["resolved_path"]),
            "payload": item["payload"],
            "id": item["id"],
            "skip": item["skip"],
        }
        for item in keymap_payloads
    ]
    return {
        "startup": startup_payload,
        "keymap_set": keymap_set_payload,
        "trigger_set_path": trigger_set_path,
        "trigger_set": trigger_payload,
        "trigger_set_skip": trigger_set_skip,
        "hotkey_presets_path": hotkey_presets_path,
        "hotkey_presets": hotkey_presets_payload,
        "keymaps": serialized_keymaps,
        "sequences": sequence_payloads,
    }

def build_keymap_payloads(service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    keymaps_dir: str = "",
    parent_ref: str = "",
    save_plan: SavePlan,
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

        stored_path = str(keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        if stored_path:
            resolved_path = service._resolve_config_relative_path(stored_path, config_root)
            relative_path = service.to_config_relative_or_absolute(resolved_path, config_root)
            collision_key = service.canonical_path(relative_path, config_root)
            if collision_key in used_relative_paths:
                base_name = service._resolve_keymap_file_base_name(keymap)
                relative_path = service._allocate_unique_keymap_path(
                    base_name,
                    used_relative_paths,
                    config_root,
                )
            else:
                used_relative_paths.add(collision_key)
        else:
            base_name = service._resolve_keymap_file_base_name(keymap)
            if keymaps_dir:
                relative_path = service._allocate_unique_absolute_path(
                    keymaps_dir,
                    base_name,
                    "keymap",
                    used_relative_paths,
                    config_root,
                )
            else:
                relative_path = service._allocate_unique_keymap_path(
                    base_name,
                    used_relative_paths,
                    config_root,
                )
        entry = save_plan.entry_for(CHILD_KEYMAP, keymap_id)
        action = entry.action if entry is not None else ACTION_SAVE
        if action == ACTION_SAVE_AS and entry is not None:
            resolved_target_path = service._resolve_config_relative_path(entry.target_path, config_root)
            relative_path = service.to_config_relative_or_absolute(resolved_target_path, config_root)
            used_relative_paths.add(service.canonical_path(relative_path, config_root))
        source_path = str(keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        resolved_source_path = (
            service._resolve_config_relative_path(source_path, config_root)
            if source_path
            else ""
        )
        skip = action == ACTION_SKIP
        index_path = relative_path
        if skip:
            index_path = (
                service.to_config_relative_or_absolute(resolved_source_path, config_root)
                if resolved_source_path and os.path.exists(resolved_source_path)
                else ""
            )
        resolved_paths.append(
            {
                "id": keymap_id,
                "path": index_path,
                "resolved_path": service._resolve_config_relative_path(relative_path, config_root),
                "source_path": resolved_source_path,
                "action": action,
                "skip": skip,
                "payload": build_keymap_file_payload(service,
                    keymap,
                    parent_ref=parent_ref,
                    config_root=config_root,
                    target_path=service._resolve_config_relative_path(relative_path, config_root)
                    if not skip
                    else "",
                ),
            }
        )
    return resolved_paths

def build_trigger_set_payloads(service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    trigger_set_path: str,
    sequences_dir: str = "",
    parent_ref: str = "",
    save_plan: SavePlan,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    triggers = runtime.get("triggers", [])
    if not isinstance(triggers, list):
        triggers = []

    used_paths: set[str] = set()
    trigger_entries: list[dict[str, Any]] = []
    sequence_payloads: list[dict[str, Any]] = []
    for trigger in triggers:
        if not isinstance(trigger, dict):
            continue

        key = normalize_key_name(str(trigger.get("key") or ""))
        if not key:
            continue

        sequence_path = service._resolve_sequence_save_path(
            trigger,
            config_root=config_root,
            trigger_set_path=trigger_set_path,
            sequences_dir=sequences_dir,
            used_paths=used_paths,
        )
        entry = save_plan.entry_for(CHILD_SEQUENCE, key)
        action = entry.action if entry is not None else ACTION_SAVE
        if action == ACTION_SAVE_AS and entry is not None:
            sequence_path = service.to_config_relative_or_absolute(
                service._resolve_config_relative_path(entry.target_path, config_root),
                config_root,
            )
        resolved_sequence_path = service._resolve_config_relative_path(sequence_path, config_root)
        stored_sequence_path = service.to_config_relative_or_absolute(resolved_sequence_path, config_root)
        source_path = str(trigger.get(service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        resolved_source_path = (
            service._resolve_config_relative_path(source_path, config_root)
            if source_path
            else ""
        )
        skip = action == ACTION_SKIP
        indexed_sequence_path = stored_sequence_path
        if skip:
            indexed_sequence_path = (
                service.to_config_relative_or_absolute(resolved_source_path, config_root)
                if resolved_source_path and os.path.exists(resolved_source_path)
                else ""
            )
        trigger_entries.append(
            {
                "key": key,
                "suppress": bool(trigger.get("suppress", True)),
                "sequence_path": indexed_sequence_path,
            }
        )
        sequence_payloads.append(
            {
                "key": key,
                "path": stored_sequence_path,
                "resolved_path": resolved_sequence_path,
                "source_path": resolved_source_path,
                "action": action,
                "skip": skip,
                "payload": build_sequence_payload(service,
                    trigger,
                    parent_ref=trigger_set_path,
                    config_root=config_root,
                    target_path=resolved_sequence_path if not skip else "",
                ),
            }
        )

    payload = {"triggers": trigger_entries}
    parent_refs = service._parent_refs_for_save(
        service._normalize_parent_refs(runtime.get(service.INTERNAL_TRIGGER_SET_PARENT_REFS)),
        target_path=trigger_set_path,
        parent_ref=parent_ref,
        config_root=config_root,
    )
    if parent_refs is not None:
        payload[service.PARENT_REFS_KEY] = parent_refs
    return payload, sequence_payloads

def build_keymap_set_payload(service,
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
        "trigger_set_path": service.to_config_relative_or_absolute(trigger_set_path, config_root)
        if trigger_set_path
        else "",
        "hotkey_presets_path": service.to_config_relative_or_absolute(hotkey_presets_path, config_root),
        "active_keymap_path": active_keymap_path,
        "keymaps": keymap_entries,
        "hook_stop_key": normalize_key_name(runtime.get("hook_stop_key", "")),
        "hook_toggle_key": normalize_key_name(runtime.get("hook_toggle_key", "")),
        "keyboard_layout": str(runtime.get("keyboard_layout") or DEFAULT_KEYBOARD_LAYOUT_ID).strip()
        or DEFAULT_KEYBOARD_LAYOUT_ID,
        "keyboard_show_physical_key_labels": bool(runtime.get("keyboard_show_physical_key_labels", False)),
        "debug_jis_special_key_events": bool(runtime.get("debug_jis_special_key_events", False)),
        "external_keyboard_layouts": safe_deepcopy(runtime.get("external_keyboard_layouts", []))
        if isinstance(runtime.get("external_keyboard_layouts"), list)
        else [],
    }

def build_startup_payload(service,
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
    payload["keymap_set_path"] = service.to_config_relative_or_absolute(keymap_set_path, config_root)
    try:
        payload["ui_font_delta_pt"] = int(payload.get("ui_font_delta_pt", 0) or 0)
    except Exception:
        payload["ui_font_delta_pt"] = 0
    payload["last_used_directory"] = str(payload.get("last_used_directory") or "")
    if legacy_path:
        payload["config_path"] = service.resolve_startup_relative_path(legacy_path, os.path.dirname(config_root))
    return payload

def build_keymap_file_payload(service,
    keymap: dict[str, Any],
    *,
    parent_ref: str = "",
    config_root: str = "",
    target_path: str = "",
) -> dict[str, Any]:
    payload = {
        "label": str(keymap.get("label") or "").strip(),
        "mappings": safe_deepcopy(keymap.get("mappings", {}))
        if isinstance(keymap.get("mappings"), dict)
        else {},
    }
    parent_refs = service._parent_refs_for_save(
        service._normalize_parent_refs(keymap.get(service.INTERNAL_KEYMAP_PARENT_REFS)),
        target_path=target_path,
        parent_ref=parent_ref,
        config_root=config_root,
    )
    if parent_refs is not None:
        payload[service.PARENT_REFS_KEY] = parent_refs
    return payload

def build_sequence_payload(service,
    trigger: dict[str, Any],
    *,
    parent_ref: str = "",
    config_root: str = "",
    target_path: str = "",
) -> dict[str, Any]:
    payload = {
        "label": str(trigger.get("label") or "").strip(),
        "run_to_end": bool(trigger.get("run_to_end", False)),
        "run_to_end_delay_ms": service._coerce_nonnegative_int(
            trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        ),
        "actions": safe_deepcopy(trigger.get("actions", []))
        if isinstance(trigger.get("actions"), list)
        else [],
    }
    parent_refs = service._parent_refs_for_save(
        service._normalize_parent_refs(trigger.get(service.INTERNAL_SEQUENCE_PARENT_REFS)),
        target_path=target_path,
        parent_ref=parent_ref,
        config_root=config_root,
    )
    if parent_refs is not None:
        payload[service.PARENT_REFS_KEY] = parent_refs
    return payload
