"""読み込み履歴の domain 規則の単体テスト。"""

from copy import deepcopy
from typing import Any
import unittest

from keyseq.domain import keymap_set_history as history_rules


def _history() -> dict[str, Any]:
    return {
        "recent": [{"path": "A"}, {"path": "B"}, {"path": "a"}],
        "categories": [
            {"name": "Work", "entries": [{"path": "A"}, {"path": "B"}]},
            {"name": "Other", "entries": []},
        ],
    }


class NormalizeHistoryTest(unittest.TestCase):
    def test_non_dict_returns_empty_history(self) -> None:
        for raw in (None, [], "bad", 1, False):
            with self.subTest(raw=raw):
                self.assertEqual(history_rules.normalize_history(raw), {
                    "recent": [], "categories": [],
                })

    def test_non_list_fields_are_empty(self) -> None:
        for raw in (None, {}, "bad", 1, ()):
            with self.subTest(raw=raw):
                self.assertEqual(history_rules.normalize_history({
                    "recent": raw, "categories": raw,
                }), {"recent": [], "categories": []})
                self.assertEqual(history_rules.normalize_history({
                    "categories": [{"name": "Work", "entries": raw}],
                })["categories"], [{"name": "Work", "entries": []}])

    def test_invalid_entries_removed_and_paths_trimmed(self) -> None:
        entries = [None, "bad", {}, {"path": None}, {"path": 1},
                   {"path": ""}, {"path": " \t "},
                   {"path": " Z.JSON ", "extra": True}, {"path": "a.JSON"}]
        raw = {"recent": entries, "categories": [
            {"name": " Work ", "entries": entries, "extra": True},
        ], "extra": True}
        before = deepcopy(raw)
        expected = [{"path": "Z.JSON"}, {"path": "a.JSON"}]
        result = history_rules.normalize_history(raw)
        self.assertEqual(result, {"recent": expected, "categories": [
            {"name": "Work", "entries": expected},
        ]})
        self.assertEqual(raw, before)
        self.assertIsNot(result["recent"], entries)
        self.assertIsNot(result["recent"][0], entries[-2])

    def test_invalid_names_removed_and_duplicate_names_first_wins(self) -> None:
        raw = {"categories": [None, "bad", {}, {"name": None}, {"name": 1},
                              {"name": ""}, {"name": " \t "},
                              {"name": " Z ", "entries": [{"path": "first"}]},
                              {"name": "Z", "entries": [{"path": "later"}]},
                              {"name": "z"}, {"name": "A"}]}
        self.assertEqual(history_rules.normalize_history(raw), {
            "recent": [], "categories": [
                {"name": "Z", "entries": [{"path": "first"}]},
                {"name": "z", "entries": []}, {"name": "A", "entries": []},
            ],
        })

    def test_limit_preserves_first_twenty_and_accepts_custom_limit(self) -> None:
        raw = {"recent": [{"path": str(i)} for i in range(25)]}
        self.assertEqual(history_rules.MAX_RECENT, 20)
        self.assertEqual(history_rules.normalize_history(raw)["recent"], raw["recent"][:20])
        for limit in (0, 2, 30):
            with self.subTest(limit=limit):
                self.assertEqual(history_rules.normalize_history(
                    raw, max_recent=limit,
                )["recent"], raw["recent"][:limit])

    def test_normalization_does_not_deduplicate_paths(self) -> None:
        raw = {"recent": [{"path": "A"}, {"path": "A"}]}
        self.assertEqual(history_rules.normalize_history(raw)["recent"], raw["recent"])


