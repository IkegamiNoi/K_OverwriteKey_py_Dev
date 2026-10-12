from __future__ import annotations

from .models import (
    AUTO_ASSIGN_ORDER, MAX_SUBDIVIDE_COUNT, MIN_SUBDIVIDE_COUNT,
    GridCell, GridRow, SubLayout, TopLayout, is_positive_ratio,
)
from .normalize import FIXED_RESERVED_KEYS, grid_key_name


_LETTER_ROWS = (
    tuple("qwertyuiop"),
    tuple("asdfghjkl;"),
    tuple("zxcvbnm,./"),
    tuple("1234567890"),
)


def _normalized_reserved(reserved: set[str]) -> set[str]:
    return {grid_key_name(key) for key in reserved if isinstance(key, str)} | set(FIXED_RESERVED_KEYS)


def next_free_key(used: set[str], reserved: set[str]) -> str:
    used_names = {grid_key_name(key) for key in used if isinstance(key, str)}
    reserved_names = _normalized_reserved(reserved)
    return next((key for key in AUTO_ASSIGN_ORDER if key not in used_names and key not in reserved_names), "")


def reassign_top_keys(layout: TopLayout, reserved: set[str]) -> TopLayout:
    blocked = _normalized_reserved(reserved)
    used: set[str] = set()
    rows = []
    for row_index, row in enumerate(layout.rows):
        preferred = _LETTER_ROWS[row_index] if row_index < len(_LETTER_ROWS) else ()
        cells = []
        for cell in row.cells:
            candidate = next((key for key in preferred if key not in used and key not in blocked), "")
            if not candidate:
                candidate = next_free_key(used, blocked)
            if candidate:
                used.add(candidate)
            cells.append(GridCell(cell.w, candidate))
        rows.append(GridRow(row.h, tuple(cells)))
    return TopLayout(tuple(rows))


def auto_fill_sub_keys(rows: int, cols: int, reserved: set[str]) -> tuple[str, ...]:
    if (not isinstance(rows, int) or isinstance(rows, bool)
            or not isinstance(cols, int) or isinstance(cols, bool)
            or not MIN_SUBDIVIDE_COUNT <= rows <= MAX_SUBDIVIDE_COUNT
            or not MIN_SUBDIVIDE_COUNT <= cols <= MAX_SUBDIVIDE_COUNT or rows * cols < 2):
        return ()
    blocked = _normalized_reserved(reserved)
    used: set[str] = set()
    keys = []
    for _ in range(rows * cols):
        key = next_free_key(used, blocked)
        keys.append(key)
        if key:
            used.add(key)
    return tuple(keys)


def _check_shape_key(key: str, location: str, used: set[str], reserved: set[str], errors: list[str]) -> None:
    if not key:
        errors.append(f"{location}: キーが空です")
    elif key in used:
        errors.append(f"{location}: キー {key!r} が重複しています")
    elif key in FIXED_RESERVED_KEYS:
        errors.append(f"{location}: 固定予約キー {key!r} は使えません")
    elif key in reserved:
        errors.append(f"{location}: 予約キー {key!r} は使えません")
    used.add(key)


def validate_top(layout: TopLayout, reserved: set[str]) -> list[str]:
    errors: list[str] = []
    used: set[str] = set()
    reserved_names = _normalized_reserved(reserved)
    if not layout.rows:
        errors.append("段がありません")
    for row_index, row in enumerate(layout.rows, start=1):
        if not is_positive_ratio(row.h):
            errors.append(f"段 {row_index}: 高さの比率は正の有限数にしてください")
        if not row.cells:
            errors.append(f"段 {row_index}: 列がありません")
        for col_index, cell in enumerate(row.cells, start=1):
            location = f"段 {row_index}・列 {col_index}"
            if not is_positive_ratio(cell.w):
                errors.append(f"{location}: 幅の比率は正の有限数にしてください")
            _check_shape_key(cell.key, location, used, reserved_names, errors)
    return errors


def validate_sub(sub: SubLayout, reserved: set[str]) -> list[str]:
    errors: list[str] = []
    if (not isinstance(sub.rows, int) or isinstance(sub.rows, bool)
            or not MIN_SUBDIVIDE_COUNT <= sub.rows <= MAX_SUBDIVIDE_COUNT):
        errors.append("細分化: 段数は1〜9にしてください")
    if (not isinstance(sub.cols, int) or isinstance(sub.cols, bool)
            or not MIN_SUBDIVIDE_COUNT <= sub.cols <= MAX_SUBDIVIDE_COUNT):
        errors.append("細分化: 列数は1〜9にしてください")
    if isinstance(sub.rows, int) and isinstance(sub.cols, int) and sub.rows * sub.cols < 2:
        errors.append("細分化: 枠を2つ以上にしてください")
    expected = sub.rows * sub.cols if isinstance(sub.rows, int) and isinstance(sub.cols, int) else -1
    if len(sub.keys) != expected:
        errors.append(f"細分化: キー数は{expected}個にしてください")
    used: set[str] = set()
    reserved_names = _normalized_reserved(reserved)
    for index, key in enumerate(sub.keys, start=1):
        _check_shape_key(key, f"細分化・枠 {index}", used, reserved_names, errors)
    return errors
