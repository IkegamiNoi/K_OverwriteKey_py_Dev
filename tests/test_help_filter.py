"""Tests for pure help search and highlight functions."""

import unittest

from keyseq.presentation.help.help_filter import (
    highlight_ranges,
    item_matches,
    normalize_with_positions,
    parse_query,
)


class HelpFilterTest(unittest.TestCase):
    def test_parse_query_normalizes_and_splits_whitespace(self) -> None:
        self.assertEqual(parse_query("  ＡＢＣ　def  "), ("abc", "def"))
        self.assertEqual(parse_query(" \t　 "), ())

    def test_normalize_with_positions_tracks_expansions(self) -> None:
        result = normalize_with_positions("ß㍿x")
        self.assertEqual(result.text, "ss株式会社x")
        self.assertEqual(result.positions, (0, 0, 1, 1, 1, 1, 2))
        self.assertEqual(len(result.positions), len(result.text))

    def test_kana_nfkc_search_and_highlight(self) -> None:
        for term in ("ｶﾞ", "ガ"):
            self.assertTrue(item_matches(("分類", "見出し", "本文ガ文字"), (term,)))
            self.assertEqual(highlight_ranges("本文ガ文字", (term,)), [(2, 3)])

    def test_expansion_highlight_positions(self) -> None:
        self.assertEqual(highlight_ranges("㍿テスト", ("テスト",)), [(1, 4)])
        self.assertEqual(highlight_ranges("ßx", ("ss",)), [(0, 1)])
        self.assertEqual(highlight_ranges("ßx", ("s",)), [(0, 1)])

    def test_item_matches_and_boundary_behavior(self) -> None:
        fields = ("大分類", "見出し", "本文のことば")
        self.assertTrue(item_matches(fields, ("大分類", "本文")))
        self.assertTrue(item_matches(("大分類", "needle", "本文"), ("needle",)))
        self.assertTrue(item_matches(("大分類", "見出し", "needle"), ("needle",)))
        self.assertTrue(item_matches(("needle", "見出し", "本文"), ("needle",)))
        self.assertFalse(item_matches(("かた", "かな", ""), ("たか",)))
        self.assertFalse(item_matches(("かな", "", ""), ("カナ",)))
        self.assertTrue(item_matches(fields, ()))

    def test_highlight_finds_each_overlapping_occurrence_in_order(self) -> None:
        self.assertEqual(highlight_ranges("aaa", ("aa",)), [(0, 2), (1, 3)])
        self.assertEqual(highlight_ranges("ababa", ("aba", "ba")), [(0, 3), (1, 3), (2, 5), (3, 5)])
        self.assertEqual(highlight_ranges("abc", ()), [])


if __name__ == "__main__":
    unittest.main()