class RecentHistoryTest(unittest.TestCase):
    def test_head_match_mismatch_empty_and_comparison_key(self) -> None:
        history = _history()
        self.assertTrue(history_rules.is_recent_head(history, "A", key_of=str))
        self.assertFalse(history_rules.is_recent_head(history, "a", key_of=str))
        self.assertFalse(history_rules.is_recent_head(history, "B", key_of=str.lower))
        self.assertTrue(history_rules.is_recent_head(history, "a", key_of=str.lower))
        self.assertFalse(history_rules.is_recent_head(
            {"recent": [], "categories": []}, "A", key_of=str,
        ))

    def test_push_new_and_existing_paths(self) -> None:
        history = _history()
        result = history_rules.push_recent(history, "C", key_of=str.lower)
        self.assertEqual(result["recent"], [{"path": "C"}] + history["recent"])
        result = history_rules.push_recent(history, "b", key_of=str.lower)
        self.assertEqual(result["recent"], [{"path": "b"}, {"path": "A"}, {"path": "a"}])
        self.assertEqual(len(result["recent"]), len(history["recent"]))
        self.assertEqual(result["categories"], history["categories"])

    def test_push_removes_all_duplicates_even_when_head_matches(self) -> None:
        result = history_rules.push_recent(_history(), "a", key_of=str.lower)
        self.assertEqual(result["recent"], [{"path": "a"}, {"path": "B"}])

    def test_push_uses_arbitrary_comparison_key(self) -> None:
        history = {"recent": [{"path": "one"}, {"path": "two"}], "categories": []}
        result = history_rules.push_recent(history, "THREE", key_of=lambda path: "same")
        self.assertEqual(result["recent"], [{"path": "THREE"}])

    def test_push_drops_oldest_and_accepts_custom_limit(self) -> None:
        history = {"recent": [{"path": str(i)} for i in range(20)], "categories": []}
        result = history_rules.push_recent(history, "new", key_of=str)
        self.assertEqual(result["recent"], [{"path": "new"}] + history["recent"][:19])
        for limit in (0, 2):
            self.assertEqual(history_rules.push_recent(
                history, "new", key_of=str, max_recent=limit,
            )["recent"], ([{"path": "new"}] + history["recent"])[:limit])

    def test_remove_recent_at_only_removes_selected_position(self) -> None:
        history = _history()
        result = history_rules.remove_recent_at(history, 0)
        self.assertEqual(result["recent"], history["recent"][1:])
        self.assertEqual(result["categories"], history["categories"])
        for index in (-1, 3, 100):
            self.assertIsNone(history_rules.remove_recent_at(history, index))
        self.assertIsNone(history_rules.remove_recent_at(
            {"recent": [], "categories": []}, 0,
        ))


