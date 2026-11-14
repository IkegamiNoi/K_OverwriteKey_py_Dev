from __future__ import annotations

from keyseq.infrastructure.os_backend import get_backend
from keyseq.presentation import tk_platform


UNRESOLVED_KEY_NAME = "??"


def is_unresolved_capture_key(name: str) -> bool:
    return name == UNRESOLVED_KEY_NAME


def numpad_name_from_tk_event(keycode: object, state: object) -> str:
    """OS backend に Tk イベントのテンキー判定を委譲する。"""
    return get_backend().tk_keys.numpad_name(keycode, state)

# Tk keysym -> keyboard ライブラリの単キー表記
TK_KEYSYM_TO_KEYBOARD_NAME = {
    "control_l": "ctrl",
    "control_r": "ctrl",
    "shift_l": "shift",
    "shift_r": "shift",
    "alt_l": "alt",
    "alt_r": "alt",
    "meta_l": "windows",
    "meta_r": "windows",
    "super_l": "windows",
    "super_r": "windows",
    "win_l": "windows",
    "win_r": "windows",
    "return": "enter",
    "escape": "esc",
    "space": "space",
    "tab": "tab",
    "backspace": "backspace",
    "prior": "page up",
    "next": "page down",
    "minus": "-",
}


def normalize_tk_keysym(keysym: str, *, widget=None) -> str:
    """Tk の keysym を keyboard ライブラリの単キー表記に寄せる。"""
    k = (keysym or "").lower()
    if k in {"super_l", "super_r"} and widget is not None and tk_platform.is_aqua(widget):
        return UNRESOLVED_KEY_NAME
    return TK_KEYSYM_TO_KEYBOARD_NAME.get(k, k)


def normalize_tk_key_event(event: object) -> str:
    """テンキーを判別してから、通常の Tk keysym を正規化する。"""
    numpad_name = numpad_name_from_tk_event(
        getattr(event, "keycode", None), getattr(event, "state", 0)
    )
    if numpad_name:
        return numpad_name
    widget = getattr(event, "widget", None)
    if not hasattr(widget, "tk"):
        widget = None
    return normalize_tk_keysym(getattr(event, "keysym", ""), widget=widget)


_KEY_HOLD_MODIFIER_KEYSYMS = {
    "control_l": "left ctrl",
    "control_r": "right ctrl",
    "shift_l": "left shift",
    "shift_r": "right shift",
    "alt_l": "left alt",
    "alt_r": "right alt",
    "meta_l": "left windows",
    "meta_r": "right windows",
    "super_l": "left windows",
    "win_l": "left windows",
    "super_r": "right windows",
    "win_r": "right windows",
}


def normalize_key_hold_tk_keysym(keysym: str, *, widget=None) -> str:
    """key_hold の記録用。修飾キーは左右を区別した名前にする（暫定 35 §2-20）。"""
    k = (keysym or "").lower()
    normalized = normalize_tk_keysym(keysym, widget=widget)
    if normalized == UNRESOLVED_KEY_NAME:
        return normalized
    return _KEY_HOLD_MODIFIER_KEYSYMS.get(k, normalized)


def normalize_key_hold_tk_key_event(event: object) -> str:
    """key_hold 記録向けにテンキーと左右修飾キーを正規化する。"""
    numpad_name = numpad_name_from_tk_event(
        getattr(event, "keycode", None), getattr(event, "state", 0)
    )
    if numpad_name:
        return numpad_name
    widget = getattr(event, "widget", None)
    if not hasattr(widget, "tk"):
        widget = None
    return normalize_key_hold_tk_keysym(getattr(event, "keysym", ""), widget=widget)
