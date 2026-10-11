from __future__ import annotations

from keyseq.domain.config import normalize_key_name


_NUMPAD_KEY_SPECS: dict[str, tuple[int, bool]] = {
    "num 0": (82, False),
    "num 1": (79, False),
    "num 2": (80, False),
    "num 3": (81, False),
    "num 4": (75, False),
    "num 5": (76, False),
    "num 6": (77, False),
    "num 7": (71, False),
    "num 8": (72, False),
    "num 9": (73, False),
    "num decimal": (83, False),
    "num multiply": (55, False),
    "num subtract": (74, False),
    "num add": (78, False),
    "num divide": (53, True),
    "num enter": (28, True),
}
_NUMPAD_NAMES_BY_SCAN_CODE = {
    scan_code: name for name, (scan_code, _extended) in _NUMPAD_KEY_SPECS.items()
}


def numpad_key_spec(name: str) -> tuple[int, bool] | None:
    return _NUMPAD_KEY_SPECS.get(normalize_key_name(name))


def is_numpad_key_name(name: str) -> bool:
    return numpad_key_spec(name) is not None


def numpad_name_from_event(scan_code: object, is_keypad: bool) -> str:
    if not is_keypad:
        return ""
    try:
        normalized_scan_code = int(scan_code)
    except Exception:
        return ""
    return _NUMPAD_NAMES_BY_SCAN_CODE.get(normalized_scan_code, "")


def is_reserved_numpad_name(name: str) -> bool:
    normalized = normalize_key_name(name)
    spaced = normalized.replace("_", " ")
    return (
        spaced.startswith("num ")
        and spaced != "num lock"
        and normalized not in _NUMPAD_KEY_SPECS
    )
