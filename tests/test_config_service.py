import ntpath
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, save_path_resolution, split_payloads
from keyseq.application.config_service import split_loading
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
from keyseq.domain.config import DEFAULT_CONFIG, safe_deepcopy
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
                os.path.join("user", "keymaps", "km1.json"),
                os.path.join("user", "sequences", "copy.json"),
            ):
                self.assertTrue(os.path.exists(os.path.join(root, rel)), rel)
            self.assertFalse(
                os.path.exists(os.path.join(root, service.HOTKEY_PRESETS_RELATIVE_PATH))
            )

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
            self.assertEqual(loaded["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])
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


class GlobalHotkeyPresetsPathTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _load_path(self, root):
        return split_loading.load_global_hotkey_presets_path(
            self.service,
            config_root=root,
        )

    def test_configured_relative_path_is_returned_without_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            configured_path = "user/hotkey_presets/custom.json"
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": configured_path},
            )

            self.assertEqual(self._load_path(root), configured_path)

    def test_missing_path_uses_new_global_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(os.path.join(root, "config.json"), {})

            self.assertEqual(
                self._load_path(root),
                os.path.join("user", "hotkey_presets", "global", "default.json"),
            )

    def test_empty_or_non_string_path_uses_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            config_path = os.path.join(root, "config.json")
            for value in ("", "   ", None, 42):
                with self.subTest(value=value):
                    self.service.repository.save_json(
                        config_path,
                        {"hotkey_presets_path": value},
                    )

                    self.assertEqual(
                        self._load_path(root),
                        self.service.HOTKEY_PRESETS_RELATIVE_PATH,
                    )

    def test_missing_or_non_dict_config_uses_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            config_path = os.path.join(root, "config.json")
            for name, content in (("missing", None), ("non_dict", [])):
                with self.subTest(name=name):
                    if content is not None:
                        self.service.repository.save_json(config_path, content)

                    self.assertEqual(
                        self._load_path(root),
                        self.service.HOTKEY_PRESETS_RELATIVE_PATH,
                    )

                    if content is not None:
                        os.remove(config_path)

    def test_empty_config_root_uses_default(self):
        self.assertEqual(
            split_loading.load_global_hotkey_presets_path(self.service, config_root=""),
            self.service.HOTKEY_PRESETS_RELATIVE_PATH,
        )


class HotkeyPresetIndividualKeymapSetSchemaTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _load_keymap_set(self, root, keymap_set):
        path = os.path.join(root, "user", "keymap_sets", "main.json")
        self.service.repository.save_json(path, keymap_set)
        return self.service.load_runtime_data_from_keymap_set_path(path, config_root=root)

    def test_legacy_path_without_individual_flag_stays_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = self._load_keymap_set(
                os.path.join(tmp, "config"),
                {"hotkey_presets_path": "user/hotkey_presets/legacy.json"},
            )

            self.assertFalse(loaded["hotkey_presets_individual"])

    def test_true_individual_flag_and_path_round_trip_into_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = self._load_keymap_set(
                os.path.join(tmp, "config"),
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": "  user/hotkey_presets/personal.json  ",
                },
            )

            self.assertTrue(loaded["hotkey_presets_individual"])
            self.assertEqual(loaded["hotkey_presets_path"], "user/hotkey_presets/personal.json")

    def test_non_boolean_individual_flag_stays_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            for raw_flag in ("true", 1, None):
                with self.subTest(raw_flag=raw_flag):
                    loaded = self._load_keymap_set(
                        root,
                        {"hotkey_presets_individual": raw_flag},
                    )

                    self.assertFalse(loaded["hotkey_presets_individual"])

    def test_legacy_residual_path_is_not_loaded_or_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global/default.json"
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            legacy_path = "user/hotkey_presets/default.json"
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self.service.repository.save_json(
                os.path.join(root, global_path),
                {"hotkey_presets": global_presets},
            )
            self.service.repository.save_json(
                os.path.join(root, legacy_path),
                {"hotkey_presets": [{"label": "Legacy", "value": "ctrl+l"}]},
            )

            loaded = self._load_keymap_set(
                root,
                {"hotkey_presets_path": legacy_path},
            )

            self.assertFalse(loaded["hotkey_presets_individual"])
            self.assertEqual(loaded["hotkey_presets_path"], "")
            self.assertEqual(loaded["hotkey_presets"], global_presets)

    def test_false_individual_flag_keeps_hotkey_presets_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = self._load_keymap_set(
                os.path.join(tmp, "config"),
                {
                    "hotkey_presets_individual": False,
                    "hotkey_presets_path": "user/hotkey_presets/main.json",
                },
            )

            self.assertFalse(loaded["hotkey_presets_individual"])
            self.assertEqual(loaded["hotkey_presets_path"], "user/hotkey_presets/main.json")

    def test_true_individual_flag_loads_presets_from_stored_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            individual_path = "user/hotkey_presets/main.json"
            individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
            self.service.repository.save_json(
                os.path.join(root, individual_path),
                {"hotkey_presets": individual_presets},
            )

            loaded = self._load_keymap_set(
                root,
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": individual_path,
                },
            )

            self.assertTrue(loaded["hotkey_presets_individual"])
            self.assertEqual(loaded["hotkey_presets"], individual_presets)

    def test_legacy_residual_path_uses_keymap_set_stem_for_individual_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            self.service.repository.save_json(
                keymap_set_path,
                {"hotkey_presets_path": "user/hotkey_presets/default.json"},
            )
            runtime = self.service.load_runtime_data_from_keymap_set_path(
                keymap_set_path,
                config_root=root,
            )

            self.assertEqual(
                self.service.resolve_hotkey_presets_save_path(
                    runtime,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                    individual=True,
                ),
                "user/hotkey_presets/main.json",
            )


class GlobalHotkeyPresetsSavingTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_save_writes_to_configured_or_default_global_presets_path(self):
        presets = [{"label": "Save", "value": "ctrl+s"}]
        for configured_path in ("user/hotkey_presets/custom.json", None):
            with self.subTest(configured_path=configured_path), tempfile.TemporaryDirectory() as tmp:
                root = os.path.join(tmp, "config")
                if configured_path is not None:
                    self.service.repository.save_json(
                        os.path.join(root, "config.json"),
                        {"hotkey_presets_path": configured_path},
                    )
                expected_path = configured_path or self.service.HOTKEY_PRESETS_RELATIVE_PATH

                self.service.save_global_hotkey_presets(presets, config_root=root)

                self.assertEqual(
                    self.service.repository.load_json(os.path.join(root, expected_path)),
                    {"hotkey_presets": presets},
                )

    def test_save_round_trips_presets_including_empty_list(self):
        for presets in ([], [{"label": "Paste", "value": "ctrl+v"}]):
            with self.subTest(presets=presets), tempfile.TemporaryDirectory() as tmp:
                root = os.path.join(tmp, "config")

                self.service.save_global_hotkey_presets(presets, config_root=root)

                self.assertEqual(
                    split_loading.load_global_hotkey_presets(
                        self.service,
                        config_root=root,
                    ),
                    presets,
                )

    def test_save_propagates_repository_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(
                self.service.repository,
                "save_json",
                side_effect=OSError("no disk"),
            ):
                with self.assertRaisesRegex(OSError, "no disk"):
                    self.service.save_global_hotkey_presets(
                        [],
                        config_root=os.path.join(tmp, "config"),
                    )


class IndividualHotkeyPresetsSavingTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_default_path_uses_keymap_set_stem_and_does_not_collide_with_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")

            path = save_path_resolution.default_individual_hotkey_presets_path(
                self.service,
                keymap_set_path,
                config_root=root,
            )
            fallback_path = save_path_resolution.default_individual_hotkey_presets_path(
                self.service,
                os.path.join(root, "user", "keymap_sets", "..."),
                config_root=root,
            )
            global_path = self.service.resolve_config_path(
                self.service.HOTKEY_PRESETS_RELATIVE_PATH,
                root,
            )

            self.assertEqual(path, os.path.join(root, "user", "hotkey_presets", "main.json"))
            self.assertEqual(
                fallback_path,
                os.path.join(root, "user", "hotkey_presets", "default.json"),
            )
            self.assertEqual(
                global_path,
                os.path.join(root, "user", "hotkey_presets", "global", "default.json"),
            )
            self.assertNotEqual(fallback_path, global_path)

    def test_resolve_save_path_redirects_invalid_individual_paths_to_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            outside_path = os.path.join(tmp, "outside.json")

            cases = (
                (
                    {"hotkey_presets_individual": True, "hotkey_presets_path": "user/hotkey_presets/custom.json"},
                    "user/hotkey_presets/custom.json",
                ),
                (
                    {"hotkey_presets_individual": True, "hotkey_presets_path": ""},
                    "user/hotkey_presets/main.json",
                ),
                ({"hotkey_presets_individual": False}, ""),
                ({}, ""),
                (
                    {"hotkey_presets_individual": True, "hotkey_presets_path": outside_path},
                    "user/hotkey_presets/main.json",
                ),
            )
            for runtime, expected_path in cases:
                with self.subTest(runtime=runtime):
                    self.assertEqual(
                        self.service.resolve_hotkey_presets_save_path(
                            runtime,
                            config_root=root,
                            keymap_set_path=keymap_set_path,
                        ),
                        expected_path,
                    )

    def test_readable_outside_individual_path_still_saves_to_default_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            outside_path = os.path.join(tmp, "outside.json")
            self.service.repository.save_json(
                outside_path,
                {"hotkey_presets": [{"label": "Outside", "value": "ctrl+o"}]},
            )

            self.assertEqual(
                self.service.resolve_hotkey_presets_save_path(
                    {
                        "hotkey_presets_individual": True,
                        "hotkey_presets_path": outside_path,
                    },
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                    individual=True,
                ),
                "user/hotkey_presets/main.json",
            )

    def test_resolve_save_path_preview_override_redirects_without_mutating_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            runtime = {
                "hotkey_presets_individual": False,
                "hotkey_presets_path": os.path.join(tmp, "outside.json"),
            }
            before = safe_deepcopy(runtime)

            self.assertEqual(
                self.service.resolve_hotkey_presets_save_path(
                    runtime,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                    individual=True,
                ),
                "user/hotkey_presets/main.json",
            )
            self.assertEqual(
                self.service.resolve_hotkey_presets_save_path(
                    runtime,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                    individual=False,
                ),
                "",
            )
            self.assertEqual(runtime, before)

    def test_individual_save_path_rejection_reason_rejects_reserved_global_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")

            self.assertEqual(
                self.service.individual_hotkey_presets_save_rejection_reason(
                    "user/hotkey_presets/global/individual.json",
                    config_root=root,
                ),
                "reserved_dir",
            )

    def test_individual_save_path_rejection_reason_detects_global_file_across_notations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": "user/hotkey_presets/default.json"},
            )
            resolved_default_path = self.service.resolve_hotkey_presets_save_path(
                {"hotkey_presets_individual": True, "hotkey_presets_path": ""},
                config_root=root,
                keymap_set_path=os.path.join(root, "user", "keymap_sets", "default.json"),
            )

            self.assertEqual(resolved_default_path, "user/hotkey_presets/default.json")
            self.assertEqual(
                self.service.individual_hotkey_presets_save_rejection_reason(
                    resolved_default_path,
                    config_root=root,
                ),
                "global_conflict",
            )

        with patch("keyseq.application.config_service.os.path", ntpath), patch.object(
            self.service,
            "_load_optional_json",
            return_value={"hotkey_presets_path": r"user\hotkey_presets\default.json"},
        ):
            root = r"C:\Config"
            resolved_default_path = self.service.resolve_hotkey_presets_save_path(
                {"hotkey_presets_individual": True, "hotkey_presets_path": ""},
                config_root=root,
                keymap_set_path=r"C:\Config\user\keymap_sets\default.json",
            )

            self.assertEqual(resolved_default_path, "user/hotkey_presets/default.json")
            for stored_path in (
                r"user\hotkey_presets\default.json",
                r"C:\Config\user\hotkey_presets\default.json",
            ):
                with self.subTest(stored_path=stored_path):
                    self.assertEqual(
                        self.service.individual_hotkey_presets_save_rejection_reason(
                            stored_path,
                            config_root=root,
                        ),
                        "global_conflict",
                    )

    def test_individual_save_path_rejection_reason_allows_separate_default_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            stored_path = self.service.resolve_hotkey_presets_save_path(
                {"hotkey_presets_individual": True, "hotkey_presets_path": ""},
                config_root=root,
                keymap_set_path=keymap_set_path,
            )

            self.assertEqual(stored_path, "user/hotkey_presets/main.json")
            self.assertEqual(
                self.service.individual_hotkey_presets_save_rejection_reason(
                    stored_path,
                    config_root=root,
                ),
                "",
            )

    def test_describe_individual_hotkey_presets_overwrite_returns_conflict_and_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            stored_path = "user/hotkey_presets/personal.json"
            loaded_presets = [{"label": "Loaded", "value": "ctrl+l"}]

            self.assertEqual(
                self.service.describe_individual_hotkey_presets_overwrite(
                    stored_path,
                    loaded_presets,
                    config_root=root,
                ),
                {"conflict": False, "existing": None},
            )

            self.service.repository.save_json(
                os.path.join(root, stored_path),
                {"hotkey_presets": [{"label": " Loaded ", "value": "CTRL+L"}]},
            )
            self.assertEqual(
                self.service.describe_individual_hotkey_presets_overwrite(
                    stored_path,
                    loaded_presets,
                    config_root=root,
                ),
                {"conflict": False, "existing": loaded_presets},
            )

            self.service.repository.save_json(
                os.path.join(root, stored_path),
                {"hotkey_presets": [{"label": "Stored", "value": "ctrl+s"}]},
            )
            stored_presets = [{"label": "Stored", "value": "ctrl+s"}]
            self.assertEqual(
                self.service.describe_individual_hotkey_presets_overwrite(
                    stored_path,
                    loaded_presets,
                    config_root=root,
                ),
                {"conflict": True, "existing": stored_presets},
            )

            self.service.repository.save_json(
                os.path.join(root, stored_path),
                {"hotkey_presets": "invalid"},
            )
            self.assertEqual(
                self.service.describe_individual_hotkey_presets_overwrite(
                    stored_path,
                    loaded_presets,
                    config_root=root,
                ),
                {"conflict": True, "existing": None},
            )

            self.service.repository.save_json(
                os.path.join(root, stored_path),
                {"hotkey_presets": stored_presets},
            )
            self.assertEqual(
                self.service.describe_individual_hotkey_presets_overwrite(
                    stored_path,
                    None,
                    config_root=root,
                ),
                {"conflict": False, "existing": stored_presets},
            )

    def test_keymap_set_payload_normalizes_hotkey_presets_path_and_keeps_empty_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            expected_keys = [
                "trigger_set_path",
                "hotkey_presets_path",
                "hotkey_presets_individual",
                "active_keymap_path",
                "keymaps",
                "hook_stop_key",
                "hook_toggle_key",
                "hook_keys_individual",
                "keyboard_layout",
                "keyboard_show_physical_key_labels",
                "debug_jis_special_key_events",
                "external_keyboard_layouts",
            ]
            for stored_path in (
                r"user\hotkey_presets\main.json",
                os.path.join(root, "user", "hotkey_presets", "main.json"),
            ):
                with self.subTest(stored_path=stored_path):
                    payload = split_payloads.build_keymap_set_payload(
                        self.service,
                        {
                            "hotkey_presets_individual": True,
                            "hotkey_presets_path": stored_path,
                        },
                        {},
                        config_root=root,
                        trigger_set_path="",
                    )
                    self.assertEqual(payload["hotkey_presets_path"], "user/hotkey_presets/main.json")
                    self.assertEqual(list(payload), expected_keys)

            off_payload = split_payloads.build_keymap_set_payload(
                self.service,
                {"hotkey_presets_individual": False, "hotkey_presets_path": ""},
                {},
                config_root=root,
                trigger_set_path="",
            )
            self.assertEqual(off_payload["hotkey_presets_path"], "")
            self.assertEqual(list(off_payload), expected_keys)

    def test_save_to_specified_path_writes_payload_and_propagates_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            stored_path = "user/hotkey_presets/custom.json"
            presets = [{"label": "Save", "value": "ctrl+s"}]

            self.service.save_hotkey_presets(
                presets,
                config_root=root,
                stored_path=stored_path,
            )

            self.assertEqual(
                self.service.repository.load_json(os.path.join(root, stored_path)),
                {"hotkey_presets": presets},
            )
            with patch.object(
                self.service.repository,
                "save_json",
                side_effect=OSError("no disk"),
            ):
                with self.assertRaisesRegex(OSError, "no disk"):
                    self.service.save_hotkey_presets(
                        presets,
                        config_root=root,
                        stored_path=stored_path,
                    )

    def test_individual_save_round_trips_through_split_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "main.json")
            stored_path = "user/hotkey_presets/main.json"
            presets = [{"label": "Paste", "value": "ctrl+v"}]
            self.service.repository.save_json(
                keymap_set_path,
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": stored_path,
                },
            )

            self.service.save_hotkey_presets(
                presets,
                config_root=root,
                stored_path=stored_path,
            )

            loaded = self.service.load_runtime_data_from_keymap_set_path(
                keymap_set_path,
                config_root=root,
            )
            self.assertEqual(loaded["hotkey_presets"], presets)

    def test_clear_individual_hotkey_presets_sets_keys_without_changing_presets(self):
        presets = [{"label": "Keep", "value": "ctrl+k"}]
        for runtime in (
            {
                "hotkey_presets_individual": True,
                "hotkey_presets_path": "user/hotkey_presets/old.json",
                "hotkey_presets": presets,
                "other": "keep",
            },
            {"hotkey_presets": presets, "other": "keep"},
        ):
            with self.subTest(runtime=runtime):
                result = self.service.clear_individual_hotkey_presets(runtime)

                self.assertIs(result, runtime)
                self.assertIs(runtime["hotkey_presets_individual"], False)
                self.assertEqual(runtime["hotkey_presets_path"], "")
                self.assertIs(runtime["hotkey_presets"], presets)
                self.assertEqual(runtime["other"], "keep")

    def test_relocate_individual_hotkey_presets_handles_copy_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            keymap_set_path = os.path.join(root, "user", "keymap_sets", "renamed.json")
            source_stored_path = "user/hotkey_presets/original.json"
            source_path = os.path.join(root, source_stored_path)
            destination_path = os.path.join(root, "user", "hotkey_presets", "renamed.json")
            destination_stored_path = "user/hotkey_presets/renamed.json"
            runtime = {
                "hotkey_presets_individual": True,
                "hotkey_presets_path": source_stored_path,
            }

            self.service.repository.save_json(source_path, {"hotkey_presets": ["source"]})
            self.assertEqual(
                self.service.relocate_individual_hotkey_presets(
                    runtime,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                ),
                destination_stored_path,
            )
            self.assertEqual(self.service.repository.load_json(source_path), {"hotkey_presets": ["source"]})
            self.assertEqual(self.service.repository.load_json(destination_path), {"hotkey_presets": ["source"]})

            self.service.repository.save_json(destination_path, {"hotkey_presets": ["destination"]})
            self.service.repository.save_json(source_path, {"hotkey_presets": ["new source"]})
            self.assertEqual(
                self.service.relocate_individual_hotkey_presets(
                    runtime,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                ),
                destination_stored_path,
            )
            self.assertEqual(
                self.service.repository.load_json(destination_path),
                {"hotkey_presets": ["destination"]},
            )

            os.remove(destination_path)
            os.remove(source_path)
            self.assertEqual(
                self.service.relocate_individual_hotkey_presets(
                    runtime,
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                ),
                destination_stored_path,
            )
            self.assertFalse(os.path.exists(destination_path))

            self.service.repository.save_json(source_path, {"hotkey_presets": ["off source"]})
            self.assertEqual(
                self.service.relocate_individual_hotkey_presets(
                    {"hotkey_presets_individual": False, "hotkey_presets_path": source_stored_path},
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                ),
                "",
            )
            self.assertFalse(os.path.exists(destination_path))

            outside_path = os.path.join(tmp, "outside.json")
            self.service.repository.save_json(outside_path, {"hotkey_presets": ["outside"]})
            self.assertEqual(
                self.service.relocate_individual_hotkey_presets(
                    {"hotkey_presets_individual": True, "hotkey_presets_path": outside_path},
                    config_root=root,
                    keymap_set_path=keymap_set_path,
                ),
                destination_stored_path,
            )
            self.assertFalse(os.path.exists(destination_path))

    def test_relocate_individual_hotkey_presets_returns_new_relative_stem_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            result = self.service.relocate_individual_hotkey_presets(
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": "user/hotkey_presets/missing.json",
                },
                config_root=root,
                keymap_set_path=os.path.join(root, "user", "keymap_sets", "new-name.json"),
            )

            self.assertEqual(result, "user/hotkey_presets/new-name.json")
            self.assertNotIn("\\\\", result)


class HotkeyPresetsSourceDescriptionTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_describes_individual_state_and_displayed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            individual_path = "user/hotkey_presets/personal.json"
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self.service.repository.save_json(
                os.path.join(root, global_path),
                {"hotkey_presets": [{"label": "Global", "value": "ctrl+g"}]},
            )

            self.assertEqual(
                self.service.describe_hotkey_presets_source({}, config_root=root),
                {"individual_state": "off", "displayed_source": "global"},
            )

            self.service.repository.save_json(
                os.path.join(root, individual_path),
                {"hotkey_presets": [{"label": "Individual", "value": "ctrl+i"}]},
            )
            self.assertEqual(
                self.service.describe_hotkey_presets_source(
                    {
                        "hotkey_presets_individual": True,
                        "hotkey_presets_path": individual_path,
                    },
                    config_root=root,
                ),
                {"individual_state": "active", "displayed_source": "individual"},
            )
            self.assertEqual(
                self.service.describe_hotkey_presets_source(
                    {
                        "hotkey_presets_individual": True,
                        "hotkey_presets_path": "user/hotkey_presets/missing.json",
                    },
                    config_root=root,
                ),
                {"individual_state": "missing", "displayed_source": "global"},
            )
            self.assertEqual(
                self.service.describe_hotkey_presets_source(
                    {
                        "hotkey_presets_individual": True,
                        "hotkey_presets_path": os.path.join(tmp, "outside.json"),
                    },
                    config_root=root,
                ),
                {"individual_state": "external_missing", "displayed_source": "global"},
            )

            os.remove(os.path.join(root, global_path))
            self.assertEqual(
                self.service.describe_hotkey_presets_source(
                    {
                        "hotkey_presets_individual": True,
                        "hotkey_presets_path": "user/hotkey_presets/missing.json",
                    },
                    config_root=root,
                )["displayed_source"],
                "builtin",
            )

    def test_describes_readable_and_unreadable_outside_individual_paths_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            outside_path = os.path.join(tmp, "outside.json")
            self.service.repository.save_json(
                outside_path,
                {"hotkey_presets": [{"label": "Outside", "value": "ctrl+o"}]},
            )
            runtime = {
                "hotkey_presets_individual": True,
                "hotkey_presets_path": outside_path,
            }

            self.assertEqual(
                self.service.describe_hotkey_presets_source(runtime, config_root=root),
                {"individual_state": "external", "displayed_source": "individual"},
            )

            os.remove(outside_path)
            self.assertEqual(
                self.service.describe_hotkey_presets_source(runtime, config_root=root),
                {"individual_state": "external_missing", "displayed_source": "builtin"},
            )


class GlobalHotkeyPresetsLoadingTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _load_keymap_set(self, root, keymap_set):
        path = os.path.join(root, "user", "keymap_sets", "main.json")
        self.service.repository.save_json(path, keymap_set)
        return self.service.load_runtime_data_from_keymap_set_path(path, config_root=root)

    def _save_presets(self, root, relative_path, presets):
        self.service.repository.save_json(
            os.path.join(root, relative_path),
            {"hotkey_presets": presets},
        )

    def test_loads_presets_from_configured_global_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            expected_presets = [{"label": "Global", "value": "ctrl+g"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, expected_presets)

            loaded = self._load_keymap_set(root, {})

            self.assertEqual(loaded["hotkey_presets"], expected_presets)

    def test_ignores_keymap_set_path_and_uses_global_presets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            legacy_path = "user/hotkey_presets/legacy.json"
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            legacy_presets = [{"label": "Legacy", "value": "ctrl+l"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, global_presets)
            self._save_presets(root, legacy_path, legacy_presets)

            loaded = self._load_keymap_set(root, {"hotkey_presets_path": legacy_path})

            self.assertEqual(loaded["hotkey_presets"], global_presets)

    def test_individual_presets_override_global_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            individual_path = "user/hotkey_presets/gaming.json"
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            individual_presets = [{"label": "Gaming", "value": "ctrl+i"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, global_presets)
            self._save_presets(root, individual_path, individual_presets)

            loaded = self._load_keymap_set(
                root,
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": individual_path,
                },
            )

            self.assertEqual(loaded["hotkey_presets"], individual_presets)

    def test_individual_presets_are_ignored_when_disabled_or_flag_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            individual_path = "user/hotkey_presets/gaming.json"
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            individual_presets = [{"label": "Gaming", "value": "ctrl+i"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, global_presets)
            self._save_presets(root, individual_path, individual_presets)

            for flag in (False, None):
                with self.subTest(flag=flag):
                    keymap_set = {"hotkey_presets_path": individual_path}
                    if flag is not None:
                        keymap_set["hotkey_presets_individual"] = flag

                    loaded = self._load_keymap_set(root, keymap_set)

                    self.assertEqual(loaded["hotkey_presets"], global_presets)

    def test_unreadable_individual_presets_fall_back_to_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            individual_path = "user/hotkey_presets/gaming.json"
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            individual_file_path = os.path.join(root, individual_path)
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, global_presets)

            for name, content in (
                ("missing", None),
                ("invalid", "{"),
                ("non_list_root", {"hotkey_presets": {}}),
            ):
                with self.subTest(name=name):
                    if os.path.exists(individual_file_path):
                        os.remove(individual_file_path)
                    if isinstance(content, str):
                        Path(individual_file_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(individual_file_path).write_text(content, encoding="utf-8")
                    elif content is not None:
                        self.service.repository.save_json(individual_file_path, content)

                    loaded = self._load_keymap_set(
                        root,
                        {
                            "hotkey_presets_individual": True,
                            "hotkey_presets_path": individual_path,
                        },
                    )

                    self.assertEqual(loaded["hotkey_presets"], global_presets)

    def test_unreadable_individual_and_global_presets_keep_builtin_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": "user/hotkey_presets/missing-global.json"},
            )

            loaded = self._load_keymap_set(
                root,
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": "user/hotkey_presets/missing-individual.json",
                },
            )

            self.assertEqual(loaded["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])

    def test_readable_empty_individual_presets_prevent_global_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            individual_path = "user/hotkey_presets/gaming.json"
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, [{"label": "Global", "value": "ctrl+g"}])
            self._save_presets(root, individual_path, [])

            loaded = self._load_keymap_set(
                root,
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": individual_path,
                },
            )

            self.assertEqual(loaded["hotkey_presets"], [])

    def test_outside_individual_presets_path_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            outside_path = os.path.join(tmp, "outside.json")
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, global_presets)
            self.service.repository.save_json(
                outside_path,
                {"hotkey_presets": [{"label": "Outside", "value": "ctrl+o"}]},
            )
            keymap_set = {
                "hotkey_presets_individual": True,
                "hotkey_presets_path": outside_path,
            }

            loaded = self._load_keymap_set(root, keymap_set)

            self.assertEqual(
                loaded["hotkey_presets"],
                [{"label": "Outside", "value": "ctrl+o"}],
            )
            self.assertEqual(loaded["hotkey_presets_path"], outside_path)

    def test_unreadable_outside_individual_presets_path_falls_back_to_global_or_builtin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            outside_path = os.path.join(tmp, "missing-outside.json")
            global_presets = [{"label": "Global", "value": "ctrl+g"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, global_presets)
            keymap_set = {
                "hotkey_presets_individual": True,
                "hotkey_presets_path": outside_path,
            }

            self.assertEqual(
                self._load_keymap_set(root, keymap_set)["hotkey_presets"],
                global_presets,
            )

            os.remove(os.path.join(root, global_path))
            self.assertEqual(
                self._load_keymap_set(root, keymap_set)["hotkey_presets"],
                DEFAULT_CONFIG["hotkey_presets"],
            )

    def test_reading_outside_individual_presets_path_keeps_stored_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            outside_path = os.path.join(tmp, "outside.json")
            self.service.repository.save_json(
                outside_path,
                {"hotkey_presets": [{"label": "Outside", "value": "ctrl+o"}]},
            )
            keymap_set = {
                "hotkey_presets_individual": True,
                "hotkey_presets_path": outside_path,
            }

            loaded = self._load_keymap_set(root, keymap_set)

            self.assertEqual(loaded["hotkey_presets_path"], outside_path)

    def test_individual_presets_are_normalized_when_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            individual_path = "user/hotkey_presets/gaming.json"
            self._save_presets(
                root,
                individual_path,
                [
                    "garbage",
                    {"label": 1, "value": "ctrl+a"},
                    {"label": " Gaming ", "value": "CTRL+I"},
                    {"label": "bad", "value": 1},
                ],
            )

            loaded = self._load_keymap_set(
                root,
                {
                    "hotkey_presets_individual": True,
                    "hotkey_presets_path": individual_path,
                },
            )

            self.assertEqual(
                loaded["hotkey_presets"],
                [{"label": "Gaming", "value": "ctrl+i"}],
            )

    def test_missing_global_path_uses_default_presets_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            expected_presets = [{"label": "Default", "value": "ctrl+d"}]
            self.service.repository.save_json(os.path.join(root, "config.json"), {})
            self._save_presets(
                root,
                self.service.HOTKEY_PRESETS_RELATIVE_PATH,
                expected_presets,
            )

            loaded = self._load_keymap_set(root, {})

            self.assertEqual(loaded["hotkey_presets"], expected_presets)

    def test_unreadable_global_presets_file_keeps_builtin_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            config_path = os.path.join(root, "config.json")
            self.service.repository.save_json(
                config_path,
                {"hotkey_presets_path": global_path},
            )

            for name, content in (("missing", None), ("invalid", "{")):
                with self.subTest(name=name):
                    presets_path = os.path.join(root, global_path)
                    if content is not None:
                        Path(presets_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(presets_path).write_text(content, encoding="utf-8")

                    loaded = self._load_keymap_set(root, {})

                    self.assertEqual(loaded["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])
                    if content is not None:
                        os.remove(presets_path)

    def test_legacy_keymap_set_presets_path_keeps_builtin_defaults_when_global_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            legacy_path = "user/hotkey_presets/legacy.json"
            self.service.repository.save_json(os.path.join(root, "config.json"), {})

            loaded = self._load_keymap_set(root, {"hotkey_presets_path": legacy_path})

            self.assertEqual(loaded["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])

    def test_legacy_default_presets_file_is_not_read_without_configured_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            legacy_path = os.path.join("user", "hotkey_presets", "default.json")
            legacy_presets = [{"label": "Legacy", "value": "ctrl+l"}]
            self.service.repository.save_json(os.path.join(root, "config.json"), {})
            self._save_presets(root, legacy_path, legacy_presets)

            loaded = self._load_keymap_set(root, {})

            self.assertEqual(loaded["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])

    def test_load_global_hotkey_presets_distinguishes_readable_and_unreadable_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            presets_path = os.path.join(root, global_path)
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )

            cases = (
                ("readable_empty", {"hotkey_presets": []}, []),
                ("missing", None, None),
                ("invalid", "{", None),
                ("non_dict", [], None),
                ("non_list_root", {"hotkey_presets": {}}, None),
            )
            for name, content, expected in cases:
                with self.subTest(name=name):
                    if os.path.exists(presets_path):
                        os.remove(presets_path)
                    if isinstance(content, str):
                        Path(presets_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(presets_path).write_text(content, encoding="utf-8")
                    elif content is not None:
                        self.service.repository.save_json(presets_path, content)

                    self.assertEqual(
                        split_loading.load_global_hotkey_presets(self.service, config_root=root),
                        expected,
                    )

    def test_global_presets_are_normalized_consistently_for_injection_and_split_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            raw_presets = [{"label": "  A  ", "value": "CTRL+A"}, "garbage"]
            expected_presets = [{"label": "A", "value": "ctrl+a"}]
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, raw_presets)

            injected_runtime = {"hotkey_presets": [{"label": "Old", "value": "ctrl+o"}]}
            self.service.apply_global_defaults(injected_runtime, config_root=root)
            loaded_runtime = self._load_keymap_set(root, {})

            self.assertEqual(injected_runtime["hotkey_presets"], expected_presets)
            self.assertEqual(loaded_runtime["hotkey_presets"], expected_presets)

    def test_load_global_hotkey_presets_returns_empty_list_after_normalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, ["garbage"])

            self.assertEqual(
                split_loading.load_global_hotkey_presets(self.service, config_root=root),
                [],
            )

    def test_build_runtime_data_from_split_drops_non_string_preset_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(
                root,
                global_path,
                [
                    {"label": 1, "value": "ctrl+a"},
                    {"label": "ok", "value": "CTRL+B"},
                ],
            )

            runtime = split_loading.build_runtime_data_from_split(
                self.service,
                {},
                config_root=root,
            )

            self.assertEqual(runtime["hotkey_presets"], [{"label": "ok", "value": "ctrl+b"}])

    def test_split_loading_adopts_empty_global_presets_and_keeps_builtins_when_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            global_path = "user/hotkey_presets/global.json"
            presets_path = os.path.join(root, global_path)
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": global_path},
            )
            self._save_presets(root, global_path, [])

            self.assertEqual(self._load_keymap_set(root, {})["hotkey_presets"], [])

            os.remove(presets_path)
            self.assertEqual(
                self._load_keymap_set(root, {})["hotkey_presets"],
                DEFAULT_CONFIG["hotkey_presets"],
            )


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

    def test_missing_individual_flag_defaults_off_without_baking_global_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hook_stop_key": "f11", "hook_toggle_key": "f12"},
            )
            runtime = {"hook_stop_key": "", "hook_toggle_key": ""}

            self.service.apply_global_hook_key_defaults(runtime, config_root=root)
            payload = split_payloads.build_keymap_set_payload(
                self.service,
                runtime,
                {},
                config_root=root,
                trigger_set_path="",
            )

            self.assertFalse(runtime["hook_keys_individual"])
            self.assertEqual(runtime["hook_stop_key"], "f11")
            self.assertEqual(runtime["hook_toggle_key"], "f12")
            self.assertEqual(payload["hook_stop_key"], "")
            self.assertEqual(payload["hook_toggle_key"], "")
            self.assertFalse(payload["hook_keys_individual"])

    def test_apply_global_hook_key_defaults_with_empty_root_uses_empty_keys(self):
        runtime = {"hook_keys_individual": False, "hook_stop_key": "f3", "hook_toggle_key": "f4"}

        self.service.apply_global_hook_key_defaults(runtime, config_root="")

        self.assertEqual(runtime["hook_stop_key"], "")
        self.assertEqual(runtime["hook_toggle_key"], "")


class ApplyGlobalDefaultsTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def _save_global_presets(self, root, presets):
        global_path = "user/hotkey_presets/global.json"
        self.service.repository.save_json(
            os.path.join(root, "config.json"),
            {"hotkey_presets_path": global_path, "hook_stop_key": "f11", "hook_toggle_key": "f12"},
        )
        self.service.repository.save_json(
            os.path.join(root, global_path),
            {"hotkey_presets": presets},
        )

    def test_replaces_hotkey_presets_when_global_file_is_readable_including_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            for presets in ([], [{"label": "Global", "value": "ctrl+g"}]):
                with self.subTest(presets=presets):
                    self._save_global_presets(root, presets)
                    runtime = {"hook_keys_individual": True, "hotkey_presets": [{"label": "Old"}]}

                    self.assertIs(self.service.apply_global_defaults(runtime, config_root=root), runtime)

                    self.assertEqual(runtime["hotkey_presets"], presets)

    def test_keeps_runtime_hotkey_presets_when_global_file_is_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self.service.repository.save_json(
                os.path.join(root, "config.json"),
                {"hotkey_presets_path": "user/hotkey_presets/missing.json"},
            )
            runtime = {"hook_keys_individual": True, "hotkey_presets": [{"label": "Edited"}]}

            self.service.apply_global_defaults(runtime, config_root=root)

            self.assertEqual(runtime["hotkey_presets"], [{"label": "Edited"}])

    def test_apply_global_defaults_drops_non_string_preset_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_presets(
                root,
                [
                    {"label": 1, "value": "ctrl+a"},
                    {"label": "ok", "value": "CTRL+B"},
                ],
            )
            runtime = {"hotkey_presets": [{"label": "Old", "value": "ctrl+o"}]}

            self.service.apply_global_defaults(runtime, config_root=root)

            self.assertEqual(runtime["hotkey_presets"], [{"label": "ok", "value": "ctrl+b"}])

    def test_injects_global_hook_keys_only_for_individual_off_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_presets(root, [])
            off_runtime = {"hook_keys_individual": False, "hook_stop_key": "", "hook_toggle_key": ""}
            on_runtime = {"hook_keys_individual": True, "hook_stop_key": "f3", "hook_toggle_key": "f4"}

            self.service.apply_global_defaults(off_runtime, config_root=root)
            self.service.apply_global_defaults(on_runtime, config_root=root)

            self.assertEqual((off_runtime["hook_stop_key"], off_runtime["hook_toggle_key"]), ("f11", "f12"))
            self.assertEqual((on_runtime["hook_stop_key"], on_runtime["hook_toggle_key"]), ("f3", "f4"))

    def test_apply_global_defaults_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            self._save_global_presets(root, [{"label": "Global", "value": "ctrl+g"}])
            runtime = {"hook_keys_individual": False, "hook_stop_key": "", "hook_toggle_key": ""}

            self.service.apply_global_defaults(runtime, config_root=root)
            once_applied = safe_deepcopy(runtime)
            self.service.apply_global_defaults(runtime, config_root=root)

            self.assertEqual(runtime, once_applied)


class KeymapFileIoTest(unittest.TestCase):
    def test_split_loading_coerces_referenced_keymap_non_string_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            repository.save_json(
                os.path.join(tmp, "map.json"),
                {"label": ["a"], "mappings": {"a": "b"}},
            )
            keymap_set = {"keymaps": [{"path": "map.json"}]}

            runtime = split_loading.build_runtime_data_from_split(
                service, keymap_set, config_root=tmp,
            )

            self.assertEqual(len(runtime["keymaps"]), 1)
            self.assertEqual(runtime["keymaps"][0]["label"], "")

    def test_non_string_ids_use_filename_stem_and_labels_become_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            path = os.path.join(tmp, "My_Map.json")
            for value in (None, 0, False, [], {}, 123, ["a"], {"a": 1}):
                with self.subTest(value=value):
                    repository.save_json(path, {"id": value, "label": value})
                    loaded = service.load_keymap_file(path)
                    self.assertEqual(loaded["id"], "my_map")
                    self.assertEqual(loaded["label"], "")

    def test_non_string_mapping_targets_are_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            path = os.path.join(tmp, "map.json")
            for value in (None, 0, False, [], {}, 123, ["a"], {"x": 1}):
                with self.subTest(value=value):
                    repository.save_json(path, {"mappings": {"a": value, "b": "c"}})
                    self.assertEqual(service.load_keymap_file(path)["mappings"], {"b": "c"})

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
    def test_load_sequence_file_coerces_non_string_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            path = os.path.join(tmp, "seq.json")
            for value in (None, 0, False, [], {}, 123, ["a"], {"a": 1}):
                with self.subTest(value=value):
                    repository.save_json(path, {
                        "label": value, "actions": [{"type": "text", "label": value}],
                    })
                    loaded = service.load_sequence_file(path)
                    self.assertEqual(loaded["label"], "")
                    self.assertEqual(loaded["actions"], [{"type": "text", "label": ""}])

    def test_normalize_sequence_payload_delegates_actions(self):
        service = ConfigService(JsonRepository())
        for sequence in ({}, {"actions": None}, {"actions": "x"}, {"actions": ["bad"]}):
            with self.subTest(sequence=sequence):
                with patch("keyseq.application.config_service.normalize_actions") as normalize:
                    normalize.return_value = [{"type": "text", "label": "normalized"}]
                    normalized = service._normalize_sequence_payload(sequence)
                    normalize.assert_called_once_with(sequence.get("actions"))
                    self.assertIs(normalized["actions"], normalize.return_value)

    def test_load_sequence_file_removes_non_dict_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = ConfigService(JsonRepository())
            path = Path(tmp) / "seq.json"
            path.write_text(
                '{"actions": [{"type": "hotkey", "value": "ctrl+c"}, "bad", 5]}',
                encoding="utf-8",
            )
            loaded = service.load_sequence_file(str(path))
            self.assertEqual(
                loaded["actions"],
                [{"type": "hotkey", "value": "ctrl+c", "label": ""}],
            )

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
            self.assertEqual(loaded["actions"], [{"type": "hotkey", "value": "ctrl+c", "label": ""}])
            self.assertEqual(loaded["_sequence_source_path"], path)
            self.assertTrue(loaded["_sequence_imported"])


class TriggerSetTypeNormalizationTest(unittest.TestCase):
    def test_load_trigger_set_coerces_non_string_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            path = os.path.join(tmp, "triggers.json")
            repository.save_json(path, {"triggers": [{
                "key": {"a": 1}, "label": ["a"],
                "actions": [{"type": "text", "label": 123}],
            }]})
            trigger = service.load_trigger_set_file(path, config_root=tmp)[0]
            self.assertEqual(trigger["key"], "")
            self.assertEqual(trigger["label"], "")
            self.assertEqual(trigger["actions"], [{"type": "text", "label": ""}])

    def test_non_string_sequence_paths_do_not_load_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            path = os.path.join(tmp, "triggers.json")
            for value in (None, 0, False, [], {}, 123, ["a"], {"a": 1}):
                with self.subTest(value=value):
                    repository.save_json(path, {"triggers": [{
                        "key": " F1 ", "label": " Keep ", "sequence_path": value,
                    }]})
                    with patch.object(service, "_load_optional_json") as load_reference:
                        trigger = service.load_trigger_set_file(path, config_root=tmp)[0]
                    load_reference.assert_not_called()
                    self.assertEqual(trigger["key"], "f1")
                    self.assertEqual(trigger["label"], "Keep")
                    self.assertNotIn(service.INTERNAL_SEQUENCE_SOURCE_PATH, trigger)

    def test_referenced_sequence_non_string_label_does_not_leak_repr(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonRepository()
            service = ConfigService(repository)
            path = os.path.join(tmp, "triggers.json")
            repository.save_json(os.path.join(tmp, "seq.json"), {"label": {"a": 1}})
            repository.save_json(path, {"triggers": [{
                "key": "f1", "label": "original", "sequence_path": "seq.json",
            }]})
            trigger = service.load_trigger_set_file(path, config_root=tmp)[0]
            self.assertEqual(trigger["label"], "")
            self.assertIn(service.INTERNAL_SEQUENCE_SOURCE_PATH, trigger)


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
                os.path.join("user", "hotkey_presets", "global"),
                os.path.join("user", "sequences"),
            ):
                self.assertTrue(os.path.isdir(os.path.join(root, relative_path)))


if __name__ == "__main__":
    unittest.main()
