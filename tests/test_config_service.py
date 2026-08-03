import ntpath
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, save_path_resolution
from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
)
from keyseq.infrastructure.json_repository import JsonRepository


def strip_internal(item):
    return {k: v for k, v in item.items() if not k.startswith("_")}


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


class SaveLoadRoundTripTest(unittest.TestCase):
    def test_round_trip_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            service = ConfigService(JsonRepository())
            saved, startup = service.save_runtime_data(
                "",
                make_runtime_data(),
                config_root=root,
                startup_data={},
                split_base_dir="",
            )
            self.assertEqual(startup["keymap_set_path"], "user/keymap_sets/default.json")

            for rel in (
                "config.json",
                os.path.join("user", "keymap_sets", "default.json"),
                os.path.join("user", "trigger_sets", "default.json"),
                os.path.join("user", "hotkey_presets", "default.json"),
                os.path.join("user", "keymaps", "km1.json"),
                os.path.join("user", "sequences", "copy.json"),
            ):
                self.assertTrue(os.path.exists(os.path.join(root, rel)), rel)

            loaded = service.load_runtime_data_from_keymap_set_path(
                os.path.join(root, "user", "keymap_sets", "default.json"),
                config_root=root,
            )
            self.assertEqual(
                [strip_internal(t) for t in loaded["triggers"]],
                [strip_internal(t) for t in saved["triggers"]],
            )
            self.assertEqual(
                [strip_internal(k) for k in loaded["keymaps"]],
                [strip_internal(k) for k in saved["keymaps"]],
            )
            self.assertEqual(loaded["hotkey_presets"], saved["hotkey_presets"])
            self.assertEqual(loaded["active_keymap_id"], "km1")
            self.assertEqual(loaded["keymap_switch_keys"], {"1": "km1"})
            self.assertEqual(loaded["hook_stop_key"], "f12")
            self.assertEqual(loaded["keyboard_layout"], "us_tkl")

    def test_save_runtime_data_omits_prompt_if_missing_without_existing_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            service = ConfigService(JsonRepository())

            _, startup = service.save_runtime_data(
                "",
                make_runtime_data(),
                config_root=root,
                startup_data={},
                split_base_dir="",
            )

            self.assertNotIn("prompt_if_missing", startup)

    def test_save_runtime_data_preserves_existing_prompt_if_missing_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            service = ConfigService(JsonRepository())

            _, startup = service.save_runtime_data(
                "",
                make_runtime_data(),
                config_root=root,
                startup_data={"prompt_if_missing": True},
                split_base_dir="",
            )

            self.assertEqual(startup["prompt_if_missing"], True)
            self.assertEqual(startup["keymap_set_path"], "user/keymap_sets/default.json")


class HookKeyResolutionTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _load_keymap_set(self, root, keymap_set):
        path = os.path.join(root, "user", "keymap_sets", "main.json")
        self.service.repository.save_json(path, keymap_set)
        return self.service.load_runtime_data_from_keymap_set_path(path, config_root=root)

    def _save_global_hook_keys(self, root, stop_key, toggle_key):
        self.service.repository.save_json(
            os.path.join(root, "config.json"),
            {"hook_stop_key": stop_key, "hook_toggle_key": toggle_key},
        )

    def test_off_legacy_keymap_set_uses_global_hook_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_hook_keys(root, "f11", "f12")

            loaded = self._load_keymap_set(
                root,
                {"hook_stop_key": "", "hook_toggle_key": ""},
            )

            self.assertEqual(loaded["hook_stop_key"], "f11")
            self.assertEqual(loaded["hook_toggle_key"], "f12")

    def test_on_legacy_keymap_set_keeps_individual_hook_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_hook_keys(root, "f11", "f12")

            loaded = self._load_keymap_set(
                root,
                {"hook_stop_key": "f3", "hook_toggle_key": ""},
            )

            self.assertTrue(loaded["hook_keys_individual"])
            self.assertEqual(loaded["hook_stop_key"], "f3")
            self.assertEqual(loaded["hook_toggle_key"], "")

    def test_explicit_off_keymap_set_uses_global_hook_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_hook_keys(root, "f11", "f12")

            loaded = self._load_keymap_set(
                root,
                {
                    "hook_keys_individual": False,
                    "hook_stop_key": "f3",
                    "hook_toggle_key": "f4",
                },
            )

            self.assertFalse(loaded["hook_keys_individual"])
            self.assertEqual(loaded["hook_stop_key"], "f11")
            self.assertEqual(loaded["hook_toggle_key"], "f12")

    def test_missing_or_invalid_global_hook_key_config_uses_empty_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            for name, content in (("missing", None), ("invalid", "{")):
                with self.subTest(name=name):
                    config_path = os.path.join(root, "config.json")
                    if content is not None:
                        Path(config_path).write_text(content, encoding="utf-8")

                    loaded = self._load_keymap_set(
                        root,
                        {"hook_stop_key": "", "hook_toggle_key": ""},
                    )

                    self.assertEqual(loaded["hook_stop_key"], "")
                    self.assertEqual(loaded["hook_toggle_key"], "")
                    if content is not None:
                        os.remove(config_path)

    def test_global_hook_keys_are_normalized_when_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_hook_keys(root, "F1", " F2 ")

            loaded = self._load_keymap_set(
                root,
                {"hook_stop_key": "", "hook_toggle_key": ""},
            )

            self.assertEqual(loaded["hook_stop_key"], "f1")
            self.assertEqual(loaded["hook_toggle_key"], "f2")

    def test_off_flag_is_preserved_after_global_hook_key_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_hook_keys(root, "f11", "f12")

            loaded = self._load_keymap_set(
                root,
                {"hook_keys_individual": False, "hook_stop_key": "", "hook_toggle_key": ""},
            )

            self.assertFalse(loaded["hook_keys_individual"])
            self.assertEqual(loaded["hook_stop_key"], "f11")
            self.assertEqual(loaded["hook_toggle_key"], "f12")

    def test_off_save_clears_individual_hook_keys_and_reloads_global_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            self._save_global_hook_keys(root, "f11", "f12")
            runtime = make_runtime_data()
            runtime.update(
                {
                    "hook_keys_individual": False,
                    "hook_stop_key": "f11",
                    "hook_toggle_key": "f12",
                }
            )

            self.service.save_runtime_data(
                keymap_set_path,
                runtime,
                config_root=root,
                startup_data=self.service.load_startup(os.path.join(root, "config.json")),
            )

            keymap_set = self.service.repository.load_json(keymap_set_path)
            self.assertFalse(keymap_set["hook_keys_individual"])
            self.assertEqual(keymap_set["hook_stop_key"], "")
            self.assertEqual(keymap_set["hook_toggle_key"], "")

            loaded = self.service.load_runtime_data_from_keymap_set_path(
                keymap_set_path,
                config_root=root,
            )

            self.assertFalse(loaded["hook_keys_individual"])
            self.assertEqual(loaded["hook_stop_key"], "f11")
            self.assertEqual(loaded["hook_toggle_key"], "f12")


class ApplyGlobalHookKeyDefaultsTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_off_runtime_is_updated_and_on_runtime_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hook_stop_key": "f11", "hook_toggle_key": "f12"},
            )
            off_runtime = {"hook_keys_individual": False, "hook_stop_key": "", "hook_toggle_key": ""}
            on_runtime = {"hook_keys_individual": True, "hook_stop_key": "f3", "hook_toggle_key": "f4"}

            self.assertIs(
                self.service.apply_global_hook_key_defaults(off_runtime, config_root=root),
                off_runtime,
            )
            self.service.apply_global_hook_key_defaults(on_runtime, config_root=root)

            self.assertEqual(off_runtime["hook_stop_key"], "f11")
            self.assertEqual(off_runtime["hook_toggle_key"], "f12")
            self.assertEqual(on_runtime, {"hook_keys_individual": True, "hook_stop_key": "f3", "hook_toggle_key": "f4"})

    def test_apply_global_hook_key_defaults_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hook_stop_key": "f11", "hook_toggle_key": "f12"},
            )
            runtime = {"hook_keys_individual": False, "hook_stop_key": "", "hook_toggle_key": ""}

            self.service.apply_global_hook_key_defaults(runtime, config_root=root)
            once_applied = dict(runtime)
            self.service.apply_global_hook_key_defaults(runtime, config_root=root)

            self.assertEqual(runtime, once_applied)

    def test_apply_global_hook_key_defaults_with_empty_root_uses_empty_keys(self):
        runtime = {"hook_keys_individual": False, "hook_stop_key": "f3", "hook_toggle_key": "f4"}

        self.service.apply_global_hook_key_defaults(runtime, config_root="")

        self.assertEqual(runtime["hook_stop_key"], "")
        self.assertEqual(runtime["hook_toggle_key"], "")


