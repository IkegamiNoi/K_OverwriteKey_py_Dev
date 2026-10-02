"""Rules for duplicate trigger keys within one ordered trigger list."""

from collections.abc import Sequence
from typing import Any

from keyseq.domain.config import normalize_key_name


def effective_rows_by_key(triggers: Sequence[Any]) -> dict[str, int]:
    """Map each non-empty normalized key to its first row's position."""
    rows: dict[str, int] = {}
    for index, trigger in enumerate(triggers):
        if isinstance(trigger, dict):
            key = normalize_key_name(trigger.get("key", ""))
            if key:
                rows.setdefault(key, index)
    return rows


def replaced_effective_keys(before: Sequence[Any], after: Sequence[Any]) -> frozenset[str]:
    """Return surviving keys whose effective row changed by identity."""
    previous = effective_rows_by_key(before)
    current = effective_rows_by_key(after)
    return frozenset(
        key for key in previous.keys() & current.keys()
        if before[previous[key]] is not after[current[key]]
    )


def shadowed_duplicate_indices(triggers: Sequence[Any]) -> frozenset[int]:
    """Return indices whose non-empty key already appeared earlier."""
    seen: set[str] = set()
    shadowed: set[int] = set()
    for index, trigger in enumerate(triggers):
        if not isinstance(trigger, dict):
            continue
        key = normalize_key_name(trigger.get("key", ""))
        if not key:
            continue
        if key in seen:
            shadowed.add(index)
        else:
            seen.add(key)
    return frozenset(shadowed)


def effective_trigger_index(triggers: Sequence[Any], key: str) -> int | None:
    """Return the first row with the normalized, non-empty key."""
    normalized = normalize_key_name(key)
    if not normalized:
        return None
    for index, trigger in enumerate(triggers):
        if not isinstance(trigger, dict):
            continue
        if normalize_key_name(trigger.get("key", "")) == normalized:
            return index
    return None


def is_effective_trigger(triggers: Sequence[Any], index: int) -> bool:
    """Return whether a valid row is the first row for its non-empty key."""
    if index < 0 or index >= len(triggers):
        return False
    trigger = triggers[index]
    if not isinstance(trigger, dict):
        return False
    key = normalize_key_name(trigger.get("key", ""))
    return bool(key) and effective_trigger_index(triggers, key) == index
