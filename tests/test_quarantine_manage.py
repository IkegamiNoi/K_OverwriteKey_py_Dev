import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service import quarantine, quarantine_manage as manage
from keyseq.infrastructure.json_repository import JsonRepository


UNIT = "20260906_101500"
CHILD = "user/keymaps/MixedCase.json"


class QuarantineManageTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "config"
        self.service = ConfigService(JsonRepository())

    def _path(self, stored):
        return Path(self.service.resolve_config_path(stored, str(self.root)))

    def _write(self, path, text="quarantined"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _unit(self, paths=(CHILD,), *, unit_id=UNIT, state=quarantine.ENTRY_MOVED):
        unit_dir = self.root / "quarantine" / unit_id
        entries = []
        for index, original in enumerate(paths):
            source = unit_dir / "user" / "keymaps" / f"{index}.json"
            self._write(source)
            entries.append(dict(kind="keymap", original_path=original, state=state,
                                quarantined_path=source.relative_to(self.root).as_posix()))
        manifest = {"created_at": "2026-09-06T10:15:00", "entries": entries}
        self._save_manifest(unit_dir, manifest)
        return unit_dir, manifest

    def _save_manifest(self, unit_dir, manifest):
        self.service.repository.save_json(str(unit_dir / "manifest.json"), manifest)

    def _list(self):
        return manage.list_quarantine_units(self.service, config_root=str(self.root))

    def _restore(self, unit_id=UNIT):
        return manage.restore_quarantine_unit(self.service, unit_id, config_root=str(self.root))

    def _snapshot(self):
        return {path.relative_to(self.root).as_posix():
                None if path.is_dir() else path.read_bytes() for path in self.root.rglob("*")}

    def test_list_without_root_does_not_create_it(self):
        self.assertEqual(self._list(), ())
        self.assertFalse(self.root.exists())

    def test_sorted_list_counts_actual_files_even_when_all_states_are_planned(self):
        self._unit(unit_id=UNIT + "_200", state=quarantine.ENTRY_PLANNED)
        unit_dir, manifest = self._unit((CHILD, "user/sequences/one.json"),
                                       state=quarantine.ENTRY_PLANNED)
        self._path(manifest["entries"][1]["quarantined_path"]).unlink()
        for name in ("foo", "2026-09-06"):
            (unit_dir.parent / name).mkdir()
        self._write(unit_dir.parent / "20260906_101500_3", "not a directory")
        units = self._list()
        self.assertEqual(tuple(unit.unit_id for unit in units), (UNIT, UNIT + "_200"))
        self.assertEqual(units[0], manage.QuarantineUnit(UNIT, "2026-09-06T10:15:00", 2, 1, True))
        self.assertEqual(units[1].remaining_count, 1)

    def test_invalid_manifests_are_listed_and_restore_does_not_touch_them(self):
        for index, payload in enumerate((None, "broken", "[]", '{"entries": {}}')):
            unit_id = f"{UNIT}_{index + 2}"
            unit_dir = self.root / "quarantine" / unit_id
            unit_dir.mkdir(parents=True)
            if payload is not None:
                self._write(unit_dir / "manifest.json", payload)
        before = self._snapshot()
        for unit in self._list():
            self.assertEqual(unit, manage.QuarantineUnit(unit.unit_id, "", 0, 0, False))
            self.assertEqual(self._restore(unit.unit_id).aborted_reason,
                             manage.RESTORE_ABORTED_NO_MANIFEST)
        self.assertEqual(len(self._list()), 4)
        self.assertEqual(self._snapshot(), before)

    def test_restore_all_four_directories_creates_parents_and_cleans_unit(self):
        paths = (CHILD, "user/trigger_sets/nested/a.json", "user/sequences/a.json",
                 "user/hotkey_presets/a.json")
        unit_dir, manifest = self._unit(paths)
        self.assertFalse((self.root / "user").exists())
        result = self._restore()
        self.assertEqual(result.restored, tuple(("keymap", path) for path in paths))
        self.assertEqual(result.skipped, ())
        self.assertEqual(result.aborted_reason, "")
        self.assertTrue(result.unit_removed)
        self.assertFalse(unit_dir.exists())
        for entry in manifest["entries"]:
            self.assertEqual(self._path(entry["original_path"]).read_text(encoding="utf-8"), "quarantined")
            self.assertFalse(self._path(entry["quarantined_path"]).exists())

    def test_planned_and_failed_states_do_not_prevent_restore(self):
        for index, state in enumerate((quarantine.ENTRY_PLANNED, quarantine.ENTRY_FAILED)):
            with self.subTest(state=state):
                child = f"user/keymaps/{index}.json"
                unit_id = f"{UNIT}_{index + 2}"
                self._unit((child,), unit_id=unit_id, state=state)
                self.assertEqual(self._restore(unit_id).restored, (("keymap", child),))
                self.assertEqual(self._path(child).read_text(encoding="utf-8"), "quarantined")

    def test_existing_destination_is_not_overwritten_and_manifest_is_unchanged(self):
        unit_dir, manifest = self._unit(state=quarantine.ENTRY_FAILED)
        self._write(self._path(CHILD), "existing")
        manifest_bytes = (unit_dir / "manifest.json").read_bytes()
        result = self._restore()
        self.assertEqual(result.skipped, ((CHILD, manage.RESTORE_SKIPPED_EXISTS),))
        self.assertEqual(result.restored, ())
        self.assertFalse(result.unit_removed)
        self.assertEqual(self._path(CHILD).read_text(encoding="utf-8"), "existing")
        self.assertTrue(self._path(manifest["entries"][0]["quarantined_path"]).exists())
        self.assertEqual((unit_dir / "manifest.json").read_bytes(), manifest_bytes)

    def test_outside_reserved_and_candidate_directory_itself_are_rejected(self):
        paths = ("../../outside.json", str(self.root.parent / "outside.json"),
                 "user/hotkey_presets/global/x.json", "user/keymaps", "user/keymaps/.",
                 str(self.root / "user" / "sequences"), "user/keymaps/../other.json")
        unit_dir, _ = self._unit(paths)
        before = self._snapshot()
        result = self._restore()
        self.assertEqual(result.skipped, tuple((path, manage.RESTORE_REJECTED_TARGET) for path in paths))
        self.assertEqual(result.restored, ())
        self.assertFalse(result.unit_removed)
        self.assertTrue(unit_dir.exists())
        self.assertEqual(self._snapshot(), before)
        self.assertFalse((self.root.parent / "outside.json").exists())

    def test_one_move_failure_does_not_stop_remaining_entries(self):
        second = "user/keymaps/second.json"
        unit_dir, _ = self._unit((CHILD, second))
        real_move = manage.shutil.move

        def move(source, target):
            if target == str(self._path(CHILD)):
                raise OSError("cannot move first file")
            return real_move(source, target)

        with patch.object(manage.shutil, "move", side_effect=move):
            result = self._restore()
        self.assertEqual(result.skipped, ((CHILD, manage.RESTORE_FAILED),))
        self.assertEqual(result.restored, (("keymap", second),))
        self.assertFalse(result.unit_removed)
        self.assertTrue(unit_dir.exists())
        self.assertEqual(self._path(second).read_text(encoding="utf-8"), "quarantined")

    def test_repeated_restore_skips_missing_sources_when_cleanup_previously_failed(self):
        unit_dir, _ = self._unit()
        manifest_bytes = (unit_dir / "manifest.json").read_bytes()
        with patch.object(manage.os, "remove", side_effect=OSError("cannot remove manifest")):
            first = self._restore()
        self.assertFalse(first.unit_removed)
        self.assertEqual(first.restored, (("keymap", CHILD),))
        self.assertEqual((unit_dir / "manifest.json").read_bytes(), manifest_bytes)
        second = self._restore()
        self.assertEqual(second.skipped, ((CHILD, manage.RESTORE_SOURCE_MISSING),))
        self.assertEqual(second.restored, ())
        self.assertTrue(second.unit_removed)
        self.assertEqual(self._restore().aborted_reason, manage.RESTORE_ABORTED_INVALID_ID)

    def test_invalid_ids_do_not_read_manifest_or_modify_anything(self):
        self._unit()
        before = self._snapshot()
        invalid = ("", "..", "../../etc", UNIT + "/child", UNIT + "\\child", "wrong",
                   "20260906_111111", UNIT + "\n", None)
        with patch.object(self.service, "_load_optional_json") as read:
            for unit_id in invalid:
                self.assertEqual(self._restore(unit_id).aborted_reason, manage.RESTORE_ABORTED_INVALID_ID)
        read.assert_not_called()
        self.assertEqual(self._snapshot(), before)

    def test_facades_forward_nondefault_arguments_and_return_identical_objects(self):
        units = (manage.QuarantineUnit(UNIT + "_90", "date", 4, 2, True),)
        result = manage.QuarantineRestoreResult(UNIT + "_90", (), (), False, "")
        root = str(self.root / "another")
        with patch.object(manage, "list_quarantine_units", return_value=units) as listing:
            self.assertIs(self.service.list_quarantine_units(config_root=root), units)
        listing.assert_called_once_with(self.service, config_root=root)
        with patch.object(manage, "restore_quarantine_unit", return_value=result) as restore:
            self.assertIs(self.service.restore_quarantine_unit(UNIT + "_90", config_root=root), result)
        restore.assert_called_once_with(self.service, UNIT + "_90", config_root=root)

    def test_unlisted_file_prevents_cleanup(self):
        unit_dir, _ = self._unit()
        self._write(unit_dir / "unlisted.txt", "keep")
        result = self._restore()
        self.assertFalse(result.unit_removed)
        self.assertEqual((unit_dir / "unlisted.txt").read_text(encoding="utf-8"), "keep")
        self.assertTrue((unit_dir / "manifest.json").exists())

    def test_missing_source_is_checked_before_rejected_target(self):
        unit_dir, manifest = self._unit(("../../outside.json",))
        self._path(manifest["entries"][0]["quarantined_path"]).unlink()
        self.assertEqual(self._restore().skipped, (("../../outside.json", manage.RESTORE_SOURCE_MISSING),))
        self.assertFalse(unit_dir.exists())

    def test_forged_source_does_not_move_external_file_or_manifest(self):
        unit_dir, manifest = self._unit((CHILD, "user/keymaps/second.json"))
        external = self.root.parent / "external.json"
        self._write(external, "external")
        manifest["entries"][0]["quarantined_path"] = str(external)
        manifest["entries"][1]["quarantined_path"] = str(unit_dir / "manifest.json")
        self._save_manifest(unit_dir, manifest)
        before = self._snapshot()
        result = self._restore()
        self.assertEqual(tuple(reason for _, reason in result.skipped), (manage.RESTORE_FAILED,) * 2)
        self.assertEqual(self._snapshot(), before)
        self.assertEqual(external.read_text(encoding="utf-8"), "external")

    def test_redirected_unit_is_ignored_without_loading_manifest(self):
        unit_dir, _ = self._unit()
        realpath = manage.os.path.realpath

        def redirect(path):
            return str(self.root.parent / "external") if str(path) == str(unit_dir) else realpath(path)

        with patch.object(manage.os.path, "realpath", side_effect=redirect):
            with patch.object(self.service, "_load_optional_json") as read:
                self.assertEqual(self._list(), ())
                self.assertEqual(self._restore().aborted_reason, manage.RESTORE_ABORTED_INVALID_ID)
        read.assert_not_called()

    def test_real_symlink_unit_is_not_followed(self):
        unit_dir, _ = self._unit()
        link = unit_dir.parent / (UNIT + "_2")
        try:
            os.symlink(unit_dir, link, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"シンボリックリンクを作成できません: {error}")
        self.addCleanup(link.unlink)
        manifest_bytes = (unit_dir / "manifest.json").read_bytes()
        self.assertEqual(tuple(unit.unit_id for unit in self._list()), (UNIT,))
        self.assertEqual(self._restore(link.name).aborted_reason, manage.RESTORE_ABORTED_INVALID_ID)
        self.assertEqual((unit_dir / "manifest.json").read_bytes(), manifest_bytes)

    def test_parent_creation_failure_is_reported_and_other_entries_continue(self):
        second = "user/sequences/second.json"
        unit_dir, _ = self._unit((CHILD, second))
        real_makedirs = manage.os.makedirs

        def makedirs(path, *args, **kwargs):
            if str(path) == str(self._path(CHILD).parent):
                raise PermissionError("cannot create parent")
            return real_makedirs(path, *args, **kwargs)

        with patch.object(manage.os, "makedirs", side_effect=makedirs):
            result = self._restore()
        self.assertEqual(result.skipped, ((CHILD, manage.RESTORE_FAILED),))
        self.assertEqual(result.restored, (("keymap", second),))
        self.assertTrue(unit_dir.exists())

    def test_malformed_entries_do_not_interrupt_valid_restore(self):
        unit_dir, manifest = self._unit()
        manifest["entries"][:0] = [None, {"quarantined_path": []}]
        self._save_manifest(unit_dir, manifest)
        result = self._restore()
        self.assertEqual(result.restored, (("keymap", CHILD),))
        self.assertEqual(result.skipped, (("", manage.RESTORE_SOURCE_MISSING),) * 2)


if __name__ == "__main__":
    unittest.main()
