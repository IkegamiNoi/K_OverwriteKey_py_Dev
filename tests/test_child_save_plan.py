import os
import tempfile
import unittest

from keyseq.application.config_service import ConfigService
from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.controllers.config_io.child_save_plan import build_save_plan
from keyseq.presentation.controllers.config_io.child_save_rows import ChildSaveRow


def make_data():
    return {
        "keymaps": [{"id": "km1", "label": "Main", "mappings": {}}],
        "triggers": [{"key": "f1", "label": "Copy", "actions": []}],
        "active_keymap_id": "km1",
    }


def row(kind, key):
    return ChildSaveRow(kind, key, key or "トリガー一覧", "", "new", "新規作成", ACTION_SAVE)


class ChildSavePlanTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _targets(self, root, data):
        return self.service.resolve_child_save_targets(
            data,
            config_root=root,
            keymap_set_path=os.path.join(root, "user", "keymap_sets", "main.json"),
        )

    def test_dirty_choices_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            data = make_data()
            targets = self._targets(root, data)
            rows = [row(CHILD_KEYMAP, "km1"), row(CHILD_TRIGGER_SET, ""), row(CHILD_SEQUENCE, "f1")]
            plan = build_save_plan(
                data=data,
                rows=rows,
                choices={
                    (CHILD_KEYMAP, "km1"): (ACTION_SAVE, ""),
                    (CHILD_TRIGGER_SET, ""): (ACTION_SAVE_AS, os.path.join(root, "trigger.json")),
                    (CHILD_SEQUENCE, "f1"): (ACTION_SKIP, ""),
                },
                targets=targets,
            )

        self.assertEqual(
            [(entry.kind, entry.key, entry.action) for entry in plan.entries],
            [(CHILD_KEYMAP, "km1", ACTION_SAVE), (CHILD_TRIGGER_SET, "", ACTION_SAVE_AS), (CHILD_SEQUENCE, "f1", ACTION_SKIP)],
        )

    def test_clean_children_skip_existing_targets_and_save_missing_targets(self):
        with tempfile.TemporaryDirectory() as root:
            data = make_data()
            targets = self._targets(root, data)
            os.makedirs(os.path.dirname(targets[(CHILD_KEYMAP, "km1")]), exist_ok=True)
            JsonRepository().save_json(targets[(CHILD_KEYMAP, "km1")], {})
            plan = build_save_plan(data=data, rows=[], choices={}, targets=targets)

        self.assertEqual(plan.entry_for(CHILD_KEYMAP, "km1").action, ACTION_SKIP)
        self.assertEqual(plan.entry_for(CHILD_TRIGGER_SET).action, ACTION_SAVE)
        self.assertEqual(plan.entry_for(CHILD_SEQUENCE, "f1").action, ACTION_SAVE)

    def test_empty_rows_create_all_entries_and_existing_children_skip(self):
        with tempfile.TemporaryDirectory() as root:
            data = make_data()
            targets = self._targets(root, data)
            for target in targets.values():
                os.makedirs(os.path.dirname(target), exist_ok=True)
                JsonRepository().save_json(target, {})
            plan = build_save_plan(data=data, rows=[], choices={}, targets=targets)

        self.assertEqual(len(plan.entries), 3)
        self.assertTrue(all(entry.action == ACTION_SKIP for entry in plan.entries))

    def test_plan_has_no_duplicates_and_passes_application_validation(self):
        with tempfile.TemporaryDirectory() as root:
            data = make_data()
            targets = self._targets(root, data)
            plan = build_save_plan(data=data, rows=[], choices={}, targets=targets)
            self.service.save_runtime_data(
                os.path.join(root, "user", "keymap_sets", "main.json"),
                data,
                config_root=root,
                startup_data={},
                save_plan=plan,
            )

        self.assertEqual(len(plan.entries), len({(entry.kind, entry.key) for entry in plan.entries}))


if __name__ == "__main__":
    unittest.main()
