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
    ChildSaveEntry,
    SavePlan,
    SavePlanError,
)
from keyseq.infrastructure.json_repository import JsonRepository


def make_data():
    return {
        "keymaps": [{"id": "km1", "label": "Main", "mappings": {}}],
        "triggers": [{"key": "f1", "label": "Copy", "actions": []}],
        "active_keymap_id": "km1",
    }


class DependencyQueryTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _paths(self, root):
        return root, os.path.join(root, "user", "keymap_sets", "main.json")

    def _plan(self, sequence_action, *, sequence_target=""):
        return SavePlan(entries=(
            ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SAVE),
            ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),
            ChildSaveEntry(CHILD_SEQUENCE, "f1", sequence_action, sequence_target),
        ))

    def test_skip_trigger_set_blocks_save_as_and_query_does_not_write(self):
        with tempfile.TemporaryDirectory() as root:
            config_root, keymap_set_path = self._paths(root)
            plan = self._plan(ACTION_SAVE_AS, sequence_target=os.path.join(root, "renamed.json"))
            before = list(os.walk(root))
            blocked = self.service.find_dependency_blocked_sequences(
                make_data(), config_root=config_root, keymap_set_path=keymap_set_path, save_plan=plan
            )
            after = list(os.walk(root))

        self.assertEqual(blocked, ["f1"])
        self.assertEqual(before, after)

    def test_skip_trigger_set_blocks_first_sequence_save(self):
        with tempfile.TemporaryDirectory() as root:
            config_root, keymap_set_path = self._paths(root)
            blocked = self.service.find_dependency_blocked_sequences(
                make_data(),
                config_root=config_root,
                keymap_set_path=keymap_set_path,
                save_plan=self._plan(ACTION_SAVE),
            )

        self.assertEqual(blocked, ["f1"])

    def test_saved_trigger_set_has_no_dependency_block(self):
        with tempfile.TemporaryDirectory() as root:
            config_root, keymap_set_path = self._paths(root)
            plan = SavePlan(entries=(
                ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SAVE),
                ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SAVE),
                ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SAVE_AS, os.path.join(root, "renamed.json")),
            ))
            blocked = self.service.find_dependency_blocked_sequences(
                make_data(), config_root=config_root, keymap_set_path=keymap_set_path, save_plan=plan
            )

        self.assertEqual(blocked, [])

    def test_query_and_save_validation_share_dependency_rule(self):
        with tempfile.TemporaryDirectory() as root:
            config_root, keymap_set_path = self._paths(root)
            plan = self._plan(ACTION_SAVE_AS, sequence_target=os.path.join(root, "renamed.json"))
            self.assertEqual(
                self.service.find_dependency_blocked_sequences(
                    make_data(), config_root=config_root, keymap_set_path=keymap_set_path, save_plan=plan
                ),
                ["f1"],
            )
            with self.assertRaises(SavePlanError):
                self.service.save_runtime_data(
                    keymap_set_path, make_data(), config_root=config_root, startup_data={}, save_plan=plan
                )

    def test_resolve_targets_uses_trigger_set_save_as_plan(self):
        with tempfile.TemporaryDirectory() as root:
            config_root, keymap_set_path = self._paths(root)
            external_trigger_set = os.path.join(root, "external", "trigger_set.json")
            plan = SavePlan(entries=(
                ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SAVE_AS, external_trigger_set),
            ))
            default_targets = self.service.resolve_child_save_targets(
                make_data(), config_root=config_root, keymap_set_path=keymap_set_path
            )
            planned_targets = self.service.resolve_child_save_targets(
                make_data(), config_root=config_root, keymap_set_path=keymap_set_path, save_plan=plan
            )

        # slugify_file_stem は大文字小文字を変換しないため、label "Copy" → "Copy.json"
        self.assertEqual(
            default_targets[(CHILD_SEQUENCE, "f1")],
            os.path.join(config_root, "user", "sequences", "Copy.json"),
        )
        self.assertEqual(
            planned_targets[(CHILD_SEQUENCE, "f1")],
            os.path.join(root, "external", "sequences", "Copy.json"),
        )


if __name__ == "__main__":
    unittest.main()
