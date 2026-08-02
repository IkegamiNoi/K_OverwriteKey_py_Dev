import ntpath
import os
import tempfile
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_NEW,
    SHARE_NEW_COLLIDES,
    SHARE_OTHER_PARENT,
    SHARE_SHARED,
    SHARE_SOLE,
    SHARE_UNKNOWN,
    collect_child_save_rows,
    default_action_for,
    judge_share_state,
    share_text_for,
    _stored_parent_path,
)


class DummyDirtyTracker:
    def __init__(self, *, trigger_set_dirty=False):
        self.trigger_set_dirty = trigger_set_dirty


def make_runtime_data():
    return {
        "keymaps": [
            {"id": "km1", "label": "Main", "mappings": {}, "_keymap_dirty": True},
            {"id": "km2", "label": "", "mappings": {}, "_keymap_dirty": False},
        ],
        "triggers": [
            {"key": "f1", "label": "Copy", "actions": [], "_sequence_dirty": True},
            {"key": "f2", "label": "", "actions": [], "_sequence_dirty": False},
        ],
    }


class ChildSaveRowsTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_collects_only_dirty_children_in_stable_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            rows = collect_child_save_rows(
                data=make_runtime_data(),
                dirty_tracker=DummyDirtyTracker(trigger_set_dirty=True),
                config_service=self.service,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )

            self.assertEqual(
                [(row.kind, row.key, row.display_name) for row in rows],
                [
                    (CHILD_KEYMAP, "km1", "Main"),
                    (CHILD_TRIGGER_SET, "", "トリガー一覧"),
                    (CHILD_SEQUENCE, "f1", "Copy"),
                ],
            )
            self.assertTrue(all(row.share_state == SHARE_NEW for row in rows))
            self.assertTrue(all(row.default_action == ACTION_SAVE for row in rows))

    def test_returns_no_rows_when_no_child_is_dirty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            data = make_runtime_data()
            data["keymaps"][0]["_keymap_dirty"] = False
            data["triggers"][0]["_sequence_dirty"] = False

            rows = collect_child_save_rows(
                data=data,
                dirty_tracker=DummyDirtyTracker(),
                config_service=self.service,
                config_root=root,
                keymap_set_path=os.path.join(root, "user", "keymap_sets", "main.json"),
            )

            self.assertEqual(rows, [])

    def test_share_states_text_and_safe_default_actions(self):
        cases = (
            (None, "parent.json", True, SHARE_UNKNOWN),
            ([], "parent.json", True, SHARE_UNKNOWN),
            (["parent.json"], "parent.json", True, SHARE_SOLE),
            (["parent.json", "other.json"], "parent.json", True, SHARE_SHARED),
            (["other.json"], "parent.json", True, SHARE_OTHER_PARENT),
            (None, "parent.json", False, SHARE_NEW),
            (["parent.json"], "", True, SHARE_UNKNOWN),
        )
        for refs, current_parent, target_exists, expected in cases:
            with self.subTest(expected=expected):
                state = judge_share_state(refs, current_parent, target_exists=target_exists)
                self.assertEqual(state, expected)
                expected_action = (
                    ACTION_SAVE_AS
                    if expected in (SHARE_UNKNOWN, SHARE_OTHER_PARENT)
                    else ACTION_SAVE
                )
                self.assertEqual(default_action_for(state), expected_action)

        self.assertIn("2", share_text_for(SHARE_SHARED, 2))

    def test_share_text_for_sole_explicitly_describes_overwrite(self):
        self.assertEqual(
            share_text_for(SHARE_SOLE, 1),
            "この構成のみが所有・既存を上書き",
        )

    def test_collect_sole_owned_existing_child_uses_overwrite_text_and_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            data = make_runtime_data()
            data["triggers"][0]["_sequence_dirty"] = False
            target = self.service.resolve_child_save_targets(
                data,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )[(CHILD_KEYMAP, "km1")]
            data["keymaps"][0][self.service.INTERNAL_KEYMAP_SOURCE_PATH] = target
            JsonRepository().save_json(
                target,
                {
                    "_parent_refs": [
                        self.service.to_config_relative_or_absolute(keymap_set_path, root)
                    ]
                },
            )

            rows = collect_child_save_rows(
                data=data,
                dirty_tracker=DummyDirtyTracker(),
                config_service=self.service,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )

            row = rows[0]
            self.assertEqual(row.share_state, SHARE_SOLE)
            self.assertEqual(row.share_text, "この構成のみが所有・既存を上書き")
            self.assertEqual(row.default_action, ACTION_SAVE)

    def test_collect_normalizes_parent_paths_uses_trigger_set_parent_and_scopes_new_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            data = make_runtime_data()
            targets = self.service.resolve_child_save_targets(
                data,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )
            keymap_target = targets[(CHILD_KEYMAP, "km1")]
            trigger_set_target = targets[(CHILD_TRIGGER_SET, "")]
            sequence_target = targets[(CHILD_SEQUENCE, "f1")]
            JsonRepository().save_json(
                keymap_target,
                {"_parent_refs": ["user\\keymap_sets\\main.json"]},
            )
            JsonRepository().save_json(
                trigger_set_target,
                {"_parent_refs": ["user/keymap_sets/main.json", "other.json"]},
            )
            JsonRepository().save_json(
                sequence_target,
                {
                    "_parent_refs": [
                        self.service.to_config_relative_or_absolute(trigger_set_target, root)
                    ]
                },
            )

            rows = collect_child_save_rows(
                data=data,
                dirty_tracker=DummyDirtyTracker(trigger_set_dirty=True),
                config_service=self.service,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )
            rows_by_kind = {row.kind: row for row in rows}

            # New keymaps and sequences avoid overwriting an existing sole-owned target.
            self.assertEqual(rows_by_kind[CHILD_KEYMAP].share_state, SHARE_NEW_COLLIDES)
            self.assertEqual(rows_by_kind[CHILD_TRIGGER_SET].share_state, SHARE_SHARED)
            self.assertEqual(rows_by_kind[CHILD_SEQUENCE].share_state, SHARE_NEW_COLLIDES)

    def test_absolute_parent_ref_and_relative_parent_share_canonical_identity(self):
        with patch("keyseq.application.config_service.os.path", ntpath):
            root = r"c:\config"
            stored_ref = _stored_parent_path(
                self.service,
                r"C:\CONFIG\user\keymap_sets\main.json",
                root,
            )
            current_parent = _stored_parent_path(
                self.service,
                r"user\keymap_sets\main.json",
                root,
            )

            self.assertEqual(
                judge_share_state(
                    [stored_ref],
                    current_parent,
                    target_exists=True,
                    config_service=self.service,
                    config_root=root,
                ),
                SHARE_SOLE,
            )

    def test_collect_treats_missing_or_empty_parent_refs_as_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            data = make_runtime_data()
            target = self.service.resolve_child_save_targets(
                data,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )[(CHILD_KEYMAP, "km1")]

            for payload in ({"label": "legacy"}, {"_parent_refs": []}):
                JsonRepository().save_json(target, payload)
                rows = collect_child_save_rows(
                    data=data,
                    dirty_tracker=DummyDirtyTracker(),
                    config_service=self.service,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                )
                self.assertEqual(rows[0].share_state, SHARE_UNKNOWN)
                self.assertEqual(rows[0].default_action, ACTION_SAVE_AS)

    def test_resolved_targets_match_default_save_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            data = make_runtime_data()
            targets = self.service.resolve_child_save_targets(
                data,
                config_root=root,
                keymap_set_path=keymap_set_path,
            )

            self.service.save_runtime_data(
                keymap_set_path,
                data,
                config_root=root,
                startup_data={},
            )

            for path in targets.values():
                self.assertTrue(os.path.exists(path), path)

    def test_read_parent_refs_returns_none_for_unavailable_or_invalid_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = os.path.join(tmp, "missing.json")
            invalid_path = os.path.join(tmp, "invalid.json")
            no_refs_path = os.path.join(tmp, "no_refs.json")
            with open(invalid_path, "w", encoding="utf-8") as stream:
                stream.write("{")
            JsonRepository().save_json(no_refs_path, {"label": "no refs"})

            self.assertIsNone(self.service.read_parent_refs(missing_path))
            self.assertIsNone(self.service.read_parent_refs(invalid_path))
            self.assertIsNone(self.service.read_parent_refs(no_refs_path))


if __name__ == "__main__":
    unittest.main()
