from __future__ import annotations

import os
from dataclasses import dataclass

from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    SavePlan,
    compose_sequence_key,
)
from keyseq.domain.keymap_triggers import iter_trigger_sets, INTERNAL_TRIGGER_SET_DIRTY
from keyseq.domain.config import normalize_key_name


SHARE_UNKNOWN = "unknown"
SHARE_SOLE = "sole"
SHARE_SHARED = "shared"
SHARE_OTHER_PARENT = "other"
SHARE_NEW = "new"
SHARE_NEW_COLLIDES = "new_collides"


@dataclass(frozen=True)
class ChildSaveRow:
    kind: str
    key: str
    display_name: str
    target_path: str
    share_state: str
    share_text: str
    default_action: str
    allow_skip: bool = True


def judge_share_state(
    parent_refs,
    current_parent,
    *,
    target_exists,
    config_service=None,
    config_root: str = "",
) -> str:
    if not target_exists:
        return SHARE_NEW
    if not current_parent or not parent_refs:
        return SHARE_UNKNOWN

    canonicalize = (
        (lambda value: config_service.canonical_path(value, config_root))
        if config_service is not None
        else (lambda value: str(value).strip().replace("\\", "/"))
    )
    canonical_current = canonicalize(current_parent)
    canonical_refs: list[str] = []
    for ref in parent_refs:
        if not isinstance(ref, str):
            continue
        canonical_ref = canonicalize(ref)
        if canonical_ref and canonical_ref not in canonical_refs:
            canonical_refs.append(canonical_ref)
    if not canonical_refs:
        return SHARE_UNKNOWN
    if canonical_current not in canonical_refs:
        return SHARE_OTHER_PARENT
    if len(canonical_refs) == 1:
        return SHARE_SOLE
    return SHARE_SHARED


def share_text_for(share_state, ref_count) -> str:
    if share_state == SHARE_NEW_COLLIDES:
        return "同名の既存ファイルあり・安全のため別名"
    if share_state == SHARE_NEW:
        return "新規作成"
    if share_state == SHARE_SOLE:
        return "この構成のみが所有・既存を上書き"
    if share_state == SHARE_SHARED:
        return f"{ref_count} 個の上位で共有中・全てに影響します"
    if share_state == SHARE_OTHER_PARENT:
        return "別の構成に属します"
    return "所有元不明・安全のため別名"


def default_action_for(share_state) -> str:
    if share_state in (SHARE_UNKNOWN, SHARE_OTHER_PARENT, SHARE_NEW_COLLIDES):
        return ACTION_SAVE_AS
    return ACTION_SAVE


