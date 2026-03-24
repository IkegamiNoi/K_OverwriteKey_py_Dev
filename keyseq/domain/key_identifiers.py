from __future__ import annotations

from keyseq.domain.config import normalize_key_name


_SPECIAL_KEY_NAME_TO_SCAN_CODE = {
    "muhenkan": 123,
    "henkan": 121,
    "kana": 112,
    "zenkaku_hankaku": 41,
}

_SPECIAL_SCAN_CODE_TO_KEY_NAME = {
    scan_code: key_name for key_name, scan_code in _SPECIAL_KEY_NAME_TO_SCAN_CODE.items()
}
SPECIAL_KEY_NAMES = frozenset(_SPECIAL_KEY_NAME_TO_SCAN_CODE)


def resolve_known_scan_code_from_key_name(key_name: str) -> int | None:
    normalized = normalize_key_name(key_name)
    if not normalized:
        return None
    return _SPECIAL_KEY_NAME_TO_SCAN_CODE.get(normalized)


def resolve_known_key_name_from_scan_code(scan_code: object) -> str:
    try:
        normalized_scan_code = int(scan_code)
    except Exception:
        return ""
    return _SPECIAL_SCAN_CODE_TO_KEY_NAME.get(normalized_scan_code, "")


def is_special_key_name(key_name: str) -> bool:
    return normalize_key_name(key_name) in SPECIAL_KEY_NAMES
