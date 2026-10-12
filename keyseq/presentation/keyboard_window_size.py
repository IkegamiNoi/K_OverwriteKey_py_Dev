"""キーボードUIの縦横比に基づくサイズ計算（Tk 非依存）。"""

KEYBOARD_WINDOW_PADDING = 10
KEYBOARD_WINDOW_MIN_WIDTH = 510
RESIZE_SETTLE_MS = 150


def layout_aspect(key_specs) -> float | None:
    """キー配置の外接矩形からキャンバスの縦横比を返す。"""
    if not key_specs:
        return None
    max_x = max(spec.x + spec.w for spec in key_specs)
    max_y = max(spec.y + spec.h for spec in key_specs)
    if max_y <= 0:
        return None
    return max_x / max_y


def size_from_width(width: int, ratio: float) -> tuple[int, int]:
    canvas_width = width - 2 * KEYBOARD_WINDOW_PADDING
    canvas_height = round(canvas_width / ratio)
    return width, canvas_height + 2 * KEYBOARD_WINDOW_PADDING


def size_from_height(height: int, ratio: float) -> tuple[int, int]:
    canvas_height = height - 2 * KEYBOARD_WINDOW_PADDING
    canvas_width = round(canvas_height * ratio)
    return canvas_width + 2 * KEYBOARD_WINDOW_PADDING, height


def minimum_size(ratio: float) -> tuple[int, int]:
    return size_from_width(KEYBOARD_WINDOW_MIN_WIDTH, ratio)


def corrected_size(
    base: tuple[int, int], current: tuple[int, int], ratio: float
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
    if result[0] < KEYBOARD_WINDOW_MIN_WIDTH:
        return minimum_size(ratio)
    return result
