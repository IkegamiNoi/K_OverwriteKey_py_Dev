"""Shared display symbols for common keyboard key names."""

import re


_MODIFIER_DISPLAY_NAMES: dict[str, str] = {}
_MODIFIER_WORD = re.compile(r"\bwindows\b|\balt\b(?!\s+gr\b)", re.IGNORECASE)


def set_modifier_display_names(mapping: dict[str, str]) -> None:
    """Set display-only modifier names without changing stored key names."""
    global _MODIFIER_DISPLAY_NAMES
    _MODIFIER_DISPLAY_NAMES = dict(mapping)


def display_modifier_names(text: str) -> str:
    """Apply only the configured modifier name replacements."""
    return _MODIFIER_WORD.sub(
        lambda match: _MODIFIER_DISPLAY_NAMES.get(match.group().lower(), match.group()), text
    )


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


def display_key_name(key_name: str) -> str:
    """Return the common display symbol, preserving unknown input verbatim."""
    symbol = KEY_SYMBOLS.get(key_name.strip().lower())
    if symbol is not None:
        return symbol
    return display_modifier_names(key_name)