class KeymapFileIoTest(unittest.TestCase):
    def test_save_and_load_keymap_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = ConfigService(JsonRepository())
            path = os.path.join(tmp, "my_map.json")
            saved = service.save_keymap_file(
                path, {"id": "km1", "label": "Main", "mappings": {"A": "B"}}
            )
            self.assertEqual(saved["_keymap_source_path"], path)
            self.assertFalse(saved["_keymap_imported"])
            self.assertFalse(saved["_keymap_dirty"])

            payload = JsonRepository().load_json(path)
            self.assertEqual(payload, {"label": "Main", "mappings": {"a": "b"}})

            loaded = service.load_keymap_file(path, used_keymap_ids=set(), imported=True)
            self.assertEqual(loaded["id"], "my_map")  # ファイル名から id が生成される
            self.assertEqual(loaded["mappings"], {"a": "b"})
            self.assertEqual(loaded["_keymap_source_path"], path)
            self.assertTrue(loaded["_keymap_imported"])


class SequenceFileIoTest(unittest.TestCase):
    def test_save_and_load_sequence_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = ConfigService(JsonRepository())
            path = os.path.join(tmp, "seq.json")
            trigger = {
                "key": "f1",
                "label": "copy",
                "run_to_end": True,
                "run_to_end_delay_ms": "abc",  # 不正値は 300 に矯正される
                "actions": [{"type": "hotkey", "value": "ctrl+c"}],
            }
            saved = service.save_sequence_file(path, trigger)
            self.assertEqual(saved["run_to_end_delay_ms"], 300)
            self.assertEqual(saved["_sequence_source_path"], path)

            loaded = service.load_sequence_file(path, imported=True)
            self.assertEqual(loaded["label"], "copy")
            self.assertTrue(loaded["run_to_end"])
            self.assertEqual(loaded["actions"], [{"type": "hotkey", "value": "ctrl+c"}])
            self.assertEqual(loaded["_sequence_source_path"], path)
            self.assertTrue(loaded["_sequence_imported"])


class IndividualSavePathTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_relative_individual_save_paths_use_config_root_and_keep_stored_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            elsewhere = os.path.join(tmp, "elsewhere")
            keymap_path = "user/keymaps/main.json"
            sequence_path = "user/sequences/copy.json"
            trigger_set_path = "user/trigger_sets/main.json"
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            previous_cwd = os.getcwd()
            os.makedirs(elsewhere)
            try:
                os.chdir(elsewhere)
                keymap = self.service.save_keymap_file(
                    keymap_path,
                    {"id": "km1", "label": "Main", "mappings": {"a": "b"}},
                    parent_ref=keymap_set_path,
                    config_root=root,
                )
                sequence = self.service.save_sequence_file(
                    sequence_path,
                    {"key": "f1", "label": "Copy", "actions": []},
                    parent_ref=os.path.join(root, trigger_set_path),
                    config_root=root,
                )
                triggers, trigger_payload = self.service.save_trigger_set_file(
                    trigger_set_path,
                    {"triggers": [{"key": "f2", "label": "Paste", "actions": []}]},
                    parent_ref=keymap_set_path,
                    config_root=root,
                )
            finally:
                os.chdir(previous_cwd)

            self.assertTrue(os.path.exists(os.path.join(root, keymap_path)))
            self.assertTrue(os.path.exists(os.path.join(root, sequence_path)))
            self.assertTrue(os.path.exists(os.path.join(root, trigger_set_path)))
            self.assertFalse(os.path.exists(os.path.join(elsewhere, "user")))
            self.assertEqual(
                keymap[self.service.INTERNAL_KEYMAP_SOURCE_PATH], keymap_path
            )
            self.assertEqual(
                sequence[self.service.INTERNAL_SEQUENCE_SOURCE_PATH], sequence_path
            )
            self.assertEqual(
                triggers[0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                "user/sequences/Paste.json",
            )
            self.assertEqual(
                trigger_payload["triggers"][0]["sequence_path"],
                "user/sequences/Paste.json",
            )
            self.assertEqual(
                JsonRepository().load_json(os.path.join(root, keymap_path))["_parent_refs"],
                ["user/keymap_sets/main.json"],
            )
            self.assertEqual(
                JsonRepository().load_json(os.path.join(root, sequence_path))["_parent_refs"],
                ["user/trigger_sets/main.json"],
            )
            self.assertEqual(
                trigger_payload["_parent_refs"], ["user/keymap_sets/main.json"]
            )

    def test_absolute_individual_save_paths_remain_external(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            external = os.path.join(tmp, "external")
            keymap_path = os.path.join(external, "main.json")
            sequence_path = os.path.join(external, "copy.json")
            trigger_set_path = os.path.join(external, "triggers.json")

            keymap = self.service.save_keymap_file(
                keymap_path,
                {"id": "km1", "label": "Main", "mappings": {}},
                config_root=root,
            )
            sequence = self.service.save_sequence_file(
                sequence_path,
                {"key": "f1", "label": "Copy", "actions": []},
                config_root=root,
            )
            self.service.save_trigger_set_file(
                trigger_set_path,
                {"triggers": []},
                config_root=root,
            )

            self.assertTrue(os.path.exists(keymap_path))
            self.assertTrue(os.path.exists(sequence_path))
            self.assertTrue(os.path.exists(trigger_set_path))
            self.assertEqual(
                keymap[self.service.INTERNAL_KEYMAP_SOURCE_PATH],
                keymap_path.replace("\\", "/"),
            )
            self.assertEqual(
                sequence[self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                sequence_path.replace("\\", "/"),
            )


class TriggerSetSavePlanTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_skip_plan_preserves_sequence_file_and_none_still_writes_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            trigger_set_path = "user/trigger_sets/main.json"
            old_sequence_path = os.path.join(root, "user", "sequences", "old.json")
            self.service.repository.save_json(old_sequence_path, {"label": "old", "actions": []})
            old_bytes = Path(old_sequence_path).read_bytes()
            data = {
                "triggers": [
                    {
                        "key": "f1",
                        "label": "Old",
                        "actions": [{"type": "text", "value": "changed", "label": ""}],
                        self.service.INTERNAL_SEQUENCE_SOURCE_PATH: "user/sequences/old.json",
                        self.service.INTERNAL_SEQUENCE_PARENT_REFS: ["legacy.json"],
                        self.service.INTERNAL_SEQUENCE_DIRTY: True,
                    },
                    {
                        "key": "f2",
                        "label": "New",
                        "actions": [],
                    },
                ]
            }
            plan = SavePlan(
                entries=(
                    ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SKIP),
                    ChildSaveEntry(CHILD_SEQUENCE, "f2", ACTION_SAVE),
                )
            )

            triggers, trigger_payload = self.service.save_trigger_set_file(
                trigger_set_path,
                data,
                config_root=root,
                save_plan=plan,
            )

            self.assertEqual(Path(old_sequence_path).read_bytes(), old_bytes)
            self.assertTrue(
                os.path.exists(os.path.join(root, trigger_set_path))
            )
            self.assertEqual(
                trigger_payload["triggers"][0]["sequence_path"],
                "user/sequences/old.json",
            )
            self.assertEqual(
                triggers[0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                "user/sequences/old.json",
            )
            self.assertTrue(triggers[0][self.service.INTERNAL_SEQUENCE_DIRTY])
            self.assertEqual(
                triggers[0][self.service.INTERNAL_SEQUENCE_PARENT_REFS],
                ["legacy.json"],
            )
            self.assertTrue(
                os.path.exists(os.path.join(root, "user", "sequences", "New.json"))
            )

            self.service.save_trigger_set_file(
                "user/trigger_sets/all.json",
                data,
                config_root=root,
            )

            self.assertNotEqual(Path(old_sequence_path).read_bytes(), old_bytes)

    def test_save_as_plan_writes_target_and_indexes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            sequence_path = os.path.join(root, "user", "sequences", "renamed.json")
            data = {
                "triggers": [
                    {
                        "key": "f1",
                        "label": "Copy",
                        "actions": [{"type": "text", "value": "copied", "label": ""}],
                    }
                ]
            }
            plan = SavePlan(
                entries=(
                    ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SAVE_AS, sequence_path),
                )
            )

            triggers, trigger_payload = self.service.save_trigger_set_file(
                "user/trigger_sets/main.json",
                data,
                config_root=root,
                save_plan=plan,
            )

            self.assertTrue(os.path.exists(sequence_path))
            self.assertEqual(
                trigger_payload["triggers"][0]["sequence_path"],
                "user/sequences/renamed.json",
            )
            self.assertEqual(
                triggers[0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH],
                "user/sequences/renamed.json",
            )


class ParentRefsSchemaTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_normalize_parent_refs_preserves_unknown_and_known_empty(self):
        self.assertIsNone(self.service._normalize_parent_refs(None))
        self.assertEqual(self.service._normalize_parent_refs([]), [])
        self.assertEqual(
            self.service._normalize_parent_refs(["a", "a", "b"]),
            ["a", "b"],
        )
        for value in ("x", {}, None):
            self.assertIsNone(self.service._normalize_parent_refs(value))
        self.assertEqual(
            self.service._normalize_parent_refs([" ", 1, " a ", "a"]),
            ["a"],
        )

    def test_merge_parent_ref_normalizes_and_deduplicates_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            inside = os.path.join(root, "user", "keymap_sets", "main.json")
            outside = os.path.join(tmp, "outside.json")
            self.assertEqual(
                self.service._merge_parent_ref(None, inside, config_root=root),
                ["user/keymap_sets/main.json"],
            )
            self.assertEqual(
                self.service._merge_parent_ref(
                    ["user\\keymap_sets\\main.json"],
                    inside,
                    config_root=root,
                ),
                ["user\\keymap_sets\\main.json"],
            )
            self.assertEqual(
                self.service._merge_parent_ref(None, "", config_root=root),
                [],
            )
            self.assertEqual(
                self.service._merge_parent_ref(None, outside, config_root=root),
                [os.path.abspath(outside).replace("\\", "/")],
            )

    def test_merge_parent_ref_deduplicates_absolute_and_relative_paths_by_identity(self):
        with patch("keyseq.application.config_service.os.path", ntpath):
            root = r"c:\config"
            absolute_parent = r"C:\CONFIG\user\keymap_sets\main.json"
            self.assertEqual(
                self.service._merge_parent_ref(
                    [absolute_parent],
                    r"c:\config\user\keymap_sets\main.json",
                    config_root=root,
                ),
                [absolute_parent],
            )

    def test_save_keymap_file_records_parent_only_when_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            path = os.path.join(root, "user", "keymaps", "main.json")
            parent_path = os.path.join(root, "user", "keymap_sets", "main.json")
            self.service.save_keymap_file(
                path,
                {"id": "km1", "label": "Main", "mappings": {"a": "b"}},
                parent_ref=parent_path,
                config_root=root,
            )
            self.assertEqual(
                JsonRepository().load_json(path)["_parent_refs"],
                ["user/keymap_sets/main.json"],
            )

            no_parent_path = os.path.join(root, "user", "keymaps", "no_parent.json")
            self.service.save_keymap_file(
                no_parent_path,
                {"id": "km2", "label": "No parent", "mappings": {"a": "b"}},
            )
            self.assertNotIn("_parent_refs", JsonRepository().load_json(no_parent_path))

    def test_keymap_and_sequence_round_trip_parent_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_path = os.path.join(root, "keymap.json")
            sequence_path = os.path.join(root, "sequence.json")
            JsonRepository().save_json(
                keymap_path,
                {"label": "Main", "mappings": {"a": "b"}, "_parent_refs": ["parent.json"]},
            )
            JsonRepository().save_json(
                sequence_path,
                {
                    "label": "copy",
                    "run_to_end": False,
                    "run_to_end_delay_ms": 300,
                    "actions": [],
                    "_parent_refs": ["trigger_set.json"],
                },
            )

            keymap = self.service.load_keymap_file(keymap_path, used_keymap_ids=set())
            sequence = self.service.load_sequence_file(sequence_path)
            self.service.save_keymap_file(keymap_path, keymap)
            self.service.save_sequence_file(sequence_path, sequence)

            self.assertEqual(JsonRepository().load_json(keymap_path)["_parent_refs"], ["parent.json"])
            self.assertEqual(
                JsonRepository().load_json(sequence_path)["_parent_refs"],
                ["trigger_set.json"],
            )

    def test_existing_files_without_parent_refs_remain_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            keymap_path = os.path.join(tmp, "keymap.json")
            sequence_path = os.path.join(tmp, "sequence.json")
            JsonRepository().save_json(keymap_path, {"label": "Main", "mappings": {}})
            JsonRepository().save_json(
                sequence_path,
                {"label": "copy", "run_to_end": False, "run_to_end_delay_ms": 300, "actions": []},
            )

            keymap = self.service.load_keymap_file(keymap_path, used_keymap_ids=set())
            sequence = self.service.load_sequence_file(sequence_path)
            self.assertNotIn(self.service.INTERNAL_KEYMAP_PARENT_REFS, keymap)
            self.assertNotIn(self.service.INTERNAL_SEQUENCE_PARENT_REFS, sequence)

    def test_legacy_children_without_parent_refs_load_and_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            self.service.save_runtime_data(
                keymap_set_path,
                make_runtime_data(),
                config_root=root,
                startup_data={},
            )
            child_paths = (
                os.path.join(root, "user", "keymaps", "km1.json"),
                os.path.join(root, "user", "trigger_sets", "main.json"),
                os.path.join(root, "user", "sequences", "copy.json"),
            )
            legacy_bytes = {}
            for child_path in child_paths:
                payload = JsonRepository().load_json(child_path)
                payload.pop("_parent_refs")
                JsonRepository().save_json(child_path, payload)
                legacy_bytes[child_path] = open(child_path, "rb").read()

            loaded = self.service.load_runtime_data_from_keymap_set_path(
                keymap_set_path,
                config_root=root,
            )
            self.service.save_runtime_data(
                keymap_set_path,
                loaded,
                config_root=root,
                startup_data={},
            )

            for child_path in child_paths:
                self.assertNotEqual(open(child_path, "rb").read(), legacy_bytes[child_path])
                self.assertIn("_parent_refs", JsonRepository().load_json(child_path))

    def test_save_runtime_data_records_all_parent_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            self.service.save_runtime_data(
                keymap_set_path,
                make_runtime_data(),
                config_root=root,
                startup_data={},
            )

            keymap = JsonRepository().load_json(os.path.join(root, "user", "keymaps", "km1.json"))
            trigger_set = JsonRepository().load_json(
                os.path.join(root, "user", "trigger_sets", "main.json")
            )
            sequence = JsonRepository().load_json(
                os.path.join(root, "user", "sequences", "copy.json")
            )
            self.assertEqual(keymap["_parent_refs"], ["user/keymap_sets/main.json"])
            self.assertEqual(trigger_set["_parent_refs"], ["user/keymap_sets/main.json"])
            self.assertEqual(sequence["_parent_refs"], ["user/trigger_sets/main.json"])

    def test_save_as_merges_existing_parent_refs_for_all_child_kinds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            target_paths = {
                CHILD_KEYMAP: os.path.join(root, "user", "keymaps", "alias.json"),
                CHILD_TRIGGER_SET: os.path.join(root, "user", "trigger_sets", "alias.json"),
                CHILD_SEQUENCE: os.path.join(root, "user", "sequences", "alias.json"),
            }
            for target_path, parent_ref in zip(target_paths.values(), ("other-keymap", "other-trigger", "other-sequence")):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                JsonRepository().save_json(target_path, {"_parent_refs": [parent_ref]})
            plan = SavePlan(
                entries=(
                    ChildSaveEntry(CHILD_KEYMAP, "km1", ACTION_SAVE_AS, target_paths[CHILD_KEYMAP]),
                    ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SAVE_AS, target_paths[CHILD_TRIGGER_SET]),
                    ChildSaveEntry(CHILD_SEQUENCE, "f1", ACTION_SAVE_AS, target_paths[CHILD_SEQUENCE]),
                )
            )

            self.service.save_runtime_data(
                keymap_set_path,
                make_runtime_data(),
                config_root=root,
                startup_data={},
                save_plan=plan,
            )

            self.assertEqual(
                JsonRepository().load_json(target_paths[CHILD_KEYMAP])["_parent_refs"],
                ["other-keymap", "user/keymap_sets/main.json"],
            )
            self.assertEqual(
                JsonRepository().load_json(target_paths[CHILD_TRIGGER_SET])["_parent_refs"],
                ["other-trigger", "user/keymap_sets/main.json"],
            )
            self.assertEqual(
                JsonRepository().load_json(target_paths[CHILD_SEQUENCE])["_parent_refs"],
                ["other-sequence", "user/trigger_sets/alias.json"],
            )

    def test_export_does_not_leak_parent_ref_runtime_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "export.json")
            data = make_runtime_data()
            data[self.service.INTERNAL_TRIGGER_SET_PARENT_REFS] = ["keymap_set.json"]
            data["keymaps"][0][self.service.INTERNAL_KEYMAP_PARENT_REFS] = ["keymap_set.json"]
            data["triggers"][0][self.service.INTERNAL_SEQUENCE_PARENT_REFS] = ["trigger_set.json"]

            sanitized = self.service._sanitize_runtime_for_storage(data)
            self.assertNotIn(self.service.INTERNAL_TRIGGER_SET_PARENT_REFS, sanitized)
            self.assertNotIn(self.service.INTERNAL_KEYMAP_PARENT_REFS, sanitized["keymaps"][0])
            self.assertNotIn(self.service.INTERNAL_SEQUENCE_PARENT_REFS, sanitized["triggers"][0])

            self.service.export_runtime_data(path, data)
            exported = JsonRepository().load_json(path)
            self.assertNotIn(self.service.INTERNAL_TRIGGER_SET_PARENT_REFS, exported)
            self.assertNotIn(self.service.INTERNAL_KEYMAP_PARENT_REFS, exported["keymaps"][0])
            self.assertNotIn(self.service.INTERNAL_SEQUENCE_PARENT_REFS, exported["triggers"][0])


class TriggerSetDefaultPathTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_keymap_set_stem_names_trigger_set_and_keeps_sequences_in_default_area(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "gaming.json")
            self.service.save_runtime_data(
                keymap_set_path,
                make_runtime_data(),
                config_root=root,
                startup_data={},
            )

            trigger_set_path = os.path.join(root, "user", "trigger_sets", "gaming.json")
            self.assertTrue(os.path.exists(trigger_set_path))
            self.assertTrue(os.path.exists(os.path.join(root, "user", "sequences", "copy.json")))
            keymap_set = JsonRepository().load_json(keymap_set_path)
            trigger_set = JsonRepository().load_json(trigger_set_path)
            self.assertEqual(keymap_set["trigger_set_path"], "user/trigger_sets/gaming.json")
            self.assertEqual(trigger_set["triggers"][0]["sequence_path"], "user/sequences/copy.json")

    def test_default_keymap_set_keeps_legacy_trigger_set_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.save_runtime_data("", make_runtime_data(), config_root=root, startup_data={})

            self.assertTrue(
                os.path.exists(os.path.join(root, "user", "trigger_sets", "default.json"))
            )

    def test_multiple_keymap_sets_do_not_share_default_trigger_set_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            paths = [
                os.path.join(root, "user", "keymap_sets", "gaming.json"),
                os.path.join(root, "user", "keymap_sets", "coding.json"),
            ]
            gaming_data = make_runtime_data()
            coding_data = make_runtime_data()
            coding_data["triggers"][0]["key"] = "f2"
            for path, data in zip(paths, (gaming_data, coding_data)):
                self.service.save_runtime_data(path, data, config_root=root, startup_data={})

            for stem, path, key in zip(("gaming", "coding"), paths, ("f1", "f2")):
                trigger_set_path = os.path.join(root, "user", "trigger_sets", f"{stem}.json")
                self.assertTrue(os.path.exists(trigger_set_path))
                keymap_set = JsonRepository().load_json(path)
                trigger_set = JsonRepository().load_json(trigger_set_path)
                self.assertEqual(keymap_set["trigger_set_path"], f"user/trigger_sets/{stem}.json")
                self.assertEqual(trigger_set["triggers"][0]["key"], key)

    def test_empty_keymap_set_stem_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            path = save_path_resolution.default_trigger_set_path(
                self.service,
                os.path.join(root, "user", "keymap_sets", "..."),
                config_root=root,
                split_base_dir="",
            )

            self.assertEqual(path, os.path.join(root, "user", "trigger_sets", "default.json"))

    def test_split_base_dir_uses_keymap_set_stem_for_trigger_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            split_base_dir = os.path.join(tmp, "sets")
            keymap_set_path = os.path.join(split_base_dir, "gaming.json")
            self.service.save_runtime_data(
                keymap_set_path,
                make_runtime_data(),
                config_root=root,
                startup_data={},
                split_base_dir=split_base_dir,
            )

            self.assertTrue(
                os.path.exists(os.path.join(split_base_dir, "trigger_sets", "gaming.json"))
            )

    @unittest.skipUnless(sys.platform == "win32", "Windows canonical identity integration")
    def test_case_variant_config_root_keeps_split_paths_relative_and_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            alternate_root = root.swapcase()
            keymap_set_path = os.path.join(
                alternate_root,
                "user",
                "keymap_sets",
                "main.json",
            )
            keymap_path = os.path.join(alternate_root, "user", "keymaps", "km1.json")
            os.makedirs(os.path.dirname(keymap_path), exist_ok=True)
            existing_parent_ref = os.path.join(
                alternate_root,
                "user",
                "keymap_sets",
                "main.json",
            )
            JsonRepository().save_json(
                keymap_path,
                {"label": "Main", "mappings": {}, "_parent_refs": [existing_parent_ref]},
            )
            data = make_runtime_data()
            data["keymaps"][0][self.service.INTERNAL_KEYMAP_SOURCE_PATH] = keymap_path

            _saved, startup = self.service.save_runtime_data(
                keymap_set_path,
                data,
                config_root=root,
                startup_data={},
            )

            trigger_set_path = os.path.join(root, "user", "trigger_sets", "main.json")
            sequence_path = os.path.join(root, "user", "sequences", "copy.json")
            self.assertTrue(self.service.is_path_within(keymap_set_path, root, root))
            self.assertEqual(startup["keymap_set_path"], "user/keymap_sets/main.json")
            self.assertEqual(
                JsonRepository().load_json(keymap_set_path)["trigger_set_path"],
                "user/trigger_sets/main.json",
            )
            self.assertEqual(
                JsonRepository().load_json(trigger_set_path)["_parent_refs"],
                ["user/keymap_sets/main.json"],
            )
            self.assertEqual(
                JsonRepository().load_json(keymap_path)["_parent_refs"],
                [existing_parent_ref],
            )
            self.assertTrue(
                save_path_resolution.is_default_trigger_set_area(
                    self.service,
                    trigger_set_path.swapcase(),
                    root,
                )
            )
            self.assertTrue(os.path.exists(sequence_path))


