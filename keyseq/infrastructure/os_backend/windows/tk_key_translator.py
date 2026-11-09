from __future__ import annotations


_NUMPAD_NAMES_BY_KEYCODE = {
    **{keycode: f"num {digit}" for digit, keycode in enumerate(range(96, 106))},
    110: "num decimal",
    106: "num multiply",
    109: "num subtract",
    107: "num add",
    111: "num divide",
}
_NUMPAD_NAMES_BY_NON_EXTENDED_KEYCODE = {
    45: "num 0",
    35: "num 1",
    40: "num 2",
    34: "num 3",
    37: "num 4",
    12: "num 5",
    39: "num 6",
    36: "num 7",
    38: "num 8",
    33: "num 9",
    46: "num decimal",
}


def numpad_name_from_tk_event(keycode: object, state: object) -> str:
    """Windows Tk keycode / extended bit からテンキー名を決める。"""
    try:
        normalized_keycode = int(keycode)
        extended = bool(int(state) & 0x40000)
    except Exception:
        return ""

    if normalized_keycode == 13:
        return "num enter" if extended else ""
    if normalized_keycode in _NUMPAD_NAMES_BY_KEYCODE:
        return _NUMPAD_NAMES_BY_KEYCODE[normalized_keycode]
    if not extended:
        return _NUMPAD_NAMES_BY_NON_EXTENDED_KEYCODE.get(normalized_keycode, "")
    return ""
