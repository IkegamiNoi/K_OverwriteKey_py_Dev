"""Shared display symbols for common keyboard key names."""

from collections.abc import Mapping

KEY_SYMBOLS: dict[str, str] = {
    "backslash": "\\",
    "slash": "/",
    "minus": "-",
    "semicolon": ";",
    "comma": ",",
    "period": ".",
    "equal": "=",
    "grave": "`",
    "quoteleft": "`",
    "apostrophe": "'",
    "quoteright": "'",
    "bracketleft": "[",
    "bracketright": "]",
    "at": "@",
    "asciicircum": "^",
    "bar": "|",
    "underscore": "_",
    "plus": "+",
    "asterisk": "*",
    "colon": ":",
    "less": "<",
    "greater": ">",
    "question": "?",
    "asciitilde": "~",
    "exclam": "!",
    "quotedbl": '"',
    "numbersign": "#",
    "dollar": "$",
    "percent": "%",
    "ampersand": "&",
    "parenleft": "(",
    "parenright": ")",
    "braceleft": "{",
    "braceright": "}",
    "yen": "¥",
    "ro": "\\",
}


def display_key_name(key_name: str, key_symbols: Mapping[str, str] | None = None) -> str:
    """Return a common display symbol, preserving other names verbatim."""
    if key_symbols is not None:
        from .config import normalize_key_name

        symbol = key_symbols.get(normalize_key_name(key_name))
        if symbol is not None:
            return symbol
    symbol = KEY_SYMBOLS.get(key_name.strip().lower())
    if symbol is not None:
        return symbol
    return key_name
