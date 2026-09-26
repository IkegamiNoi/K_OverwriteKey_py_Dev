from __future__ import annotations

import os
from typing import Any

from keyseq.application.save_plan import SavePlan
from keyseq.domain.config import ensure_config_compatibility, normalize_key_name, safe_deepcopy
from keyseq.domain.keymap_triggers import get_active_triggers, trigger_set_members

from . import split_loading, split_payloads


def load_sequence_file(
    service,
    path: str,
    *,
    imported: bool = True,
    config_root: str = "",
) -> dict[str, Any]:
    raw_sequence = service.repository.load_json(path)
    if not isinstance(raw_sequence, dict):
        raise ValueError("sequence JSON の形式が不正です。")
    sequence = service._normalize_sequence_payload(raw_sequence)
    parent_refs = service._normalize_parent_refs(raw_sequence.get(service.PARENT_REFS_KEY))
    if parent_refs is not None:
        sequence[service.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
    sequence[service.INTERNAL_SEQUENCE_SOURCE_PATH] = (
        service.to_config_relative_or_absolute(path, config_root)
        if config_root
        else path
    )
    sequence[service.INTERNAL_SEQUENCE_IMPORTED] = bool(imported)
    sequence[service.INTERNAL_SEQUENCE_DIRTY] = False
    return sequence


def save_sequence_file(
    service,
    path: str,
    trigger: dict[str, Any],
    *,
    parent_ref: str = "",
    config_root: str = "",
) -> dict[str, Any]:
    resolved_path = service._resolve_config_relative_path(path, config_root)
    stored_path = (
        service.to_config_relative_or_absolute(resolved_path, config_root)
        if config_root
        else path
    )
    payload = split_payloads.build_sequence_payload(service,
        trigger,
        parent_ref=parent_ref,
        config_root=config_root,
        target_path=resolved_path,
    )
    service.repository.save_json(resolved_path, payload)
    sequence = service._normalize_sequence_payload(payload)
    if service.PARENT_REFS_KEY in payload:
        sequence[service.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(payload[service.PARENT_REFS_KEY])
    sequence[service.INTERNAL_SEQUENCE_SOURCE_PATH] = stored_path
    sequence[service.INTERNAL_SEQUENCE_IMPORTED] = False
    sequence[service.INTERNAL_SEQUENCE_DIRTY] = False
    return sequence


def load_trigger_set_file(
    service,
    path: str,
    *,
    config_root: str,
    imported: bool = True,
) -> list[dict[str, Any]]:
    payload = service.repository.load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("trigger_set JSON の形式が不正です。")
    triggers, _parent_refs = split_loading.load_triggers_from_trigger_set(
        service,
        payload,
        config_root=config_root,
        imported=imported,
    )
    return triggers


def save_trigger_set_file(
    service,
    path: str,
    data: dict[str, Any],
    *,
    config_root: str,
    parent_ref: str = "",
    parent_refs: list[str] | None = None,
    save_plan: SavePlan | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolved_path = service._resolve_config_relative_path(path, config_root)
    normalized = ensure_config_compatibility(data)
    raw_triggers = get_active_triggers(data)
    normalized_triggers = get_active_triggers(normalized)
    for raw_trigger, trigger in zip(
        (item for item in raw_triggers if isinstance(item, dict)),
        normalized_triggers,
    ):
        sequence_parent_refs = service._normalize_parent_refs(raw_trigger.get(service.INTERNAL_SEQUENCE_PARENT_REFS))
        if sequence_parent_refs is not None:
            trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = sequence_parent_refs
    trigger_payload, sequence_items = split_payloads.build_trigger_set_payloads(service,
        normalized,
        config_root=os.path.abspath(config_root),
        trigger_set_path=resolved_path,
        parent_ref=parent_ref,
        additional_parent_refs=parent_refs,
        save_plan=save_plan or SavePlan(),
    )
    for item in sequence_items:
        if item["skip"]:
            continue
        service.repository.save_json(str(item["resolved_path"]), item["payload"])
    service.repository.save_json(resolved_path, trigger_payload)

    triggers = safe_deepcopy(get_active_triggers(normalized))
    by_key = {
        normalize_key_name(str(item.get("key") or "")): item
        for item in sequence_items
        if isinstance(item, dict) and not item["skip"]
    }
    for trigger in triggers:
        key = normalize_key_name(str(trigger.get("key") or ""))
        sequence_item = by_key.get(key)
        if not isinstance(sequence_item, dict):
            continue
        trigger[service.INTERNAL_SEQUENCE_SOURCE_PATH] = str(sequence_item.get("path") or "")
        if service.PARENT_REFS_KEY in sequence_item.get("payload", {}):
            trigger[service.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(
                sequence_item["payload"][service.PARENT_REFS_KEY]
            )
        trigger[service.INTERNAL_SEQUENCE_IMPORTED] = False
        trigger[service.INTERNAL_SEQUENCE_DIRTY] = False
    if service.PARENT_REFS_KEY in trigger_payload:
        for member in trigger_set_members(data):
            member[service.INTERNAL_TRIGGER_SET_PARENT_REFS] = safe_deepcopy(
                trigger_payload[service.PARENT_REFS_KEY]
            )
    return triggers, trigger_payload
