import unittest

from keyseq.application.hotkey_service import HotkeyService


class FakeKeyNameValidator:
    def __init__(self, invalid_keys: set[str] | None = None) -> None:
        self.calls: list[str] = []
        self._invalid_keys = invalid_keys or set()

    def validate(self, key_name: str) -> None:
        self.calls.append(key_name)
        if key_name in self._invalid_keys:
            raise ValueError(f"{key_name} is invalid")


class HotkeyServiceTest(unittest.TestCase):
    def test_empty_hotkey_returns_syntax_error_without_key_name_validation(self):
        validator = FakeKeyNameValidator()
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate("")

        self.assertEqual(result, ("hotkey が空です。", ""))
        self.assertEqual(validator.calls, [])

    def test_empty_key_around_plus_returns_syntax_error_without_key_name_validation(self):
        validator = FakeKeyNameValidator()
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate("ctrl++c")

        self.assertEqual(
            result,
            ("hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。", ""),
        )
        self.assertEqual(validator.calls, [])

    def test_duplicate_key_returns_syntax_error_without_key_name_validation(self):
        validator = FakeKeyNameValidator()
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate("ctrl+ctrl+c")

        self.assertEqual(result, ("hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", ""))
        self.assertEqual(validator.calls, [])

    def test_valid_hotkey_returns_normalized_value(self):
        validator = FakeKeyNameValidator()
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate("ctrl+c")

        self.assertEqual(result, ("", "ctrl+c"))
        self.assertEqual(validator.calls, ["ctrl", "c"])

    def test_hotkey_is_normalized_before_key_name_validation(self):
        validator = FakeKeyNameValidator()
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate(" Ctrl + C ")

        self.assertEqual(result, ("", "ctrl+c"))
        self.assertEqual(validator.calls, ["ctrl", "c"])

    def test_unknown_key_returns_error_message(self):
        validator = FakeKeyNameValidator({"notakey"})
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate("notakey")

        self.assertEqual(result, ("不明なキー名があります: 'notakey'（詳細: notakey is invalid）", ""))

    def test_error_message_identifies_failing_key(self):
        validator = FakeKeyNameValidator({"notakey"})
        service = HotkeyService(validate_key_name=validator.validate)

        error_message, normalized = service.validate("ctrl+notakey")

        self.assertIn("'notakey'", error_message)
        self.assertNotIn("'ctrl'", error_message)
        self.assertEqual(normalized, "")

    def test_key_name_validation_stops_at_first_failure(self):
        validator = FakeKeyNameValidator({"bad1", "bad2"})
        service = HotkeyService(validate_key_name=validator.validate)

        error_message, normalized = service.validate("bad1+bad2")

        self.assertIn("'bad1'", error_message)
        self.assertEqual(normalized, "")
        self.assertEqual(validator.calls, ["bad1"])

    def test_validate_returns_two_element_tuple(self):
        validator = FakeKeyNameValidator()
        service = HotkeyService(validate_key_name=validator.validate)

        result = service.validate("ctrl+c")

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
