from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


ACTION_TYPE_MOUSE_SCROLL = "mouse_scroll"
DIRECTIONS = ("up", "down", "left", "right")
UNIT_NOTCH = "notch"
UNIT_DELTA = "delta"
WHEEL_DELTA = 120
MAX_NOTCHES = 100
MAX_DELTA = 12000
DEFAULT_NOTCHES = 1

_DIRECTION_NAMES = {"up": "上", "down": "下", "left": "左", "right": "右"}


@dataclass(frozen=True)
class MouseScrollSpec:
    direction: str
    unit: str
    amount: int
    position: tuple[int, int] | None


def parse_mouse_scroll(action: Mapping[str, Any]) -> MouseScrollSpec | str:
    direction_value = action.get("direction")
    if not isinstance(direction_value, str):
        return "向きはup / down / left / rightのいずれかを指定してください。"
    direction = direction_value.strip().lower()
    if direction not in DIRECTIONS:
        return "向きはup / down / left / rightのいずれかを指定してください。"

    unit_value = action.get("unit", UNIT_NOTCH)
    if isinstance(unit_value, str):
        unit = unit_value.strip().lower() or UNIT_NOTCH
    else:
        return "単位はnotchまたはdeltaを指定してください。"
    if unit not in (UNIT_NOTCH, UNIT_DELTA):
        return "単位はnotchまたはdeltaを指定してください。"

    amount_value = action.get("amount")
    if isinstance(amount_value, bool):
        return "量は整数で指定してください。"
    if isinstance(amount_value, int):
        amount = amount_value
    elif isinstance(amount_value, float):
        if not amount_value.is_integer():
            return "量は整数で指定してください。"
        amount = int(amount_value)
    elif isinstance(amount_value, str):
        try:
            amount = int(amount_value.strip())
        except (ValueError, OverflowError):
            return "量は整数に変換できる値を指定してください。"
    else:
        return "量は整数で指定してください。"

    maximum = MAX_NOTCHES if unit == UNIT_NOTCH else MAX_DELTA
    if not 1 <= amount <= maximum:
        return f"量は1〜{maximum}の範囲で指定してください。"

    has_x = "x" in action
    has_y = "y" in action
    if has_x != has_y:
        return "マウス座標はxとyの両方を指定してください。"
    position = None
    if has_x:
        try:
            position = (int(action["x"]), int(action["y"]))
        except (TypeError, ValueError, OverflowError):
            return "マウス座標xとyは整数に変換できる値を指定してください。"
    return MouseScrollSpec(direction, unit, amount, position)


def scroll_deltas(spec: MouseScrollSpec) -> tuple[bool, tuple[int, ...]]:
    vertical = spec.direction in ("up", "down")
    sign = 1 if spec.direction in ("up", "right") else -1
    if spec.unit == UNIT_NOTCH:
        return vertical, (sign * WHEEL_DELTA,) * spec.amount
    whole, remainder = divmod(spec.amount, WHEEL_DELTA)
    values = (sign * WHEEL_DELTA,) * whole
    if remainder:
        values += (sign * remainder,)
    return vertical, values


def format_mouse_scroll_value(action: Mapping[str, Any]) -> str:
    parsed = parse_mouse_scroll(action)
    if isinstance(parsed, str):
        direction = action.get("direction")
        if isinstance(direction, str):
            return f"[{ACTION_TYPE_MOUSE_SCROLL}] {direction}"
        return f"[{ACTION_TYPE_MOUSE_SCROLL}]"
    display = f"[スクロール] {_DIRECTION_NAMES[parsed.direction]}{parsed.amount}"
    if parsed.unit == UNIT_DELTA:
        display += "（生）"
    if parsed.position is not None:
        display += f" ({parsed.position[0]}, {parsed.position[1]})"
    return display


def describe_mouse_scroll(action: Mapping[str, Any]) -> str:
    parts = []
    for key in ("direction", "unit", "amount"):
        parts.append(f"{key}={str(action[key]) if key in action else '（なし）'}")
    if "x" in action or "y" in action:
        parts.extend(
            f"{key}={str(action[key]) if key in action else '（なし）'}"
            for key in ("x", "y")
        )
    return " ".join(parts)
