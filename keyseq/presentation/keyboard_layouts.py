from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class KeySpec:
    id: str
    label: str
    x: float
    y: float
    w: float = 1.0
    h: float = 1.0


@dataclass(frozen=True)
class KeyboardLayout:
    layout_id: str
    display_name: str
    keys: tuple[KeySpec, ...]


DEFAULT_LAYOUT_ID = "us_tkl"

_DEFAULT_US_TKL_KEYS: tuple[KeySpec, ...] = (
    KeySpec("esc", "Esc", 0.0, 0.0),
    KeySpec("f1", "F1", 2.0, 0.0),
    KeySpec("f2", "F2", 3.0, 0.0),
    KeySpec("f3", "F3", 4.0, 0.0),
    KeySpec("f4", "F4", 5.0, 0.0),
    KeySpec("f5", "F5", 6.5, 0.0),
    KeySpec("f6", "F6", 7.5, 0.0),
    KeySpec("f7", "F7", 8.5, 0.0),
    KeySpec("f8", "F8", 9.5, 0.0),
    KeySpec("f9", "F9", 11.0, 0.0),
    KeySpec("f10", "F10", 12.0, 0.0),
    KeySpec("f11", "F11", 13.0, 0.0),
    KeySpec("f12", "F12", 14.0, 0.0),
    KeySpec("print screen", "PrtSc", 15.25, 0.0),
    KeySpec("scroll lock", "Scroll", 16.25, 0.0),
    KeySpec("pause", "Pause", 17.25, 0.0),
    KeySpec("`", "`", 0.0, 1.2),
    KeySpec("1", "1", 1.0, 1.2),
    KeySpec("2", "2", 2.0, 1.2),
    KeySpec("3", "3", 3.0, 1.2),
    KeySpec("4", "4", 4.0, 1.2),
    KeySpec("5", "5", 5.0, 1.2),
    KeySpec("6", "6", 6.0, 1.2),
    KeySpec("7", "7", 7.0, 1.2),
    KeySpec("8", "8", 8.0, 1.2),
    KeySpec("9", "9", 9.0, 1.2),
    KeySpec("0", "0", 10.0, 1.2),
    KeySpec("-", "-", 11.0, 1.2),
    KeySpec("=", "=", 12.0, 1.2),
    KeySpec("backspace", "Backspace", 13.0, 1.2, 2.0),
    KeySpec("insert", "Ins", 15.25, 1.2),
    KeySpec("home", "Home", 16.25, 1.2),
    KeySpec("page up", "PgUp", 17.25, 1.2),
    KeySpec("tab", "Tab", 0.0, 2.2, 1.5),
    KeySpec("q", "Q", 1.5, 2.2),
    KeySpec("w", "W", 2.5, 2.2),
    KeySpec("e", "E", 3.5, 2.2),
    KeySpec("r", "R", 4.5, 2.2),
    KeySpec("t", "T", 5.5, 2.2),
    KeySpec("y", "Y", 6.5, 2.2),
    KeySpec("u", "U", 7.5, 2.2),
    KeySpec("i", "I", 8.5, 2.2),
    KeySpec("o", "O", 9.5, 2.2),
    KeySpec("p", "P", 10.5, 2.2),
    KeySpec("[", "[", 11.5, 2.2),
    KeySpec("]", "]", 12.5, 2.2),
    KeySpec("\\", "\\", 13.5, 2.2, 1.5),
    KeySpec("delete", "Del", 15.25, 2.2),
    KeySpec("end", "End", 16.25, 2.2),
    KeySpec("page down", "PgDn", 17.25, 2.2),
    KeySpec("caps lock", "Caps", 0.0, 3.2, 1.75),
    KeySpec("a", "A", 1.75, 3.2),
    KeySpec("s", "S", 2.75, 3.2),
    KeySpec("d", "D", 3.75, 3.2),
    KeySpec("f", "F", 4.75, 3.2),
    KeySpec("g", "G", 5.75, 3.2),
    KeySpec("h", "H", 6.75, 3.2),
    KeySpec("j", "J", 7.75, 3.2),
    KeySpec("k", "K", 8.75, 3.2),
    KeySpec("l", "L", 9.75, 3.2),
    KeySpec(";", ";", 10.75, 3.2),
    KeySpec("'", "'", 11.75, 3.2),
    KeySpec("enter", "Enter", 12.75, 3.2, 2.25),
    KeySpec("shift_l", "Shift", 0.0, 4.2, 2.25),
    KeySpec("z", "Z", 2.25, 4.2),
    KeySpec("x", "X", 3.25, 4.2),
    KeySpec("c", "C", 4.25, 4.2),
    KeySpec("v", "V", 5.25, 4.2),
    KeySpec("b", "B", 6.25, 4.2),
    KeySpec("n", "N", 7.25, 4.2),
    KeySpec("m", "M", 8.25, 4.2),
    KeySpec(",", ",", 9.25, 4.2),
    KeySpec(".", ".", 10.25, 4.2),
    KeySpec("/", "/", 11.25, 4.2),
    KeySpec("shift_r", "Shift", 12.25, 4.2, 2.75),
    KeySpec("up", "Up", 16.25, 4.2),
    KeySpec("ctrl_l", "Ctrl", 0.0, 5.2, 1.5),
    KeySpec("windows_l", "Win", 1.5, 5.2, 1.5),
    KeySpec("alt_l", "Alt", 3.0, 5.2, 1.5),
    KeySpec("space", "Space", 4.5, 5.2, 4.5),
    KeySpec("alt_r", "Alt", 9.0, 5.2, 1.5),
    KeySpec("windows_r", "Win", 10.5, 5.2, 1.5),
    KeySpec("menu", "Menu", 12.0, 5.2, 1.5),
    KeySpec("ctrl_r", "Ctrl", 13.5, 5.2, 1.5),
    KeySpec("left", "Left", 15.25, 5.2),
    KeySpec("down", "Down", 16.25, 5.2),
    KeySpec("right", "Right", 17.25, 5.2),
)

