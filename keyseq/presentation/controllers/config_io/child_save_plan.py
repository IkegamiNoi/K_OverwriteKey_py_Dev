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
)
from keyseq.domain.config import normalize_key_name


Choice = tuple[str, str]
ChildId = tuple[str, str]


def build_save_plan(
    *,
    data: dict[str, Any],
    rows: Sequence[Any],
    choices: Mapping[ChildId, Choice],
    targets: Mapping[ChildId, str],
) -> SavePlan:
    """dirty 行の選択と未変更の既定動作から、全子ファイルの保存計画を作る。"""
    choices_by_child = _choices_by_child(rows, choices)
    entries = [
        _entry_for(CHILD_KEYMAP, key, choices_by_child, targets)
        for key in _keymap_ids(data)
    ]
    entries.append(_entry_for(CHILD_TRIGGER_SET, "", choices_by_child, targets))
    entries.extend(
        _entry_for(CHILD_SEQUENCE, key, choices_by_child, targets)
        for key in _sequence_keys(data)
    )
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
) -> ChildSaveEntry:
    child_id = (kind, key)
    choice = choices.get(child_id)
    if choice is not None:
        action, target_path = choice
        return ChildSaveEntry(kind, key, action, target_path if action == ACTION_SAVE_AS else "")
    action = ACTION_SKIP if os.path.exists(targets[child_id]) else ACTION_SAVE
    return ChildSaveEntry(kind, key, action)


def _keymap_ids(data: dict[str, Any]) -> list[str]:
    keymaps = data.get("keymaps", [])
    if not isinstance(keymaps, list):
        return []
    return _unique_normalized_keys(keymap.get("id") for keymap in keymaps if isinstance(keymap, dict))


def _sequence_keys(data: dict[str, Any]) -> list[str]:
    triggers = data.get("triggers", [])
    if not isinstance(triggers, list):
        return []
    return _unique_normalized_keys(trigger.get("key") for trigger in triggers if isinstance(trigger, dict))


def _unique_normalized_keys(values) -> list[str]:
    result: list[str] = []
    for value in values:
        key = normalize_key_name(str(value or ""))
        if key and key not in result:
            result.append(key)
    return result
