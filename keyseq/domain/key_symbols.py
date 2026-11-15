"""Shared display symbols for common keyboard key names."""

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
    """Return a common display symbol, preserving other names verbatim."""
    symbol = KEY_SYMBOLS.get(key_name.strip().lower())
    if symbol is not None:
        return symbol
    return key_name
