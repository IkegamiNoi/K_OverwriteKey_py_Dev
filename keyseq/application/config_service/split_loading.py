from __future__ import annotations

import os
from typing import Any

from keyseq.domain.config import (
    DEFAULT_RUN_TO_END_DELAY_MS,
    HOOK_KEY_FIELDS,
    HOOK_STOP_KEY,
    HOOK_TOGGLE_KEY,
    coerce_key_name,
    coerce_label,
    ensure_config_compatibility,
    normalize_hotkey_presets,
    normalize_hook_key_pair,
    normalize_key_name,
    resolve_hook_keys_individual,
    safe_deepcopy,
)
from . import save_path_resolution
from keyseq.application.keymap_service import KeymapService
from keyseq.domain.keymap_triggers import ensure_at_least_one_keymap


TriggerSetCache = dict[
    str, tuple[list[dict[str, Any]], list[str] | None, str, bool | None, bool | None]
]


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


def load_hotkey_presets_file(
    service,
    stored_path: Any,
    *,
    config_root: str,
) -> list[Any] | None:
    """プリセットファイルを読み、読めた場合だけ正規化済みの list を返す。"""
    if not isinstance(stored_path, str) or not stored_path.strip():
        return None

    try:
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


def load_global_hotkey_presets(service, *, config_root: str) -> list[Any] | None:
    """config.json が指すグローバルプリセットを、読めた場合だけ返す。"""
    try:
        stored_path = load_global_hotkey_presets_path(service, config_root=config_root)
    except Exception:
        return None
    return load_hotkey_presets_file(service, stored_path, config_root=config_root)


def resolve_individual_hotkey_presets_path(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
) -> str:
    """有効な個別プリセットの保存表記パスだけを返す。"""
    if runtime.get("hotkey_presets_individual") is not True or not config_root:
        return ""

    stored_path = runtime.get("hotkey_presets_path")
    if not isinstance(stored_path, str) or not stored_path.strip():
        return ""

    resolved_path = service._resolve_config_relative_path(stored_path, config_root)
    if not service.is_path_within(resolved_path, config_root, config_root):
        return ""
    return stored_path


def resolve_individual_hotkey_presets_read_path(runtime: dict[str, Any]) -> str:
    """config 外を含む個別プリセットの読み出し用保存表記パスを返す。"""
    if runtime.get("hotkey_presets_individual") is not True:
        return ""

    stored_path = runtime.get("hotkey_presets_path")
    if not isinstance(stored_path, str) or not stored_path.strip():
        return ""
    return stored_path


def resolve_hotkey_presets_save_path(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    keymap_set_path: str,
    individual: bool | None = None,
) -> str:
    """個別プリセットの保存表記パス、またはグローバル用の空文字を返す。"""
    use_individual = (
        runtime.get("hotkey_presets_individual") is True
        if individual is None
        else individual
    )
    effective_runtime = runtime
    if individual is not None:
        effective_runtime = {**runtime, "hotkey_presets_individual": use_individual}

    individual_path = resolve_individual_hotkey_presets_path(
        service,
        effective_runtime,
        config_root=config_root,
    )
    if individual_path:
        return individual_path

    if (
        not use_individual
        or not config_root
    ):
        return ""

    default_path = save_path_resolution.default_individual_hotkey_presets_path(
        service,
        keymap_set_path,
        config_root=config_root,
    )
    return service.to_config_relative_or_absolute(default_path, config_root)


def individual_hotkey_presets_save_rejection_reason(
    service,
    stored_path: str,
    *,
    config_root: str,
) -> str:
    """個別プリセットの最終保存先がグローバル領域と衝突する理由を返す。"""
    if not stored_path or not config_root:
        return ""

    resolved_path = service.resolve_config_path(stored_path, config_root)
    global_dir = os.path.dirname(service.HOTKEY_PRESETS_RELATIVE_PATH)
    if service.is_path_within(resolved_path, global_dir, config_root):
        return "reserved_dir"

    global_stored_path = load_global_hotkey_presets_path(
        service,
        config_root=config_root,
    )
    global_resolved_path = service.resolve_config_path(global_stored_path, config_root)
    if service.canonical_path(resolved_path, config_root) == service.canonical_path(
        global_resolved_path,
        config_root,
    ):
        return "global_conflict"
    return ""


def describe_individual_hotkey_presets_overwrite(
    service,
    stored_path: str,
    loaded_presets: list[Any] | None,
    *,
    config_root: str,
) -> dict[str, bool | list[Any] | None]:
    """個別プリセットの上書き確認要否と保存先の既存内容を返す。"""
    existing_presets = None

    resolved_path = service.resolve_config_path(stored_path, config_root)
    exists = bool(resolved_path and os.path.exists(resolved_path))
    if exists:
        existing_presets = load_hotkey_presets_file(
            service,
            stored_path,
            config_root=config_root,
        )

    conflict = (
        loaded_presets is not None
        and exists
        and (
            existing_presets is None
            or existing_presets != normalize_hotkey_presets(loaded_presets)
        )
    )
    return {"conflict": conflict, "existing": existing_presets}


