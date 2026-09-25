from __future__ import annotations

import os
from typing import Any

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP, CHILD_KEYMAP, CHILD_SEQUENCE, CHILD_TRIGGER_SET, SavePlan, compose_sequence_key
from keyseq.domain.keymap_triggers import iter_trigger_sets, trigger_set_members
from keyseq.domain.config import (
    DEFAULT_KEYBOARD_LAYOUT_ID,
    DEFAULT_RUN_TO_END_DELAY_MS,
    HOOK_STOP_KEY,
    HOOK_TOGGLE_KEY,
    normalize_key_name,
    resolve_hook_keys_individual,
    safe_deepcopy,
)
from . import save_path_resolution


def build_split_save_payloads(service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    startup_data: Any,
    startup_entry_loaded: bool = False,
    keymap_set_path: str,
    keymap_set_name_path: str = "",
    legacy_path: str,
    split_base_dir: str,
    save_plan: SavePlan,
) -> dict[str, Any]:
    keymaps_dir = os.path.join(split_base_dir, "keymaps") if split_base_dir else ""
    sequences_dir = os.path.join(split_base_dir, "sequences") if split_base_dir else ""
    keymap_payloads = build_keymap_payloads(service,
        runtime,
        config_root=config_root,
        keymaps_dir=keymaps_dir,
        parent_ref=keymap_set_path,
        keymap_set_name_path=keymap_set_name_path,
        save_plan=save_plan,
    )
    keymap_paths_by_id = {
        str(item["id"]): str(item["path"])
        for item in keymap_payloads
        if str(item.get("id") or "").strip() and str(item.get("path") or "").strip()
    }
    startup_payload = build_startup_payload(service,
        startup_data,
        startup_entry_loaded=startup_entry_loaded,
        config_root=config_root,
        keymap_set_path=keymap_set_path,
        legacy_path=legacy_path,
    )
    trigger_sets = []
    sequence_payloads = []
    used_trigger_paths = {
        service.canonical_path(entry.target_path, config_root)
        for entry in save_plan.entries
        if entry.kind == CHILD_TRIGGER_SET and entry.action == ACTION_SAVE_AS and entry.target_path
    }
    used_sequence_paths = {
        service.canonical_path(entry.target_path, config_root)
        for entry in save_plan.entries
        if entry.kind == CHILD_SEQUENCE and entry.action == ACTION_SAVE_AS and entry.target_path
    }
    keymaps_by_id = {item["id"]: item for item in keymap_payloads}
    for owner, members, triggers in iter_trigger_sets(runtime):
        key = str(owner["id"])
        if not triggers and not owner.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH):
            for member in members:
                keymaps_by_id[member["id"]]["payload"]["trigger_set_path"] = ""
            continue
        parent = keymaps_by_id[key]["resolved_path"]
        path = save_path_resolution.resolve_trigger_set_save_path(
            service, owner, config_root=config_root, keymap_set_path=parent,
            split_base_dir=split_base_dir, save_plan=save_plan,
            used_paths=used_trigger_paths,
        )
        entry = save_plan.entry_for(CHILD_TRIGGER_SET, key)
        action = entry.action if entry else ACTION_SAVE
        skip = action == ACTION_SKIP
        payload, sequences = build_trigger_set_payloads(
            service, runtime, config_root=config_root, trigger_set_path=path,
            sequences_dir=sequences_dir, parent_ref=parent, save_plan=save_plan,
            trigger_set_id=key, used_paths=used_sequence_paths,
        )
        for member in members[1:]:
            refs = service._merge_parent_ref(
                payload.get(service.PARENT_REFS_KEY),
                keymaps_by_id[member["id"]]["resolved_path"],
                config_root=config_root,
            )
            if refs is not None:
                payload[service.PARENT_REFS_KEY] = refs
        source = str(owner.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH) or "")
        trigger_sets.append({
            "key": key, "path": service.to_config_relative_or_absolute(path, config_root),
            "resolved_path": path, "source_path": service._resolve_config_relative_path(source, config_root) if source else "",
            "action": action, "skip": skip, "payload": payload,
            "parent_ids": [str(member["id"]) for member in members],
        })
        sequence_payloads.extend(sequences)
        indexed_path = service.to_config_relative_or_absolute(path, config_root) if not skip or os.path.exists(path) else ""
        for member in members:
            keymaps_by_id[member["id"]]["payload"]["trigger_set_path"] = indexed_path
    keymap_set_payload = build_keymap_set_payload(
        service, runtime, keymap_paths_by_id, config_root=config_root,
        trigger_set_path="",
    )
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
        "trigger_sets": trigger_sets,
        "keymaps": serialized_keymaps,
        "sequences": sequence_payloads,
    }

