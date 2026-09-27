"""Pure helpers for editing action sequences and loop markers."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from typing import Any

from keyseq.domain.sequence_control import (
    ACTION_TYPE_SYSTEM,
    MAX_LOOP_DEPTH,
    OP_BACK,
    OP_LOOP_END,
    OP_LOOP_START,
    OP_REWIND,
    analyze_loops,
    action_type,
    system_op,
)


def standalone_violation(
    actions: Sequence[Any],
    item: Any,
    *,
    replace_index: int | None = None,
) -> bool:
    """Return whether adding or replacing an item breaks standalone controls."""
    is_standalone = (
        isinstance(item, Mapping)
        and action_type(item) == ACTION_TYPE_SYSTEM
        and system_op(item) in (OP_BACK, OP_REWIND)
    )
    result_length = len(actions) + (replace_index is None)
    has_standalone = is_standalone or any(
        index != replace_index
        and isinstance(action, Mapping)
        and action_type(action) == ACTION_TYPE_SYSTEM
        and system_op(action) in (OP_BACK, OP_REWIND)
        for index, action in enumerate(actions)
    )
    return has_standalone and result_length != 1


def insert_actions(
    actions: MutableSequence[dict[str, Any]],
    new_items: Sequence[dict[str, Any]],
    *,
    after_index: int | None,
) -> int:
    """Insert items after an existing row (or at the end) and return the start index."""
    insert_at = len(actions) if after_index is None else after_index + 1
    actions[insert_at:insert_at] = new_items
    return insert_at


def adjust_position_after_insert(position: int, insert_at: int, count: int) -> int:
    """Keep a runtime position attached to its original row after insertion."""
    return position + count if insert_at <= position else position


def loop_pair_items(start_fields: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a loop start/end pair, retaining only the persisted loop keys."""
    start = {
        "type": start_fields.get("type", ACTION_TYPE_SYSTEM),
        "op": start_fields.get("op", OP_LOOP_START),
        "count": start_fields.get("count", 1),
        "infinite": start_fields.get("infinite", False),
        "label": start_fields.get("label", ""),
    }
    end = {"type": ACTION_TYPE_SYSTEM, "op": OP_LOOP_END, "label": ""}
    return [start, end]


def can_insert_loop(actions: Sequence[Any], after_index: int | None) -> bool:
    """Return whether adding an empty loop pair keeps all loops within the limit."""
    insert_at = len(actions) if after_index is None else after_index + 1
    candidate = list(actions)
    candidate[insert_at:insert_at] = loop_pair_items({})
    return not analyze_loops(candidate).too_deep


def pair_index(actions: Sequence[Any], index: int) -> int | None:
    """Return the matching loop marker index, or None for unmatched/non-loop rows."""
    if index < 0 or index >= len(actions):
        return None
    structure = analyze_loops(actions)
    if index in structure.pairs:
        return structure.pairs[index]
    return structure.reverse_pairs.get(index)


def delete_indices(actions: Sequence[Any], index: int) -> list[int]:
    """Return sorted rows to delete, removing a matched loop as a pair."""
    if index < 0 or index >= len(actions):
        return []
    paired = pair_index(actions, index)
    return sorted((index, paired)) if paired is not None else [index]


def can_move(actions: Sequence[Any], index: int, delta: int) -> bool:
    """Allow one-row moves unless two loop markers would exchange positions."""
    if index < 0 or index >= len(actions) or delta not in (-1, 1):
        return False
    other_index = index + delta
    if other_index < 0 or other_index >= len(actions):
        return False
    return not (_is_loop_marker(actions[index]) and _is_loop_marker(actions[other_index]))


def _is_loop_marker(action: Any) -> bool:
    return (
        isinstance(action, Mapping)
        and action_type(action) == ACTION_TYPE_SYSTEM
        and system_op(action) in (OP_LOOP_START, OP_LOOP_END)
    )
