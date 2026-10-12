from __future__ import annotations

from .models import MIN_SUBDIVIDE_PX, SubLayout, TopLayout

Rect = tuple[int, int, int, int]


def _boundaries(start: int, length: int, ratios: tuple[float, ...]) -> list[int]:
    boundaries = [start]
    total = 0.0
    ratio_sum = sum(ratios)
    for ratio in ratios[:-1]:
        total += ratio / ratio_sum
        boundaries.append(start + round(length * total))
    boundaries.append(start + length)
    return boundaries


def top_cell_rects(region: Rect, layout: TopLayout) -> list[list[tuple[Rect, str]]]:
    left, top, right, bottom = region
    ys = _boundaries(top, bottom - top, tuple(row.h for row in layout.rows))
    result: list[list[tuple[Rect, str]]] = []
    for index, row in enumerate(layout.rows):
        xs = _boundaries(left, right - left, tuple(cell.w for cell in row.cells))
        result.append([
            ((xs[col], ys[index], xs[col + 1], ys[index + 1]), cell.key)
            for col, cell in enumerate(row.cells)
        ])
    return result


def sub_cell_rects(region: Rect, sub: SubLayout) -> list[tuple[Rect, str]]:
    left, top, right, bottom = region
    xs = [left + round((right - left) * col / sub.cols) for col in range(sub.cols + 1)]
    ys = [top + round((bottom - top) * row / sub.rows) for row in range(sub.rows + 1)]
    return [
        ((xs[col], ys[row], xs[col + 1], ys[row + 1]), sub.keys[row * sub.cols + col])
        for row in range(sub.rows)
        for col in range(sub.cols)
    ]


def rect_center(rect: Rect) -> tuple[int, int]:
    left, top, right, bottom = rect
    return ((left + right) // 2, (top + bottom) // 2)


def can_subdivide(rect: Rect, sub: SubLayout) -> bool:
    left, top, right, bottom = rect
    return ((right - left) // sub.cols >= MIN_SUBDIVIDE_PX
            and (bottom - top) // sub.rows >= MIN_SUBDIVIDE_PX)
