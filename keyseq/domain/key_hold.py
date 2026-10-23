from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


ACTION_TYPE_KEY_HOLD = "key_hold"
EDGE_DOWN = "down"
EDGE_UP = "up"
MOUSE_BUTTONS = ("left", "right", "middle")
MODIFIER_KEY_NAMES = frozenset(
    {
        "alt",
        "alt gr",
        "ctrl",
        "shift",
        "windows",
        "left alt",
        "right alt",
        "left ctrl",
        "right ctrl",
        "left shift",
        "right shift",
        "left windows",
        "right windows",
        "altgr",
        "cmd",
        "command",
        "control",
        "left control",
        "right control",
        "left menu",
        "left win",
        "right win",
        "win",
        "option",
    }
)


@dataclass(frozen=True)
class KeyHoldSpec:
    edge: str
    button: str | None
    key: str | None
    position: tuple[int, int] | None


def parse_key_hold(action: Mapping[str, Any]) -> KeyHoldSpec | str:
    edge_value = action.get("edge")
    if not isinstance(edge_value, str):
        return "押下方向はdownまたはupを指定してください。"
    edge = edge_value.strip().lower()
    if edge not in (EDGE_DOWN, EDGE_UP):
        return "押下方向はdownまたはupを指定してください。"

    button_value = action.get("button")
    if isinstance(button_value, str) and button_value.strip():
        button = button_value.strip().lower()
        if button not in MOUSE_BUTTONS:
            return "マウスボタンはleft / right / middleのいずれかを指定してください。"
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
        return KeyHoldSpec(edge=edge, button=button, key=None, position=position)

    value = action.get("value")
    if not isinstance(value, str) or not value.strip():
        return "キー名は空でない文字列で指定してください。"
    key = value.strip().lower()
    if "+" in key or "," in key:
        return "キー名に + または , は使用できません。"
    return KeyHoldSpec(edge=edge, button=None, key=key, position=None)


def is_modifier_key(name: str) -> bool:
    """キー名を正規化して修飾キーか判定する。"""
    return name.strip().lower().replace("_", " ") in MODIFIER_KEY_NAMES


def wants_repeat(action: Mapping[str, Any]) -> bool:
    """repeat が bool の True ならリピートを求める。"""
    return action.get("repeat") is True


def is_repeat_enabled(action: Mapping[str, Any]) -> bool:
    """正しいキーボードの押す行でリピートが有効か判定する。"""
    parsed = parse_key_hold(action)
    return (
        not isinstance(parsed, str)
        and parsed.edge == EDGE_DOWN
        and parsed.button is None
        and wants_repeat(action)
        and not is_modifier_key(parsed.key or "")
    )


def held_display_name(kind: str, name: str) -> str:
    if kind == "key":
        return name
    button_names = {"left": "左", "right": "右", "middle": "中"}
    return f"マウス{button_names[name]}"


def format_key_hold_value(action: Mapping[str, Any]) -> str:
    parsed = parse_key_hold(action)
    if isinstance(parsed, str):
        button = action.get("button")
        raw_value = button if isinstance(button, str) and button.strip() else (action.get("value") or "")
        return f"[{ACTION_TYPE_KEY_HOLD}] {raw_value}"

    direction = "押す" if parsed.edge == EDGE_DOWN else "離す"
    if parsed.button is None:
        display = f"[{direction}] {parsed.key}"
        if is_repeat_enabled(action):
            display += "（リピート）"
        return display
    display = f"[{direction}] {held_display_name('mouse', parsed.button)}"
    if parsed.position is not None:
        display += f" ({parsed.position[0]}, {parsed.position[1]})"
    return display
