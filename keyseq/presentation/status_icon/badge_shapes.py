"""Tk independent pixel calculations for status badges."""

from keyseq.presentation.status_text import HookDisplayState

BADGE_COLORS: dict[HookDisplayState, str] = {
    "on": "#1E9E3E",
    "off": "#D93025",
    "paused": "#F2B400",
}
BADGE_BACKGROUND = "#FFFFFF"


def badge_pixels(size: int, state: HookDisplayState, *, full: bool = False) -> dict[tuple[int, int], str]:
    s = size if full else max(7, int(size * 0.45 + 0.5))
    left = 0 if full else size - s
    pixels = {(left + x, y): BADGE_BACKGROUND for y in range(s) for x in range(s)}
    border = 1 if size < 32 else 2
    inner = s - 2 * border
    color = BADGE_COLORS[state]

    if state == "on":
        center = s / 2
        radius = inner / 2
        for y in range(border, s - border):
            for x in range(border, s - border):
                if (x + 0.5 - center) ** 2 + (y + 0.5 - center) ** 2 <= radius ** 2:
                    pixels[left + x, y] = color
    elif state == "off":
        for y in range(border, s - border):
            for x in range(border, s - border):
                pixels[left + x, y] = color
    else:
        gap = max(1, int(inner * 0.2 + 0.5))
        bar_width = (inner - gap) // 2
        spare_left = (inner - (2 * bar_width + gap)) // 2
        first = border + spare_left
        second = first + bar_width + gap
        for y in range(border, s - border):
            for x in range(first, first + bar_width):
                pixels[left + x, y] = color
            for x in range(second, second + bar_width):
                pixels[left + x, y] = color
    return pixels


def pixel_runs(pixels: dict[tuple[int, int], str], size: int) -> list[tuple[int, int, tuple[str, ...]]]:
    runs: list[tuple[int, int, tuple[str, ...]]] = []
    for y in range(size):
        start: int | None = None
        colors: list[str] = []
        for x in range(size + 1):
            color = pixels.get((x, y)) if x < size else None
            if color is None:
                if start is not None:
                    runs.append((start, y, tuple(colors)))
                    start, colors = None, []
            else:
                if start is None:
                    start = x
                colors.append(color)
    return runs
