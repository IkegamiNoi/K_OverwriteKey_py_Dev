import os
import tempfile
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service.contracts import (
    SOURCE_MISSING,
    SOURCE_UNREADABLE,
)
from keyseq.application.config_service.reference_scan import (
    _entry_path,
    _is_keymap_set,
    _path_value,
    _source_path,
    collect_reference_paths,
)
from keyseq.infrastructure.json_repository import JsonRepository


class ReferenceScanTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())
        self.repository = JsonRepository()

    def test_verification_1_non_string_paths_return_empty(self):
        for value in ({"a": 1}, [1], 123):
            with self.subTest(value=value):
                self.assertEqual(_source_path(value), "")
                self.assertEqual(_path_value(value), "")

    def test_verification_2_entry_path_rejects_non_string_path(self):
        self.assertEqual(_entry_path({"path": {"a": 1}}), "")

    def test_verification_3_falsy_and_normal_paths_are_unchanged(self):
        for value in (0, False, [], {}, None):
            with self.subTest(value=value):
                self.assertEqual(_source_path(value), "")
                self.assertEqual(_path_value(value), "")
        self.assertEqual(_source_path("  User/Keymaps/A.json  "), "User/Keymaps/A.json")

    def test_collects_all_first_level_keymap_set_paths(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            paths = {
                "trigger": "user/trigger_sets/main.json",
                "keymap": "user/keymaps/main.json",
                "active": "user/keymaps/active.json",
                "presets": "user/hotkey_presets/main.json",
            }
            self._save_resolved(root, keymap_set, {
                "trigger_set_path": paths["trigger"],
                "keymaps": [{"path": paths["keymap"]}],
                "active_keymap_path": paths["active"],
                "hotkey_presets_path": paths["presets"],
            })
            self._save_resolved(root, paths["trigger"], {"triggers": []})
            self._save_resolved(root, paths["keymap"], {"mappings": {}})
            self._save_resolved(root, paths["active"], {"mappings": {}})
            self._save_resolved(root, paths["presets"], {"hotkey_presets": []})

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.referenced, self._canonicals(root, paths.values()))

    def test_collects_legacy_string_keymap_entries(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            keymap = "user/keymaps/legacy.json"
            self._save_resolved(root, keymap_set, {"keymaps": [keymap]})
            self._save_resolved(root, keymap, {"mappings": {}})

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.referenced, self._canonicals(root, [keymap]))

    def test_collects_hotkey_presets_when_individual_is_false(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            presets = "user/hotkey_presets/main.json"
            self._save_resolved(root, keymap_set, {
                "hotkey_presets_individual": False,
                "hotkey_presets_path": presets,
            })
            self._save_resolved(root, presets, {"hotkey_presets": []})

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.referenced, self._canonicals(root, [presets]))

    def test_collects_sequence_paths_from_trigger_set(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            trigger_set = "user/trigger_sets/main.json"
            sequence = "user/sequences/copy.json"
            self._save_resolved(root, keymap_set, {"trigger_set_path": trigger_set})
            self._save_resolved(root, trigger_set, {"triggers": [{"sequence_path": sequence}]})
            self._save_resolved(root, sequence, {"actions": []})

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.referenced, self._canonicals(root, [trigger_set, sequence]))

    def test_collects_new_keymap_trigger_set_and_sequence_references(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            keymap = "user/keymaps/main.json"
            trigger_set = "user/trigger_sets/main.json"
            sequence = "user/sequences/copy.json"
            self._save_resolved(root, keymap_set, {"keymaps": [{"path": keymap}]})
            self._save_resolved(root, keymap, {
                "mappings": {}, "trigger_set_path": trigger_set,
            })
            self._save_resolved(root, trigger_set, {
                "triggers": [{"sequence_path": sequence}],
            })
            self._save_resolved(root, sequence, {"actions": []})

            result = self._collect(root, [keymap_set])

            self.assertEqual(
                result.referenced,
                self._canonicals(root, [keymap, trigger_set, sequence]),
            )

    def test_collects_legacy_keymap_set_trigger_set_and_sequence_references(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/legacy.json"
            trigger_set = "user/trigger_sets/legacy.json"
            sequence = "user/sequences/legacy.json"
            self._save_resolved(root, keymap_set, {"trigger_set_path": trigger_set})
            self._save_resolved(root, trigger_set, {
                "triggers": [{"sequence_path": sequence}],
            })
            self._save_resolved(root, sequence, {"actions": []})

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.referenced, self._canonicals(root, [trigger_set, sequence]))

    def test_collects_legacy_and_per_keymap_trigger_sets_together(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/mixed.json"
            keymap = "user/keymaps/main.json"
            old_trigger_set = "user/trigger_sets/legacy.json"
            new_trigger_set = "user/trigger_sets/per_keymap.json"
            old_sequence = "user/sequences/legacy.json"
            new_sequence = "user/sequences/per_keymap.json"
            self._save_resolved(root, keymap_set, {
                "keymaps": [{"path": keymap}],
                "trigger_set_path": old_trigger_set,
            })
            self._save_resolved(root, keymap, {
                "mappings": {}, "trigger_set_path": new_trigger_set,
            })
            self._save_resolved(root, old_trigger_set, {
                "triggers": [{"sequence_path": old_sequence}],
            })
            self._save_resolved(root, new_trigger_set, {
                "triggers": [{"sequence_path": new_sequence}],
            })
            self._save_resolved(root, old_sequence, {"actions": []})
            self._save_resolved(root, new_sequence, {"actions": []})

            result = self._collect(root, [keymap_set])

            self.assertEqual(
                result.referenced,
                self._canonicals(root, [
                    keymap, old_trigger_set, new_trigger_set, old_sequence, new_sequence,
                ]),
            )

    def test_unreadable_keymap_is_reported_without_following_its_trigger_set(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            keymap = "user/keymaps/broken.json"
            trigger_set = "user/trigger_sets/unavailable.json"
            self._save_resolved(root, keymap_set, {"keymaps": [{"path": keymap}]})
            self._save_resolved(root, keymap, {"mappings": {}})
            self._save_resolved(root, trigger_set, {"triggers": []})
            with open(self._resolved(root, keymap), "w", encoding="utf-8") as stream:
                stream.write("{")

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.unreadable_sources, ((keymap, SOURCE_UNREADABLE),))
            self.assertIn(self._canonical(root, keymap), result.referenced)
            self.assertNotIn(self._canonical(root, trigger_set), result.referenced)

    def test_keymap_set_detection_excludes_mapping_files_but_keeps_legacy_sets(self):
        self.assertFalse(_is_keymap_set({"mappings": {}, "trigger_set_path": "triggers.json"}))
        self.assertTrue(_is_keymap_set({"trigger_set_path": "triggers.json"}))

    def test_records_unreadable_trigger_set_without_its_sequences(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            trigger_set = "user/trigger_sets/broken.json"
            sequence = "user/sequences/copy.json"
            self._save_resolved(root, keymap_set, {"trigger_set_path": trigger_set})
            self._save_resolved(root, trigger_set, {"triggers": [{"sequence_path": sequence}]})
            self._save_resolved(root, sequence, {"actions": []})
            with open(self._resolved(root, trigger_set), "w", encoding="utf-8") as stream:
                stream.write("{")

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.unreadable_sources, ((trigger_set, SOURCE_UNREADABLE),))
            self.assertIn(self._canonical(root, trigger_set), result.referenced)
            self.assertNotIn(self._canonical(root, sequence), result.referenced)

    def test_records_missing_and_unreadable_keymap_sets(self):
        with tempfile.TemporaryDirectory() as root:
            missing = "user/keymap_sets/missing.json"
            broken = "user/keymap_sets/broken.json"
            self._save_resolved(root, broken, {"keymaps": []})
            with open(self._resolved(root, broken), "w", encoding="utf-8") as stream:
                stream.write("{")

            result = self._collect(root, [missing, broken])

            self.assertEqual(
                result.unreadable_sources,
                ((missing, SOURCE_MISSING), (broken, SOURCE_UNREADABLE)),
            )

    def test_records_json_without_keymap_set_keys_as_non_keymap_set(self):
        with tempfile.TemporaryDirectory() as root:
            source = "user/keymap_sets/other.json"
            self._save_resolved(root, source, {"label": "Other"})

            result = self._collect(root, [source])

            self.assertEqual(result.non_keymap_set_sources, (source,))
            self.assertEqual(result.unreadable_sources, ())
            self.assertEqual(result.referenced, frozenset())

    def test_collects_external_layout_paths_from_both_bases(self):
        with tempfile.TemporaryDirectory() as root:
            config_root = os.path.join(root, "config")
            keymap_set = "user/keymap_sets/main.json"
            layout = "user/keylayout/custom.json"
            self._save_resolved(config_root, keymap_set, {
                "keymaps": [],
                "external_keyboard_layouts": [layout],
            })
            self._save_resolved(config_root, layout, {"keys": []})
            self._save_resolved(os.path.dirname(config_root), layout, {"keys": []})

            result = self._collect(config_root, [keymap_set])

            self.assertEqual(
                result.referenced,
                self._canonicals(config_root, [layout])
                | self._canonicals(os.path.dirname(config_root), [layout]),
            )

    def test_deduplicates_relative_absolute_and_separator_variants(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            relative = "user\\keymaps\\main.json"
            absolute = self._resolved(root, relative).replace("\\", "/")
            self._save_resolved(root, keymap_set, {
                "keymaps": [relative, relative.replace("\\", "/"), absolute],
            })
            self._save_resolved(root, relative, {"mappings": {}})

            result = self._collect(root, [keymap_set])

            self.assertEqual(result.referenced, self._canonicals(root, [relative]))

    def test_reads_shared_trigger_set_once(self):
        with tempfile.TemporaryDirectory() as root:
            first = "user/keymap_sets/first.json"
            second = "user/keymap_sets/second.json"
            trigger_set = "user/trigger_sets/shared.json"
            self._save_resolved(root, first, {"trigger_set_path": trigger_set})
            self._save_resolved(root, second, {"trigger_set_path": trigger_set})
            self._save_resolved(root, trigger_set, {"triggers": []})

            with patch.object(self.service, "_load_optional_json", wraps=self.service._load_optional_json) as loader:
                self._collect(root, [first, second])

            loaded_paths = [call.args[0] for call in loader.call_args_list]
            self.assertEqual(loaded_paths.count(self._resolved(root, trigger_set)), 1)
            self.assertEqual(loader.call_count, 3)

    def test_scan_is_read_only_and_creates_no_files_or_directories(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            trigger_set = "user/trigger_sets/main.json"
            sequence = "user/sequences/copy.json"
            self._save_resolved(root, keymap_set, {"trigger_set_path": trigger_set})
            self._save_resolved(root, trigger_set, {"triggers": [{"sequence_path": sequence}]})
            self._save_resolved(root, sequence, {"actions": []})
            before = self._tree_snapshot(root)

            self._collect(root, [keymap_set])

            self.assertEqual(self._tree_snapshot(root), before)

    def test_config_service_delegate_matches_module_function(self):
        with tempfile.TemporaryDirectory() as root:
            keymap_set = "user/keymap_sets/main.json"
            keymap = "user/keymaps/main.json"
            self._save_resolved(root, keymap_set, {"keymaps": [keymap]})
            self._save_resolved(root, keymap, {"mappings": {}})

            module_result = collect_reference_paths(
                self.service, [keymap_set], config_root=root
            )
            delegated_result = self.service.collect_reference_paths(
                [keymap_set], config_root=root
            )

            self.assertEqual(delegated_result, module_result)

    def _collect(self, root, keymap_set_paths):
        return collect_reference_paths(self.service, keymap_set_paths, config_root=root)

    def _resolved(self, root, stored_path):
        return self.service.resolve_config_path(stored_path, root)

    def _canonical(self, root, stored_path):
        return self.service.canonical_path(self._resolved(root, stored_path), root)

    def _canonicals(self, root, stored_paths):
        return frozenset(self._canonical(root, path) for path in stored_paths)

    def _save_resolved(self, root, stored_path, payload):
        self.repository.save_json(self._resolved(root, stored_path), payload)

    def _tree_snapshot(self, root):
        directories: set[str] = set()
        files: dict[str, bytes] = {}
        for directory, _, filenames in os.walk(root):
            directories.add(os.path.relpath(directory, root))
            for filename in filenames:
                path = os.path.join(directory, filename)
                files[os.path.relpath(path, root)] = self._read_bytes(path)
        return directories, files

    def _read_bytes(self, path):
        with open(path, "rb") as stream:
            return stream.read()


if __name__ == "__main__":
    unittest.main()
