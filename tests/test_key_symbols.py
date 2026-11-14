import unittest

from keyseq.domain.key_symbols import (
    KEY_SYMBOLS, display_key_name, display_modifier_names, set_modifier_display_names,
)


class DisplayKeyNameTests(unittest.TestCase):
    def setUp(self):
        set_modifier_display_names({})

    def tearDown(self):
        set_modifier_display_names({})

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

    def test_modifier_display_names_default_to_empty(self):
        self.assertEqual(display_key_name("left windows"), "left windows")
        self.assertEqual(display_key_name("alt"), "alt")
        self.assertEqual(display_modifier_names("windows+c"), "windows+c")

    def test_modifier_only_replacement_preserves_alt_gr(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        self.assertEqual(display_modifier_names("windows+c"), "Command+c")
        self.assertEqual(display_modifier_names("alt gr"), "alt gr")

    def test_modifier_display_names_replace_words_without_changing_saved_names(self):
        names = {"windows": "Command", "alt": "Option"}
        set_modifier_display_names(names)
        names["windows"] = "Mutated"
        self.assertEqual(display_key_name("left windows"), "left Command")
        self.assertEqual(display_key_name("alt"), "Option")
        self.assertEqual(display_key_name("right alt"), "right Option")
        self.assertEqual(display_key_name("windowsill"), "windowsill")
        self.assertEqual(display_key_name("altitude"), "altitude")
        self.assertEqual(display_key_name("alt gr"), "alt gr")
        self.assertEqual(display_key_name("backslash"), "\\")

    def test_replacing_modifier_display_names_replaces_previous_table(self):
        set_modifier_display_names({"windows": "Command", "alt": "Option"})
        set_modifier_display_names({"alt": "Option"})

        self.assertEqual(display_key_name("left windows"), "left windows")
        self.assertEqual(display_key_name("left alt"), "left Option")


if __name__ == "__main__":
    unittest.main()
