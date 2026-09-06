import inspect
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service import quarantine as quarantine_module
from keyseq.application.config_service.orphan_scan import (
    KIND_KEYMAP, KIND_SEQUENCE, ORPHAN_CANDIDATE, scan_orphans,
)
from keyseq.application.config_service.quarantine import (
    ENTRY_FAILED, ENTRY_MOVED, ENTRY_PLANNED, MANIFEST_FILE_NAME, QUARANTINE_DIR_NAME,
    QUARANTINE_MANIFEST_WRITE_FAILED, QUARANTINE_MOVE_FAILED, quarantine_orphans,
)
from keyseq.infrastructure.json_repository import JsonRepository


FIXED_NOW = datetime(2026, 9, 6, 10, 15, 0)


class QuarantineTest(unittest.TestCase):
    def setUp(self):
        self.service = ConfigService(JsonRepository())
        self.repository = JsonRepository()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = os.path.join(self.directory.name, "config")

    def _resolved(self, path, root=None):
        return self.service.resolve_config_path(path, root or self.root)

    def _save(self, path, payload, root=None):
        self.repository.save_json(self._resolved(path, root), payload)

    def _quarantine(self, presented_paths, **overrides):
        options = dict(config_root=self.root, scan_dirs=[], startup_keymap_set_path="",
                       current_keymap_set_path="", protected_paths=[])
        options.update(overrides)
        return quarantine_orphans(self.service, presented_paths, **options)

    def _scan(self, **overrides):
        options = dict(config_root=self.root, scan_dirs=[], startup_keymap_set_path="",
                       current_keymap_set_path="", protected_paths=[])
        options.update(overrides)
        return scan_orphans(self.service, **options)

    def _quarantine_root(self):
        return os.path.join(self.root, QUARANTINE_DIR_NAME)

    def _manifest(self, unit_id):
        path = os.path.join(self._quarantine_root(), unit_id, MANIFEST_FILE_NAME)
        with open(path, "r", encoding="utf-8") as stream:
            return json.load(stream)

    def _quarantined_file(self, unit_id, path):
        return os.path.join(self._quarantine_root(), unit_id, *path.split("/"))

    def test_move_keeps_relative_structure_and_leaves_no_original(self):
        self._save("user/keymaps/foo.json", {"mappings": {"a": "b"}})
        result = self._quarantine(["user/keymaps/foo.json"])
        self.assertEqual(result.moved, ((KIND_KEYMAP, "user/keymaps/foo.json"),))
        self.assertEqual((result.failed, result.dropped_paths, result.aborted_reason), ((), (), ""))
        moved_path = self._quarantined_file(result.unit_id, "user/keymaps/foo.json")
        self.assertTrue(os.path.isfile(moved_path))
        self.assertFalse(os.path.exists(self._resolved("user/keymaps/foo.json")))
        with open(moved_path, "r", encoding="utf-8") as stream:
            self.assertEqual(json.load(stream), {"mappings": {"a": "b"}})

    def test_manifest_is_written_in_unit_dir_with_stored_paths(self):
        self._save("user/sequences/one.json", {"actions": []})
        result = self._quarantine(["user/sequences/one.json"])
        manifest = self._manifest(result.unit_id)
        self.assertEqual(datetime.fromisoformat(manifest["created_at"]).year, datetime.now().year)
        self.assertEqual(manifest["entries"], [{
            "kind": KIND_SEQUENCE,
            "original_path": "user/sequences/one.json",
            "quarantined_path":
                f"{QUARANTINE_DIR_NAME}/{result.unit_id}/user/sequences/one.json",
            "state": ENTRY_MOVED,
        }])
        text = json.dumps(manifest, ensure_ascii=False)
        self.assertNotIn("\\", text)
        self.assertNotIn(os.path.normcase(os.path.abspath(self.root)), text)

    def test_manifest_is_written_before_any_move_with_planned_states(self):
        for name in ("first", "second"):
            self._save(f"user/keymaps/{name}.json", {"mappings": {}})
        events = []
        real_save = self.service.repository.save_json
        real_move = shutil.move

        def save_json(path, data):
            events.append(("save", tuple(entry["state"] for entry in data["entries"])))
            real_save(path, data)

        def move(source, destination):
            events.append(("move", os.path.basename(source)))
            return real_move(source, destination)

        with patch.object(self.service.repository, "save_json", side_effect=save_json):
            with patch.object(quarantine_module.shutil, "move", side_effect=move):
                self._quarantine(["user/keymaps/first.json", "user/keymaps/second.json"])
        self.assertEqual(events[0], ("save", (ENTRY_PLANNED, ENTRY_PLANNED)))
        self.assertEqual(events[1], ("move", "first.json"))
        self.assertEqual(events[2], ("save", (ENTRY_MOVED, ENTRY_PLANNED)))

    def test_unwritable_manifest_moves_nothing_and_leaves_no_directory(self):
        paths = ["user/keymaps/first.json", "user/trigger_sets/second.json"]
        self._save(paths[0], {"mappings": {}})
        self._save(paths[1], {"triggers": []})
        with patch.object(self.service.repository, "save_json", side_effect=OSError("書き込み不可")):
            with patch.object(quarantine_module.shutil, "move",
                              side_effect=AssertionError("中止後に移動してはならない")):
                result = self._quarantine(paths)
        self.assertEqual(result.aborted_reason, QUARANTINE_MANIFEST_WRITE_FAILED)
        self.assertEqual((result.unit_id, result.moved, result.failed), ("", (), ()))
        for path in paths:
            self.assertTrue(os.path.isfile(self._resolved(path)))
        self.assertFalse(os.path.exists(self._quarantine_root()))

    def test_candidate_referenced_after_presentation_is_dropped(self):
        child = "user/keymaps/foo.json"
        self._save(child, {"mappings": {}})
        self._save("user/keymap_sets/main.json", {"keymaps": [child]})
        result = self._quarantine([child])
        self.assertEqual(result.dropped_paths, (child,))
        self.assertEqual((result.unit_id, result.moved, result.newly_orphan_count), ("", (), 0))
        self.assertTrue(os.path.isfile(self._resolved(child)))
        self.assertFalse(os.path.exists(self._quarantine_root()))

    def test_candidate_that_became_orphan_after_presentation_is_not_moved(self):
        presented = "user/keymaps/presented.json"
        newly = "user/keymaps/newly.json"
        for path in (presented, newly):
            self._save(path, {"mappings": {}})
        result = self._quarantine([presented])
        self.assertEqual(result.newly_orphan_count, 1)
        self.assertEqual(result.moved, ((KIND_KEYMAP, presented),))
        self.assertTrue(os.path.isfile(self._resolved(newly)))
        self.assertFalse(os.path.exists(self._quarantined_file(result.unit_id, newly)))

    def test_empty_intersection_creates_no_directory(self):
        self._save("user/keymaps/foo.json", {"mappings": {}})
        for presented in ([], ["", "  "], ["user/keymaps/missing.json"]):
            with self.subTest(presented=presented):
                result = self._quarantine(presented)
                self.assertEqual((result.unit_id, result.moved, result.failed), ("", (), ()))
                self.assertFalse(os.path.exists(self._quarantine_root()))

    def test_scan_alone_does_not_create_quarantine_root(self):
        self._save("user/keymaps/foo.json", {"mappings": {}})
        result = self._scan()
        self.assertTrue(any(entry.state == ORPHAN_CANDIDATE for entry in result.entries))
        self.assertFalse(os.path.exists(self._quarantine_root()))

    def test_second_run_in_same_second_uses_serial_unit_id(self):
        for name in ("first", "second"):
            self._save(f"user/keymaps/{name}.json", {"mappings": {}})
        with patch.object(quarantine_module, "_now", return_value=FIXED_NOW):
            first = self._quarantine(["user/keymaps/first.json"])
            second = self._quarantine(["user/keymaps/second.json"])
        self.assertEqual((first.unit_id, second.unit_id), ("20260906_101500", "20260906_101500_2"))
        self.assertEqual(self._manifest(first.unit_id)["created_at"], "2026-09-06T10:15:00")
        for unit_id, name in ((first.unit_id, "first"), (second.unit_id, "second")):
            self.assertTrue(os.path.isfile(
                self._quarantined_file(unit_id, f"user/keymaps/{name}.json")
            ))

    def test_failed_move_is_reported_and_does_not_stop_the_rest(self):
        paths = ["user/keymaps/first.json", "user/keymaps/second.json"]
        for path in paths:
            self._save(path, {"mappings": {}})
        real_move = shutil.move

        def move(source, destination):
            if os.path.basename(source) == "first.json":
                raise OSError("移動できません")
            return real_move(source, destination)

        with patch.object(quarantine_module.shutil, "move", side_effect=move):
            result = self._quarantine(paths)
        self.assertEqual(result.failed, ((paths[0], QUARANTINE_MOVE_FAILED),))
        self.assertEqual(result.moved, ((KIND_KEYMAP, paths[1]),))
        self.assertEqual(
            [entry["state"] for entry in self._manifest(result.unit_id)["entries"]],
            [ENTRY_FAILED, ENTRY_MOVED],
        )
        self.assertTrue(os.path.isfile(self._resolved(paths[0])))
        self.assertFalse(os.path.exists(self._resolved(paths[1])))

    def test_api_has_no_runtime_argument_and_only_relocates_content(self):
        parameters = inspect.signature(quarantine_orphans).parameters
        self.assertNotIn("runtime", parameters)
        self.assertEqual(list(parameters)[:2], ["service", "presented_paths"])
        self._save("user/hotkey_presets/one.json", {"hotkey_presets": [{"label": "A"}]})
        result = self._quarantine(["user/hotkey_presets/one.json"])
        moved_path = self._quarantined_file(result.unit_id, "user/hotkey_presets/one.json")
        with open(moved_path, "r", encoding="utf-8") as stream:
            self.assertEqual(json.load(stream), {"hotkey_presets": [{"label": "A"}]})
        self.assertEqual(sorted(os.listdir(self._resolved("user/hotkey_presets"))), [])

    def test_protected_and_referenced_paths_are_never_moved(self):
        orphan = "user/keymaps/orphan.json"
        protected = "user/keymaps/protected.json"
        referenced = "user/sequences/referenced.json"
        for path in (orphan, protected):
            self._save(path, {"mappings": {}})
        self._save(referenced, {"actions": []})
        self._save("user/trigger_sets/main.json", {"triggers": [{"sequence_path": referenced}]})
        self._save("user/keymap_sets/main.json", {"trigger_set_path": "user/trigger_sets/main.json"})
        result = self._quarantine([orphan, protected, referenced], protected_paths=[protected])
        self.assertEqual(result.moved, ((KIND_KEYMAP, orphan),))
        self.assertEqual(sorted(result.dropped_paths), sorted([protected, referenced]))
        for path in (protected, referenced):
            self.assertTrue(os.path.isfile(self._resolved(path)))

    def test_quarantined_files_are_not_candidates_on_a_later_scan(self):
        child = "user/keymaps/foo.json"
        self._save(child, {"mappings": {}})
        result = self._quarantine([child])
        entries = self._scan().entries
        self.assertEqual([entry.stored_path for entry in entries], [])
        self.assertTrue(os.path.isfile(self._quarantined_file(result.unit_id, child)))

    def test_facade_matches_module_function(self):
        other_root = os.path.join(self.directory.name, "other")
        child = "user/keymaps/foo.json"
        for root in (self.root, other_root):
            self._save(child, {"mappings": {}}, root=root)
        with patch.object(quarantine_module, "_now", return_value=FIXED_NOW):
            module_result = self._quarantine([child])
            facade_result = self.service.quarantine_orphans(
                [child], config_root=other_root, scan_dirs=[], startup_keymap_set_path="",
                current_keymap_set_path="", protected_paths=[],
            )
        self.assertEqual(facade_result, module_result)
        self.assertEqual(module_result.moved, ((KIND_KEYMAP, child),))


if __name__ == "__main__":
    unittest.main()
