from __future__ import annotations

import os
from typing import Any

from keyseq.application.save_plan import (
    CHILD_TRIGGER_SET,
    SavePlan,
    SavePlanError,
    split_sequence_key,
)
from keyseq.domain.config import normalize_key_name, safe_deepcopy
from keyseq.domain.keymap_triggers import (
    INTERNAL_TRIGGER_SET_DIRTY,
    INTERNAL_TRIGGER_SET_IMPORTED,
    trigger_set_members,
)

from . import save_plan_execution, split_payloads


def save_keymap_with_plan(
    service,
    path: str,
    keymap: dict[str, Any],
    *,
    runtime_data: dict[str, Any],
    parent_ref: str,
    config_root: str,
    save_plan: SavePlan,
) -> dict[str, Any]:
    resolved_path = service._resolve_config_relative_path(path, config_root)
    root = os.path.abspath(config_root)
    payloads = _build_keymap_save_payloads(
        service, runtime_data, parent_ref=parent_ref, config_root=root, save_plan=save_plan,
    )
    _validate_requested_keymap_target(
        service, keymap, resolved_path, payloads, config_root=root,
    )
    _validate_keymap_save_plan(
        service, runtime_data, payloads, config_root=root, parent_ref=parent_ref, save_plan=save_plan,
    )
    _write_keymap_save_payloads(service, payloads)
    _apply_keymap_save_payloads(service, runtime_data, payloads, config_root=root)
    saved = safe_deepcopy(keymap)
    _apply_saved_keymap_state(service, saved, path, resolved_path, config_root, payloads)
    return saved


def _validate_requested_keymap_target(
    service,
    keymap: dict[str, Any],
    resolved_path: str,
    payloads: dict[str, Any],
    *,
    config_root: str,
) -> None:
    item = next(
        (entry for entry in payloads["keymaps"] if entry.get("id") == keymap.get("id")),
        None,
    )
    if item is None or item["skip"] or service.canonical_path(
        item["resolved_path"], config_root
    ) != service.canonical_path(resolved_path, config_root):
        raise SavePlanError("キーマップの保存計画と保存先が一致しません。")


def _build_keymap_save_payloads(
    service,
    runtime_data: dict[str, Any],
    *,
    parent_ref: str,
    config_root: str,
    save_plan: SavePlan,
) -> dict[str, Any]:
    return split_payloads.build_split_save_payloads(
        service, runtime_data, config_root=config_root, startup_data=None,
        keymap_set_path=parent_ref, keymap_set_name_path=parent_ref,
        legacy_path="", split_base_dir="", save_plan=save_plan,
    )


def _validate_keymap_save_plan(
    service,
    runtime_data: dict[str, Any],
    payloads: dict[str, Any],
    *,
    config_root: str,
    parent_ref: str,
    save_plan: SavePlan,
) -> None:
    blocked = save_plan_execution.find_dependency_blocked_parents(
        service, runtime_data, config_root=config_root,
        keymap_set_path=parent_ref or service._default_keymap_set_path(config_root),
        save_plan=save_plan,
    )
    if any(kind == CHILD_TRIGGER_SET for kind, _ in blocked):
        raise SavePlanError("sequence の保存先変更には trigger_set の保存が必要です。")
    save_plan_execution.validate_save_plan(
        service, save_plan, runtime_data, payloads, config_root=config_root,
    )


def _write_keymap_save_payloads(service, payloads: dict[str, Any]) -> None:
    for item in payloads["sequences"]:
        if not item["skip"]:
            service.repository.save_json(item["resolved_path"], item["payload"])
    for item in payloads["trigger_sets"]:
        if not item["skip"]:
            service.repository.save_json(item["resolved_path"], item["payload"])
    for item in payloads["keymaps"]:
        if not item["skip"]:
            service.repository.save_json(item["resolved_path"], item["payload"])


def _apply_keymap_save_payloads(
    service, runtime_data: dict[str, Any], payloads: dict[str, Any], *, config_root: str,
) -> None:
    save_plan_execution.apply_saved_child_paths(service, runtime_data, payloads, config_root)
    _clear_saved_keymap_child_state(service, runtime_data, payloads)