BUILTIN_LAYOUTS: dict[str, KeyboardLayout] = {
    DEFAULT_LAYOUT_ID: KeyboardLayout(
        layout_id=DEFAULT_LAYOUT_ID,
        display_name="US TKL",
        keys=_DEFAULT_US_TKL_KEYS,
    )
}


def keyboard_layout_from_dict(data: dict) -> KeyboardLayout:
    if not isinstance(data, dict):
        raise ValueError("Keyboard layout data must be a dict.")

    layout_id = str(data.get("layout_id") or "").strip()
    if not layout_id:
        raise ValueError("layout_id is required.")

    display_name = str(data.get("display_name") or layout_id).strip() or layout_id
    raw_keys = data.get("keys")
    if not isinstance(raw_keys, list) or not raw_keys:
        raise ValueError("keys must be a non-empty list.")

    keys: list[KeySpec] = []
    for raw_key in raw_keys:
        keys.append(_keyspec_from_dict(raw_key))

    return KeyboardLayout(layout_id=layout_id, display_name=display_name, keys=tuple(keys))


def load_layout_from_json(path: str) -> KeyboardLayout:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return keyboard_layout_from_dict(data)


def resolve_keyboard_layout(*, json_path: str | None = None, layout_id: str | None = None) -> KeyboardLayout:
    if json_path:
        try:
            return load_layout_from_json(json_path)
        except Exception:
            pass

    if layout_id:
        builtin = BUILTIN_LAYOUTS.get(str(layout_id).strip())
        if builtin is not None:
            return builtin

    return BUILTIN_LAYOUTS[DEFAULT_LAYOUT_ID]


def _keyspec_from_dict(data: dict) -> KeySpec:
    if not isinstance(data, dict):
        raise ValueError("Each key definition must be a dict.")

    key_id = str(data.get("id") or "").strip()
    if not key_id:
        raise ValueError("Key id is required.")

    label = str(data.get("label") or key_id)
    x = _coerce_float(data.get("x"), "x")
    y = _coerce_float(data.get("y"), "y")
    w = _coerce_float(data.get("w", 1.0), "w")
    h = _coerce_float(data.get("h", 1.0), "h")
    if w <= 0 or h <= 0:
        raise ValueError("Key width/height must be positive.")

    return KeySpec(id=key_id, label=label, x=x, y=y, w=w, h=h)


def _coerce_float(value, field_name: str) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc
