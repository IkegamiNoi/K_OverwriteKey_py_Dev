from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


SINGLE_LINE_MAIN_SCALE = 0.37
MAIN_WITH_SUB_SCALE = 0.27
SUB_SCALE = 0.19
MIN_MAIN_PX = 7
MIN_SUB_PX = 6
PX_STEP = 1


@dataclass(frozen=True)
class KeyTextFit:
    main_px: int
    sub_px: int
    main_lines: list[str]
    sub_lines: list[str]


def _split_lines(text: str) -> list[str]:
    return text.split("\n") if text else []


def _text_size(
    lines: list[str], px_size: int, bold: bool,
    measure: Callable[[str, int, bool], tuple[int, int]],
) -> tuple[int, int]:
    if not lines:
        return 0, 0
    measured = [measure(line, px_size, bold) for line in lines]
    return max(width for width, _ in measured), sum(height for _, height in measured)


def fit_key_text(
    main: str,
    sub: str,
    inner_w: float,
    inner_h: float,
    unit: float,
    measure: Callable[[str, int, bool], tuple[int, int]],
) -> KeyTextFit:
    main_lines = _split_lines(main)
    sub_lines = _split_lines(sub)
    has_sub = bool(sub_lines)
    main_scale = MAIN_WITH_SUB_SCALE if has_sub else SINGLE_LINE_MAIN_SCALE
    main_upper = max(MIN_MAIN_PX, int(unit * main_scale))
    minimum_sub_px = (
        max(MIN_SUB_PX, int(MIN_MAIN_PX * SUB_SCALE / MAIN_WITH_SUB_SCALE))
        if has_sub else 0
    )

    for main_px in range(main_upper, MIN_MAIN_PX - PX_STEP, -PX_STEP):
        sub_px = (
            max(MIN_SUB_PX, int(main_px * SUB_SCALE / MAIN_WITH_SUB_SCALE))
            if has_sub else 0
        )
        main_width, main_height = _text_size(main_lines, main_px, True, measure)
        sub_width, sub_height = _text_size(sub_lines, sub_px, False, measure)
        if max(main_width, sub_width) <= inner_w and main_height + sub_height <= inner_h:
            return KeyTextFit(main_px, sub_px, main_lines, sub_lines)

    return KeyTextFit(MIN_MAIN_PX, minimum_sub_px, main_lines, sub_lines)