def _clear_saved_keymap_child_state(
    service, runtime_data: dict[str, Any], payloads: dict[str, Any],
) -> None:
    saved_keymaps = _clear_saved_keymap_states(service, runtime_data, payloads["keymaps"])
    _clear_saved_trigger_set_states(service, runtime_data, payloads["trigger_sets"])
    _clear_saved_sequence_states(service, runtime_data, payloads["sequences"])
    _mark_deferred_keymap_states(
        service, runtime_data, payloads["trigger_sets"], saved_keymaps
    )


def _clear_saved_keymap_states(
    service, runtime_data: dict[str, Any], items: list[dict[str, Any]],
) -> set[str]:
    saved_ids: set[str] = set()
    for item in items:
        keymap_id = str(item.get("id") or "")
        keymap = next(
            (entry for entry in runtime_data.get("keymaps", [])
             if isinstance(entry, dict) and entry.get("id") == keymap_id),
            None,
        )
        if item["skip"] or keymap is None:
            continue
        saved_ids.add(keymap_id)
        keymap[service.INTERNAL_KEYMAP_IMPORTED] = False
        keymap[service.INTERNAL_KEYMAP_DIRTY] = False
        refs = item["payload"].get(service.PARENT_REFS_KEY)
        if refs is not None:
            keymap[service.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(refs)
    return saved_ids


def _clear_saved_trigger_set_states(
    service, runtime_data: dict[str, Any], items: list[dict[str, Any]],
) -> None:
    for item in items:
        if item["skip"]:
            continue
        for member in trigger_set_members(runtime_data, str(item["key"])):
            member[INTERNAL_TRIGGER_SET_DIRTY] = False
            member[INTERNAL_TRIGGER_SET_IMPORTED] = False
            refs = item["payload"].get(service.PARENT_REFS_KEY)
            if refs is not None:
                member[service.INTERNAL_TRIGGER_SET_PARENT_REFS] = safe_deepcopy(refs)


def _clear_saved_sequence_states(
    service, runtime_data: dict[str, Any], items: list[dict[str, Any]],
) -> None:
    for item in items:
        if item["skip"]:
            continue
        trigger_set_id, trigger_key = split_sequence_key(str(item["key"]))
        for member in trigger_set_members(runtime_data, trigger_set_id):
            for trigger in member.get("triggers", []):
                if normalize_key_name(str(trigger.get("key") or "")) != trigger_key:
                    continue
                trigger[service.INTERNAL_SEQUENCE_IMPORTED] = False
                trigger[service.INTERNAL_SEQUENCE_DIRTY] = False
                refs = item["payload"].get(service.PARENT_REFS_KEY)
                if refs is not None:
                    trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(refs)


def _mark_deferred_keymap_states(
    service,
    runtime_data: dict[str, Any],
    trigger_sets: list[dict[str, Any]],
    saved_keymaps: set[str],
) -> None:
    for item in trigger_sets:
        if item["skip"] or not save_plan_execution.sequence_save_path_changed(item):
            continue
        for keymap_id in item["parent_ids"]:
            if keymap_id in saved_keymaps:
                continue
            keymap = next(
                (entry for entry in runtime_data.get("keymaps", [])
                 if isinstance(entry, dict) and entry.get("id") == keymap_id),
                None,
            )
            if keymap is not None:
                keymap[service.INTERNAL_KEYMAP_DIRTY] = True


def _apply_saved_keymap_state(
    service,
    saved: dict[str, Any],
    path: str,
    resolved_path: str,
    config_root: str,
    payloads: dict[str, Any],
) -> None:
    saved[service.INTERNAL_KEYMAP_SOURCE_PATH] = service.to_config_relative_or_absolute(
        resolved_path, config_root
    ) if config_root else path
    saved[service.INTERNAL_KEYMAP_IMPORTED] = False
    saved[service.INTERNAL_KEYMAP_DIRTY] = False
    item = next(
        (entry for entry in payloads["keymaps"] if entry.get("id") == saved.get("id")),
        None,
    )
    if item is not None and service.PARENT_REFS_KEY in item["payload"]:
        saved[service.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(
            item["payload"][service.PARENT_REFS_KEY]
        )