class PathHelperTest(unittest.TestCase):
    # 注意: R14 でメソッドが公開名に変わったら、このテストの呼び出しも新名に更新する
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_public_slug_generation(self):
        self.assertEqual(self.service.slugify_file_stem("a/b:c"), "a_b_c")
        self.assertEqual(self.service.slugify_file_stem("con"), "con_")
        self.assertEqual(self.service.slugify_file_stem("  "), "")
        self.assertEqual(self.service.slugify_file_stem("..name.."), "name")

    def test_public_config_relative_or_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            inside = os.path.join(root, "user", "x.json")
            outside = os.path.join(tmp, "outside.json")
            self.assertEqual(
                self.service.to_config_relative_or_absolute(inside, root), "user/x.json"
            )
            self.assertEqual(
                self.service.to_config_relative_or_absolute(outside, root),
                os.path.abspath(outside).replace("\\", "/"),
            )

    def test_canonical_path_and_containment_use_windows_identity(self):
        with patch("keyseq.application.config_service.os.path", ntpath):
            root = r"C:\Config"
            self.assertEqual(self.service.canonical_path("", root), "")
            self.assertEqual(
                self.service.canonical_path(r"user\Maps\Main.json", root),
                r"c:\config\user\maps\main.json",
            )
            self.assertTrue(
                self.service.is_path_within(r"c:\CONFIG\user\Maps\Main.json", root, root)
            )
            self.assertFalse(
                self.service.is_path_within(r"C:\Configx\main.json", root, root)
            )
            self.assertFalse(
                self.service.is_path_within(r"D:\Config\main.json", root, root)
            )


class EnsureSplitConfigDirsTest(unittest.TestCase):
    def test_creates_all_directories_and_allows_existing_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            service = ConfigService(JsonRepository())

            service.ensure_split_config_dirs(root)
            service.ensure_split_config_dirs(root)

            for relative_path in (
                "",
                "user",
                os.path.join("user", "keymap_sets"),
                os.path.join("user", "keymaps"),
                os.path.join("user", "trigger_sets"),
                os.path.join("user", "hotkey_presets"),
                os.path.join("user", "sequences"),
            ):
                self.assertTrue(os.path.isdir(os.path.join(root, relative_path)))


if __name__ == "__main__":
    unittest.main()
