"""Physical Mac virtual keys mapped to Windows keyboard receive identities."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MacKey:
    scan_code: int
    is_keypad: bool
    name: str


# Base US identities; JIS overrides are applied below, independent of IME.
_KEY_ROWS = (
    (0, 30, "a"), (1, 31, "s"), (2, 32, "d"), (3, 33, "f"),
    (4, 35, "h"), (5, 34, "g"), (6, 44, "z"), (7, 45, "x"),
    (8, 46, "c"), (9, 47, "v"), (11, 48, "b"), (12, 16, "q"),
    (13, 17, "w"), (14, 18, "e"), (15, 19, "r"), (16, 21, "y"),
    (17, 20, "t"), (18, 2, "1"), (19, 3, "2"), (20, 4, "3"),
    (21, 5, "4"), (22, 7, "6"), (23, 6, "5"), (24, 13, "="),
    (25, 10, "9"), (26, 8, "7"), (27, 12, "-"), (28, 9, "8"),
    (29, 11, "0"), (30, 27, "]"), (31, 24, "o"), (32, 22, "u"),
    (33, 26, "["), (34, 23, "i"), (35, 25, "p"), (36, 28, "enter"),
    (37, 38, "l"), (38, 36, "j"), (39, 40, "'"), (40, 37, "k"),
    (41, 39, ";"), (42, 43, "\\"), (43, 51, ","), (44, 53, "/"),
    (45, 49, "n"), (46, 50, "m"), (47, 52, "."), (48, 15, "tab"),
    (49, 57, "space"), (50, 41, "`"), (51, 14, "backspace"),
    (53, 1, "esc"), (54, 92, "right command"), (55, 91, "left command"),
    (56, 42, "shift"), (58, 56, "option"), (59, 29, "ctrl"),
    (60, 54, "right shift"), (61, 56, "right option"), (62, 29, "right ctrl"),
    (93, 125, "yen"), (94, 115, "ro"), (96, 63, "f5"),
    (97, 64, "f6"), (98, 65, "f7"), (99, 61, "f3"), (100, 66, "f8"),
    (101, 67, "f9"), (102, 123, "muhenkan"), (103, 87, "f11"),
    (104, 121, "henkan"), (109, 68, "f10"), (111, 88, "f12"),
    (114, 82, "insert"), (115, 71, "home"), (116, 73, "page up"),
    (117, 83, "delete"), (118, 62, "f4"), (119, 79, "end"),
    (120, 60, "f2"), (121, 81, "page down"), (122, 59, "f1"),
    (123, 75, "left"), (124, 77, "right"), (125, 80, "down"),
    (126, 72, "up"),
)
KEY_TABLE: dict[int, MacKey] = {
    vk: MacKey(scan, False, name) for vk, scan, name in _KEY_ROWS
}

# Apple Events.h kVK_ANSI_Keypad* values, paired with the compatibility
# scan codes used by the application's numpad layouts.
_KEYPAD_ROWS = (
    (82, 82, "num 0"), (83, 79, "num 1"), (84, 80, "num 2"),
    (85, 81, "num 3"), (86, 75, "num 4"), (87, 76, "num 5"),
    (88, 77, "num 6"), (89, 71, "num 7"), (91, 72, "num 8"),
    (92, 73, "num 9"), (65, 83, "num decimal"),
    (67, 55, "num multiply"), (78, 74, "num subtract"),
    (69, 78, "num add"), (75, 53, "num divide"),
    (76, 28, "num enter"),
)
KEY_TABLE.update({
    vk: MacKey(scan, True, name) for vk, scan, name in _KEYPAD_ROWS
})

_JIS_ROWS = (
    (50, 41, "zenkaku_hankaku"), (24, 13, "^"), (33, 26, "@"),
    (30, 27, "["), (42, 43, "]"), (39, 40, ":"),
)
JIS_KEY_TABLE: dict[int, MacKey] = {
    vk: MacKey(scan, False, name) for vk, scan, name in _JIS_ROWS
}

_SHIFTED_ROWS_US = (
    ("!", "1"), ("@", "2"), ("#", "3"), ("$", "4"),
    ("%", "5"), ("^", "6"), ("&", "7"), ("*", "8"),
    ("(", "9"), (")", "0"), ("_", "-"), ("+", "="),
    ("{", "["), ("}", "]"), ("|", "\\"), (":", ";"),
    ('"', "'"), ("<", ","), (">", "."), ("?", "/"), ("~", "`"),
)
SHIFTED_US: dict[str, str] = dict(_SHIFTED_ROWS_US)

_SHIFTED_ROWS_JIS = (
    ("!", "1"), ('"', "2"), ("#", "3"), ("$", "4"),
    ("%", "5"), ("&", "6"), ("'", "7"), ("(", "8"),
    (")", "9"), ("=", "-"), ("~", "^"), ("`", "@"),
    ("{", "["), ("+", ";"), ("*", ":"), ("}", "]"),
    ("_", "ro"), ("|", "yen"), ("<", ","), (">", "."),
    ("?", "/"),
)
SHIFTED_JIS: dict[str, str] = dict(_SHIFTED_ROWS_JIS)

_SEND_ALIASES = {
    "command": 55,
    "left shift": 56,
    "left ctrl": 59,
    "left option": 58,
}
_JIS_OVERRIDDEN_VKS = frozenset(JIS_KEY_TABLE)

MODIFIER_NAMES = {
    "shift_l": "shift", "shift_r": "right shift",
    "ctrl_l": "ctrl", "ctrl_r": "right ctrl",
    "alt_l": "alt", "alt_r": "right alt",
    "windows_l": "left windows", "windows_r": "right windows",
    "command_l": "left command", "command_r": "right command",
    "option_l": "option", "option_r": "right option",
}

# NX_DEVICE*KEYMASK: right Option/Control still require physical confirmation.
MODIFIERS: dict[int, tuple[str, str, int]] = {
    55: ("command", "left", 0x08), 54: ("command", "right", 0x10),
    56: ("shift", "left", 0x02), 60: ("shift", "right", 0x04),
    58: ("option", "left", 0x20), 61: ("option", "right", 0x40),
    59: ("control", "left", 0x01), 62: ("control", "right", 0x2000),
}
COMMON_FLAGS = {
    "shift": 0x20000, "control": 0x40000,
    "option": 0x80000, "command": 0x100000,
}


def is_jis_layout(key_ids: frozenset[str]) -> bool:
    """Return whether layout IDs identify the Japanese JIS physical layout."""
    return "yen" in key_ids or "ro" in key_ids


def key_for_vk(vk: int, *, jis: bool) -> MacKey | None:
    """Resolve a physical virtual key to its name for the active layout."""
    if jis:
        override = JIS_KEY_TABLE.get(vk)
        if override is not None:
            return override
    return KEY_TABLE.get(vk)


def vk_for_name(name: str, *, jis: bool = False) -> int | None:
    if name in _SEND_ALIASES:
        return _SEND_ALIASES[name]
    keys = KEY_TABLE.items()
    if jis:
        keys = (
            (vk, key) for vk, key in KEY_TABLE.items()
            if vk not in _JIS_OVERRIDDEN_VKS
        )
        keys = (*keys, *JIS_KEY_TABLE.items())
    matches = [vk for vk, key in keys if key.name == name]
    return matches[0] if len(matches) == 1 else None
