from __future__ import annotations

# Tk keysym -> keyboard ライブラリの単キー表記
TK_KEYSYM_TO_KEYBOARD_NAME = {
    "control_l": "ctrl",
    "control_r": "ctrl",
    "shift_l": "shift",
    "shift_r": "shift",
    "alt_l": "alt",
    "alt_r": "alt",
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
}


def normalize_tk_keysym(keysym: str) -> str:
    """Tk の keysym を keyboard ライブラリの単キー表記に寄せる。"""
    k = (keysym or "").lower()
    return TK_KEYSYM_TO_KEYBOARD_NAME.get(k, k)


_KEY_HOLD_MODIFIER_KEYSYMS = {
    "control_l": "left ctrl",
    "control_r": "right ctrl",
    "shift_l": "left shift",
    "shift_r": "right shift",
    "alt_l": "left alt",
    "alt_r": "right alt",
    "super_l": "left windows",
    "win_l": "left windows",
    "super_r": "right windows",
    "win_r": "right windows",
}


def normalize_key_hold_tk_keysym(keysym: str) -> str:
    """key_hold の記録用。修飾キーは左右を区別した名前にする（暫定 35 §2-20）。"""
    k = (keysym or "").lower()
    return _KEY_HOLD_MODIFIER_KEYSYMS.get(k, normalize_tk_keysym(keysym))