class CategoryHistoryTest(unittest.TestCase):
    def test_add_category_trims_and_appends_case_sensitive_name(self) -> None:
        history = _history()
        result = history_rules.add_category(history, " work ")
        self.assertEqual(result["categories"], history["categories"] + [
            {"name": "work", "entries": []},
        ])
        for name in ("", " \t ", "Work", " Work "):
            self.assertIsNone(history_rules.add_category(history, name))

    def test_rename_category_trims_preserves_entries_and_order(self) -> None:
        history = _history()
        result = history_rules.rename_category(history, "Work", " work ")
        self.assertEqual(result["categories"], [
            {"name": "work", "entries": history["categories"][0]["entries"]},
            history["categories"][1],
        ])
        for name in ("", " \t ", "Work", " Work ", " Other "):
            self.assertIsNone(history_rules.rename_category(history, "Work", name))
        self.assertIsNone(history_rules.rename_category(history, "missing", "new"))

    def test_name_conflicts_compare_trimmed_existing_names(self) -> None:
        history = {"recent": [], "categories": [
            {"name": " Work ", "entries": []}, {"name": "Other", "entries": []},
        ]}
        self.assertIsNone(history_rules.add_category(history, "Work"))
        self.assertIsNone(history_rules.rename_category(history, "Other", "Work"))

    def test_remove_category_removes_entries_together(self) -> None:
        history = _history()
        result = history_rules.remove_category(history, "Work")
        self.assertEqual(result, {"recent": history["recent"], "categories": [
            {"name": "Other", "entries": []},
        ]})
        for name in ("missing", "", " "):
            self.assertIsNone(history_rules.remove_category(history, name))

    def test_add_to_category_appends_and_rejects_local_duplicates(self) -> None:
        history = _history()
        result = history_rules.add_to_category(history, "Work", "C", key_of=str.lower)
        self.assertEqual(result["categories"][0]["entries"], [
            {"path": "A"}, {"path": "B"}, {"path": "C"},
        ])
        self.assertEqual(result["recent"], history["recent"])
        self.assertIsNone(history_rules.add_to_category(history, "Work", "a", key_of=str.lower))
        result = history_rules.add_to_category(history, "Other", "a", key_of=str.lower)
        self.assertEqual(result["categories"][1]["entries"], [{"path": "a"}])
        self.assertIsNone(history_rules.add_to_category(history, "missing", "C", key_of=str))
        self.assertIsNotNone(history_rules.add_to_category(history, "Work", "a", key_of=str))
        self.assertIsNone(history_rules.add_to_category(
            history, "Work", "unrelated", key_of=lambda path: "same",
        ))

    def test_remove_category_entry_only_removes_selected_position(self) -> None:
        history = _history()
        result = history_rules.remove_category_entry_at(history, "Work", 0)
        self.assertEqual(result["categories"][0]["entries"], [{"path": "B"}])
        self.assertEqual(result["recent"], history["recent"])
        for name, index in (("Work", -1), ("Work", 2), ("Other", 0), ("missing", 0)):
            self.assertIsNone(history_rules.remove_category_entry_at(history, name, index))

    def test_sorted_categories_casefold_order_and_stability(self) -> None:
        history = {"recent": [], "categories": [
            {"name": name, "entries": [{"path": name}]}
            for name in ("z", "Straße", "STRASSE", "a", "A")
        ]}
        before = deepcopy(history)
        result = history_rules.sorted_categories(history)
        self.assertEqual([c["name"] for c in result], ["a", "A", "Straße", "STRASSE", "z"])
        self.assertEqual(history, before)
        result[0]["entries"][0]["path"] = "changed"
        self.assertEqual(history, before)


class HistoryPurityTest(unittest.TestCase):
    def test_all_history_results_are_independent_copies(self) -> None:
        operations = [
            lambda h: history_rules.normalize_history(h),
            lambda h: history_rules.push_recent(h, "C", key_of=str),
            lambda h: history_rules.remove_recent_at(h, 1),
            lambda h: history_rules.add_category(h, "New"),
            lambda h: history_rules.rename_category(h, "Work", "New"),
            lambda h: history_rules.remove_category(h, "Other"),
            lambda h: history_rules.add_to_category(h, "Work", "C", key_of=str),
            lambda h: history_rules.remove_category_entry_at(h, "Work", 1),
        ]
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                history = _history()
                before = deepcopy(history)
                result = operation(history)
                self.assertIsNotNone(result)
                self.assertIsNot(result, history)
                self.assertEqual(history, before)
                result["recent"][0]["path"] = "changed"
                result["categories"][0]["entries"][0]["path"] = "changed"
                self.assertEqual(history, before)

    def test_rejected_edits_and_head_checks_leave_input_unchanged(self) -> None:
        history = _history()
        before = deepcopy(history)
        history_rules.is_recent_head(history, "a", key_of=str.lower)
        self.assertIsNone(history_rules.add_category(history, "Work"))
        self.assertIsNone(history_rules.rename_category(history, "Work", "Other"))
        self.assertIsNone(history_rules.remove_category(history, "missing"))
        self.assertIsNone(history_rules.add_to_category(history, "Work", "a", key_of=str.lower))
        self.assertIsNone(history_rules.remove_recent_at(history, -1))
        self.assertIsNone(history_rules.remove_category_entry_at(history, "Work", -1))
        self.assertEqual(history, before)


if __name__ == "__main__":
    unittest.main()
