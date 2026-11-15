from __future__ import annotations

import re

from keyseq.infrastructure.os_backend import get_backend
from keyseq.presentation import tk_platform
from keyseq.domain.config import normalize_key_name
from keyseq.domain.numpad_keys import is_numpad_key_name
from keyseq.domain.key_symbols import KEY_SYMBOLS
from keyseq.presentation.keyboard_layouts import resolve_layout_key_id_from_scan_code


UNRESOLVED_KEY_NAME = "??"
# Tk の Unicode の keysym（例 U2264）。Mac の Option で変わった文字に出る。
_UNICODE_KEYSYM = re.compile(r"U[0-9a-fA-F]{4,}")


def is_unresolved_capture_key(name: str) -> bool:
    return name == UNRESOLVED_KEY_NAME


def numpad_name_from_tk_event(keycode: object, state: object) -> str:
    """OS backend に Tk イベントのテンキー判定を委譲する。"""
    return get_backend().tk_keys.numpad_name(keycode, state)


def resolve_tk_event_key_name(event: object, layout: object) -> str:
    """Resolve an event's physical key through its keycode and keyboard layout."""
    numpad_name = numpad_name_from_tk_event(
        getattr(event, "keycode", None), getattr(event, "state", 0)
    )
    if numpad_name:
        return numpad_name
    keysym = str(getattr(event, "keysym", "") or "").lower()
    if keysym in TK_KEYSYM_TO_KEYBOARD_NAME:
        return ""
    try:
        vk = int(getattr(event, "keycode", None))
    except (TypeError, ValueError, OverflowError):
        return ""
    scan_code = get_backend().tk_keys.vk_to_scan_code(vk)
    if scan_code is None:
        return ""
    resolved = normalize_key_name(resolve_layout_key_id_from_scan_code(layout, scan_code))
    return resolved if resolved and not is_numpad_key_name(resolved) else ""


def resolve_modified_char_key_name(event: object, resolve_name) -> str:
    """Resolve only keys whose produced character may differ from the physical key."""
    raw = str(getattr(event, "keysym", "") or "")
    normalized = normalize_tk_keysym(raw)
    is_unicode_keysym = bool(_UNICODE_KEYSYM.fullmatch(raw))
    is_non_ascii_char = len(normalized) == 1 and not normalized.isascii()
    char = str(getattr(event, "char", "") or "")
    if not (is_unicode_keysym or is_non_ascii_char or (len(char) == 1 and not char.isascii())):
        return ""
    if numpad_name_from_tk_event(getattr(event, "keycode", None), getattr(event, "state", 0)):
        return ""
    try:
        vk = int(getattr(event, "keycode", None))
    except (TypeError, ValueError, OverflowError):
        return ""
    # キーマップ編集のグリッドと同じ順: レイアウトの走査コード → 修飾なしの文字（backend）。
    tk_keys = get_backend().tk_keys
    scan_code = tk_keys.vk_to_scan_code(vk)
    physical = ""
    if resolve_name is not None and scan_code is not None:
        physical = normalize_key_name(resolve_name(scan_code))
    if not physical:
        physical = normalize_key_name(tk_keys.vk_to_char(vk))
    if not physical:
        return ""
    if len(physical) == 1 and not physical.isalnum():
        physical = next((name for name, symbol in KEY_SYMBOLS.items() if symbol == physical), physical)
    return TK_KEYSYM_TO_KEYBOARD_NAME.get(physical.lower(), physical.lower())

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
