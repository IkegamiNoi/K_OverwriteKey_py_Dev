import ast
from pathlib import Path
import unittest

from keyseq.domain.keymap_triggers import (
    ensure_active_triggers,
    get_active_triggers,
    set_active_triggers,
)


class KeymapTriggersTest(unittest.TestCase):
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
