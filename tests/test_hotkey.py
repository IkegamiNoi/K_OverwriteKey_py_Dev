import unittest

from keyseq.domain.hotkey import validate_hotkey_syntax


class HotkeySyntaxTest(unittest.TestCase):
    def test_empty_hotkey(self):
        self.assertEqual(validate_hotkey_syntax(""), ("hotkey が空です。", "", []))
        self.assertEqual(validate_hotkey_syntax(None), ("hotkey が空です。", "", []))

    def test_whitespace_only_hotkey(self):
        self.assertEqual(validate_hotkey_syntax("   "), ("hotkey が空です。", "", []))

    def test_empty_component(self):
        expected = (
            "hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。",
            "",
            [],
        )
        for hotkey in ("ctrl++c", "+ctrl+c", "ctrl+c+"):
            with self.subTest(hotkey=hotkey):
                self.assertEqual(validate_hotkey_syntax(hotkey), expected)

    def test_duplicate_key(self):
        self.assertEqual(
            validate_hotkey_syntax("ctrl+ctrl+c"),
            ("hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", "", []),
        )

    def test_valid_hotkey(self):
        self.assertEqual(validate_hotkey_syntax("ctrl+c"), ("", "ctrl+c", ["ctrl", "c"]))

    def test_normalizes_whitespace_and_case(self):
        self.assertEqual(validate_hotkey_syntax(" Ctrl + C "), ("", "ctrl+c", ["ctrl", "c"]))

    def test_single_key(self):
        self.assertEqual(validate_hotkey_syntax("f12"), ("", "f12", ["f12"]))

    def test_unknown_key_name_is_valid_syntax(self):
        self.assertEqual(validate_hotkey_syntax("notakey"), ("", "notakey", ["notakey"]))

    def test_normalized_matches_parts(self):
        for hotkey in ("ctrl+c", " Ctrl + C ", "f12", "notakey"):
            with self.subTest(hotkey=hotkey):
                error_message, normalized, parts = validate_hotkey_syntax(hotkey)
                self.assertEqual(error_message, "")
                self.assertEqual(normalized, "+".join(parts))


if __name__ == "__main__":
    unittest.main()
