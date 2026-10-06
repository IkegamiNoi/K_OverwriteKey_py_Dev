"""省略表示の保存サイズの解釈と表示サイズの計算（Tk 非依存）。"""

COMPACT_WINDOW_SIZE_KEY = "compact_window_size"


def parse_compact_window_size(raw: object) -> tuple[int | None, int | None]:
    if not isinstance(raw, dict):
        return None, None

    def positive_int(value: object) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else None

    return positive_int(raw.get("width")), positive_int(raw.get("height"))


def compact_geometry(
    saved_w: int | None, saved_h: int | None, current_h: int,
    minimum_h: int, screen_w: int, screen_h: int,
) -> tuple[int, int]:
    width = min(270 if saved_w is None else saved_w, screen_w)
    height = min(max(360, current_h) if saved_h is None else saved_h, screen_h)
    return width, max(minimum_h, height)
