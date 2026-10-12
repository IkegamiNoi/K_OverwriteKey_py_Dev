from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any


DEFAULT_TOP_KEYS = (("q", "w", "e", "r"), ("a", "s", "d", "f"), ("z", "x", "c", "v"))
DEFAULT_SUB_ROWS = 3
DEFAULT_SUB_COLS = 3
DEFAULT_SUB_KEYS = ("q", "w", "e", "a", "s", "d", "z", "x", "c")
AUTO_ASSIGN_ORDER = tuple("qwertyuiopasdfghjkl;zxcvbnm,./1234567890")
MIN_SUBDIVIDE_PX = 4
MIN_EDIT_CELL_PX = 8
MIN_SUBDIVIDE_COUNT = 1
MAX_SUBDIVIDE_COUNT = 9


@dataclass(frozen=True)
class GridCell:
    w: float
    key: str


@dataclass(frozen=True)
class GridRow:
    h: float
    cells: tuple[GridCell, ...]


@dataclass(frozen=True)
class TopLayout:
    rows: tuple[GridRow, ...]


@dataclass(frozen=True)
class SubLayout:
    rows: int
    cols: int
    keys: tuple[str, ...]


def is_positive_ratio(value: object) -> bool:
    """Return whether value is a positive, finite numeric ratio."""
    if not isinstance(value, Real) or isinstance(value, bool) or value <= 0:
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def default_top_layout() -> TopLayout:
    """Build the immutable, equally divided three by four default layout."""
    return TopLayout(tuple(
        GridRow(1 / len(DEFAULT_TOP_KEYS), tuple(
            GridCell(1 / len(row), key) for key in row
        ))
        for row in DEFAULT_TOP_KEYS
    ))


def default_sub_layout() -> SubLayout:
    return SubLayout(DEFAULT_SUB_ROWS, DEFAULT_SUB_COLS, DEFAULT_SUB_KEYS)


def new_enabled_grid() -> dict[str, Any]:
    return {"enabled": True, "monitors": {}, "sub": sub_layout_to_json(default_sub_layout())}


def top_layout_to_json(layout: TopLayout) -> dict[str, Any]:
    return {"rows": [
        {"h": row.h, "cells": [{"w": cell.w, "key": cell.key} for cell in row.cells]}
        for row in layout.rows
    ]}


def sub_layout_to_json(layout: SubLayout) -> dict[str, Any]:
    return {"rows": layout.rows, "cols": layout.cols, "keys": list(layout.keys)}
