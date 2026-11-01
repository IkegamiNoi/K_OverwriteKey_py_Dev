from __future__ import annotations

from collections.abc import Collection, Mapping
from types import MappingProxyType
from typing import Any

from keyseq.shared.i18n import tr

from ..key_hold import MODIFIER_KEY_NAMES
from .models import grid_key_name


GRID_OPS = ("deepen", "back", "click", "next_screen", "up", "down", "left", "right")
ARROW_OPS = ("up", "down", "left", "right")
DEFAULT_OPS: Mapping[str, str] = MappingProxyType({
    "deepen": "space",
    "back": "backspace",
    "click": "enter",
    "next_screen": "tab",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
})
FIXED_BACK_KEY = "esc"
FIXED_CLICK_KEY = "num enter"
FIXED_OP_KEYS = frozenset({FIXED_BACK_KEY, FIXED_CLICK_KEY})
_OP_LABEL_KEYS: Mapping[str, str] = MappingProxyType({
    "deepen": "deepen", "back": "back", "click": "click",
    "next_screen": "next_screen", "up": "up", "down": "down",
    "left": "left", "right": "right",
})


class _TranslatedOperationLabels(Mapping[str, str]):
    def __getitem__(self, operation: str) -> str:
        return tr(f"domain.screen_grid.ops.label.{_OP_LABEL_KEYS[operation]}")

    def __iter__(self):
        return iter(_OP_LABEL_KEYS)

    def __len__(self) -> int:
        return len(_OP_LABEL_KEYS)


OP_LABELS: Mapping[str, str] = _TranslatedOperationLabels()


def arrow_keys(ops: Mapping[str, str]) -> frozenset[str]:
    return frozenset(ops[name] for name in ARROW_OPS)


def normalize_ops(raw: Any) -> tuple[dict[str, str], tuple[str, ...]]:
    if not isinstance(raw, dict):
        return dict(DEFAULT_OPS), GRID_OPS
    normalized: dict[str, str] = {}
    reverted: list[str] = []
    for operation in GRID_OPS:
        if operation not in raw:
            normalized[operation] = DEFAULT_OPS[operation]
            continue
        value = raw[operation]
        key = grid_key_name(value)
        if (not isinstance(value, str) or not key or key in MODIFIER_KEY_NAMES
                or key in FIXED_OP_KEYS):
            normalized[operation] = DEFAULT_OPS[operation]
            reverted.append(operation)
        else:
            normalized[operation] = key
    return normalized, tuple(reverted)


def ops_of(grid: Any) -> dict[str, str]:
    return normalize_ops(grid.get("ops") if isinstance(grid, dict) else None)[0]


def ops_to_json(ops: Mapping[str, str]) -> dict[str, str] | None:
    normalized = {operation: ops[operation] for operation in GRID_OPS}
    if all(normalized[operation] == DEFAULT_OPS[operation] for operation in GRID_OPS):
        return None
    return normalized


def operation_keys(ops: Mapping[str, str]) -> frozenset[str]:
    return frozenset(grid_key_name(ops[operation]) for operation in GRID_OPS) | FIXED_OP_KEYS


def default_operation_keys() -> frozenset[str]:
    return operation_keys(DEFAULT_OPS)


def validate_ops(
    ops: Mapping[str, str], reserved: Collection[str], frame_keys: Collection[str],
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    reserved_names = {grid_key_name(key) for key in reserved if isinstance(key, str)}
    frame_names = {grid_key_name(key) for key in frame_keys if isinstance(key, str)}
    for operation in GRID_OPS:
        key = grid_key_name(ops.get(operation))
        if not key:
            reason_key = "key_empty"
        elif key in MODIFIER_KEY_NAMES:
            reason_key = "modifier_key"
        elif key in FIXED_OP_KEYS:
            reason_key = "fixed_key"
        elif key in seen:
            reason_key = "duplicate_key"
        elif key in reserved_names:
            reason_key = "reserved_key"
        elif key in frame_names:
            reason_key = "cell_key"
        else:
            reason_key = ""
        if reason_key:
            errors.append(tr(
                f"domain.screen_grid.ops.error.{reason_key}",
                operation=OP_LABELS[operation],
                key=key,
            ))
        seen.add(key)
    if FIXED_BACK_KEY in frame_names:
        errors.append(tr("domain.screen_grid.ops.fixed_back_overlap", key=FIXED_BACK_KEY))
    if FIXED_CLICK_KEY in frame_names:
        errors.append(tr("domain.screen_grid.ops.fixed_click_overlap", key=FIXED_CLICK_KEY))
    return errors