def collect_child_save_rows(
    *,
    data,
    dirty_tracker,
    config_service,
    config_root,
    keymap_set_path,
    split_base_dir: str = "",
    save_plan: SavePlan | None = None,
    migration_source_path: str = "",
) -> list[ChildSaveRow]:
    if not isinstance(data, dict):
        return []

    targets = config_service.resolve_child_save_targets(
        data,
        config_root=config_root,
        keymap_set_path=keymap_set_path,
        split_base_dir=split_base_dir,
        save_plan=save_plan,
    )
    keymap_parent = _stored_parent_path(
        config_service,
        keymap_set_path,
        config_root,
    )
    rows: list[ChildSaveRow] = []
    legacy = data.get(config_service.INTERNAL_LEGACY_TRIGGER_SET, {})
    migrated_id = (
        normalize_key_name(str(legacy.get("keymap_id") or ""))
        if legacy.get("state") == "migrated"
        else ""
    )
    keymaps = data.get("keymaps", [])
    if isinstance(keymaps, list):
        for keymap in keymaps:
            if not isinstance(keymap, dict):
                continue
            source_path = str(keymap.get(config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
            if not keymap.get(config_service.INTERNAL_KEYMAP_DIRTY, False) and source_path:
                continue
            key = normalize_key_name(str(keymap.get("id") or ""))
            target_path = targets.get((CHILD_KEYMAP, key))
            if not key or not target_path:
                continue
            rows.append(
                build_row(
                    kind=CHILD_KEYMAP,
                    allow_skip=key != migrated_id,
                    key=key,
                    display_name=str(keymap.get("label") or "").strip() or key,
                    target_path=target_path,
                    current_parent=keymap_parent,
                    config_service=config_service,
                    config_root=config_root,
                    has_source_path=bool(source_path),
                )
            )
    for owner, _, triggers in iter_trigger_sets(data):
        owner_id = normalize_key_name(str(owner.get("id") or ""))
        if not owner_id:
            continue
        owner_name = str(owner.get("label") or owner_id)
        trigger_target = targets.get((CHILD_TRIGGER_SET, owner_id))
        source_path = str(owner.get(config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH) or "").strip()
        is_migrated = owner_id == migrated_id
        if trigger_target and (source_path or triggers) and (
            owner.get(INTERNAL_TRIGGER_SET_DIRTY, False)
            or (not source_path and bool(triggers))
            or is_migrated
        ):
            rows.append(build_row(
                kind=CHILD_TRIGGER_SET, key=owner_id,
                display_name=f"{owner_name} / トリガー一覧", target_path=trigger_target,
                current_parent=_stored_parent_path(config_service, targets[(CHILD_KEYMAP, owner_id)], config_root),
                config_service=config_service, config_root=config_root,
                has_source_path=bool(source_path),
                migration_parent_path=(
                    migration_source_path or keymap_set_path
                ) if is_migrated else "",
            ))
        for trigger in triggers:
            source_path = str(trigger.get(config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
            if not trigger.get(config_service.INTERNAL_SEQUENCE_DIRTY, False) and source_path:
                continue
            key = compose_sequence_key(owner_id, normalize_key_name(str(trigger.get("key") or "")))
            target_path = targets.get((CHILD_SEQUENCE, key))
            if not target_path:
                continue
            rows.append(build_row(
                kind=CHILD_SEQUENCE, key=key,
                display_name=f"{owner_name} / {trigger.get('label') or trigger['key']}",
                target_path=target_path,
                current_parent=_stored_parent_path(config_service, trigger_target, config_root),
                config_service=config_service, config_root=config_root,
                has_source_path=bool(source_path),
            ))
    return rows


def build_row(
    *,
    kind: str,
    key: str,
    display_name: str,
    target_path: str,
    current_parent: str,
    config_service,
    config_root: str,
    has_source_path: bool,
    allow_skip: bool = True,
    migration_parent_path: str = "",
) -> ChildSaveRow:
    target_exists = os.path.exists(target_path)
    refs = config_service.read_parent_refs(target_path) if target_exists else None
    normalized_refs = _stored_parent_refs(config_service, refs, config_root)
    share_state = judge_share_state(
        normalized_refs,
        current_parent,
        target_exists=target_exists,
        config_service=config_service,
        config_root=config_root,
    )
    if kind == CHILD_TRIGGER_SET and migration_parent_path and normalized_refs:
        migration_parent = _stored_parent_path(config_service, migration_parent_path, config_root)
        if migration_parent in normalized_refs:
            share_state = judge_share_state(
                normalized_refs,
                migration_parent,
                target_exists=target_exists,
                config_service=config_service,
                config_root=config_root,
            )
    if (
        kind in (CHILD_KEYMAP, CHILD_TRIGGER_SET, CHILD_SEQUENCE)
        and target_exists
        and not has_source_path
        and share_state in (SHARE_SOLE, SHARE_SHARED)
    ):
        share_state = SHARE_NEW_COLLIDES
    return ChildSaveRow(
        kind=kind,
        key=key,
        display_name=display_name,
        target_path=target_path,
        share_state=share_state,
        share_text=share_text_for(share_state, len(normalized_refs or [])),
        default_action=default_action_for(share_state),
        allow_skip=allow_skip,
    )


def _stored_parent_refs(config_service, refs, config_root: str) -> list[str] | None:
    if refs is None:
        return None
    stored_refs: list[str] = []
    for ref in refs:
        stored_path = _stored_parent_path(config_service, ref, config_root)
        if stored_path and stored_path not in stored_refs:
            stored_refs.append(stored_path)
    return stored_refs


def _stored_parent_path(config_service, path, config_root: str) -> str:
    value = str(path or "").strip()
    if not value:
        return ""
    return config_service.canonical_path(value, config_root)
