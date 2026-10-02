"""Pure helpers shared by ordered-list editing operations."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")
_NUMBERED_SUFFIX = re.compile(r" \(([0-9]+)\)$")


def move_block(items: Sequence[T], start: int, end: int, target_start: int) -> list[T]:
    """Return a copy with the inclusive block moved to its new start index."""
    if start < 0 or end < start or end >= len(items):
        raise ValueError("block indices are outside the items")
    block = list(items[start : end + 1])
    remaining = list(items[:start]) + list(items[end + 1 :])
    target = min(max(target_start, 0), len(remaining))
    return remaining[:target] + block + remaining[target:]


def shift_block(length: int, start: int, end: int, delta: int) -> int | None:
    """Return the adjacent block start, or None when it cannot shift."""
    if delta not in (-1, 1) or length < 0 or start < 0 or end < start or end >= length:
        return None
    target = start + delta
    return target if 0 <= target <= length - (end - start + 1) else None


def index_after_reorder(
    before: Sequence[object], after: Sequence[object], position: int
) -> int:
    """Find the new index of the same row object, preserving terminal positions."""
    if position < 0 or position >= len(before):
        return position
    target = before[position]
    for index, item in enumerate(after):
        if item is target:
            return index
    raise ValueError("the selected item is missing after reorder")


def _normalized(label: str) -> str:
    return label.strip()


def _base_label(label: str) -> str:
    match = _NUMBERED_SUFFIX.search(label)
    base = label[: match.start()] if match and int(match.group(1)) >= 2 else label
    return base or label


def numbered_label(label: str, existing: Iterable[str]) -> str:
    """Return label unchanged when unique, otherwise choose the first free suffix."""
    if not _normalized(label):
        return ""
    occupied = {_normalized(value) for value in existing}
    if _normalized(label) not in occupied:
        return label
    base = _base_label(_normalized(label))
    number = 2
    while _normalized(f"{base} ({number})") in occupied:
        number += 1
    return f"{base} ({number})"


def numbered_labels(labels: Sequence[str], existing: Iterable[str]) -> list[str]:
    """Number labels in order, adding each result to the occupied labels."""
    occupied = list(existing)
    result: list[str] = []
    for label in labels:
        numbered = numbered_label(label, occupied)
        result.append(numbered)
        occupied.append(numbered)
    return result
