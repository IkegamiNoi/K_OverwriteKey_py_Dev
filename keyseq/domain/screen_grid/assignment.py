from __future__ import annotations

from collections.abc import Collection

from keyseq.shared.i18n import tr

from ..key_hold import MODIFIER_KEY_NAMES
from .models import (
    AUTO_ASSIGN_ORDER, MAX_SUBDIVIDE_COUNT, MIN_SUBDIVIDE_COUNT,
    GridCell, GridRow, SubLayout, TopLayout, grid_key_name, is_positive_ratio,
)
from .ops import default_operation_keys


_LETTER_ROWS = tuple(
    AUTO_ASSIGN_ORDER[index:index + 10]
    for index in range(0, len(AUTO_ASSIGN_ORDER), 10)
)


def _normalized_reserved(reserved: Collection[str]) -> set[str]:
    return {grid_key_name(key) for key in reserved if isinstance(key, str)} | set(MODIFIER_KEY_NAMES)


def _normalized_op_keys(op_keys: Collection[str] | None) -> set[str]:
    keys = default_operation_keys() if op_keys is None else op_keys
    return {grid_key_name(key) for key in keys if isinstance(key, str)}


def next_free_key(used: set[str], reserved: set[str], *, op_keys: Collection[str] | None = None) -> str:
    used_names = {grid_key_name(key) for key in used if isinstance(key, str)}
    reserved_names = _normalized_reserved(reserved) | _normalized_op_keys(op_keys)
    return next((key for key in AUTO_ASSIGN_ORDER if key not in used_names and key not in reserved_names), "")


def reassign_top_keys(
    layout: TopLayout, reserved: set[str], *, op_keys: Collection[str] | None = None,
) -> TopLayout:
    blocked = _normalized_reserved(reserved) | _normalized_op_keys(op_keys)
    used: set[str] = set()
    rows = []
    for row_index, row in enumerate(layout.rows):
        preferred = _LETTER_ROWS[row_index] if row_index < len(_LETTER_ROWS) else ()
        cells = []
        for cell in row.cells:
            candidate = next((key for key in preferred if key not in used and key not in blocked), "")
            if not candidate:
                candidate = next_free_key(used, blocked, op_keys=())
            if candidate:
                used.add(candidate)
            cells.append(GridCell(cell.w, candidate))
        rows.append(GridRow(row.h, tuple(cells)))
    return TopLayout(tuple(rows))


def auto_fill_sub_keys(
    rows: int, cols: int, reserved: set[str], *, op_keys: Collection[str] | None = None,
) -> tuple[str, ...]:
    if (not isinstance(rows, int) or isinstance(rows, bool)
            or not isinstance(cols, int) or isinstance(cols, bool)
            or not MIN_SUBDIVIDE_COUNT <= rows <= MAX_SUBDIVIDE_COUNT
            or not MIN_SUBDIVIDE_COUNT <= cols <= MAX_SUBDIVIDE_COUNT or rows * cols < 2):
        return ()
    blocked = _normalized_reserved(reserved) | _normalized_op_keys(op_keys)
    used: set[str] = set()
    keys = []
    for _ in range(rows * cols):
        key = next_free_key(used, blocked, op_keys=())
        keys.append(key)
        if key:
            used.add(key)
    return tuple(keys)


def _check_shape_key(
    key: str, location: str, used: set[str], reserved: set[str], op_keys: set[str], errors: list[str],
) -> None:
    if not key:
        errors.append(tr("domain.screen_grid.assignment.key_empty", location=location))
    elif key in used:
        errors.append(tr("domain.screen_grid.assignment.key_duplicate", location=location, key=key))
    elif key in MODIFIER_KEY_NAMES:
        errors.append(tr("domain.screen_grid.assignment.modifier_key", location=location, key=key))
    elif key in op_keys:
        errors.append(tr("domain.screen_grid.assignment.operation_key", location=location, key=key))
    elif key in reserved:
        errors.append(tr("domain.screen_grid.assignment.reserved_key", location=location, key=key))
    used.add(key)


def validate_top(
    layout: TopLayout, reserved: set[str], *, op_keys: Collection[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    used: set[str] = set()
    reserved_names = _normalized_reserved(reserved)
    operation_names = _normalized_op_keys(op_keys)
    if not layout.rows:
        errors.append(tr("domain.screen_grid.assignment.rows_missing"))
    for row_index, row in enumerate(layout.rows, start=1):
        if not is_positive_ratio(row.h):
            errors.append(tr("domain.screen_grid.assignment.height_ratio_invalid", row=row_index))
        if not row.cells:
            errors.append(tr("domain.screen_grid.assignment.cells_missing", row=row_index))
        for col_index, cell in enumerate(row.cells, start=1):
            location = tr("domain.screen_grid.assignment.location", row=row_index, column=col_index)
            if not is_positive_ratio(cell.w):
                errors.append(tr("domain.screen_grid.assignment.width_ratio_invalid", location=location))
            _check_shape_key(cell.key, location, used, reserved_names, operation_names, errors)
    return errors


def validate_sub(
    sub: SubLayout, reserved: set[str], *, op_keys: Collection[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    if (not isinstance(sub.rows, int) or isinstance(sub.rows, bool)
            or not MIN_SUBDIVIDE_COUNT <= sub.rows <= MAX_SUBDIVIDE_COUNT):
        errors.append(tr("domain.screen_grid.assignment.subdivision_rows_invalid"))
    if (not isinstance(sub.cols, int) or isinstance(sub.cols, bool)
            or not MIN_SUBDIVIDE_COUNT <= sub.cols <= MAX_SUBDIVIDE_COUNT):
        errors.append(tr("domain.screen_grid.assignment.subdivision_columns_invalid"))
    if isinstance(sub.rows, int) and isinstance(sub.cols, int) and sub.rows * sub.cols < 2:
        errors.append(tr("domain.screen_grid.assignment.subdivision_min_cells"))
    expected = sub.rows * sub.cols if isinstance(sub.rows, int) and isinstance(sub.cols, int) else -1
    if len(sub.keys) != expected:
        errors.append(tr("domain.screen_grid.assignment.subdivision_key_count", expected=expected))
    used: set[str] = set()
    reserved_names = _normalized_reserved(reserved)
    operation_names = _normalized_op_keys(op_keys)
    for index, key in enumerate(sub.keys, start=1):
        _check_shape_key(key, tr("domain.screen_grid.assignment.subdivision_location", index=index), used, reserved_names, operation_names, errors)
    return errors
