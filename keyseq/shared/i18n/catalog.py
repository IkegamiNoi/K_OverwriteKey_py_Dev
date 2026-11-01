"""Lazy, thread-safe access to the bundled language catalogs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import re
import threading


_DEFAULT_LOCALES = Path(__file__).parent / "locales"
_CODE_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_lock = threading.Lock()
_locales_dir = _DEFAULT_LOCALES
_catalogs: dict[str, dict[str, object] | None] = {}
_language = "ja"
_fixed = False
_warned_keys: set[str] = set()


def _load_catalog(code: str) -> dict[str, object] | None:
    """Load once; the caller holds _lock."""
    if code in _catalogs:
        return _catalogs[code]
    catalog = None
    try:
        if not _CODE_PATTERN.fullmatch(code):
            raise ValueError("invalid language code")
        data = json.loads((_locales_dir / f"{code}.json").read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("catalog must be an object")
        meta = data.get("_meta")
        if not isinstance(meta, dict) or not isinstance(meta.get("name"), str):
            raise ValueError("_meta.name must be a string")
        catalog = data
    except (OSError, UnicodeError, ValueError) as exc:
        logging.warning("Cannot load language catalog %s: %s", code, exc)
    _catalogs[code] = catalog
    return catalog


def available_languages() -> list[tuple[str, str]]:
    with _lock:
        try:
            paths = sorted(_locales_dir.glob("*.json"))
        except OSError as exc:
            logging.warning("Cannot list language catalogs: %s", exc)
            return []
        languages = []
        for path in paths:
            catalog = _load_catalog(path.stem)
            if catalog is not None:
                languages.append((path.stem, catalog["_meta"]["name"]))
        return sorted(languages, key=lambda item: (
            {"ja": 0, "en": 1}.get(item[0], 2), item[0],
        ))


def resolve_language(value: object) -> str:
    if isinstance(value, str) and any(code == value for code, _ in available_languages()):
        return value
    return "en"


def set_language(code: str) -> None:
    global _language
    with _lock:
        if not _fixed:
            _language = code


def current_language() -> str:
    with _lock:
        return _language


def fix_language(code: str) -> None:
    global _language, _fixed
    with _lock:
        _language = code
        _fixed = True


def reset_for_tests(locales_dir: Path | None = None) -> None:
    global _locales_dir, _language, _fixed
    with _lock:
        _locales_dir = _DEFAULT_LOCALES if locales_dir is None else locales_dir
        _catalogs.clear()
        _warned_keys.clear()
        _language = "ja"
        _fixed = False


def tr(key: str, /, **params: object) -> str:
    return tr_in(current_language(), key, **params)


def tr_in(lang: str, key: str, /, **params: object) -> str:
    text = key
    with _lock:
        for code in dict.fromkeys((lang, "en", "ja")):
            catalog = _load_catalog(code)
            value = catalog.get(key) if catalog is not None else None
            if isinstance(value, str):
                text = value
                break
        else:
            if key not in _warned_keys:
                _warned_keys.add(key)
                logging.warning("Missing translation: %s", key)
    if params:
        try:
            return text.format_map(params)
        except Exception as exc:
            logging.warning("Cannot format translation %s: %s", key, exc)
    return text
