from __future__ import annotations

import json
import os
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


@dataclass(frozen=True)
class KeyboardLayoutEntry:
    layout: KeyboardLayout
    source: str
    path: str | None = None


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


def validate_layout_json(data, *, existing_layout_ids: set[str] | None = None) -> dict:
    if not isinstance(data, dict):
        raise ValueError("JSONルートは object である必要があります。")

    for required_key in ("layout_id", "display_name", "keys"):
        if required_key not in data:
            raise ValueError(f"{required_key} がありません。")

    layout_id_value = data.get("layout_id")
    if not isinstance(layout_id_value, str):
        raise ValueError("layout_id は文字列である必要があります。")
    layout_id = layout_id_value.strip()
    if not layout_id:
        raise ValueError("layout_id が空です。")

    if existing_layout_ids and layout_id in {str(v).strip() for v in existing_layout_ids if str(v).strip()}:
        raise ValueError(f"layout_id '{layout_id}' は既に存在します。")

    display_name_value = data.get("display_name")
    if not isinstance(display_name_value, str):
        raise ValueError("display_name は文字列である必要があります。")
    display_name = display_name_value.strip()
    if not display_name:
        raise ValueError("display_name が空です。")

    raw_keys = data.get("keys")
    if not isinstance(raw_keys, list):
        raise ValueError("keys が配列ではありません。")
    if not raw_keys:
        raise ValueError("keys が空です。")

    normalized_keys: list[dict] = []
    seen_key_ids: set[str] = set()
    for index, raw_key in enumerate(raw_keys):
        key_prefix = f"keys[{index}]"
        if not isinstance(raw_key, dict):
            raise ValueError(f"{key_prefix} は object である必要があります。")

        for required_key in ("id", "label", "x", "y", "w", "h"):
            if required_key not in raw_key:
                raise ValueError(f"{key_prefix}.{required_key} がありません。")

        key_id_value = raw_key.get("id")
        if not isinstance(key_id_value, str):
            raise ValueError(f"{key_prefix}.id は文字列である必要があります。")
        key_id = key_id_value.strip()
        if not key_id:
            raise ValueError(f"{key_prefix}.id が空です。")
        if key_id in seen_key_ids:
            raise ValueError(f"{key_prefix}.id が重複しています: {key_id}")
        seen_key_ids.add(key_id)

        label_value = raw_key.get("label")
        if not isinstance(label_value, str):
            raise ValueError(f"{key_prefix}.label は文字列である必要があります。")

        x = _coerce_float(raw_key.get("x"), f"{key_prefix}.x")
        y = _coerce_float(raw_key.get("y"), f"{key_prefix}.y")
        w = _coerce_float(raw_key.get("w"), f"{key_prefix}.w")
        h = _coerce_float(raw_key.get("h"), f"{key_prefix}.h")

        if x < 0:
            raise ValueError(f"{key_prefix}.x は 0 以上である必要があります。")
        if y < 0:
            raise ValueError(f"{key_prefix}.y は 0 以上である必要があります。")
        if w <= 0:
            raise ValueError(f"{key_prefix}.w は 0 より大きい必要があります。")
        if h <= 0:
            raise ValueError(f"{key_prefix}.h は 0 より大きい必要があります。")

        normalized_keys.append(
            {
                "id": key_id,
                "label": label_value,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            }
        )

    return {
        "layout_id": layout_id,
        "display_name": display_name,
        "keys": normalized_keys,
    }


def keyboard_layout_from_dict(data: dict, *, existing_layout_ids: set[str] | None = None) -> KeyboardLayout:
    normalized = validate_layout_json(data, existing_layout_ids=existing_layout_ids)
    keys = [
        KeySpec(
            id=key_data["id"],
            label=key_data["label"],
            x=key_data["x"],
            y=key_data["y"],
            w=key_data["w"],
            h=key_data["h"],
        )
        for key_data in normalized["keys"]
    ]
    return KeyboardLayout(
        layout_id=normalized["layout_id"],
        display_name=normalized["display_name"],
        keys=tuple(keys),
    )


def load_layout_from_json(path: str, *, existing_layout_ids: set[str] | None = None) -> KeyboardLayout:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return keyboard_layout_from_dict(data, existing_layout_ids=existing_layout_ids)


def save_layout_to_json(path: str, layout: KeyboardLayout) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(layout_to_dict(layout), f, ensure_ascii=False, indent=2)


def layout_to_dict(layout: KeyboardLayout) -> dict:
    return {
        "layout_id": layout.layout_id,
        "display_name": layout.display_name,
        "keys": [
            {
                "id": key.id,
                "label": key.label,
                "x": key.x,
                "y": key.y,
                "w": key.w,
                "h": key.h,
            }
            for key in layout.keys
        ],
    }


def collect_keyboard_layouts(registrations=None, *, base_dir: str | None = None) -> dict[str, KeyboardLayoutEntry]:
    layouts: dict[str, KeyboardLayoutEntry] = {
        layout_id: KeyboardLayoutEntry(layout=layout, source="builtin", path=None)
        for layout_id, layout in BUILTIN_LAYOUTS.items()
    }

    if not isinstance(registrations, list):
        return layouts

    for registration in registrations:
        stored_path = _get_registration_path(registration)
        if not stored_path:
            continue
        resolved_path = _resolve_layout_path(stored_path, base_dir)
        try:
            layout = load_layout_from_json(resolved_path, existing_layout_ids=set(layouts.keys()))
        except Exception:
            continue
        layouts[layout.layout_id] = KeyboardLayoutEntry(layout=layout, source="external", path=stored_path)
    return layouts


def resolve_registered_layout_path(path: str, *, base_dir: str | None = None) -> str:
    return _resolve_layout_path(path, base_dir)


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


def _coerce_float(value, field_name: str) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"{field_name} は数値である必要があります。") from exc


def _get_registration_path(registration) -> str:
    if isinstance(registration, str):
        return registration.strip()
    if isinstance(registration, dict):
        return str(registration.get("path") or "").strip()
    return ""


def _resolve_layout_path(path: str, base_dir: str | None) -> str:
    if os.path.isabs(path) or not base_dir:
        return path
    return os.path.join(base_dir, path)
