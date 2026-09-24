from __future__ import annotations

import os
from typing import Any

from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    SavePlan,
    SavePlanError,
    compose_sequence_key,
    split_sequence_key,
)
from keyseq.domain.keymap_triggers import iter_trigger_sets
from keyseq.domain.config import ensure_config_compatibility, normalize_key_name, safe_deepcopy

from . import split_payloads


def normalize_save_runtime(data: Any) -> dict[str, Any]:
    """区切りが strip で失われる前に保存識別子を検査する。"""
    for owner, _, triggers in iter_trigger_sets(data):
        owner_id = str(owner.get("id") or "")
        if not owner_id:
            continue
        compose_sequence_key(owner_id, "identifier")
        for trigger in triggers:
            key = str(trigger.get("key") or "") if isinstance(trigger, dict) else ""
            if key:
                compose_sequence_key(owner_id, key)
    return ensure_config_compatibility(data)

def save_runtime_data(service,
    keymap_set_path: str,
    data: Any,
    *,
    config_root: str,
    startup_data: Any = None,
    startup_entry_loaded: bool = False,
    keep_legacy_copy: bool = False,
    legacy_path: str = "",
    split_base_dir: str = "",
    save_plan: SavePlan | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_save_runtime(data)
    raw_keymaps = (
        data.get("keymaps")
        if isinstance(data, dict) and isinstance(data.get("keymaps"), list)
        else []
    )
    normalized_keymaps = normalized.get("keymaps", [])
    parent_refs_by_id = {
        normalize_key_name(keymap.get("id", "")): parent_refs
        for keymap in raw_keymaps
        if isinstance(keymap, dict)
        for parent_refs in [service._normalize_parent_refs(keymap.get(service.INTERNAL_KEYMAP_PARENT_REFS))]
        if parent_refs is not None
    }
    for keymap in normalized_keymaps:
        parent_refs = parent_refs_by_id.get(normalize_key_name(keymap.get("id", "")))
        if parent_refs is not None:
            keymap[service.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs

    raw_groups = {
        normalize_key_name(str(owner.get("id") or "")): triggers
        for owner, _, triggers in iter_trigger_sets(data)
    }
    for owner, _, triggers in iter_trigger_sets(normalized):
        raw_group = raw_groups.get(str(owner["id"]), [])
        for raw_trigger, trigger in zip((item for item in raw_group if isinstance(item, dict)), triggers):
            parent_refs = service._normalize_parent_refs(raw_trigger.get(service.INTERNAL_SEQUENCE_PARENT_REFS))
            if parent_refs is not None:
                trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
    sanitized_legacy = service._sanitize_runtime_for_storage(normalized)
    resolved_config_root = os.path.abspath(config_root)
    resolved_keymap_set_path = os.path.abspath(keymap_set_path) if keymap_set_path else service._default_keymap_set_path(resolved_config_root)
    resolved_split_base_dir = os.path.abspath(split_base_dir) if split_base_dir else ""

    resolved_save_plan = save_plan or SavePlan()
    payloads = split_payloads.build_split_save_payloads(service,
        normalized,
        config_root=resolved_config_root,
        startup_data=startup_data,
        startup_entry_loaded=startup_entry_loaded,
        keymap_set_path=resolved_keymap_set_path,
        legacy_path=legacy_path if keep_legacy_copy else "",
        split_base_dir=resolved_split_base_dir,
        save_plan=resolved_save_plan,
    )
    validate_save_plan(
        service,
        resolved_save_plan,
        normalized,
        payloads,
        config_root=resolved_config_root,
    )

    keymap_parent_refs_by_id = {
        str(item.get("id") or ""): item["payload"][service.PARENT_REFS_KEY]
        for item in payloads["keymaps"]
        if not item["skip"] and service.PARENT_REFS_KEY in item.get("payload", {})
    }
    for keymap in normalized_keymaps:
        parent_refs = keymap_parent_refs_by_id.get(str(keymap.get("id") or ""))
        if parent_refs is not None:
            keymap[service.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(parent_refs)

    service.ensure_split_config_dirs(resolved_config_root)
    for item in payloads["sequences"]:
        if item["skip"]:
            continue
        service.repository.save_json(
            str(item["resolved_path"]),
            item["payload"],
        )
    for item in payloads["trigger_sets"]:
        if not item["skip"]:
            service.repository.save_json(str(item["resolved_path"]), item["payload"])
    for item in payloads["keymaps"]:
        if item["skip"]:
            continue
        service.repository.save_json(
            service._resolve_config_relative_path(str(item["path"]), resolved_config_root),
            item["payload"],
        )
    service.repository.save_json(resolved_keymap_set_path, payloads["keymap_set"])
    service.repository.save_json(service._startup_entry_path(resolved_config_root), payloads["startup"])

    if keep_legacy_copy:
        target_legacy_path = legacy_path or service._default_legacy_config_path(resolved_config_root)
        service.repository.save_json(target_legacy_path, sanitized_legacy)

    apply_saved_child_paths(service, normalized, payloads, resolved_config_root)
    if normalized.get(service.INTERNAL_LEGACY_TRIGGER_SET, {}).get("state") != "unused":
        normalized[service.INTERNAL_LEGACY_TRIGGER_SET] = {"state": "none", "path": "", "keymap_id": ""}
    # 保存時の補完値を明示指定へ変換しない。フラグ省略時のキーからの推論を維持する。
    if isinstance(data, dict) and "hook_keys_individual" not in data:
        normalized.pop("hook_keys_individual", None)
    return normalized, payloads["startup"]

def resolve_child_save_targets(service,
    data: Any,
    *,
    config_root: str,
    keymap_set_path: str,
    split_base_dir: str = "",
    save_plan: SavePlan | None = None,
) -> dict[tuple[str, str], str]:
    """ACTION_SAVE 時の子ファイル保存先を、書き込まずに解決する。"""
    runtime = normalize_save_runtime(data)
    resolved_config_root = os.path.abspath(config_root)
    resolved_keymap_set_path = (
        os.path.abspath(keymap_set_path)
        if keymap_set_path
        else service._default_keymap_set_path(resolved_config_root)
    )
    resolved_split_base_dir = os.path.abspath(split_base_dir) if split_base_dir else ""
    payloads = split_payloads.build_split_save_payloads(service,
        runtime,
        config_root=resolved_config_root,
        startup_data=None,
        keymap_set_path=resolved_keymap_set_path,
        legacy_path="",
        split_base_dir=resolved_split_base_dir,
        save_plan=save_plan or SavePlan(),
    )

    targets = {
        (CHILD_TRIGGER_SET, item["key"]): os.path.abspath(item["resolved_path"])
        for item in payloads["trigger_sets"]
    }
    for keymap in payloads["keymaps"]:
        targets[(CHILD_KEYMAP, str(keymap["id"]))] = os.path.abspath(
            keymap["resolved_path"]
        )
    for sequence in payloads["sequences"]:
        targets[(CHILD_SEQUENCE, str(sequence["key"]))] = os.path.abspath(
            sequence["resolved_path"]
        )
    return targets

def find_dependency_blocked_sequences(service,
    data: Any,
    *,
    config_root: str,
    keymap_set_path: str,
    split_base_dir: str = "",
    save_plan: SavePlan,
) -> list[str]:
    """trigger_set を保存しない計画で、保存先が変わる sequence を返す。"""
    runtime = normalize_save_runtime(data)
    resolved_config_root = os.path.abspath(config_root)
    resolved_keymap_set_path = (
        os.path.abspath(keymap_set_path)
        if keymap_set_path
        else service._default_keymap_set_path(resolved_config_root)
    )
    payloads = split_payloads.build_split_save_payloads(service,
        runtime,
        config_root=resolved_config_root,
        startup_data=None,
        keymap_set_path=resolved_keymap_set_path,
        legacy_path="",
        split_base_dir=os.path.abspath(split_base_dir) if split_base_dir else "",
        save_plan=save_plan,
    )
    return sequence_keys_requiring_trigger_set_save(service, save_plan, payloads)

def find_dependency_blocked_parents(service, data: Any, *, config_root: str,
    keymap_set_path: str, split_base_dir: str = "", save_plan: SavePlan,
) -> dict[tuple[str, str], list[str]]:
    """子の保存先変更によって保存が必要になる、SKIP 指定の直接の親。"""
    payloads = split_payloads.build_split_save_payloads(
        service, normalize_save_runtime(data), config_root=os.path.abspath(config_root),
        startup_data=None, keymap_set_path=os.path.abspath(keymap_set_path), legacy_path="",
        split_base_dir=split_base_dir, save_plan=save_plan,
    )
    blocked: dict[tuple[str, str], list[str]] = {}
    for key in sequence_keys_requiring_trigger_set_save(service, save_plan, payloads):
        blocked.setdefault((CHILD_TRIGGER_SET, split_sequence_key(key)[0]), []).append(key)
    for item in payloads["trigger_sets"]:
        if item["skip"] or not sequence_save_path_changed(item):
            continue
        for key in item["parent_ids"]:
            entry = save_plan.entry_for(CHILD_KEYMAP, key)
            if entry and entry.action == ACTION_SKIP:
                blocked.setdefault((CHILD_KEYMAP, key), []).append(item["key"])
    return blocked

def sequence_keys_requiring_trigger_set_save(service,
    save_plan: SavePlan,
    payloads: dict[str, Any],
) -> list[str]:
    return [
        str(item["key"])
        for item in payloads["sequences"]
        if not item["skip"] and sequence_save_path_changed(item)
        and (entry := save_plan.entry_for(CHILD_TRIGGER_SET, split_sequence_key(item["key"])[0]))
        and entry.action == ACTION_SKIP
    ]


def trigger_sets_requiring_keymap_save(save_plan: SavePlan, payloads: dict[str, Any]) -> list[str]:
    """保存先が変わる一覧を参照する全キーマップの保存を要求する。"""
    return [
        item["key"] for item in payloads["trigger_sets"]
        if not item["skip"] and sequence_save_path_changed(item)
        and any(
            (entry := save_plan.entry_for(CHILD_KEYMAP, key)) and entry.action == ACTION_SKIP
            for key in item["parent_ids"]
        )
    ]

def sequence_save_path_changed(item: dict[str, Any]) -> bool:
    source_path = str(item.get("source_path") or "")
    return item["action"] == ACTION_SAVE_AS or (
        not source_path
        or os.path.normcase(os.path.abspath(str(item["resolved_path"])))
        != os.path.normcase(os.path.abspath(source_path))
    )

def validate_save_plan(service,
    save_plan: SavePlan,
    runtime: dict[str, Any],
    payloads: dict[str, Any],
    *,
    config_root: str,
) -> None:
    keymap_ids = {
        normalize_key_name(item.get("id", ""))
        for item in runtime.get("keymaps", [])
        if isinstance(item, dict) and normalize_key_name(item.get("id", ""))
    }
    sequence_keys = {item["key"] for item in payloads["sequences"]}
    trigger_set_ids = {item["key"] for item in payloads["trigger_sets"]}
    seen: set[tuple[str, str]] = set()
    for entry in save_plan.entries:
        if entry.kind not in {CHILD_KEYMAP, CHILD_TRIGGER_SET, CHILD_SEQUENCE}:
            raise SavePlanError(f"未知の子種別です: {entry.kind}")
        if entry.action not in {ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP}:
            raise SavePlanError(f"不正な保存操作です: {entry.kind}:{entry.key}")
        entry_id = (entry.kind, entry.key)
        if entry_id in seen:
            raise SavePlanError(f"保存計画が重複しています: {entry.kind}:{entry.key}")
        seen.add(entry_id)
        if entry.kind == CHILD_KEYMAP and entry.key not in keymap_ids:
            raise SavePlanError(f"存在しない keymap です: {entry.key}")
        if entry.kind == CHILD_SEQUENCE and entry.key not in sequence_keys:
            raise SavePlanError(f"存在しない sequence です: {entry.key}")
        if entry.kind == CHILD_TRIGGER_SET and entry.key not in trigger_set_ids:
            raise SavePlanError(f"存在しない trigger_set です: {entry.key}")
        legacy = runtime.get(service.INTERNAL_LEGACY_TRIGGER_SET, {})
        if (entry.kind == CHILD_KEYMAP and entry.action == ACTION_SKIP
                and legacy.get("state") == "migrated" and entry.key == legacy.get("keymap_id")):
            raise SavePlanError("移行先キーマップは保存しないを選択できません。")
        if entry.action == ACTION_SAVE_AS:
            if not entry.target_path.strip():
                raise SavePlanError(f"別名保存先が空です: {entry.kind}:{entry.key}")
            target_path = service._resolve_config_relative_path(entry.target_path, config_root)
            try:
                os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            except OSError as exc:
                raise SavePlanError(
                    f"別名保存先のディレクトリを作成できません: {entry.kind}:{entry.key}"
                ) from exc

    destinations: set[str] = set()
    for item in (*payloads["keymaps"], *payloads["trigger_sets"], *payloads["sequences"]):
        if item["skip"]:
            continue
        canonical = service.canonical_path(item["resolved_path"], config_root)
        if canonical in destinations:
            raise SavePlanError(f"子ファイルの保存先が重複しています: {item['resolved_path']}")
        destinations.add(canonical)
    blocked_sets = trigger_sets_requiring_keymap_save(save_plan, payloads)
    if blocked_sets and not save_plan.allow_deferred_index:
        raise SavePlanError(f"trigger_set {blocked_sets[0]} の保存先変更には keymap の保存が必要です。")

    blocked_keys = sequence_keys_requiring_trigger_set_save(service, save_plan, payloads)
    if blocked_keys and not save_plan.allow_deferred_index:
        raise SavePlanError(
            f"sequence {blocked_keys[0]} の保存先変更には trigger_set の保存が必要です。"
        )

def apply_saved_child_paths(service,
    runtime: dict[str, Any],
    payloads: dict[str, Any],
    config_root: str,
) -> None:
    paths_by_keymap_id = {
        str(item["id"]): str(item["path"])
        for item in payloads["keymaps"]
        if not item["skip"]
    }
    for keymap in runtime.get("keymaps", []):
        if isinstance(keymap, dict):
            path = paths_by_keymap_id.get(str(keymap.get("id") or ""))
            if path:
                keymap[service.INTERNAL_KEYMAP_SOURCE_PATH] = path

    sequences = {item["key"]: item for item in payloads["sequences"] if not item["skip"]}
    sets = {item["key"]: item for item in payloads["trigger_sets"] if not item["skip"]}
    for owner, members, triggers in iter_trigger_sets(runtime):
        key = str(owner["id"])
        item = sets.get(key)
        if item:
            for member in members:
                member[service.INTERNAL_TRIGGER_SET_SOURCE_PATH] = item["path"]
                if service.PARENT_REFS_KEY in item["payload"]:
                    member[service.INTERNAL_TRIGGER_SET_PARENT_REFS] = safe_deepcopy(item["payload"][service.PARENT_REFS_KEY])
        for trigger in triggers:
            item = sequences.get(compose_sequence_key(key, normalize_key_name(str(trigger.get("key") or ""))))
            if item:
                trigger[service.INTERNAL_SEQUENCE_SOURCE_PATH] = item["path"]
                if service.PARENT_REFS_KEY in item["payload"]:
                    trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(item["payload"][service.PARENT_REFS_KEY])
