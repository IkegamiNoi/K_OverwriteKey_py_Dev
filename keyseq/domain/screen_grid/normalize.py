from __future__ import annotations

import logging
from typing import Any

from ..key_hold import MODIFIER_KEY_NAMES
from .models import (
    GridCell,
    GridRow,
    SubLayout,
    TopLayout,
    default_sub_layout,
    default_top_layout,
    is_positive_ratio,
    sub_layout_to_json,
    top_layout_to_json,
)


FIXED_RESERVED_KEYS = frozenset({
    "enter", "num enter", "space", "esc", "backspace", "tab",
}) | MODIFIER_KEY_NAMES


def has_enabled_grid(keymaps: Any) -> bool:
    return isinstance(keymaps, (list, tuple)) and any(
        isinstance(keymap, dict)
        and isinstance(keymap.get("grid"), dict)
        and keymap["grid"].get("enabled") is True
        for keymap in keymaps
    )


def monitor_identifier(left: int, top: int, right: int, bottom: int) -> str:
    return f"{right - left}x{bottom - top}{left:+d}{top:+d}"


def grid_key_name(value: Any) -> str:
    """Normalize a grid key without importing config and creating a cycle."""
    return (value or "").strip().lower() if isinstance(value, str) else ""


def _key_error(key: str, seen: set[str]) -> str | None:
    if not key:
        return "キーが空です"
    if key in seen:
        return "キーが重複しています"
    if key in FIXED_RESERVED_KEYS:
        return f"固定の予約キー {key!r} です"
    seen.add(key)
    return None


def _top_layout_with_reason(raw: Any) -> tuple[TopLayout | None, str | None]:
    if not isinstance(raw, dict) or not isinstance(raw.get("rows"), list) or not raw["rows"]:
        return None, "行がありません"
    rows: list[GridRow] = []
    seen: set[str] = set()
    for raw_row in raw["rows"]:
        if not isinstance(raw_row, dict):
            return None, "行の形が不正です"
        if not is_positive_ratio(raw_row.get("h")):
            return None, "比率が不正です"
        raw_cells = raw_row.get("cells")
        if not isinstance(raw_cells, list) or not raw_cells:
            return None, "列がありません"
        cells: list[GridCell] = []
        for raw_cell in raw_cells:
            if not isinstance(raw_cell, dict):
                return None, "列の形が不正です"
            if not is_positive_ratio(raw_cell.get("w")):
                return None, "比率が不正です"
            key = grid_key_name(raw_cell.get("key"))
            reason = _key_error(key, seen)
            if reason:
                return None, reason
            cells.append(GridCell(float(raw_cell["w"]), key))
        rows.append(GridRow(float(raw_row["h"]), tuple(cells)))
    height_total = sum(row.h for row in rows)
    if not is_positive_ratio(height_total):
        return None, "比率が不正です"
    normalized_rows: list[GridRow] = []
    for row in rows:
        width_total = sum(cell.w for cell in row.cells)
        if not is_positive_ratio(width_total):
            return None, "比率が不正です"
        normalized_rows.append(GridRow(
            row.h / height_total,
            tuple(GridCell(cell.w / width_total, cell.key) for cell in row.cells),
        ))
    return TopLayout(tuple(normalized_rows)), None


def top_layout_from_json(raw: Any) -> TopLayout | None:
    return _top_layout_with_reason(raw)[0]


def _sub_layout_with_reason(raw: Any) -> tuple[SubLayout | None, str | None]:
    if not isinstance(raw, dict):
        return None, "形が不正です"
    rows, cols, raw_keys = raw.get("rows"), raw.get("cols"), raw.get("keys")
    if not isinstance(rows, int) or isinstance(rows, bool) or not 1 <= rows <= 9:
        return None, "行数が不正です"
    if not isinstance(cols, int) or isinstance(cols, bool) or not 1 <= cols <= 9:
        return None, "列数が不正です"
    if rows * cols < 2:
        return None, "行数・列数が不正です（枠を2つ以上にしてください）"
    if not isinstance(raw_keys, list) or len(raw_keys) != rows * cols:
        return None, "キー数が不正です"
    keys = [grid_key_name(key) for key in raw_keys]
    seen: set[str] = set()
    for key in keys:
        reason = _key_error(key, seen)
        if reason:
            return None, reason
    return SubLayout(rows, cols, tuple(keys)), None


def sub_layout_from_json(raw: Any) -> SubLayout | None:
    return _sub_layout_with_reason(raw)[0]


def normalize_grid(raw: Any) -> dict[str, Any] | None:
    """Normalize grid JSON. Invalid individual shapes revert independently."""
    if not isinstance(raw, dict):
        return None
    logger = logging.getLogger(__name__)
    monitors: dict[str, Any] = {}
    raw_monitors = raw.get("monitors")
    if isinstance(raw_monitors, dict):
        for monitor_id, record in raw_monitors.items():
            if not isinstance(monitor_id, str):
                logger.warning("Invalid screen grid monitor identifier; using default layout")
                continue
            layout, reason = _top_layout_with_reason(record)
            if layout is None:
                logger.warning(
                    "Invalid screen grid layout for monitor %s (%s); using default layout",
                    monitor_id, reason,
                )
                continue
            monitors[monitor_id] = top_layout_to_json(layout)
    raw_sub = raw.get("sub")
    sub, reason = _sub_layout_with_reason(raw_sub)
    if sub is None:
        if "sub" in raw:
            logger.warning("Invalid screen grid sub layout (%s); using default layout", reason)
        sub = default_sub_layout()
    enabled = raw.get("enabled") if isinstance(raw.get("enabled"), bool) else False
    return {"enabled": enabled, "monitors": monitors, "sub": sub_layout_to_json(sub)}


def top_layout_for(grid: dict[str, Any] | None, monitor_id: str) -> TopLayout:
    monitors = grid.get("monitors") if isinstance(grid, dict) else None
    record = monitors.get(monitor_id) if isinstance(monitors, dict) else None
    return top_layout_from_json(record) or default_top_layout()


def sub_layout_of(grid: dict[str, Any] | None) -> SubLayout:
    raw = grid.get("sub") if isinstance(grid, dict) else None
    return sub_layout_from_json(raw) or default_sub_layout()
