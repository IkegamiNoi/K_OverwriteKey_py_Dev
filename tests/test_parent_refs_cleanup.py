import copy
import os
import tempfile
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service.contracts import (
    CLEANUP_ALL_STALE,
    CLEANUP_PROTECTED,
    CLEANUP_TARGET,
    PRUNE_FAILURE_INVALID_DATA,
    PRUNE_FAILURE_SAVE_FAILED,
    PRUNE_FAILURE_UNREADABLE,
)
from keyseq.application.config_service.parent_refs_cleanup import (
    inspect_parent_refs,
    prune_parent_refs,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_SHARED,
    SHARE_SOLE,
    judge_share_state,
)


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
                {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []},
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
                    "keymaps": [self._keymap(path, keymap_id=f"km{index}")
                                for index, path in enumerate(source_paths, 1)],
                    "active_keymap_id": "km1",
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
                {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []},
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
                    "active_keymap_id": "km1",
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
                    "keymaps": [self._keymap("", triggers=[self._sequence(sequence_path)])],
                    "active_keymap_id": "km1",
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: missing_trigger_set_path,
                    "triggers": [],
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
                        self._keymap(all_stale_path, keymap_id="km2"),
                        self._keymap(protected_path, keymap_id="km3"),
                    ],
                    "active_keymap_id": "km1",
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
                        self._keymap("", triggers=[
                            {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: ""},
                            {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: []},
                        ]),
                        self._keymap(None, keymap_id="km2"),
                    ],
                    "active_keymap_id": "km1",
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: 1,
                    "triggers": [],
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
                    "keymaps": [self._keymap("", triggers=[
                        self._sequence(sequence_path),
                        self._sequence(sequence_path.replace("\\", "/")),
                    ])],
                    "active_keymap_id": "km1",
                    "triggers": [],
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
                    "keymaps": [self._keymap(keymap_path, triggers=[self._sequence(sequence_path)])],
                    "active_keymap_id": "km1",
                    self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: trigger_set_path,
                    "triggers": [],
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
                {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []},
            )

            self.assertEqual(inspections[0].state, CLEANUP_ALL_STALE)
            self.assertEqual(self._read_bytes(child_path), before)

    def test_prune_removes_only_stale_refs_and_preserves_runtime(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            alive_path = os.path.join(root, "user", "keymap_sets", "alive.json")
            alive_ref = "user\\keymap_sets\\alive.json"
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(alive_path, {"keymaps": []})
            self._save(child_path, {"_parent_refs": ["missing.json", alive_ref]})
            before_runtime = copy.deepcopy(runtime)
            keymaps = runtime["keymaps"]
            keymap = keymaps[0]
            triggers = keymap["triggers"]

            inspections = self._inspect(root, runtime)
            self.assertEqual(runtime, before_runtime)
            result = self._prune(root, inspections, runtime)

            self.assertEqual(result.updated_files, ((child_path, 1),))
            self.assertEqual(result.failed_files, ())
            self.assertEqual(self.service.read_parent_refs(child_path), [alive_ref])
            self.assertEqual(runtime, before_runtime)
            self.assertIs(runtime["keymaps"], keymaps)
            self.assertIs(runtime["keymaps"][0], keymap)
            self.assertIs(runtime["keymaps"][0]["triggers"], triggers)

    def test_prune_changes_share_state_from_shared_to_sole(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "current.json")
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(keymap_set_path, {"keymaps": []})
            self._save(
                child_path,
                {"_parent_refs": [keymap_set_path, "missing-keymap-set.json"]},
            )

            before_state = judge_share_state(
                self.service.read_parent_refs(child_path),
                keymap_set_path,
                target_exists=True,
                config_service=self.service,
                config_root=root,
            )
            inspections = self._inspect(
                root,
                runtime,
                keymap_set_path=keymap_set_path,
            )
            self._prune(
                root,
                inspections,
                runtime,
                keymap_set_path=keymap_set_path,
            )
            after_state = judge_share_state(
                self.service.read_parent_refs(child_path),
                keymap_set_path,
                target_exists=True,
                config_service=self.service,
                config_root=root,
            )

            self.assertEqual(before_state, SHARE_SHARED)
            self.assertEqual(after_state, SHARE_SOLE)

    def test_prune_writes_empty_list_without_removing_parent_refs_key(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(child_path, {"label": "Main", "_parent_refs": ["missing.json"]})

            result = self._prune(root, self._inspect(root, runtime), runtime)

            self.assertEqual(result.updated_files, ((child_path, 1),))
            payload = self.service._load_optional_json(child_path)
            self.assertIn(self.service.PARENT_REFS_KEY, payload)
            self.assertEqual(payload[self.service.PARENT_REFS_KEY], [])

    def test_prune_retains_missing_current_keymap_set_and_trigger_set_refs(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "current.json")
            trigger_set_path = os.path.join(root, "user", "trigger_sets", "current.json")
            keymap_path = os.path.join(root, "user", "keymaps", "main.json")
            sequence_path = os.path.join(root, "user", "sequences", "copy.json")
            self._save(keymap_path, {"_parent_refs": [keymap_set_path, "missing-keymap-set.json"]})
            self._save(sequence_path, {"_parent_refs": [trigger_set_path, "missing-trigger-set.json"]})
            runtime = {
                "keymaps": [self._keymap(keymap_path, triggers=[self._sequence(sequence_path)])],
                "active_keymap_id": "km1",
                self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: trigger_set_path,
                "triggers": [],
            }

            result = self._prune(
                root,
                self._inspect(root, runtime, keymap_set_path=keymap_set_path),
                runtime,
                keymap_set_path=keymap_set_path,
            )

            self.assertEqual(result.updated_files, ((keymap_path, 1), (sequence_path, 1)))
            self.assertEqual(
                self.service.read_parent_refs(keymap_path),
                [keymap_set_path],
            )
            self.assertEqual(
                self.service.read_parent_refs(sequence_path),
                [trigger_set_path],
            )

    def test_prune_keeps_other_keys_from_the_pre_save_reload(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(
                child_path,
                {"label": "Before", "nested": {"version": 1}, "_parent_refs": ["missing.json"]},
            )
            inspections = self._inspect(root, runtime)
            self._save(
                child_path,
                {"label": "After", "nested": {"version": 2}, "_parent_refs": ["missing.json"]},
            )

            self._prune(root, inspections, runtime)

            self.assertEqual(
                self.service._load_optional_json(child_path),
                {"label": "After", "nested": {"version": 2}, "_parent_refs": []},
            )

    def test_prune_does_not_write_when_stale_ref_was_resolved_before_reload(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            parent_path = os.path.join(root, "missing.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(child_path, {"_parent_refs": ["missing.json"]})
            inspections = self._inspect(root, runtime)
            self._save(parent_path, {"keymaps": []})
            before = self._read_bytes(child_path)

            result = self._prune(root, inspections, runtime)

            self.assertEqual(result.updated_files, ())
            self.assertEqual(result.failed_files, ())
            self.assertEqual(self._read_bytes(child_path), before)

    def test_prune_skips_when_parent_refs_becomes_unknown_before_reload(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(child_path, {"_parent_refs": ["missing.json"]})
            inspections = self._inspect(root, runtime)
            self._save(child_path, {"label": "Legacy", "_parent_refs": None})
            before = self._read_bytes(child_path)

            result = self._prune(root, inspections, runtime)

            self.assertEqual(result.updated_files, ())
            self.assertEqual(result.failed_files, ())
            self.assertEqual(self._read_bytes(child_path), before)

    def test_prune_is_idempotent_for_the_same_inspections(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(child_path, {"_parent_refs": ["missing.json"]})
            inspections = self._inspect(root, runtime)

            first_result = self._prune(root, inspections, runtime)
            before_second_prune = self._read_bytes(child_path)
            second_result = self._prune(root, inspections, runtime)

            self.assertEqual(first_result.updated_files, ((child_path, 1),))
            self.assertEqual(second_result.updated_files, ())
            self.assertEqual(second_result.failed_files, ())
            self.assertEqual(self._read_bytes(child_path), before_second_prune)

    def test_prune_records_reload_failures_and_continues(self):
        with tempfile.TemporaryDirectory() as root:
            unreadable_path = os.path.join(root, "user", "keymaps", "unreadable.json")
            invalid_path = os.path.join(root, "user", "keymaps", "invalid.json")
            valid_path = os.path.join(root, "user", "keymaps", "valid.json")
            runtime = {
                "keymaps": [
                    self._keymap(unreadable_path),
                    self._keymap(invalid_path, keymap_id="km2"),
                    self._keymap(valid_path, keymap_id="km3"),
                ],
                "active_keymap_id": "km1",
                "triggers": [],
            }
            for child_path in (unreadable_path, invalid_path, valid_path):
                self._save(child_path, {"_parent_refs": ["missing.json"]})
            inspections = self._inspect(root, runtime)
            with open(unreadable_path, "w", encoding="utf-8") as stream:
                stream.write("{")
            self._save(invalid_path, ["not a child JSON"])

            result = self._prune(root, inspections, runtime)

            self.assertEqual(result.updated_files, ((valid_path, 1),))
            self.assertEqual(
                result.failed_files,
                (
                    (unreadable_path, PRUNE_FAILURE_UNREADABLE),
                    (invalid_path, PRUNE_FAILURE_INVALID_DATA),
                ),
            )
            self.assertEqual(self.service.read_parent_refs(valid_path), [])

    def test_prune_records_save_failures_and_continues(self):
        with tempfile.TemporaryDirectory() as root:
            failing_path = os.path.join(root, "user", "keymaps", "failing.json")
            valid_path = os.path.join(root, "user", "keymaps", "valid.json")
            runtime = {
                "keymaps": [self._keymap(failing_path), self._keymap(valid_path, keymap_id="km3")],
                "active_keymap_id": "km1",
                "triggers": [],
            }
            self._save(failing_path, {"_parent_refs": ["missing.json"]})
            self._save(valid_path, {"_parent_refs": ["missing.json"]})
            original_save_json = self.service.repository.save_json

            def save_json(path, data):
                if path == failing_path:
                    raise OSError("cannot save")
                original_save_json(path, data)

            with patch.object(self.service.repository, "save_json", side_effect=save_json):
                result = self._prune(root, self._inspect(root, runtime), runtime)

            self.assertEqual(result.updated_files, ((valid_path, 1),))
            self.assertEqual(
                result.failed_files,
                ((failing_path, PRUNE_FAILURE_SAVE_FAILED),),
            )
            self.assertEqual(self.service.read_parent_refs(valid_path), [])

    def test_prune_does_not_write_protected_only_inspection(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "current.json")
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            self._save(child_path, {"_parent_refs": [keymap_set_path]})
            inspections = self._inspect(root, runtime, keymap_set_path=keymap_set_path)
            before = self._read_bytes(child_path)

            result = self._prune(
                root,
                inspections,
                runtime,
                keymap_set_path=keymap_set_path,
            )

            self.assertEqual(inspections[0].state, CLEANUP_PROTECTED)
            self.assertEqual(result.updated_files, ())
            self.assertEqual(result.failed_files, ())
            self.assertEqual(self._read_bytes(child_path), before)

    def test_config_service_cleanup_delegates_match_module_functions(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "user", "keymaps", "main.json")
            runtime = {"keymaps": [self._keymap(child_path)], "active_keymap_id": "km1", "triggers": []}
            payload = {"_parent_refs": ["missing.json"]}
            self._save(child_path, payload)

            module_inspections = inspect_parent_refs(
                self.service,
                runtime,
                config_root=root,
                keymap_set_path="",
            )
            delegated_inspections = self.service.inspect_parent_refs(
                runtime,
                config_root=root,
                keymap_set_path="",
            )
            module_result = prune_parent_refs(
                self.service,
                module_inspections,
                runtime=runtime,
                config_root=root,
                keymap_set_path="",
            )
            self._save(child_path, payload)
            delegated_result = self.service.prune_parent_refs(
                delegated_inspections,
                runtime=runtime,
                config_root=root,
                keymap_set_path="",
            )

            self.assertEqual(delegated_inspections, module_inspections)
            self.assertEqual(delegated_result, module_result)
            self.assertEqual(self.service.read_parent_refs(child_path), [])

    def _inspect(self, root, runtime, *, keymap_set_path=""):
        return inspect_parent_refs(
            self.service,
            runtime,
            config_root=root,
            keymap_set_path=keymap_set_path,
        )

    def _prune(self, root, inspections, runtime, *, keymap_set_path=""):
        return prune_parent_refs(
            self.service,
            inspections,
            runtime=runtime,
            config_root=root,
            keymap_set_path=keymap_set_path,
        )

    def _keymap(self, path, *, keymap_id="km1", triggers=None):
        return {
            "id": keymap_id, "label": "", "mappings": {},
            "triggers": [] if triggers is None else triggers,
            self.service.INTERNAL_KEYMAP_SOURCE_PATH: path,
        }

    def _sequence(self, path):
        return {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: path}

    def _save(self, path, payload):
        self.repository.save_json(path, payload)

    def _read_bytes(self, path):
        with open(path, "rb") as stream:
            return stream.read()


if __name__ == "__main__":
    unittest.main()
