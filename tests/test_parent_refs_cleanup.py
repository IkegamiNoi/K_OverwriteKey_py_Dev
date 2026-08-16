import os
import tempfile
import unittest

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service.parent_refs_cleanup import (
    CLEANUP_ALL_STALE,
    CLEANUP_PROTECTED,
    CLEANUP_TARGET,
    inspect_parent_refs,
)
from keyseq.infrastructure.json_repository import JsonRepository


class ParentRefsCleanupTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())
        self.repository = JsonRepository()

    def test_existing_parent_refs_are_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            alive_parent = os.path.join(root, "user", "keymap_sets", "main.json")
            self._save(child_path, {"_parent_refs": ["user/keymap_sets/main.json"]})
            self._save(alive_parent, {"keymaps": []})

            inspections = self._inspect(
                root,
                {"keymaps": [self._keymap(child_path)], "triggers": []},
            )

            self.assertEqual(inspections, [])

    def test_unknown_empty_and_invalid_parent_refs_are_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            source_paths = []
            for name, payload in (
                ("missing.json", {"label": "legacy"}),
                ("none.json", {"_parent_refs": None}),
                ("empty.json", {"_parent_refs": []}),
                ("invalid.json", {"_parent_refs": "parent.json"}),
            ):
                child_path = os.path.join(root, "user", "keymaps", name)
                self._save(child_path, payload)
                source_paths.append(child_path)

            inspections = self._inspect(
                root,
                {
                    "keymaps": [self._keymap(path) for path in source_paths],
                    "triggers": [],
                },
            )

            self.assertEqual(inspections, [])

    def test_relative_absolute_and_separator_variants_are_resolved_before_exists(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            relative_parent = os.path.join(root, "user", "keymap_sets", "relative.json")
            absolute_parent = os.path.join(root, "user", "keymap_sets", "absolute.json")
            self._save(relative_parent, {"keymaps": []})
            self._save(absolute_parent, {"keymaps": []})
            self._save(
                child_path,
                {
                    "_parent_refs": [
                        "user\\keymap_sets\\relative.json",
                        absolute_parent.replace("\\", "/"),
                    ]
                },
            )

            inspections = self._inspect(
                root,
                {"keymaps": [self._keymap(child_path)], "triggers": []},
            )

            self.assertEqual(inspections, [])

    def test_current_keymap_set_and_trigger_set_refs_are_protected_when_missing(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "current.json")
            trigger_set_path = os.path.join(root, "user", "trigger_sets", "current.json")
            missing_trigger_set_path = "user/trigger_sets/missing.json"
            keymap_path = os.path.join(root, "user", "keymaps", "main.json")
            sequence_path = os.path.join(root, "user", "sequences", "copy.json")
            self._save(keymap_path, {"_parent_refs": [keymap_set_path.replace("\\", "/")]})
            self._save(trigger_set_path, {"_parent_refs": ["user\\keymap_sets\\current.json"]})
            self._save(
                sequence_path,
                {"_parent_refs": [missing_trigger_set_path.replace("/", "\\")]},
            )

            inspections = self._inspect(
                root,
                {
                    "keymaps": [self._keymap(keymap_path)],
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: trigger_set_path,
                    "triggers": [],
                },
                keymap_set_path=keymap_set_path,
            )

            self.assertEqual([item.state for item in inspections], [CLEANUP_PROTECTED] * 2)
            self.assertEqual(inspections[0].protected_refs, (keymap_set_path.replace("\\", "/"),))
            self.assertEqual(inspections[1].protected_refs, ("user\\keymap_sets\\current.json",))
            self.assertEqual(inspections[0].stale_refs, ())
            self.assertEqual(inspections[1].stale_refs, ())

            sequence_inspections = self._inspect(
                root,
                {
                    "keymaps": [],
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: missing_trigger_set_path,
                    "triggers": [self._sequence(sequence_path)],
                },
            )

            self.assertEqual([item.state for item in sequence_inspections], [CLEANUP_PROTECTED])
            self.assertEqual(
                sequence_inspections[0].protected_refs,
                (missing_trigger_set_path.replace("/", "\\"),),
            )

    def test_cleanup_states_follow_priority_order(self):
        with tempfile.TemporaryDirectory() as root:
            alive_parent = os.path.join(root, "user", "keymap_sets", "alive.json")
            protected_parent = os.path.join(root, "user", "keymap_sets", "current.json")
            target_path = os.path.join(root, "user", "keymaps", "target.json")
            all_stale_path = os.path.join(root, "user", "keymaps", "all-stale.json")
            protected_path = os.path.join(root, "user", "keymaps", "protected.json")
            self._save(alive_parent, {"keymaps": []})
            self._save(
                target_path,
                {"_parent_refs": ["user/keymap_sets/alive.json", "missing.json"]},
            )
            self._save(all_stale_path, {"_parent_refs": ["missing.json"]})
            self._save(
                protected_path,
                {"_parent_refs": [protected_parent, "also-missing.json"]},
            )

            inspections = self._inspect(
                root,
                {
                    "keymaps": [
                        self._keymap(target_path),
                        self._keymap(all_stale_path),
                        self._keymap(protected_path),
                    ],
                    "triggers": [],
                },
                keymap_set_path=protected_parent,
            )

            self.assertEqual(
                [item.state for item in inspections],
                [CLEANUP_TARGET, CLEANUP_ALL_STALE, CLEANUP_TARGET],
            )
            self.assertEqual(inspections[0].stale_refs, ("missing.json",))
            self.assertEqual(inspections[1].stale_refs, ("missing.json",))
            self.assertEqual(inspections[2].protected_refs, (protected_parent,))
            self.assertEqual(inspections[2].stale_refs, ("also-missing.json",))

    def test_empty_source_paths_are_not_inspected_even_when_default_file_exists(self):
        with tempfile.TemporaryDirectory() as root:
            unrelated_path = os.path.join(root, "user", "keymaps", "unrelated.json")
            self._save(unrelated_path, {"_parent_refs": ["missing.json"]})

            inspections = self._inspect(
                root,
                {
                    "keymaps": [
                        {self.service.INTERNAL_KEYMAP_SOURCE_PATH: ""},
                        {self.service.INTERNAL_KEYMAP_SOURCE_PATH: None},
                    ],
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: 1,
                    "triggers": [
                        {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: ""},
                        {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: []},
                    ],
                },
            )

            self.assertEqual(inspections, [])

    def test_shared_sequence_source_is_inspected_once(self):
        with tempfile.TemporaryDirectory() as root:
            sequence_path = os.path.join(root, "user", "sequences", "shared.json")
            self._save(sequence_path, {"_parent_refs": ["missing-trigger-set.json"]})

            inspections = self._inspect(
                root,
                {
                    "keymaps": [],
                    "triggers": [
                        self._sequence(sequence_path),
                        self._sequence(sequence_path.replace("\\", "/")),
                    ],
                },
            )

            self.assertEqual(len(inspections), 1)
            self.assertEqual(inspections[0].kind, "sequence")
            self.assertEqual(inspections[0].stored_path, sequence_path)

    def test_children_are_enumerated_in_keymap_trigger_set_sequence_order(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_path = os.path.join(root, "user", "keymaps", "main.json")
            trigger_set_path = os.path.join(root, "user", "trigger_sets", "main.json")
            sequence_path = os.path.join(root, "user", "sequences", "main.json")
            for child_path in (keymap_path, trigger_set_path, sequence_path):
                self._save(child_path, {"_parent_refs": ["missing.json"]})

            inspections = self._inspect(
                root,
                {
                    "keymaps": [self._keymap(keymap_path)],
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: trigger_set_path,
                    "triggers": [self._sequence(sequence_path)],
                },
            )

            self.assertEqual(
                [(item.kind, item.stored_path) for item in inspections],
                [
                    ("keymap", keymap_path),
                    ("trigger_set", trigger_set_path),
                    ("sequence", sequence_path),
                ],
            )

    def test_inspection_does_not_modify_child_json(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            self._save(child_path, {"label": "Main", "_parent_refs": ["missing.json"]})
            before = self._read_bytes(child_path)

            inspections = self._inspect(
                root,
                {"keymaps": [self._keymap(child_path)], "triggers": []},
            )

            self.assertEqual(inspections[0].state, CLEANUP_ALL_STALE)
            self.assertEqual(self._read_bytes(child_path), before)

    def _inspect(self, root, runtime, *, keymap_set_path=""):
        return inspect_parent_refs(
            self.service,
            runtime,
            config_root=root,
            keymap_set_path=keymap_set_path,
        )

    def _keymap(self, path):
        return {self.service.INTERNAL_KEYMAP_SOURCE_PATH: path}

    def _sequence(self, path):
        return {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: path}

    def _save(self, path, payload):
        self.repository.save_json(path, payload)

    def _read_bytes(self, path):
        with open(path, "rb") as stream:
            return stream.read()


if __name__ == "__main__":
    unittest.main()