def describe_hotkey_presets_source(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
) -> dict[str, str]:
    """個別プリセットの状態と、現在表示中の一覧の出どころを返す。"""
    individual_enabled = runtime.get("hotkey_presets_individual") is True
    individual_path = resolve_individual_hotkey_presets_read_path(runtime)
    individual_presets = None

    if not individual_enabled:
        individual_state = "off"
    elif individual_path:
        individual_presets = load_hotkey_presets_file(
            service,
            individual_path,
            config_root=config_root,
        )
        individual_save_path = resolve_individual_hotkey_presets_path(
            service,
            runtime,
            config_root=config_root,
        )
        if individual_save_path:
            individual_state = "active" if individual_presets is not None else "missing"
        else:
            individual_state = "external" if individual_presets is not None else "external_missing"
    else:
        individual_state = "missing"

    if individual_presets is not None:
        displayed_source = "individual"
    elif load_global_hotkey_presets(service, config_root=config_root) is not None:
        displayed_source = "global"
    else:
        displayed_source = "builtin"

    return {
        "individual_state": individual_state,
        "displayed_source": displayed_source,
    }


def build_runtime_data_from_split(
    service,
    keymap_set: dict[str, Any],
    *,
    config_root: str,
) -> dict[str, Any]:
    runtime = service.new_default_data()
    runtime.update(keymaps=[], triggers=[], active_keymap_id="")

    for key in (
        *HOOK_KEY_FIELDS,
        "hotkey_presets_individual",
        "keyboard_layout",
        "keyboard_show_physical_key_labels",
        "debug_jis_special_key_events",
    ):
        if key in keymap_set:
            runtime[key] = safe_deepcopy(keymap_set.get(key))

    if "hotkey_presets_individual" in keymap_set and "hotkey_presets_path" in keymap_set:
        runtime["hotkey_presets_path"] = safe_deepcopy(keymap_set.get("hotkey_presets_path"))

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
    individual_presets_path = resolve_individual_hotkey_presets_read_path(runtime)
    hotkey_presets = (
        load_hotkey_presets_file(
            service,
            individual_presets_path,
            config_root=config_root,
        )
        if individual_presets_path
        else None
    )
    if hotkey_presets is None:
        hotkey_presets = load_global_hotkey_presets(service, config_root=config_root)
    if hotkey_presets is not None:
        runtime["hotkey_presets"] = hotkey_presets

    keymaps: list[dict[str, Any]] = []
    keymap_switch_keys: dict[str, str] = {}
    loaded_keymap_ids_by_path: dict[str, str] = {}
    keymap_trigger_path_presence: dict[str, bool] = {}
    used_keymap_ids: set[str] = set()
    trigger_sets: dict[
        str, tuple[list[dict[str, Any]], list[str] | None, str, bool | None, bool | None]
    ] = {}

    active_keymap_path = coerce_label(keymap_set.get("active_keymap_path"))
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
            keymap_id = str(keymap.get("id") or "")
            keymap_trigger_path_presence[keymap_id] = loaded_entry["has_trigger_set_path"]
            if loaded_entry["trigger_set_path"]:
                attach_trigger_set(
                    service,
                    keymap,
                    loaded_entry["trigger_set_path"],
                    config_root=config_root,
                    trigger_sets=trigger_sets,
                )
            keymaps.append(keymap)
            loaded_keymap_ids_by_path[loaded_entry["resolved_path"]] = keymap_id

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
            keymap_id = str(active_keymap["keymap"].get("id") or "")
            keymap_trigger_path_presence[keymap_id] = active_keymap["has_trigger_set_path"]
            if active_keymap["trigger_set_path"]:
                attach_trigger_set(
                    service,
                    active_keymap["keymap"],
                    active_keymap["trigger_set_path"],
                    config_root=config_root,
                    trigger_sets=trigger_sets,
                )
            keymaps.append(active_keymap["keymap"])
            active_keymap_id = keymap_id

    runtime["keymaps"] = keymaps
    runtime["active_keymap_id"] = active_keymap_id
    runtime["keymap_switch_keys"] = keymap_switch_keys
    generated_keymap = ensure_at_least_one_keymap(runtime)
    keymaps = runtime["keymaps"]
    if generated_keymap is not None:
        keymap_trigger_path_presence[str(generated_keymap["id"])] = False
    if not runtime["active_keymap_id"]:
        runtime["active_keymap_id"] = keymaps[0]["id"]
    active = next(item for item in keymaps if item["id"] == runtime["active_keymap_id"])
    legacy_path = coerce_label(keymap_set.get("trigger_set_path"))
    state, migration_target, auto_created = _migrate_legacy_trigger_set(
        service,
        legacy_path,
        keymaps,
        active,
        has_trigger_set_path=keymap_trigger_path_presence.get(str(active["id"]), False),
        config_root=config_root,
        trigger_sets=trigger_sets,
    )
    runtime[service.INTERNAL_LEGACY_TRIGGER_SET] = {
        "state": state,
        "path": legacy_path,
        "keymap_id": str(migration_target.get("id") or active["id"]),
    }
    if auto_created:
        runtime[service.INTERNAL_LEGACY_TRIGGER_SET]["auto_created"] = True
    for keymap in keymaps:
        keymap.setdefault("triggers", [])
    if state == "migrated":
        migration_target[service.INTERNAL_KEYMAP_DIRTY] = True
    normalized = ensure_config_compatibility(runtime)
    normalized_keymaps = normalized.get("keymaps", [])
    for keymap, normalized_keymap in zip(keymaps, normalized_keymaps):
        parent_refs = service._normalize_parent_refs(keymap.get(service.INTERNAL_KEYMAP_PARENT_REFS))
        if parent_refs is not None:
            normalized_keymap[service.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
    return normalized


def _migrate_legacy_trigger_set(
    service,
    legacy_path: str,
    keymaps: list[dict[str, Any]],
    active: dict[str, Any],
    *,
    has_trigger_set_path: bool,
    config_root: str,
    trigger_sets: TriggerSetCache,
) -> tuple[str, dict[str, Any], bool]:
    if not legacy_path:
        return "none", active, False
    legacy_identity = service.canonical_path(legacy_path, config_root)
    if any(
        source and service.canonical_path(source, config_root) == legacy_identity
        for source in (item.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH, "") for item in keymaps)
    ):
        return "same", active, False
    active_source = active.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH, "")
    if not has_trigger_set_path:
        target = active
        created = False
    elif active_source:
        target = _create_legacy_trigger_keymap(service, legacy_path, keymaps)
        created = True
    else:
        return "none", active, False
    attach_trigger_set(
        service, target, legacy_path, config_root=config_root, trigger_sets=trigger_sets
    )
    return "migrated", target, created


