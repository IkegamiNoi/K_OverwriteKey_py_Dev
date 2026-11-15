import unittest

from keyseq.infrastructure.os_backend.macos.backend import (
    MacKeyboardBackend,
    MacTkKeyTranslator,
)


class MacTkKeyTranslatorTests(unittest.TestCase):
    @staticmethod
    def _keycode(vk: int, low_bits: int = 0x0041) -> int:
        return (vk << 24) | low_bits

    def test_aqua_keycode_uses_high_byte_virtual_key(self):
        translator = MacTkKeyTranslator(MacKeyboardBackend())
        keycode = self._keycode(18)

        self.assertEqual(translator.vk_to_scan_code(keycode), 2)
        self.assertEqual(translator.vk_to_char(keycode), "1")

    def test_numpad_vk_uses_mac_key_table_name(self):
        translator = MacTkKeyTranslator(MacKeyboardBackend())

        self.assertEqual(translator.numpad_name(self._keycode(82), 0), "num 0")
        self.assertEqual(translator.numpad_name(self._keycode(18), 0), "")

    def test_unavailable_vk_and_invalid_keycodes_are_unresolved(self):
        translator = MacTkKeyTranslator(MacKeyboardBackend())

        self.assertIsNone(translator.vk_to_scan_code(self._keycode(0xFF)))
        self.assertEqual(translator.vk_to_char(self._keycode(0xFF)), "")
        self.assertEqual(translator.numpad_name(self._keycode(0xFF), 0), "")
        self.assertIsNone(translator.vk_to_scan_code("invalid"))
        self.assertEqual(translator.vk_to_char("invalid"), "")
        self.assertIsNone(translator.vk_to_scan_code(self._keycode(10)))
        self.assertEqual(translator.vk_to_char(self._keycode(36)), "")

    def test_all_keypad_virtual_keys_map_to_expected_names(self):
        translator = MacTkKeyTranslator(MacKeyboardBackend())
        expected = {
            82: ("num 0", 82), 83: ("num 1", 79), 84: ("num 2", 80),
            85: ("num 3", 81), 86: ("num 4", 75), 87: ("num 5", 76),
            88: ("num 6", 77), 89: ("num 7", 71), 91: ("num 8", 72),
            92: ("num 9", 73), 65: ("num decimal", 83),
            67: ("num multiply", 55), 78: ("num subtract", 74),
            69: ("num add", 78), 75: ("num divide", 53),
            76: ("num enter", 28),
        }
        for vk, (name, scan_code) in expected.items():
            with self.subTest(vk=vk):
                self.assertEqual(translator.numpad_name(self._keycode(vk), 0), name)
                self.assertEqual(translator.vk_to_scan_code(self._keycode(vk)), scan_code)

    def test_zero_vk_keycode_and_layout_change_are_read_from_keyboard(self):
        keyboard = MacKeyboardBackend()
        translator = MacTkKeyTranslator(keyboard)

        self.assertEqual(translator.vk_to_scan_code(0x61), 30)
        self.assertEqual(translator.vk_to_char(0x61), "a")
        keyboard.set_layout_key_ids(frozenset({"yen"}))
        self.assertEqual(translator.vk_to_char(self._keycode(33)), "@")
        keyboard.set_layout_key_ids(frozenset())
        self.assertEqual(translator.vk_to_char(self._keycode(33)), "[")

    def test_selected_jis_layout_changes_vk_33_to_at(self):
        keyboard = MacKeyboardBackend()
        translator = MacTkKeyTranslator(keyboard)

        keyboard.set_layout_key_ids(frozenset({"yen"}))

        self.assertEqual(translator.vk_to_scan_code(self._keycode(33)), 26)
        self.assertEqual(translator.vk_to_char(self._keycode(33)), "@")

    def test_modifier_name_uses_macos_command_and_option_names(self):
        translator = MacTkKeyTranslator(MacKeyboardBackend())
        expected = (
            ("Meta_L", "command", "left command"),
            ("Meta_R", "command", "right command"),
            ("Alt_L", "option", "left option"),
            ("Alt_R", "option", "right option"),
        )
        for keysym, generic, sided in expected:
            with self.subTest(keysym=keysym):
                self.assertEqual(translator.modifier_name(keysym, sided=False), generic)
                self.assertEqual(translator.modifier_name(keysym, sided=True), sided)
        self.assertEqual(translator.modifier_name("Super_L", sided=False), "??")
        self.assertIsNone(translator.modifier_name("Other", sided=False))


if __name__ == "__main__":
    unittest.main()
