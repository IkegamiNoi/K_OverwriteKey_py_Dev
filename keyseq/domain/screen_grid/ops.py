from __future__ import annotations

from collections.abc import Collection, Mapping
from types import MappingProxyType
from typing import Any

from ..key_hold import MODIFIER_KEY_NAMES
from .models import grid_key_name


GRID_OPS = ("deepen", "back", "click", "next_screen", "up", "down", "left", "right")
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
OP_LABELS: Mapping[str, str] = MappingProxyType({
    "deepen": "深くする",
    "back": "戻る",
    "click": "クリック",
    "next_screen": "次の画面へ",
    "up": "上へ",
    "down": "下へ",
    "left": "左へ",
    "right": "右へ",
})


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
        prefix = f"操作キー（{OP_LABELS[operation]}）: "
        if not key:
            reason = "キーが空です"
        elif key in MODIFIER_KEY_NAMES:
            reason = f"修飾キー {key!r} です"
        elif key in FIXED_OP_KEYS:
            reason = f"固定の操作キー {key!r} です"
        elif key in seen:
            reason = f"キー {key!r} が先の操作と重複しています"
        elif key in reserved_names:
            reason = f"予約キー {key!r} と重なっています"
        elif key in frame_names:
            reason = f"枠のキー {key!r} と重なっています"
        else:
            reason = ""
        if reason:
            errors.append(prefix + reason)
        seen.add(key)
    if FIXED_BACK_KEY in frame_names:
        errors.append(f"操作キー（戻る・固定）: 枠のキー {FIXED_BACK_KEY!r} と重なっています")
    if FIXED_CLICK_KEY in frame_names:
        errors.append(f"操作キー（クリック・固定）: 枠のキー {FIXED_CLICK_KEY!r} と重なっています")
    return errors