def build_keymap_payloads(service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    keymaps_dir: str = "",
    parent_ref: str = "",
    keymap_set_name_path: str = "",
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
                base_name = save_path_resolution.resolve_keymap_file_base_name(
                    service, keymap, keymap_set_name_path
                )
                relative_path = save_path_resolution.allocate_unique_keymap_path(
                    service,
                    base_name,
                    used_relative_paths,
                    config_root,
                )
            else:
                used_relative_paths.add(collision_key)
        else:
            base_name = save_path_resolution.resolve_keymap_file_base_name(
                service, keymap, keymap_set_name_path
            )
            if keymaps_dir:
                relative_path = save_path_resolution.allocate_unique_absolute_path(
                    service,
                    keymaps_dir,
                    base_name,
                    "keymap",
                    used_relative_paths,
                    config_root,
                )
            else:
                relative_path = save_path_resolution.allocate_unique_keymap_path(
                    service,
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
    trigger_set_id: str | None = None,
    used_paths: set[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    members = trigger_set_members(runtime, trigger_set_id)
    owner = members[0] if members else {}
    triggers = next((items for candidate, _, items in iter_trigger_sets(runtime) if candidate is owner), [])
    if not isinstance(triggers, list):
        triggers = []

    used_paths = used_paths if used_paths is not None else set()
    trigger_entries: list[dict[str, Any]] = []
    sequence_payloads: list[dict[str, Any]] = []
    for trigger in triggers:
        if not isinstance(trigger, dict):
            continue

        key = normalize_key_name(str(trigger.get("key") or ""))
        if not key:
            continue

        sequence_path = save_path_resolution.resolve_sequence_save_path(
            service,
            trigger,
            config_root=config_root,
            trigger_set_path=trigger_set_path,
            sequences_dir=sequences_dir,
            used_paths=used_paths,
        )
        plan_key = compose_sequence_key(trigger_set_id, key) if trigger_set_id is not None else key
        entry = save_plan.entry_for(CHILD_SEQUENCE, plan_key)
        action = entry.action if entry is not None else ACTION_SAVE
        if action == ACTION_SAVE_AS and entry is not None:
            sequence_path = service.to_config_relative_or_absolute(
                service._resolve_config_relative_path(entry.target_path, config_root),
                config_root,
            )
        resolved_sequence_path = service._resolve_config_relative_path(sequence_path, config_root)
        used_paths.add(service.canonical_path(resolved_sequence_path, config_root))
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
                "key": plan_key,
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
        service._normalize_parent_refs(owner.get(service.INTERNAL_TRIGGER_SET_PARENT_REFS)),
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
) -> dict[str, Any]:
    legacy = runtime.get(service.INTERNAL_LEGACY_TRIGGER_SET, {})
    trigger_set_path = str(legacy.get("path") or "") if legacy.get("state") == "unused" else ""
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

    hook_keys_individual = resolve_hook_keys_individual(runtime)
    hotkey_presets_individual = runtime.get("hotkey_presets_individual", False)
    return {
        "trigger_set_path": service.to_config_relative_or_absolute(trigger_set_path, config_root)
        if trigger_set_path
        else "",
        "hotkey_presets_path": service.to_config_relative_or_absolute(
            str(runtime.get("hotkey_presets_path") or "").strip(),
            config_root,
        )
        if str(runtime.get("hotkey_presets_path") or "").strip()
        else "",
        "hotkey_presets_individual": (
            hotkey_presets_individual if isinstance(hotkey_presets_individual, bool) else False
        ),
        "active_keymap_path": active_keymap_path,
        "keymaps": keymap_entries,
        "hook_stop_key": normalize_key_name(runtime.get(HOOK_STOP_KEY, "")) if hook_keys_individual else "",
        "hook_toggle_key": normalize_key_name(runtime.get(HOOK_TOGGLE_KEY, "")) if hook_keys_individual else "",
        "hook_keys_individual": hook_keys_individual,
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
    startup_entry_loaded: bool = False,
    config_root: str,
    keymap_set_path: str,
    legacy_path: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if isinstance(startup_data, dict):
        payload.update(safe_deepcopy(startup_data))

    payload.pop("config_path", None)
    existing_entry = payload.get("keymap_set_path")
    if not (isinstance(existing_entry, str) and existing_entry and startup_entry_loaded):
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
        "id": normalize_key_name(keymap.get("id", "")),
        "trigger_set_path": str(keymap.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH) or ""),
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
