from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
    SavePlanError,
    compose_sequence_key,
)
from keyseq.domain.keymap_triggers import iter_trigger_sets
from keyseq.domain.config import normalize_key_name


Choice = tuple[str, str]
ChildId = tuple[str, str]


def build_save_plan(
    *,
    data: dict[str, Any],
    rows: Sequence[Any],
    choices: Mapping[ChildId, Choice],
    targets: Mapping[ChildId, str],
    confirmed: SavePlan | None = None,
) -> SavePlan:
    """一覧選択、確定済み操作、未変更既定の優先順で保存計画を作る。"""
    choices_by_child = _choices_by_child(rows, choices)
    entries = [
        _entry_for(CHILD_KEYMAP, key, choices_by_child, targets, confirmed)
        for key in _keymap_ids(data)
    ]
    entries.extend(
        _entry_for(CHILD_TRIGGER_SET, str(owner["id"]), choices_by_child, targets, confirmed)
        for owner, _, _ in iter_trigger_sets(data)
        if (CHILD_TRIGGER_SET, str(owner["id"])) in targets
    )
    entries.extend(
        _entry_for(CHILD_SEQUENCE, key, choices_by_child, targets, confirmed)
        for key in _sequence_keys(data)
    )
    legacy = data.get("_legacy_trigger_set", {})
    if legacy.get("state") == "migrated":
        migrated_id = str(legacy.get("keymap_id") or "")
        for index, entry in enumerate(entries):
            if entry.kind in {CHILD_KEYMAP, CHILD_TRIGGER_SET} and entry.key == migrated_id:
                if choices_by_child.get((entry.kind, entry.key), (None, ""))[0] == ACTION_SKIP:
                    raise SavePlanError("移行対象は保存しないを選択できません。")
                if entry.action == ACTION_SKIP:
                    entries[index] = ChildSaveEntry(entry.kind, entry.key, ACTION_SAVE)
    return SavePlan(entries=tuple(entries))


def _choices_by_child(
    rows: Sequence[Any], choices: Mapping[ChildId, Choice]
) -> dict[ChildId, Choice]:
    result: dict[ChildId, Choice] = {}
    for row in rows:
        child_id = (str(row.kind), str(row.key))
        if child_id not in choices:
            raise ValueError(f"保存操作が未指定です: {child_id[0]}:{child_id[1]}")
        result[child_id] = choices[child_id]
    return result


def _entry_for(
    kind: str,
    key: str,
    choices: Mapping[ChildId, Choice],
    targets: Mapping[ChildId, str],
    confirmed: SavePlan | None,
) -> ChildSaveEntry:
    child_id = (kind, key)
    choice = choices.get(child_id)
    if choice is not None:
        action, target_path = choice
        return ChildSaveEntry(kind, key, action, target_path if action == ACTION_SAVE_AS else "")
    confirmed_entry = confirmed.entry_for(kind, key) if confirmed is not None else None
    if confirmed_entry is not None:
        return confirmed_entry
    action = ACTION_SKIP if os.path.exists(targets[child_id]) else ACTION_SAVE
    return ChildSaveEntry(kind, key, action)


def _keymap_ids(data: dict[str, Any]) -> list[str]:
    keymaps = data.get("keymaps", [])
    if not isinstance(keymaps, list):
        return []
    return _unique_normalized_keys(keymap.get("id") for keymap in keymaps if isinstance(keymap, dict))


def _sequence_keys(data: dict[str, Any]) -> list[str]:
    return [
        compose_sequence_key(str(owner["id"]), key)
        for owner, _, triggers in iter_trigger_sets(data)
        for key in _unique_normalized_keys(item.get("key") for item in triggers if isinstance(item, dict))
    ]

def _unique_normalized_keys(values) -> list[str]:
    result: list[str] = []
    for value in values:
        key = normalize_key_name(str(value or ""))
        if key and key not in result:
            result.append(key)
    return result
