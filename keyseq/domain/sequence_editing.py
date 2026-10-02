"""Pure helpers for editing action sequences and loop markers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableSequence, Sequence
from typing import Any

from keyseq.domain.list_editing import move_block
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

PASTE_UNBALANCED_LOOP = "paste_unbalanced_loop"
PASTE_TOO_DEEP = "paste_too_deep"
PASTE_STANDALONE = "paste_standalone"


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


def can_move_block(
    actions: Sequence[Any], start: int, end: int, target_start: int
) -> bool:
    """Allow a block move only when loop relations stay valid by row identity."""
    try:
        candidate = move_block(actions, start, end, target_start)
    except ValueError:
        return False
    before = analyze_loops(actions)
    after = analyze_loops(candidate)
    before_pairs = _identity_pairs(actions, before.pairs)
    after_pairs = _identity_pairs(candidate, after.pairs)
    if before_pairs != after_pairs:
        return False
    before_unmatched = _identity_indices(actions, before.unmatched)
    after_unmatched = _identity_indices(candidate, after.unmatched)
    if before_unmatched != after_unmatched:
        return False
    before_deep = _identity_indices(actions, before.too_deep)
    after_deep = _identity_indices(candidate, after.too_deep)
    return after_deep <= before_deep


def _identity_pairs(actions: Sequence[Any], pairs: Mapping[int, int]) -> set[frozenset[int]]:
    return {frozenset((id(actions[start]), id(actions[end]))) for start, end in pairs.items()}


def _identity_indices(actions: Sequence[Any], indices: Iterable[int]) -> set[int]:
    return {id(actions[index]) for index in indices}


def paste_violation(actions: Sequence[Any], items: Sequence[Any]) -> str | None:
    """Return the first loop or standalone rule violated by appending items."""
    if not items:
        return None
    if analyze_loops(items).unmatched:
        return PASTE_UNBALANCED_LOOP
    before_deep = _identity_indices(actions, analyze_loops(actions).too_deep)
    combined = list(actions) + list(items)
    if not _identity_indices(combined, analyze_loops(combined).too_deep) <= before_deep:
        return PASTE_TOO_DEEP
    has_standalone = any(
        isinstance(action, Mapping)
        and action_type(action) == ACTION_TYPE_SYSTEM
        and system_op(action) in (OP_BACK, OP_REWIND)
        for action in combined
    )
    if has_standalone and len(combined) != 1:
        return PASTE_STANDALONE
    return None
