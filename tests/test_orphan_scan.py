import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service import orphan_scan as orphan_scan_module
from keyseq.application.config_service import quarantine as quarantine_module
from keyseq.application.config_service import candidate_dirs, path_boundary, quarantine_manage
from keyseq.application.config_service.contracts import (
    KIND_HOTKEY_PRESETS,
    KIND_KEYMAP,
    KIND_SEQUENCE,
    KIND_TRIGGER_SET,
    ORPHAN_CANDIDATE,
    ORPHAN_EXCLUDED,
    ORPHAN_PROTECTED,
    ORPHAN_REFERENCED,
)
from keyseq.application.config_service.orphan_scan import (
    collect_protected_paths,
    normalize_scan_dirs,
    scan_orphans,
)
from keyseq.application.config_service.contracts import (
    SOURCE_REDIRECTED,
    SOURCE_DIRECTORY_UNREADABLE,
)
from keyseq.application.config_service.reference_scan import (
    collect_reference_paths,
)
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

    def _make_junction(self, junction, target):
        try:
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", junction, target],
                capture_output=True, check=False,
            )
        except OSError as error:
            self.skipTest(f"ジャンクションを作成できません: {error}")
        if result.returncode:
            self.skipTest(f"ジャンクションを作成できません: {result.stderr!r}")
        self.addCleanup(os.rmdir, junction)

    def test_candidate_junction_outside_config_is_excluded_before_reading(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = os.path.join(directory.name, "config")
        outside = os.path.join(directory.name, "outside")
        child = "user/keymaps/outside.json"
        self._save(root, os.path.join(outside, "outside.json"), {"mappings": {}})
        os.makedirs(os.path.join(root, "user"))
        self._make_junction(os.path.join(root, "user", "keymaps"), outside)
        with patch.object(self.service, "_load_optional_json",
                          wraps=self.service._load_optional_json) as loader:
            result = self._scan(root)
        self.assertEqual(self._states(result), {child: ORPHAN_EXCLUDED})
        self.assertNotIn(self._resolved(root, child), [call.args[0] for call in loader.call_args_list])
        self.assertTrue(os.path.isfile(os.path.join(outside, "outside.json")))

    def test_real_boundary_errors_exclude_candidates(self):
        with tempfile.TemporaryDirectory() as root:
            child = "user/keymaps/child.json"
            self._save(root, child, {"mappings": {}})
            for operation in ("realpath", "commonpath"):
                for error in (OSError("unreadable"), ValueError("invalid")):
                    with self.subTest(operation=operation, error=error), patch.object(
                        orphan_scan_module.os.path, operation, side_effect=error,
                    ):
                        result = self._scan(root)
                        self.assertEqual([entry.state for entry in result.entries], [ORPHAN_EXCLUDED])

    def test_real_boundary_does_not_override_protected_or_referenced(self):
        with tempfile.TemporaryDirectory() as root:
            protected, referenced = "user/keymaps/a.json", "user/keymaps/b.json"
            for child in (protected, referenced):
                self._save(root, child, {"mappings": {}})
            self._save(root, "user/keymap_sets/main.json", {"keymaps": [referenced]})
            with patch.object(path_boundary, "is_real_path_within",
                              side_effect=AssertionError("保護・参照ありは実体検証しない")):
                result = self._scan(root, protected_paths=[protected])
            self.assertEqual(self._states(result),
                             {protected: ORPHAN_PROTECTED, referenced: ORPHAN_REFERENCED})

    def test_external_scan_directory_still_references_config_child(self):
        with tempfile.TemporaryDirectory() as base:
            root, outside = os.path.join(base, "config"), os.path.join(base, "outside")
            child = "user/keymaps/child.json"
            self._save(root, child, {"mappings": {}})
            self._save(root, os.path.join(outside, "set.json"), {"keymaps": [child]})
            self.assertEqual(self._states(self._scan(root, scan_dirs=[outside])),
                             {child: ORPHAN_REFERENCED})

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
            self.assertEqual(result.missing_scan_dirs, ())
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

    def test_redirected_reference_warns_and_its_child_becomes_candidate(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = os.path.join(directory.name, "config")
        target = os.path.join(directory.name, "parents")
        child = "user/keymaps/child.json"
        self._save(root, child, {"mappings": {}})
        self._save(root, os.path.join(target, "linked.json"), {"keymaps": [child]})
        source_dir = self._resolved(root, "user/keymap_sets")
        os.mkdir(source_dir)
        link = os.path.join(source_dir, "linked.json")
        try:
            os.symlink(os.path.join(target, "linked.json"), link)
        except (OSError, NotImplementedError):
            self.skipTest("参照側のファイル symlink を作成できません")
        result = self._scan(root)
        self.assertEqual(result.unreadable_sources,
                         (("user/keymap_sets/linked.json", SOURCE_REDIRECTED),))
        self.assertEqual(self._states(result), {child: ORPHAN_CANDIDATE})

    def test_reference_directory_junction_keeps_child_referenced(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = os.path.join(directory.name, "config")
        target = os.path.join(directory.name, "parents")
        child = "user/keymaps/child.json"
        self._save(root, child, {"mappings": {}})
        self._save(root, os.path.join(target, "parent.json"), {"keymaps": [child]})
        self._make_junction(self._resolved(root, "user/keymap_sets"), target)
        result = self._scan(root)
        self.assertEqual(result.unreadable_sources, ())
        self.assertEqual(self._states(result), {child: ORPHAN_REFERENCED})

    def test_candidate_link_is_skipped_without_source_warning(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = os.path.join(directory.name, "config")
        target = os.path.join(directory.name, "target")
        self._save(root, os.path.join(target, "child.json"), {"mappings": {}})
        os.makedirs(self._resolved(root, "user/keymaps"))
        link = self._resolved(root, "user/keymaps/linked.json")
        try:
            os.symlink(os.path.join(target, "child.json"), link)
        except (OSError, NotImplementedError):
            self.skipTest("候補側のファイル symlink を作成できません")
        result = self._scan(root)
        self.assertEqual(result.entries, ())
        self.assertEqual(result.unreadable_sources, ())

    def test_unreadable_source_directory_warns_and_other_scans_continue(self):
        with tempfile.TemporaryDirectory() as root:
            child = "user/keymaps/child.json"
            self._save(root, child, {"mappings": {}})
            self._save(root, "denied/parent.json", {"keymaps": [child]})
            self._save(root, "readable/parent.json", {"keymaps": [child]})
            listdir = os.listdir

            def deny_source(path):
                if path == self._resolved(root, "denied"):
                    raise PermissionError("参照側の列挙拒否")
                return listdir(path)

            with patch.object(orphan_scan_module.os, "listdir", side_effect=deny_source):
                result = self._scan(root, scan_dirs=["denied", "readable"])
            self.assertEqual(result.unreadable_sources, (("denied", SOURCE_DIRECTORY_UNREADABLE),))
            self.assertEqual(self._states(result), {child: ORPHAN_REFERENCED})

    def test_unreadable_candidate_directory_is_empty_without_source_warning(self):
        with tempfile.TemporaryDirectory() as root:
            self._save(root, "user/keymaps/hidden.json", {"mappings": {}})
            self._save(root, "user/sequences/visible.json", {"actions": []})
            listdir = os.listdir

            def deny_candidates(path):
                if path == self._resolved(root, "user/keymaps"):
                    raise PermissionError("候補側の列挙拒否")
                return listdir(path)

            with patch.object(orphan_scan_module.os, "listdir", side_effect=deny_candidates):
                result = self._scan(root)
            self.assertEqual(result.unreadable_sources, ())
            self.assertEqual(self._states(result), {"user/sequences/visible.json": ORPHAN_CANDIDATE})

    def test_missing_default_directory_is_not_reported_but_user_directory_is(self):
        with tempfile.TemporaryDirectory() as root:
            missing = " Missing/../Specified "
            result = self._scan(root, scan_dirs=[missing])
            self.assertEqual(result.missing_scan_dirs, (missing,))
            self.assertEqual(result.entries, ())

    def test_candidate_dirs_use_shared_module_without_legacy_alias(self):
        for module in (orphan_scan_module, quarantine_manage):
            self.assertIs(module.candidate_dirs, candidate_dirs)
        self.assertEqual(
            tuple(spec[1] for spec in orphan_scan_module._CANDIDATE_SPECS),
            quarantine_manage.candidate_dirs.CANDIDATE_DIRS,
        )
        self.assertFalse(hasattr(quarantine_manage, "_CANDIDATE_DIRS"))
        self.assertFalse(hasattr(quarantine_manage, "_RESERVED_DIR"))

    def test_real_boundary_uses_shared_module_without_legacy_alias(self):
        self.assertFalse(hasattr(orphan_scan_module, "_is_real_path_within"))
        self.assertFalse(hasattr(orphan_scan_module, "is_real_path_within"))
        self.assertFalse(hasattr(quarantine_module, "is_real_path_within"))
        for module in (orphan_scan_module, quarantine_module, quarantine_manage):
            self.assertIs(module.path_boundary, path_boundary)
        with tempfile.TemporaryDirectory() as root:
            for path, expected in ((root, True), (os.path.join(root, "child.json"), True),
                                   (os.path.dirname(root), False)):
                with self.subTest(path=path):
                    self.assertEqual(path_boundary.is_real_path_within(path, root), expected)

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


class CollectProtectedPathsTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_collects_all_five_path_kinds_in_order(self):
        runtime = {
            "active_keymap_id": "km1",
            "keymaps": [{"id": "km1", self.service.INTERNAL_KEYMAP_SOURCE_PATH: "keymap.json",
                         self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: "triggers.json",
                         "triggers": [None, {self.service.INTERNAL_SEQUENCE_SOURCE_PATH: "sequence.json"}]}, None, "skip"],
            "triggers": [],
            "hotkey_presets_path": "presets.json",
        }
        self.assertEqual(collect_protected_paths(self.service, runtime, keymap_set_path="set.json"),
                         ("set.json", "keymap.json", "triggers.json", "sequence.json", "presets.json"))

    def test_keeps_stored_spelling_and_deduplicates_in_input_order(self):
        stored = "user/Keymaps/../Keymaps/Mixed.JSON"
        runtime = {
            "active_keymap_id": "km1",
            "keymaps": [{"id": "km1", self.service.INTERNAL_KEYMAP_SOURCE_PATH: f" {stored} ",
                         self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: stored,
                         "triggers": [{self.service.INTERNAL_SEQUENCE_SOURCE_PATH: " sequence.json "}]},
                        {self.service.INTERNAL_KEYMAP_SOURCE_PATH: " set.json "},
                        {self.service.INTERNAL_KEYMAP_SOURCE_PATH: None}],
            "triggers": [],
            "hotkey_presets_path": "sequence.json",
        }
        with patch.object(self.service, "canonical_path") as canonical, patch.object(
            self.service, "resolve_config_path",
        ) as resolve:
            paths = collect_protected_paths(self.service, runtime, keymap_set_path=" set.json ")
        self.assertEqual(paths, ("set.json", stored, "sequence.json"))
        canonical.assert_not_called()
        resolve.assert_not_called()

    def test_missing_or_invalid_runtime_values_are_safe(self):
        for runtime in (None, [], "invalid", {}, {"keymaps": [None, {}], "triggers": [3, {}]},
                        {"keymaps": "invalid", "triggers": {}}, {"hotkey_presets_path": 0}):
            for source, expected in ((" set.json ", ("set.json",)), (" ", ())):
                with self.subTest(runtime=runtime, source=source):
                    self.assertEqual(collect_protected_paths(
                        self.service, runtime, keymap_set_path=source,
                    ), expected)

    def test_facade_matches_module_function(self):
        runtime = {"hotkey_presets_path": 123}
        self.assertEqual(self.service.collect_protected_paths(runtime, keymap_set_path="set.json"),
                         collect_protected_paths(self.service, runtime, keymap_set_path="set.json"))
        self.assertEqual(self.service.collect_protected_paths(runtime, keymap_set_path=""), ("123",))


class NormalizeScanDirsTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = os.path.join(self.directory.name, "config")

    def _normalize(self, values):
        return normalize_scan_dirs(self.service, values, config_root=self.root)

    def test_non_string_elements_are_removed(self):
        self.assertEqual(self._normalize([None, 1, {}, ["nested"], "valid"]), ("valid",))

    def test_non_list_or_tuple_returns_empty_tuple(self):
        for values in (None, "directory", {"directory": []}):
            with self.subTest(values=values):
                self.assertEqual(self._normalize(values), ())

    def test_empty_and_whitespace_elements_are_removed(self):
        self.assertEqual(self._normalize(("", " \t\n", " Extra ")), ("Extra",))

    def test_aliases_are_deduplicated_in_input_order(self):
        absolute = os.path.join(self.root, "Extra", "Sets")
        self.assertEqual(self._normalize([
            "Extra/Sets", "Second", absolute, "Extra\\Sets", "Third", "Second",
        ]), ("Extra/Sets", "Second", "Third"))

    def test_storage_spelling_preserves_case_and_relative_or_absolute_location(self):
        outside = os.path.join(self.directory.name, "Outside")
        with patch.object(self.service, "canonical_path", side_effect=lambda path, root: path.lower()):
            self.assertEqual(self._normalize(["Mixed/Inside", outside]),
                             ("Mixed/Inside", outside.replace("\\", "/")))

    def test_missing_directory_is_kept_without_existence_checks(self):
        with patch.object(os.path, "exists", side_effect=AssertionError("existence check")), patch.object(
            os.path, "isdir", side_effect=AssertionError("directory check"),
        ):
            self.assertEqual(self._normalize(["NotCreated"]), ("NotCreated",))

    def test_facade_matches_module_function(self):
        values = [" Extra ", None, "Extra", "Other"]
        self.assertEqual(self.service.normalize_scan_dirs(values, config_root=self.root),
                         self._normalize(values))


if __name__ == "__main__":
    unittest.main()
