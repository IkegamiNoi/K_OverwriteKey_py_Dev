import unittest

from keyseq.domain.key_identifiers import (
    is_special_key_name,
    resolve_known_key_name_from_scan_code,
    resolve_known_scan_code_from_key_name,
)


class KeyIdentifiersTest(unittest.TestCase):
    def test_known_key_to_scan_code(self):
        self.assertEqual(resolve_known_scan_code_from_key_name("MUHENKAN"), 123)
        self.assertIsNone(resolve_known_scan_code_from_key_name("a"))
        self.assertIsNone(resolve_known_scan_code_from_key_name(""))

    def test_scan_code_to_key(self):
        self.assertEqual(resolve_known_key_name_from_scan_code(121), "henkan")
        self.assertEqual(resolve_known_key_name_from_scan_code(999), "")
        self.assertEqual(resolve_known_key_name_from_scan_code("abc"), "")

    def test_is_special_key_name(self):
        self.assertTrue(is_special_key_name("kana"))
        self.assertFalse(is_special_key_name("f1"))


if __name__ == "__main__":
    unittest.main()
