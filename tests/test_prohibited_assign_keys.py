import unittest

from keyseq.domain.key_identifiers import is_prohibited_assign_key


class ProhibitedAssignKeyTest(unittest.TestCase):
    def test_prohibited_names_are_case_and_whitespace_insensitive(self):
        for name in (
            "left windows",
            "RIGHT WINDOWS",
            " Windows ",
            "caps lock",
            "CAPS_LOCK",
            " capslock ",
            "alt gr",
            " ALTGR ",
        ):
            with self.subTest(name=name):
                self.assertTrue(is_prohibited_assign_key(name))

    def test_other_names_are_allowed(self):
        for name in ("ctrl", "right alt", "a", ""):
            with self.subTest(name=name):
                self.assertFalse(is_prohibited_assign_key(name))


if __name__ == "__main__":
    unittest.main()
