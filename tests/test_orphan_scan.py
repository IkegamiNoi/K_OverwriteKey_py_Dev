import os
import tempfile
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service.orphan_scan import (
    KIND_HOTKEY_PRESETS, KIND_KEYMAP, KIND_SEQUENCE, KIND_TRIGGER_SET,
    ORPHAN_CANDIDATE, ORPHAN_EXCLUDED, ORPHAN_PROTECTED, ORPHAN_REFERENCED,
    scan_orphans,
)
from keyseq.application.config_service.reference_scan import collect_reference_paths
from keyseq.infrastructure.json_repository import JsonRepository


CHILD_SHAPES = (
    (KIND_KEYMAP, "keymaps", "mappings", {}),
    (KIND_TRIGGER_SET, "trigger_sets", "triggers", []),
    (KIND_SEQUENCE, "sequences", "actions", []),
    (KIND_HOTKEY_PRESETS, "hotkey_presets", "hotkey_presets", []),
)


class OrphanScanTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())
        self.repository = JsonRepository()

    def test_multiple_sets_reference_children_and_second_level_sequences(self):
        with tempfile.TemporaryDirectory() as root:
            expected = {}
            for name in ("first", "second"):
                keymap = f"user/keymaps/{name}.json"
                trigger = f"user/trigger_sets/{name}.json"
                sequence = f"user/sequences/{name}.json"
                self._save(root, f"user/keymap_sets/{name}.json", {
                    "keymaps": [keymap], "trigger_set_path": trigger,
                })
                self._save(root, keymap, {"mappings": {}})
                self._save(root, trigger, {"triggers": [{"sequence_path": sequence}]})
                self._save(root, sequence, {"actions": []})
                expected.update(dict.fromkeys((keymap, trigger, sequence), ORPHAN_REFERENCED))
            for _, directory, key, value in CHILD_SHAPES:
                child = f"user/{directory}/unused.json"
                self._save(root, child, {key: value})
                expected[child] = ORPHAN_CANDIDATE
            self.assertEqual(self._states(self._scan(root)), expected)

    def test_individual_presets_are_referenced_even_when_disabled(self):
        with tempfile.TemporaryDirectory() as root:
            child = "user/hotkey_presets/individual.json"
            self._save(root, child, {"hotkey_presets": []})
            self._save(root, "user/keymap_sets/main.json", {
                "hotkey_presets_individual": False, "hotkey_presets_path": child,
            })
            self.assertEqual(self._states(self._scan(root)), {child: ORPHAN_REFERENCED})

    def test_current_set_outside_config_is_scanned_without_startup_config(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "config")
            source = os.path.join(base, "current.json")
            child = "user/keymaps/current.json"
            self._save(root, child, {"mappings": {}})
            self._save(root, source, {"keymaps": [child]})
            result = self._scan(root, current_keymap_set_path=source)
            self.assertEqual(self._states(result), {child: ORPHAN_REFERENCED})
            self.assertFalse(os.path.exists(os.path.join(root, "config.json")))

    def test_startup_set_outside_default_directory_is_scanned(self):
        with tempfile.TemporaryDirectory() as root:
            source = "other/startup.json"
            child = "user/keymaps/startup.json"
            self._save(root, child, {"mappings": {}})
            self._save(root, source, {"active_keymap_path": child})
            result = self._scan(root, startup_keymap_set_path=f" {source} ")
            self.assertEqual(self._states(result), {child: ORPHAN_REFERENCED})

    def test_candidates_are_only_direct_json_files_in_four_directories(self):
        with tempfile.TemporaryDirectory() as root:
            expected = {}
            for _, directory, key, value in CHILD_SHAPES:
                child = f"user/{directory}/direct.JSON"
                self._save(root, child, {key: value})
                expected[child] = ORPHAN_CANDIDATE
                self._save(root, f"user/{directory}/nested/child.json", {key: value})
                self._save(root, f"user/{directory}/ignored.txt", {key: value})
                os.makedirs(os.path.join(root, "user", directory, "folder.json"))
            self._save(root, "user/hotkey_presets/global/default.json", {"hotkey_presets": []})
            self._save(root, "quarantine/child.json", {"mappings": {}})
            self._save(root, "user/keylayout/child.json", {"mappings": {}})
            self.assertEqual(self._states(self._scan(root)), expected)

    def test_protection_accepts_missing_and_external_paths_without_references(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "config")
            child = "user/keymaps/protected.json"
            external = os.path.join(base, "external.json")
            self._save(root, child, {"mappings": {}})
            self._save(root, external, {"mappings": {}})
            paths = [f" {child} ", "missing.json", external, "", "   "]
            self.assertEqual(
                self._states(self._scan(root, protected_paths=paths)),
                {child: ORPHAN_PROTECTED},
            )

    def test_all_kinds_exclude_missing_keys_wrong_types_lists_and_broken_json(self):
        with tempfile.TemporaryDirectory() as root:
            expected = {}
            for _, directory, key, value in CHILD_SHAPES:
                for name, payload in (("missing", {}), ("list", []), ("wrong", {key: None})):
                    child = f"user/{directory}/{name}.json"
                    self._save(root, child, payload)
                    expected[child] = ORPHAN_EXCLUDED
                broken = f"user/{directory}/broken.json"
                self._save(root, broken, {key: value})
                with open(self._resolved(root, broken), "w", encoding="utf-8") as stream:
                    stream.write("{")
                expected[broken] = ORPHAN_EXCLUDED
            self.assertEqual(self._states(self._scan(root)), expected)

    def test_missing_scan_dirs_keep_input_spelling_and_other_scans_continue(self):
        with tempfile.TemporaryDirectory() as root:
            child = "user/keymaps/main.json"
            self._save(root, child, {"mappings": {}})
            self._save(root, "extra/set.json", {"keymaps": [child]})
            self._save(root, "user/keymap_sets/empty.json", {"keymaps": []})
            missing = " missing/../NotCreated "
            result = self._scan(root, scan_dirs=["", "   ", missing, " extra "])
            self.assertEqual(result.missing_scan_dirs, (missing,))
            self.assertEqual(self._states(result), {child: ORPHAN_REFERENCED})

    def test_scan_dirs_are_nonrecursive_and_accept_absolute_directories(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "config")
            extra = os.path.join(base, "extra")
            child, nested = "user/keymaps/direct.json", "user/keymaps/nested.json"
            for path in (child, nested):
                self._save(root, path, {"mappings": {}})
            self._save(root, os.path.join(extra, "set.JSON"), {"keymaps": [child]})
            self._save(root, os.path.join(extra, "nested", "set.json"), {"keymaps": [nested]})
            self._save(root, "user/keymap_sets/nested/set.json", {"keymaps": [nested]})
            result = self._scan(root, scan_dirs=[extra])
            self.assertEqual(self._states(result), {child: ORPHAN_REFERENCED, nested: ORPHAN_CANDIDATE})

    def test_source_diagnostics_pass_through_reference_scan(self):
        with tempfile.TemporaryDirectory() as root:
            broken, other = "user/keymap_sets/broken.json", "user/keymap_sets/other.json"
            self._save(root, broken, {})
            self._save(root, other, {"label": "not a set"})
            with open(self._resolved(root, broken), "w", encoding="utf-8") as stream:
                stream.write("{")
            paths = [self._resolved(root, path) for path in (broken, other)]
            reference = collect_reference_paths(self.service, paths, config_root=root)
            result = self._scan(root)
            self.assertEqual(len(reference.unreadable_sources), 1)
            self.assertEqual(len(reference.non_keymap_set_sources), 1)
            self.assertEqual(result.unreadable_sources, reference.unreadable_sources)
            self.assertEqual(result.non_keymap_set_sources, reference.non_keymap_set_sources)

    def test_global_presets_from_config_are_referenced(self):
        with tempfile.TemporaryDirectory() as root:
            child = "user/hotkey_presets/global-in-candidates.json"
            self._save(root, child, {"hotkey_presets": []})
            self._save(root, "config.json", {"hotkey_presets_path": child})
            self.assertEqual(self._states(self._scan(root)), {child: ORPHAN_REFERENCED})

    def test_external_layout_references_resolve_against_both_bases(self):
        for stored in ("user/keymaps/layout.json", "config/user/keymaps/layout.json"):
            with self.subTest(stored=stored), tempfile.TemporaryDirectory() as base:
                root = os.path.join(base, "config")
                child = "user/keymaps/layout.json"
                self._save(root, child, {"mappings": {}})
                self._save(root, "user/keymap_sets/main.json", {
                    "keymaps": [], "external_keyboard_layouts": [stored],
                })
                self.assertEqual(self._states(self._scan(root)), {child: ORPHAN_REFERENCED})

    def test_scan_never_writes_or_creates_missing_directories(self):
        with tempfile.TemporaryDirectory() as root:
            before = self._tree_snapshot(root)
            result = self._scan(root)
            self.assertEqual(result.entries, ())
            self.assertEqual(len(result.missing_scan_dirs), 1)
            self.assertEqual(self._tree_snapshot(root), before)
            self._save(root, "user/keymaps/unused.json", {"mappings": {}})
            self._save(root, "user/keymap_sets/main.json", {"keymaps": []})
            before = self._tree_snapshot(root)
            self._scan(root)
            self.assertEqual(self._tree_snapshot(root), before)
            for directory in ("trigger_sets", "sequences", "hotkey_presets"):
                self.assertFalse(os.path.exists(os.path.join(root, "user", directory)))
            self.assertFalse(os.path.exists(os.path.join(root, "quarantine")))

    def test_stored_paths_are_relative_and_entries_have_stable_kind_filename_order(self):
        with tempfile.TemporaryDirectory() as root:
            for _, directory, key, value in reversed(CHILD_SHAPES):
                for name in ("z.json", "A.JSON", "b.json"):
                    self._save(root, f"user/{directory}/{name}", {key: value})
            expected = [(kind, f"user/{directory}/{name}")
                        for kind, directory, _, _ in CHILD_SHAPES
                        for name in ("A.JSON", "b.json", "z.json")]
            result = self._scan(root)
            self.assertEqual([(entry.kind, entry.stored_path) for entry in result.entries], expected)
            self.assertEqual(self._scan(root), result)
            for entry in result.entries:
                self.assertFalse(os.path.isabs(entry.stored_path))
                self.assertNotEqual(entry.stored_path, self.service.canonical_path(entry.stored_path, root))

    def test_config_service_delegate_matches_module_function(self):
        with tempfile.TemporaryDirectory() as root:
            child = "user/keymaps/main.json"
            self._save(root, child, {"mappings": {}})
            self._save(root, "extra/main.json", {"keymaps": [child]})
            options = dict(config_root=root, scan_dirs=["extra"],
                           startup_keymap_set_path="extra/main.json",
                           current_keymap_set_path="extra/main.json", protected_paths=[child])
            self.assertEqual(self.service.scan_orphans(**options), scan_orphans(self.service, **options))

    def test_protection_precedes_reference_and_shape_reads_are_lazy(self):
        with tempfile.TemporaryDirectory() as root:
            protected, referenced = "user/keymaps/protected.json", "user/keymaps/referenced.json"
            for child in (protected, referenced):
                self._save(root, child, [])
            self._save(root, "user/keymap_sets/main.json", {"keymaps": [protected, referenced]})
            with patch.object(self.service, "_load_optional_json", wraps=self.service._load_optional_json) as loader:
                result = self._scan(root, protected_paths=[self._resolved(root, protected)])
            self.assertEqual(self._states(result), {protected: ORPHAN_PROTECTED, referenced: ORPHAN_REFERENCED})
            loaded = [call.args[0] for call in loader.call_args_list]
            for child in (protected, referenced):
                self.assertNotIn(self._resolved(root, child), loaded)

    def _scan(self, root, **overrides):
        options = dict(config_root=root, scan_dirs=[], startup_keymap_set_path="",
                       current_keymap_set_path="", protected_paths=[])
        options.update(overrides)
        return scan_orphans(self.service, **options)

    def _states(self, result):
        return {entry.stored_path: entry.state for entry in result.entries}

    def _resolved(self, root, path):
        return self.service.resolve_config_path(path, root)

    def _save(self, root, path, payload):
        self.repository.save_json(self._resolved(root, path), payload)

    def _tree_snapshot(self, root):
        directories: set[str] = set()
        files: dict[str, bytes] = {}
        for directory, _, filenames in os.walk(root):
            directories.add(os.path.relpath(directory, root))
            for filename in filenames:
                path = os.path.join(directory, filename)
                with open(path, "rb") as stream:
                    files[os.path.relpath(path, root)] = stream.read()
        return directories, files


if __name__ == "__main__":
    unittest.main()
