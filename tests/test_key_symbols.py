import unittest

from keyseq.domain.key_symbols import KEY_SYMBOLS, display_key_name


class DisplayKeyNameTests(unittest.TestCase):
    def test_symbol_table(self):
        expected = {
            "backslash": "\\", "slash": "/", "semicolon": ";", "comma": ",",
            "period": ".", "equal": "=", "grave": "`", "quoteleft": "`",
            "apostrophe": "'", "quoteright": "'", "bracketleft": "[",
            "bracketright": "]", "at": "@", "asciicircum": "^", "bar": "|",
            "underscore": "_", "plus": "+", "asterisk": "*", "colon": ":",
            "less": "<", "greater": ">", "question": "?", "asciitilde": "~",
            "exclam": "!", "quotedbl": '"', "numbersign": "#", "dollar": "$",
            "percent": "%", "ampersand": "&", "parenleft": "(",
            "parenright": ")", "braceleft": "{", "braceright": "}",
            "yen": "¥", "ro": "\\", "minus": "-",
        }
        self.assertEqual(len(KEY_SYMBOLS), 36)
        self.assertEqual(KEY_SYMBOLS, expected)
        for name, symbol in expected.items():
            with self.subTest(name=name):
                self.assertEqual(display_key_name(name), symbol)

    def test_normalizes_lookup_but_preserves_unknown_input(self):
        self.assertEqual(display_key_name("  BAR  "), "|")
        self.assertEqual(display_key_name("  Unknown  "), "  Unknown  ")
        self.assertEqual(display_key_name(""), "")


if __name__ == "__main__":
    unittest.main()
