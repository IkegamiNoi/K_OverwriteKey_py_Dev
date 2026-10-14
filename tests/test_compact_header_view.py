import unittest

from keyseq.presentation.compact_header_view import (
    COMPACT_HEADER_VIEW_KEY,
    parse_compact_header_view,
)


class ParseCompactHeaderViewTests(unittest.TestCase):
    def test_constant_and_valid_values(self):
        self.assertEqual(COMPACT_HEADER_VIEW_KEY, "compact_header_view")
        self.assertEqual(
            parse_compact_header_view({"hook": False, "display": True}),
            {"hook": False, "display": True},
        )
        self.assertEqual(
            parse_compact_header_view({"hook": False, "display": False}),
            {"hook": False, "display": False},
        )

    def test_non_dictionary_values_default_both_sections_open(self):
        for raw in (None, [], "invalid"):
            with self.subTest(raw=raw):
                self.assertEqual(
                    parse_compact_header_view(raw),
                    {"hook": True, "display": True},
                )

    def test_missing_and_invalid_values_default_independently(self):
        self.assertEqual(
            parse_compact_header_view({}),
            {"hook": True, "display": True},
        )
        for invalid in ("x", 1, None):
            with self.subTest(invalid=invalid):
                self.assertEqual(
                    parse_compact_header_view({"hook": False, "display": invalid}),
                    {"hook": False, "display": True},
                )
                self.assertEqual(
                    parse_compact_header_view({"hook": invalid, "display": False}),
                    {"hook": True, "display": False},
                )

    def test_unknown_keys_are_ignored(self):
        self.assertEqual(
            parse_compact_header_view({"hook": False, "other": False}),
            {"hook": False, "display": True},
        )


if __name__ == "__main__":
    unittest.main()
