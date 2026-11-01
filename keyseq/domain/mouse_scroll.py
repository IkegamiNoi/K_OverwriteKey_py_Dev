from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from keyseq.shared.i18n import tr


ACTION_TYPE_MOUSE_SCROLL = "mouse_scroll"
DIRECTIONS = ("up", "down", "left", "right")
UNIT_NOTCH = "notch"
UNIT_DELTA = "delta"
WHEEL_DELTA = 120
MAX_NOTCHES = 100
MAX_DELTA = 12000
DEFAULT_NOTCHES = 1

_DIRECTION_KEYS = {
    "up": "domain.mouse_scroll.direction.up",
    "down": "domain.mouse_scroll.direction.down",
    "left": "domain.mouse_scroll.direction.left",
    "right": "domain.mouse_scroll.direction.right",
}


@dataclass(frozen=True)
class MouseScrollSpec:
    direction: str
    unit: str
    amount: int
    position: tuple[int, int] | None


def parse_mouse_scroll(action: Mapping[str, Any]) -> MouseScrollSpec | str:
    direction_value = action.get("direction")
    if not isinstance(direction_value, str):
        return tr("domain.mouse_scroll.direction_invalid")
    direction = direction_value.strip().lower()
    if direction not in DIRECTIONS:
        return tr("domain.mouse_scroll.direction_invalid")

    unit_value = action.get("unit", UNIT_NOTCH)
    if isinstance(unit_value, str):
        unit = unit_value.strip().lower() or UNIT_NOTCH
    else:
        return tr("domain.mouse_scroll.unit_invalid")
    if unit not in (UNIT_NOTCH, UNIT_DELTA):
        return tr("domain.mouse_scroll.unit_invalid")

    amount_value = action.get("amount")
    if isinstance(amount_value, bool):
        return tr("domain.mouse_scroll.amount_integer")
    if isinstance(amount_value, int):
        amount = amount_value
    elif isinstance(amount_value, float):
        if not amount_value.is_integer():
            return tr("domain.mouse_scroll.amount_integer")
        amount = int(amount_value)
    elif isinstance(amount_value, str):
        try:
            amount = int(amount_value.strip())
        except (ValueError, OverflowError):
            return tr("domain.mouse_scroll.amount_convertible")
    else:
        return tr("domain.mouse_scroll.amount_integer")

    maximum = MAX_NOTCHES if unit == UNIT_NOTCH else MAX_DELTA
    if not 1 <= amount <= maximum:
        return tr("domain.mouse_scroll.amount_range", maximum=maximum)

    has_x = "x" in action
    has_y = "y" in action
    if has_x != has_y:
        return tr("domain.mouse_scroll.coordinates_both")
    position = None
    if has_x:
        try:
            position = (int(action["x"]), int(action["y"]))
        except (TypeError, ValueError, OverflowError):
            return tr("domain.mouse_scroll.coordinates_convertible")
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
    direction = tr(_DIRECTION_KEYS[parsed.direction])
    display_key = (
        "domain.mouse_scroll.display_value_raw"
        if parsed.unit == UNIT_DELTA
        else "domain.mouse_scroll.display_value"
    )
    display = tr(display_key, direction=direction, amount=parsed.amount)
    if parsed.position is not None:
        display += f" ({parsed.position[0]}, {parsed.position[1]})"
    return display


def describe_mouse_scroll(action: Mapping[str, Any]) -> str:
    parts = []
    for key in ("direction", "unit", "amount"):
        parts.append(f"{key}={str(action[key]) if key in action else tr('domain.mouse_scroll.value_none')}")
    if "x" in action or "y" in action:
        parts.extend(
            f"{key}={str(action[key]) if key in action else tr('domain.mouse_scroll.value_none')}"
            for key in ("x", "y")
        )
    return " ".join(parts)
