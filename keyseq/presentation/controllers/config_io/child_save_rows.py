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
)
from keyseq.domain.config import normalize_key_name


SHARE_UNKNOWN = "unknown"
SHARE_SOLE = "sole"
SHARE_SHARED = "shared"
SHARE_OTHER_PARENT = "other"
SHARE_NEW = "new"


@dataclass(frozen=True)
class ChildSaveRow:
    kind: str
    key: str
    display_name: str
    target_path: str
    share_state: str
    share_text: str
    default_action: str


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
    if share_state == SHARE_NEW:
        return "新規作成"
    if share_state == SHARE_SOLE:
        return "単独"
    if share_state == SHARE_SHARED:
        return f"{ref_count} 個の上位で共有中・全てに影響します"
    if share_state == SHARE_OTHER_PARENT:
        return "別の構成に属します"
    return "所有元不明・安全のため別名"


def default_action_for(share_state) -> str:
    if share_state in (SHARE_UNKNOWN, SHARE_OTHER_PARENT):
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
    trigger_set_parent = _stored_parent_path(
        config_service,
        targets[(CHILD_TRIGGER_SET, "")],
        config_root,
    )

    rows: list[ChildSaveRow] = []
    keymaps = data.get("keymaps", [])
    if isinstance(keymaps, list):
        for keymap in keymaps:
            if not isinstance(keymap, dict) or not bool(
                keymap.get(config_service.INTERNAL_KEYMAP_DIRTY, False)
            ):
                continue
            key = normalize_key_name(str(keymap.get("id") or ""))
            target_path = targets.get((CHILD_KEYMAP, key))
            if not key or not target_path:
                continue
            rows.append(
                build_row(
                    kind=CHILD_KEYMAP,
                    key=key,
                    display_name=str(keymap.get("label") or "").strip() or key,
                    target_path=target_path,
                    current_parent=keymap_parent,
                    config_service=config_service,
                    config_root=config_root,
                )
            )
    if bool(dirty_tracker.trigger_set_dirty):
        rows.append(
            build_row(
                kind=CHILD_TRIGGER_SET,
                key="",
                display_name="トリガー一覧",
                target_path=targets[(CHILD_TRIGGER_SET, "")],
                current_parent=keymap_parent,
                config_service=config_service,
                config_root=config_root,
            )
        )
    triggers = data.get("triggers", [])
    if isinstance(triggers, list):
        for trigger in triggers:
            if not isinstance(trigger, dict) or not bool(
                trigger.get(config_service.INTERNAL_SEQUENCE_DIRTY, False)
            ):
                continue
            key = normalize_key_name(str(trigger.get("key") or ""))
            target_path = targets.get((CHILD_SEQUENCE, key))
            if not key or not target_path:
                continue
            rows.append(
                build_row(
                    kind=CHILD_SEQUENCE,
                    key=key,
                    display_name=str(trigger.get("label") or "").strip() or key,
                    target_path=target_path,
                    current_parent=trigger_set_parent,
                    config_service=config_service,
                    config_root=config_root,
                )
            )
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
    return ChildSaveRow(
        kind=kind,
        key=key,
        display_name=display_name,
        target_path=target_path,
        share_state=share_state,
        share_text=share_text_for(share_state, len(normalized_refs or [])),
        default_action=default_action_for(share_state),
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
