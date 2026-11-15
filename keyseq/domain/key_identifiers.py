from __future__ import annotations

from keyseq.domain.config import normalize_key_name


PROHIBITED_ASSIGN_KEY_NAMES = frozenset(
    {
        "left windows",
        "right windows",
        "windows",
        "command",
        "left command",
        "right command",
        "caps lock",
        "fn",
        "caps_lock",
        "capslock",
        "alt gr",
        "altgr",
    }
)


def is_prohibited_assign_key(name: str) -> bool:
    return normalize_key_name(name) in PROHIBITED_ASSIGN_KEY_NAMES
