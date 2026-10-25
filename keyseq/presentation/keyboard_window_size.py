"""キーボードUIの縦横比に基づくサイズ計算（Tk 非依存）。"""

from math import ceil


KEYBOARD_WINDOW_PADDING = 10
KEYBOARD_WINDOW_MIN_WIDTH = 510
KEYBOARD_KEY_MIN_UNIT = 27
RESIZE_SETTLE_MS = 150


def layout_extent(key_specs) -> tuple[float, float] | None:
    """キー配置の外接矩形を返す。"""
    if not key_specs:
        return None
    max_x = max(spec.x + spec.w for spec in key_specs)
    max_y = max(spec.y + spec.h for spec in key_specs)
    if max_y <= 0:
        return None
    return max_x, max_y


def layout_aspect(key_specs) -> float | None:
    """キー配置の外接矩形からキャンバスの縦横比を返す。"""
    extent = layout_extent(key_specs)
    if extent is None:
        return None
    return extent[0] / extent[1]


def size_from_width(width: int, ratio: float) -> tuple[int, int]:
    canvas_width = width - 2 * KEYBOARD_WINDOW_PADDING
    canvas_height = round(canvas_width / ratio)
    return width, canvas_height + 2 * KEYBOARD_WINDOW_PADDING


def size_from_height(height: int, ratio: float) -> tuple[int, int]:
    canvas_height = height - 2 * KEYBOARD_WINDOW_PADDING
    canvas_width = round(canvas_height * ratio)
    return canvas_width + 2 * KEYBOARD_WINDOW_PADDING, height


def minimum_size(extent: tuple[float, float]) -> tuple[int, int]:
    max_x, max_y = extent
    canvas_width = ceil(KEYBOARD_KEY_MIN_UNIT * max_x)
    canvas_height = ceil(KEYBOARD_KEY_MIN_UNIT * max_y)
    ratio = max_x / max_y
    width_size = size_from_width(
        canvas_width + 2 * KEYBOARD_WINDOW_PADDING, ratio
    )
    height_size = size_from_height(
        canvas_height + 2 * KEYBOARD_WINDOW_PADDING, ratio
    )
    result = max(width_size, height_size, key=lambda size: (size[0], size[1]))
    while (
        result[0] - 2 * KEYBOARD_WINDOW_PADDING < canvas_width
        or result[1] - 2 * KEYBOARD_WINDOW_PADDING < canvas_height
        or (result[0] - 2 * KEYBOARD_WINDOW_PADDING) / max_x < KEYBOARD_KEY_MIN_UNIT - 0.1
        or (result[1] - 2 * KEYBOARD_WINDOW_PADDING) / max_y < KEYBOARD_KEY_MIN_UNIT - 0.1
    ):
        result = size_from_width(result[0] + 1, ratio)
    return result


def corrected_size(
    base: tuple[int, int],
    current: tuple[int, int],
    ratio: float,
    minimum: tuple[int, int],
) -> tuple[int, int] | None:
    base_width, base_height = base
    current_width, current_height = current
    width_changed = current_width != base_width
    height_changed = current_height != base_height
    if not width_changed and not height_changed:
        return None
    if width_changed and not height_changed:
        result = size_from_width(current_width, ratio)
    elif height_changed and not width_changed:
        result = size_from_height(current_height, ratio)
    else:
        width_result = size_from_width(current_width, ratio)
        if width_result[1] <= current_height:
            result = width_result
        else:
            result = size_from_height(current_height, ratio)
    if result[0] < minimum[0]:
        return minimum
    return result
