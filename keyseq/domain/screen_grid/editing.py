from __future__ import annotations

from collections.abc import Collection

from .assignment import next_free_key
from .models import GridCell, GridRow, TopLayout


def _all_keys(layout: TopLayout) -> set[str]:
    return {cell.key for row in layout.rows for cell in row.cells}


def split_row(
    layout: TopLayout, row_index: int, reserved: set[str], *, op_keys: Collection[str] | None = None,
) -> TopLayout:
    """Split one row into equal-height rows, assigning fresh keys below it."""
    if not 0 <= row_index < len(layout.rows):
        return layout
    row = layout.rows[row_index]
    used = _all_keys(layout)
    new_cells = []
    for cell in row.cells:
        key = next_free_key(used, reserved, op_keys=op_keys)
        if key:
            used.add(key)
        new_cells.append(GridCell(cell.w, key))
    half = row.h / 2
    rows = list(layout.rows)
    rows[row_index:row_index + 1] = [
        GridRow(half, row.cells), GridRow(half, tuple(new_cells))
    ]
    return TopLayout(tuple(rows))


def split_cell(
    layout: TopLayout, row_index: int, col_index: int, reserved: set[str], *,
    op_keys: Collection[str] | None = None,
) -> TopLayout:
    """Split one cell into equal-width cells, placing a fresh key on the right."""
    if not 0 <= row_index < len(layout.rows):
        return layout
    row = layout.rows[row_index]
    if not 0 <= col_index < len(row.cells):
        return layout
    used = _all_keys(layout)
    key = next_free_key(used, reserved, op_keys=op_keys)
    half = row.cells[col_index].w / 2
    cells = list(row.cells)
    cells[col_index:col_index + 1] = [GridCell(half, row.cells[col_index].key), GridCell(half, key)]
    rows = list(layout.rows)
    rows[row_index] = GridRow(row.h, tuple(cells))
    return TopLayout(tuple(rows))


def delete_row(layout: TopLayout, row_index: int) -> TopLayout:
    """Delete a row, expanding the next row or the previous row at the end."""
    if len(layout.rows) <= 1 or not 0 <= row_index < len(layout.rows):
        return layout
    rows = list(layout.rows)
    removed = rows.pop(row_index)
    neighbor_index = row_index if row_index < len(rows) else row_index - 1
    neighbor = rows[neighbor_index]
    rows[neighbor_index] = GridRow(neighbor.h + removed.h, neighbor.cells)
    return TopLayout(tuple(rows))


def delete_cell(layout: TopLayout, row_index: int, col_index: int) -> TopLayout:
    """Delete a cell, expanding the next cell or the previous cell at the end."""
    if not 0 <= row_index < len(layout.rows):
        return layout
    row = layout.rows[row_index]
    if len(row.cells) <= 1 or not 0 <= col_index < len(row.cells):
        return layout
    cells = list(row.cells)
    removed = cells.pop(col_index)
    neighbor_index = col_index if col_index < len(cells) else col_index - 1
    neighbor = cells[neighbor_index]
    cells[neighbor_index] = GridCell(neighbor.w + removed.w, neighbor.key)
    rows = list(layout.rows)
    rows[row_index] = GridRow(row.h, tuple(cells))
    return TopLayout(tuple(rows))


def _move_pair_boundary(
    values: tuple[float, ...], boundary_index: int, new_ratio: float, min_ratio: float
) -> tuple[float, ...]:
    if not 0 <= boundary_index < len(values) - 1:
        return values
    first = values[boundary_index]
    second = values[boundary_index + 1]
    pair_total = first + second
    before = sum(values[:boundary_index])
    pair_start = before
    pair_end = before + pair_total
    minimum = max(min_ratio, 0.0)
    if pair_total < 2 * minimum:
        return values
    target = min(max(new_ratio, pair_start + minimum), pair_end - minimum)
    first_new = target - pair_start
    changed = list(values)
    changed[boundary_index] = first_new
    changed[boundary_index + 1] = pair_total - first_new
    return tuple(changed)


def move_row_boundary(
    layout: TopLayout, boundary_index: int, new_ratio: float, min_ratio: float
) -> TopLayout:
    """Move a row boundary at a global vertical ratio, clamped by min_ratio."""
    heights = _move_pair_boundary(
        tuple(row.h for row in layout.rows), boundary_index, new_ratio, min_ratio
    )
    if heights == tuple(row.h for row in layout.rows):
        return layout
    return TopLayout(tuple(GridRow(height, row.cells) for row, height in zip(layout.rows, heights)))


def move_cell_boundary(
    layout: TopLayout,
    row_index: int,
    boundary_index: int,
    new_ratio: float,
    min_ratio: float,
) -> TopLayout:
    """Move a cell boundary at a row-local horizontal ratio."""
    if not 0 <= row_index < len(layout.rows):
        return layout
    row = layout.rows[row_index]
    widths = _move_pair_boundary(
        tuple(cell.w for cell in row.cells), boundary_index, new_ratio, min_ratio
    )
    if widths == tuple(cell.w for cell in row.cells):
        return layout
    cells = tuple(GridCell(width, cell.key) for cell, width in zip(row.cells, widths))
    rows = list(layout.rows)
    rows[row_index] = GridRow(row.h, cells)
    return TopLayout(tuple(rows))


def set_cell_key(layout: TopLayout, row_index: int, col_index: int, key: str) -> TopLayout:
    """Return a layout with one cell's key replaced."""
    if not 0 <= row_index < len(layout.rows):
        return layout
    row = layout.rows[row_index]
    if not 0 <= col_index < len(row.cells):
        return layout
    cells = list(row.cells)
    cell = cells[col_index]
    if cell.key == key:
        return layout
    cells[col_index] = GridCell(cell.w, key)
    rows = list(layout.rows)
    rows[row_index] = GridRow(row.h, tuple(cells))
    return TopLayout(tuple(rows))
