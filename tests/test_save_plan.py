import os
import tempfile
import unittest

from keyseq.application.config_service import ConfigService, split_payloads
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


def _read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def make_runtime_data():
    return {
        "triggers": [
            {
                "key": "f1",
                "suppress": True,
                "label": "copy",
                "run_to_end": False,
                "run_to_end_delay_ms": 300,
                "actions": [{"type": "text", "value": "hello", "label": ""}],
            }
        ],
        "hotkey_presets": [{"label": "Alt+Tab", "value": "alt+tab"}],
        "hook_stop_key": "f12",
        "hook_toggle_key": "",
        "keyboard_layout": "us_tkl",
        "keyboard_show_physical_key_labels": False,
        "debug_jis_special_key_events": False,
        "external_keyboard_layouts": [],
        "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}}],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"1": "km1"},
    }


class RecordingRepository(JsonRepository):
    def __init__(self):
        self.saved_paths: list[str] = []
        self.fail_path = ""

    def save_json(self, path, data):
        self.saved_paths.append(path)
        if self.fail_path and os.path.normcase(path) == os.path.normcase(self.fail_path):
            raise OSError("simulated write failure")
        super().save_json(path, data)


class SavePlanTest(unittest.TestCase):
    def setUp(self):
        self.repository = RecordingRepository()
        self.service = ConfigService(self.repository)

    def _save(self, root, data=None, plan=None):
        return self.service.save_runtime_data(
            os.path.join(root, "user", "keymap_sets", "main.json"),
            data or make_runtime_data(),
            config_root=root,
            startup_data={},
            save_plan=plan,
        )

    def _build_keymap_set_payload(self, runtime):
        return split_payloads.build_keymap_set_payload(
            self.service,
            runtime,
            {"km1": "user/keymaps/km1.json"},
            config_root="",
            trigger_set_path="user/trigger_sets/main.json",
            hotkey_presets_path="user/hotkey_presets/default.json",
        )

    def test_none_and_empty_plan_have_equivalent_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            none_root = os.path.join(tmp, "none")
            empty_root = os.path.join(tmp, "empty")
            self._save(none_root)
            self._save(empty_root, plan=SavePlan())

            relative_paths = (
                "config.json",
                os.path.join("user", "keymap_sets", "main.json"),
                os.path.join("user", "trigger_sets", "main.json"),
                os.path.join("user", "hotkey_presets", "default.json"),
                os.path.join("user", "keymaps", "km1.json"),
                os.path.join("user", "sequences", "copy.json"),
            )
            for relative_path in relative_paths:
                self.assertEqual(
                    JsonRepository().load_json(os.path.join(none_root, relative_path)),
                    JsonRepository().load_json(os.path.join(empty_root, relative_path)),
                )
            self.assertEqual(
                JsonRepository().load_json(
                    os.path.join(none_root, "user", "keymap_sets", "main.json")
                ),
                {
                    "trigger_set_path": "user/trigger_sets/main.json",
                    "hotkey_presets_path": "user/hotkey_presets/default.json",
                    "active_keymap_path": "user/keymaps/km1.json",
                    "keymaps": [{"path": "user/keymaps/km1.json", "switch_key": "1"}],
                    "hook_stop_key": "f12",
                    "hook_toggle_key": "",
                    "hook_keys_individual": True,
                    "keyboard_layout": "us_tkl",
                    "keyboard_show_physical_key_labels": False,
                    "debug_jis_special_key_events": False,
                    "external_keyboard_layouts": [],
                },
            )

            self.assertEqual(
                JsonRepository().load_json(
                    os.path.join(none_root, "user", "trigger_sets", "main.json")
                ),
                {
                    "triggers": [
                        {
                            "key": "f1",
                            "suppress": True,
                            "sequence_path": "user/sequences/copy.json",
                        }
                    ],
                    "_parent_refs": ["user/keymap_sets/main.json"],
                },
            )
            self.assertEqual(
                JsonRepository().load_json(
                    os.path.join(none_root, "user", "keymaps", "km1.json")
                ),
                {
                    "label": "Main",
                    "mappings": {"a": "b"},
                    "_parent_refs": ["user/keymap_sets/main.json"],
                },
            )
            self.assertEqual(
                JsonRepository().load_json(
                    os.path.join(none_root, "user", "sequences", "copy.json")
                ),
                {
                    "label": "copy",
                    "run_to_end": False,
                    "run_to_end_delay_ms": 300,
                    "actions": [{"type": "text", "value": "hello", "label": ""}],
                    "_parent_refs": ["user/trigger_sets/main.json"],
                },
            )
            self.assertEqual(
                JsonRepository().load_json(
                    os.path.join(none_root, "user", "hotkey_presets", "default.json")
                ),
                {"hotkey_presets": [{"label": "Alt+Tab", "value": "alt+tab"}]},
            )
            self.assertEqual(
                JsonRepository().load_json(os.path.join(none_root, "config.json")),
                {
                    "keymap_set_path": "user/keymap_sets/main.json",
                    "ui_font_delta_pt": 0,
                    "last_used_directory": "",
                },
            )

    def test_build_keymap_set_payload_saves_individual_hook_keys(self):
        payload = self._build_keymap_set_payload(
            {
                "hook_keys_individual": True,
                "hook_stop_key": "f3",
                "hook_toggle_key": "f4",
            }
        )

        self.assertEqual(payload["hook_stop_key"], "f3")
        self.assertEqual(payload["hook_toggle_key"], "f4")
        self.assertTrue(payload["hook_keys_individual"])

    def test_build_keymap_set_payload_clears_off_hook_keys_without_mutating_runtime(self):
        runtime = {
            "hook_keys_individual": False,
            "hook_stop_key": "f11",
            "hook_toggle_key": "f12",
        }

        payload = self._build_keymap_set_payload(runtime)

        self.assertIn("hook_stop_key", payload)
        self.assertIn("hook_toggle_key", payload)
        self.assertEqual(payload["hook_stop_key"], "")
        self.assertEqual(payload["hook_toggle_key"], "")
        self.assertFalse(payload["hook_keys_individual"])
        self.assertEqual(runtime["hook_stop_key"], "f11")
        self.assertEqual(runtime["hook_toggle_key"], "f12")

    def test_build_keymap_set_payload_applies_legacy_hook_key_migration(self):
        for runtime, expected_stop_key, expected_toggle_key, expected_individual in (
            ({"hook_stop_key": "f3", "hook_toggle_key": "f4"}, "f3", "f4", True),
            ({"hook_stop_key": "", "hook_toggle_key": ""}, "", "", False),
        ):
            with self.subTest(runtime=runtime):
                payload = self._build_keymap_set_payload(runtime)

                self.assertEqual(payload["hook_stop_key"], expected_stop_key)
                self.assertEqual(payload["hook_toggle_key"], expected_toggle_key)
                self.assertEqual(payload["hook_keys_individual"], expected_individual)

    def test_single_skip_omits_only_the_selected_child(self):
        cases = (
            (
                ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SKIP),
                "user/keymaps/km1.json",
                ("user/sequences/copy.json", "user/trigger_sets/main.json"),
            ),
            (
                ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SKIP),
                "user/sequences/copy.json",
                ("user/keymaps/km1.json", "user/trigger_sets/main.json"),
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for index, (entry, skipped_path, written_paths) in enumerate(cases):
                root = os.path.join(tmp, str(index))
                self._save(root, plan=SavePlan((entry,)))

                self.assertFalse(os.path.exists(os.path.join(root, skipped_path)))
                for written_path in written_paths:
                    self.assertTrue(os.path.exists(os.path.join(root, written_path)))
                self.assertTrue(
                    os.path.exists(os.path.join(root, "user", "hotkey_presets", "default.json"))
                )

    def test_skipped_trigger_set_does_not_write_when_sequence_path_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            sequence_path = os.path.join(root, "user", "sequences", "copy.json")
            JsonRepository().save_json(sequence_path, {"label": "old", "actions": []})
            data = make_runtime_data()
            data["triggers"][0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH] = (
                "user/sequences/copy.json"
            )
            self._save(
                root,
                data=data,
                plan=SavePlan((ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),)),
            )

            self.assertFalse(
                os.path.exists(os.path.join(root, "user", "trigger_sets", "main.json"))
            )
            self.assertTrue(os.path.exists(sequence_path))
            self.assertTrue(os.path.exists(os.path.join(root, "user", "keymaps", "km1.json")))

    def test_trigger_set_does_not_write_skipped_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save(
                root,
                plan=SavePlan((ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SKIP),)),
            )

            self.assertFalse(os.path.exists(os.path.join(root, "user", "sequences", "copy.json")))
            trigger_set = JsonRepository().load_json(
                os.path.join(root, "user", "trigger_sets", "main.json")
            )
            self.assertEqual(trigger_set["triggers"][0]["sequence_path"], "")

    def test_save_as_updates_parent_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            trigger_set_path = os.path.join(root, "custom", "triggers.json")
            sequence_path = os.path.join(root, "custom", "copy.json")
            keymap_path = os.path.join(root, "custom", "main.json")
            saved, _ = self._save(
                root,
                plan=SavePlan(
                    (
                        ChildSaveEntry(
                            CHILD_TRIGGER_SET,
                            "",
                            ACTION_SAVE_AS,
                            trigger_set_path,
                        ),
                        ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SAVE_AS, sequence_path),
                        ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SAVE_AS, keymap_path),
                    )
                ),
            )

            self.assertTrue(os.path.exists(trigger_set_path))
            self.assertTrue(os.path.exists(sequence_path))
            self.assertTrue(os.path.exists(keymap_path))
            keymap_set = JsonRepository().load_json(
                os.path.join(root, "user", "keymap_sets", "main.json")
            )
            trigger_set = JsonRepository().load_json(trigger_set_path)
            self.assertEqual(keymap_set["trigger_set_path"], "custom/triggers.json")
            self.assertEqual(keymap_set["keymaps"][0]["path"], "custom/main.json")
            self.assertEqual(trigger_set["triggers"][0]["sequence_path"], "custom/copy.json")
            self.assertEqual(
                saved[self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH],
                "custom/triggers.json",
            )
            self.assertEqual(
                saved["keymaps"][0][self.service.INTERNAL_KEYMAP_SOURCE_PATH],
                "custom/main.json",
            )
            self.assertEqual(
                saved["triggers"][0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                "custom/copy.json",
            )

    def test_invalid_plan_writes_no_files(self):
        invalid_plans = (
            SavePlan((ChildSaveEntry("unknown", "", ACTION_SKIP),)),
            SavePlan((ChildSaveEntry(CHILD_KEYMAP, "missing", ACTION_SKIP),)),
            SavePlan((ChildSaveEntry(CHILD_SEQUENCE, "f1", "invalid"),)),
            SavePlan((ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SAVE_AS),)),
            SavePlan(
                (
                    ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SKIP),
                    ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SKIP),
                )
            ),
            SavePlan(
                (
                    ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SAVE_AS, "new-copy.json"),
                    ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),
                )
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for index, plan in enumerate(invalid_plans):
                root = os.path.join(tmp, str(index))
                with self.assertRaises(SavePlanError):
                    self._save(root, plan=plan)
                self.assertFalse(os.path.exists(os.path.join(root, "config.json")))
                self.assertFalse(
                    os.path.exists(os.path.join(root, "user", "keymap_sets", "main.json"))
                )
                self.assertEqual(self.repository.saved_paths, [])

    def test_save_to_changed_sequence_path_requires_trigger_set_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            data = make_runtime_data()
            data["triggers"][0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH] = (
                "user/sequences/shared.json"
            )
            second_trigger = dict(data["triggers"][0])
            second_trigger["key"] = "f2"
            second_trigger["label"] = "paste"
            data["triggers"].append(second_trigger)

            with self.assertRaises(SavePlanError):
                self._save(
                    root,
                    data=data,
                    plan=SavePlan(
                        (
                            ChildSaveEntry(CHILD_SEQUENCE, "f2", ACTION_SAVE),
                            ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),
                        ),
                        allow_deferred_index=False,
                    ),
                )

            self.assertEqual(self.repository.saved_paths, [])
            self.assertFalse(os.path.exists(os.path.join(root, "config.json")))

    def test_deferred_index_writes_changed_sequence_without_updating_trigger_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save(root)
            trigger_set_path = os.path.join(root, "user", "trigger_sets", "main.json")
            previous_trigger_set = _read_bytes(trigger_set_path)
            data = self.service.load_runtime_data_from_keymap_set_path(
                os.path.join(root, "user", "keymap_sets", "main.json"),
                config_root=root,
            )
            second_trigger = dict(data["triggers"][0])
            second_trigger.update(
                {
                    "key": "f2",
                    "label": "paste",
                    "actions": [{"type": "text", "value": "deferred", "label": ""}],
                    self.service.INTERNAL_SEQUENCE_SOURCE_PATH: "user/sequences/copy.json",
                }
            )
            data["triggers"].append(second_trigger)
            plan = SavePlan(
                (
                    ChildSaveEntry(CHILD_SEQUENCE, "f2", ACTION_SAVE),
                    ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),
                ),
                allow_deferred_index=True,
            )
            targets = self.service.resolve_child_save_targets(
                data,
                config_root=root,
                keymap_set_path=os.path.join(root, "user", "keymap_sets", "main.json"),
                save_plan=plan,
            )
            saved, _ = self._save(root, data=data, plan=plan)

            self.assertTrue(os.path.exists(targets[(CHILD_SEQUENCE, "f2")]))
            self.assertEqual(_read_bytes(trigger_set_path), previous_trigger_set)
            self.assertTrue(os.path.exists(os.path.join(root, "user", "keymap_sets", "main.json")))
            self.assertTrue(os.path.exists(os.path.join(root, "config.json")))
            self.assertEqual(
                saved["triggers"][1][self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                self.service.to_config_relative_or_absolute(targets[(CHILD_SEQUENCE, "f2")], root),
            )

    def test_deferred_index_resave_updates_trigger_set_and_reloads_new_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            self._save(root)
            data = self.service.load_runtime_data_from_keymap_set_path(keymap_set_path, config_root=root)
            second_trigger = dict(data["triggers"][0])
            second_trigger.update(
                {
                    "key": "f2",
                    "label": "paste",
                    "actions": [{"type": "text", "value": "deferred", "label": ""}],
                    self.service.INTERNAL_SEQUENCE_SOURCE_PATH: "user/sequences/copy.json",
                }
            )
            data["triggers"].append(second_trigger)
            deferred_plan = SavePlan(
                (
                    ChildSaveEntry(CHILD_SEQUENCE, "f2", ACTION_SAVE),
                    ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),
                ),
                allow_deferred_index=True,
            )
            saved, _ = self._save(root, data=data, plan=deferred_plan)
            sequence_path = saved["triggers"][1][self.service.INTERNAL_SEQUENCE_SOURCE_PATH]

            self._save(
                root,
                data=saved,
                plan=SavePlan((ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SAVE),)),
            )
            loaded = self.service.load_runtime_data_from_keymap_set_path(keymap_set_path, config_root=root)

            self.assertEqual(
                loaded["triggers"][1][self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                sequence_path,
            )
            self.assertEqual(loaded["triggers"][1]["actions"], saved["triggers"][1]["actions"])

    def test_skip_keeps_existing_indexes_and_omits_missing_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "existing")
            self._save(root)
            loaded = self.service.load_runtime_data_from_keymap_set_path(
                os.path.join(root, "user", "keymap_sets", "main.json"),
                config_root=root,
            )
            self.assertEqual(
                loaded[self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH],
                "user/trigger_sets/main.json",
            )
            plan = SavePlan(
                (
                    ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SKIP),
                    ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SKIP),
                    ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SKIP),
                )
            )
            self._save(root, data=loaded, plan=plan)
            keymap_set = JsonRepository().load_json(
                os.path.join(root, "user", "keymap_sets", "main.json")
            )
            self.assertEqual(keymap_set["keymaps"][0]["path"], "user/keymaps/km1.json")
            self.assertEqual(keymap_set["trigger_set_path"], "user/trigger_sets/main.json")
            trigger_set = JsonRepository().load_json(
                os.path.join(root, "user", "trigger_sets", "main.json")
            )
            self.assertEqual(trigger_set["triggers"][0]["sequence_path"], "user/sequences/copy.json")

            missing_root = os.path.join(tmp, "missing")
            self._save(missing_root, plan=plan)
            missing_keymap_set = JsonRepository().load_json(
                os.path.join(missing_root, "user", "keymap_sets", "main.json")
            )
            self.assertEqual(missing_keymap_set["keymaps"], [])
            self.assertEqual(missing_keymap_set["trigger_set_path"], "")

    def test_child_write_failure_keeps_parent_and_startup_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save(root)
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            startup_path = os.path.join(root, "config.json")
            previous_keymap_set = _read_bytes(keymap_set_path)
            previous_startup = _read_bytes(startup_path)
            self.repository.fail_path = os.path.join(root, "user", "sequences", "copy.json")

            with self.assertRaises(OSError):
                self._save(root)

            self.assertEqual(_read_bytes(keymap_set_path), previous_keymap_set)
            self.assertEqual(_read_bytes(startup_path), previous_startup)

    def test_writes_children_before_parent_and_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save(root)
            relative_paths = [
                os.path.relpath(path, root).replace("\\", "/")
                for path in self.repository.saved_paths
            ]
            self.assertEqual(
                relative_paths,
                [
                    "user/sequences/copy.json",
                    "user/trigger_sets/main.json",
                    "user/keymaps/km1.json",
                    "user/hotkey_presets/default.json",
                    "user/keymap_sets/main.json",
                    "config.json",
                ],
            )


if __name__ == "__main__":
    unittest.main()
