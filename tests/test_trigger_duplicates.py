import unittest

from keyseq.domain.trigger_duplicates import (
    effective_trigger_index,
    effective_rows_by_key,
    is_effective_trigger,
    replaced_effective_keys,
    shadowed_duplicate_indices,
)


class TriggerDuplicatesTest(unittest.TestCase):
    def test_effective_rows_use_positions_and_normalized_nonempty_keys(self):
        rows = [None, {"key": " F1 "}, {"key": "f1"}, {"key": ""}, {"key": "f2"}]
        self.assertEqual(effective_rows_by_key(rows), {"f1": 1, "f2": 4})

    def test_replacement_compares_identity_not_equal_content_or_position(self):
        first, second, other = {"key": "f1"}, {"key": "f1"}, {"key": "f2"}
        before = [first, second, other]
        self.assertEqual(replaced_effective_keys(before, [second, other]), {"f1"})
        self.assertEqual(replaced_effective_keys(before, [second, first, other]), {"f1"})
        self.assertEqual(replaced_effective_keys(before, [other, first, second]), set())
        self.assertEqual(replaced_effective_keys(before, [first, other]), set())
        self.assertEqual(replaced_effective_keys(before, [other]), set())

    def test_key_change_replaces_old_key_only_when_another_row_survives(self):
        first, second = {"key": "f1"}, {"key": "F1"}
        renamed = dict(first, key="f2")
        self.assertEqual(replaced_effective_keys([first, second], [renamed, second]), {"f1"})
        self.assertEqual(replaced_effective_keys([first], [renamed]), set())

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
