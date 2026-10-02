import unittest

from keyseq.domain.trigger_duplicates import (
    effective_trigger_index,
    is_effective_trigger,
    shadowed_duplicate_indices,
)


class TriggerDuplicatesTest(unittest.TestCase):
    def test_empty_keys_and_non_dict_rows_are_ignored(self):
        rows = [
            {"key": ""},
            None,
            "not a row",
            {"key": "f1"},
            {"key": " "},
            {"key": "f1"},
        ]
        self.assertEqual(shadowed_duplicate_indices(rows), frozenset({5}))
        self.assertEqual(effective_trigger_index(rows, " f1 "), 3)
        self.assertIsNone(effective_trigger_index(rows, " "))
        self.assertFalse(is_effective_trigger(rows, 0))
        self.assertTrue(is_effective_trigger(rows, 3))
        self.assertFalse(is_effective_trigger(rows, 5))

    def test_three_or_more_rows_mark_every_row_after_the_first(self):
        rows = [{"key": "a"}, {"key": "a"}, {"key": "b"}, {"key": "a"}, {"key": "a"}]
        self.assertEqual(shadowed_duplicate_indices(rows), frozenset({1, 3, 4}))

    def test_key_normalization_is_case_and_whitespace_insensitive(self):
        rows = [{"key": " F1 "}, {"key": "f1"}, {"key": "F1"}]
        self.assertEqual(shadowed_duplicate_indices(rows), frozenset({1, 2}))
        self.assertEqual(effective_trigger_index(rows, " f1 "), 0)
        self.assertTrue(is_effective_trigger(rows, 0))


if __name__ == "__main__":
    unittest.main()