def _create_legacy_trigger_keymap(
    service, legacy_path: str, keymaps: list[dict[str, Any]]
) -> dict[str, Any]:
    data = {"keymaps": keymaps}
    stem = os.path.splitext(os.path.basename(legacy_path))[0]
    keymap = {
        "id": KeymapService.next_keymap_id(data),
        "label": f"旧トリガー一覧（{stem}）",
        "mappings": {},
        "triggers": [],
    }
    keymaps.append(keymap)
    return keymap


def attach_trigger_set(
    service,
    keymap: dict[str, Any],
    stored_path: str,
    *,
    config_root: str,
    trigger_sets: dict[
        str, tuple[list[dict[str, Any]], list[str] | None, str, bool | None, bool | None]
    ],
) -> None:
    """同じ解決済みパスの trigger_set を共有し、配下 sequence も読み込む。"""
    identity = service.canonical_path(stored_path, config_root)
    if identity not in trigger_sets:
        triggers, refs = load_trigger_set(service, stored_path, config_root=config_root)
        trigger_sets[identity] = (triggers, refs, stored_path, None, None)
    triggers, refs, source_path, dirty, imported = trigger_sets[identity]
    keymap["triggers"] = triggers
    keymap[service.INTERNAL_TRIGGER_SET_SOURCE_PATH] = source_path
    if dirty is not None:
        keymap["_trigger_set_dirty"] = dirty
    if imported is not None:
        keymap["_trigger_set_imported"] = imported
    if refs is not None:
        keymap[service.INTERNAL_TRIGGER_SET_PARENT_REFS] = refs


def load_keymap_entry(
    service,
    entry: Any,
    *,
    config_root: str,
    used_keymap_ids: set[str],
) -> dict[str, Any] | None:
    if isinstance(entry, dict):
        stored_path = coerce_label(entry.get("path"))
        switch_key = coerce_key_name(entry.get("switch_key"))
    else:
        stored_path = coerce_label(entry)
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
        "has_trigger_set_path": "trigger_set_path" in raw_keymap,
        "trigger_set_path": coerce_label(raw_keymap.get("trigger_set_path")),
        "switch_key": switch_key,
        "keymap": {
            "id": keymap_id,
            "label": coerce_label(raw_keymap.get("label")),
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
    stored_path = coerce_label(path_value)
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
            "key": coerce_key_name(raw_trigger.get("key")),
            "suppress": bool(raw_trigger.get("suppress", True)),
            "label": coerce_label(raw_trigger.get("label")),
            "run_to_end": bool(raw_trigger.get("run_to_end", False)),
            "run_to_end_delay_ms": service._coerce_nonnegative_int(
                raw_trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                DEFAULT_RUN_TO_END_DELAY_MS,
            ),
            "actions": safe_deepcopy(raw_trigger.get("actions", []))
            if isinstance(raw_trigger.get("actions"), list)
            else [],
        }
        sequence_path = coerce_label(raw_trigger.get("sequence_path"))
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
            stored_path = coerce_label(item.get("path"))
        else:
            stored_path = coerce_label(item)
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
