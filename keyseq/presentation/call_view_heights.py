"""呼び出し枠の希望の高さと表示の高さ（tkinter 非依存）。"""

CALL_VIEW_HEIGHTS_KEY = "call_view_heights"


def parse_call_view_heights(raw: object) -> dict[str, int]:
    """正の整数を表示モードごとに採用する。未知のキーは捨てる。"""
    if not isinstance(raw, dict):
        return {}
    return {
        mode: value for mode in ("full", "compact")
        if not isinstance(value := raw.get(mode), bool)
        and isinstance(value, int) and value > 0
    }


def default_call_view_height(total_height: int) -> int:
    """一覧と枠に使える合計の高さの 3 分の 1 を希望値にする。"""
    return max(1, total_height // 3)


def displayed_call_view_height(
    desired: int, minimum: int, total_height: int, list_minimum: int,
    sash_height: int,
) -> int:
    """希望値を変えず、一覧の最小を残し、枠の最小まで引き上げる。"""
    maximum = max(minimum, total_height - list_minimum - sash_height)
    return max(minimum, min(desired, maximum))
