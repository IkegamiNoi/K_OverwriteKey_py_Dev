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
