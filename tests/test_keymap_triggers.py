import ast
from copy import deepcopy
from pathlib import Path
import unittest

from keyseq.domain.keymap_triggers import (
    duplicate_keymap,
    ensure_active_triggers,
    get_active_triggers,
    keymap_trigger_list,
    set_active_triggers,
)


class KeymapTriggersTest(unittest.TestCase):
    def test_duplicate_keymap_copies_without_internal_values(self):
        source = {
            "id": "old",
            "label": "Original",
            "_private": {"hidden": True},
            "mappings": {"_": "underscore", "f1": {"actions": [{"value": "original"}]}},
            "triggers": [
                {"key": "f2", "actions": [{"value": "trigger"}], "_runtime": 2},
                {"key": "f3", "_runtime": {"nested": True}},
            ],
        }
        original = deepcopy(source)

        duplicate = duplicate_keymap(source, "new", "Copy")

        self.assertEqual(duplicate["id"], "new")
        self.assertEqual(duplicate["label"], "Copy")
        self.assertNotIn("_private", duplicate)
        self.assertEqual(duplicate["mappings"]["_"], "underscore")
        self.assertEqual(duplicate["triggers"], [
            {"key": "f2", "actions": [{"value": "trigger"}]},
            {"key": "f3"},
        ])
        self.assertIsNot(duplicate["triggers"], source["triggers"])
        for index, row in enumerate(source["triggers"]):
            self.assertIsNot(duplicate["triggers"][index], row)
        self.assertIsNot(duplicate["mappings"], source["mappings"])
        self.assertIsNot(duplicate["mappings"]["f1"], source["mappings"]["f1"])
        self.assertIsNot(
            duplicate["mappings"]["f1"]["actions"][0],
            source["mappings"]["f1"]["actions"][0],
        )
        self.assertEqual(source, original)

    def test_keymap_trigger_list_returns_same_list(self):
        for triggers in ([], [{"key": "f1"}]):
            with self.subTest(triggers=triggers):
                self.assertIs(keymap_trigger_list({"triggers": triggers}), triggers)

    def test_keymap_trigger_list_missing_or_non_list_returns_none(self):
        self.assertIsNone(keymap_trigger_list({}))
        for value in (None, {}, (), "invalid", 0):
            with self.subTest(value=value):
                self.assertIsNone(keymap_trigger_list({"triggers": value}))

    def test_get_returns_same_list(self):
        for triggers in ([], [{"key": "f1"}]):
            with self.subTest(triggers=triggers):
                data = {"keymaps": [{"id": "km1", "triggers": triggers}], "active_keymap_id": "km1"}
                self.assertIs(get_active_triggers(data), triggers)

    def test_get_missing_returns_fresh_list_without_mutation(self):
        data = {}
        triggers = get_active_triggers(data)
        self.assertEqual(triggers, [])
        self.assertIsNot(triggers, get_active_triggers(data))
        self.assertEqual(data, {})

    def test_get_non_list_returns_fresh_list_without_mutation(self):
        for value in (None, {}, (), "invalid", 0):
            with self.subTest(value=value):
                data = {"keymaps": [{"id": "km1", "triggers": value}], "active_keymap_id": "km1"}
                triggers = get_active_triggers(data)
                self.assertEqual(triggers, [])
                self.assertIsNot(triggers, get_active_triggers(data))
                self.assertIs(data["keymaps"][0]["triggers"], value)

    def test_ensure_preserves_existing_list(self):
        for triggers in ([], [{"key": "f1"}]):
            with self.subTest(triggers=triggers):
                data = {"keymaps": [{"id": "km1", "triggers": triggers}], "active_keymap_id": "km1"}
                self.assertIs(ensure_active_triggers(data), triggers)
                self.assertIs(data["keymaps"][0]["triggers"], triggers)

    def test_ensure_missing_stores_list(self):
        data = {}
        triggers = ensure_active_triggers(data)
        self.assertEqual(triggers, [])
        self.assertIs(data["keymaps"][0]["triggers"], triggers)
        self.assertIs(ensure_active_triggers(data), triggers)

    def test_ensure_non_list_stores_list(self):
        for value in (None, {}, (), "invalid", 0):
            with self.subTest(value=value):
                data = {"keymaps": [{"id": "km1", "triggers": value}], "active_keymap_id": "km1"}
                triggers = ensure_active_triggers(data)
                self.assertEqual(triggers, [])
                self.assertIs(data["keymaps"][0]["triggers"], triggers)
                self.assertIs(ensure_active_triggers(data), triggers)

    def test_set_stores_same_list(self):
        for data in ({}, {"triggers": None}, {"triggers": [{"key": "f1"}]}):
            for triggers in ([], [{"key": "f2"}]):
                with self.subTest(data=data, triggers=triggers):
                    self.assertIsNone(set_active_triggers(data, triggers))
                    self.assertIs(data["keymaps"][0]["triggers"], triggers)

    def test_presentation_has_no_triggers_literal(self):
        presentation = Path(__file__).resolve().parents[1] / "keyseq" / "presentation"
        paths = sorted(presentation.rglob("*.py"))
        self.assertTrue(paths)
        violations = []
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and node.value == "triggers":
                    violations.append(f"{path.relative_to(presentation)}:{node.lineno}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
