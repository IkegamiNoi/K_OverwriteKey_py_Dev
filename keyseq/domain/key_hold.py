from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


ACTION_TYPE_KEY_HOLD = "key_hold"
EDGE_DOWN = "down"
EDGE_UP = "up"
MOUSE_BUTTONS = ("left", "right", "middle")


@dataclass(frozen=True)
class KeyHoldSpec:
    edge: str
    button: str | None
    key: str | None
    position: tuple[int, int] | None


def parse_key_hold(action: Mapping[str, Any]) -> KeyHoldSpec | str:
    edge_value = action.get("edge")
    if not isinstance(edge_value, str):
        return "押下方向は down または up を指定してください。"
    edge = edge_value.strip().lower()
    if edge not in (EDGE_DOWN, EDGE_UP):
        return "押下方向は down または up を指定してください。"

    button_value = action.get("button")
    if isinstance(button_value, str) and button_value.strip():
        button = button_value.strip().lower()
        if button not in MOUSE_BUTTONS:
            return "マウスボタンは left / right / middle のいずれかを指定してください。"
        has_x = "x" in action
        has_y = "y" in action
        if has_x != has_y:
            return "マウス座標は x と y の両方を指定してください。"
        position = None
        if has_x:
            try:
                position = (int(action["x"]), int(action["y"]))
            except (TypeError, ValueError, OverflowError):
                return "マウス座標 x と y は整数に変換できる値を指定してください。"
        return KeyHoldSpec(edge=edge, button=button, key=None, position=position)

    value = action.get("value")
    if not isinstance(value, str) or not value.strip():
        return "キー名は空でない文字列で指定してください。"
    key = value.strip().lower()
    if "+" in key or "," in key:
        return "キー名に + または , は使用できません。"
    return KeyHoldSpec(edge=edge, button=None, key=key, position=None)


def format_key_hold_value(action: Mapping[str, Any]) -> str:
    parsed = parse_key_hold(action)
    if isinstance(parsed, str):
        button = action.get("button")
        raw_value = button if isinstance(button, str) and button.strip() else (action.get("value") or "")
        return f"[{ACTION_TYPE_KEY_HOLD}] {raw_value}"

    direction = "押す" if parsed.edge == EDGE_DOWN else "離す"
    if parsed.button is None:
        return f"[{direction}] {parsed.key}"
    button_names = {"left": "左", "right": "右", "middle": "中"}
    display = f"[{direction}] マウス{button_names[parsed.button]}"
    if parsed.position is not None:
        display += f" ({parsed.position[0]}, {parsed.position[1]})"
    return display
