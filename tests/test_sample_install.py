import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service.sample_install import SAMPLE_DIR, sample_keymap_set_path
from keyseq.infrastructure.json_repository import JsonRepository


class SampleInstallTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "config"
        self.service = ConfigService(JsonRepository())
        self.path = Path(self.service.sample_keymap_set_path(str(self.root)))

    def install(self, **kwargs):
        return self.service.install_sample(
            config_root=str(self.root), keyboard_layout_id=kwargs.pop("keyboard_layout_id", "us_tkl"),
            **kwargs,
        )

    def snapshot(self):
        return {
            path.relative_to(self.root).as_posix(): (path.stat().st_mtime_ns, path.read_bytes())
            for path in self.root.rglob("*") if path.is_file()
        }

    def test_writes_fixed_paths_without_startup_or_user_files(self):
        result = self.install(keyboard_layout_id="us_full")
        self.assertEqual(result.status, "written", result.error)
        self.assertEqual(result.error, "")
        self.assertEqual(result.keymap_set_path, str(self.path))
        self.assertEqual(SAMPLE_DIR, "sample")
        self.assertEqual(sample_keymap_set_path(str(self.root)), str(self.path))
        expected = {"sample/keymap_sets/sample.json"}
        for directory in ("keymaps", "trigger_sets"):
            expected.update(f"sample/{directory}/{name}.json" for name in (
                "shortcuts", "right_hand", "numpad",
            ))
        expected.update(f"sample/sequences/{name}.json" for name in (
            "select_line", "copy", "paste", "switch_app", "paste_line_to_app",
            "right_hand_guide", "numpad_guide",
        ))
        self.assertEqual(set(self.snapshot()), expected)
        self.assertFalse((self.root / "config.json").exists())
        self.assertFalse(any(path.is_file() for path in (self.root / "user").rglob("*")))
        loaded = self.service.load_runtime_data_from_keymap_set_path(
            str(self.path), config_root=str(self.root),
        )
        self.assertEqual(len(loaded["keymaps"]), 3)
        self.assertEqual(loaded["hook_stop_key"], "f12")
        self.assertEqual(loaded["hook_toggle_key"], "f1")
        self.assertIs(loaded["hook_keys_individual"], True)
        self.assertEqual(loaded["keyboard_layout"], "us_full")
        self.assertTrue(self.service.check_sample_complete(config_root=str(self.root)))

    def test_jis_registration_and_existing_sample_preserve_layout(self):
        result = self.install(
            keyboard_layout_id="jis", external_layout_path="user/keylayout/jis.json",
        )
        self.assertEqual(result.status, "written", result.error)
        loaded = self.service.load_runtime_data_from_keymap_set_path(
            str(self.path), config_root=str(self.root),
        )
        self.assertEqual(loaded["keyboard_layout"], "jis")
        self.assertEqual(loaded["external_keyboard_layouts"], [{"path": "user/keylayout/jis.json"}])
        before = self.snapshot()
        self.assertEqual(self.install().status, "existing")
        self.assertEqual(self.snapshot(), before)

    def test_existing_sample_is_not_written(self):
        self.assertEqual(self.install().status, "written")
        before = self.snapshot()
        with patch.object(self.service.repository, "save_json") as save:
            result = self.install(keyboard_layout_id="jis")
        self.assertEqual(result.status, "existing", result.error)
        self.assertEqual(result.error, "")
        save.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_missing_or_invalid_references_are_incomplete_and_unchanged(self):
        self.assertEqual(self.install().status, "written")
        for relative in (
            "keymaps/shortcuts.json", "trigger_sets/shortcuts.json", "sequences/copy.json",
        ):
            path = self.root / SAMPLE_DIR / relative
            original = path.read_bytes()
            for content in (None, b"{broken", b"null"):
                with self.subTest(relative=relative, content=content):
                    if content is None:
                        path.unlink()
                    else:
                        path.write_bytes(content)
                    before = self.snapshot()
                    with patch.object(self.service.repository, "save_json") as save:
                        self.assertFalse(self.service.check_sample_complete(config_root=str(self.root)))
                        result = self.install()
                    self.assertEqual(result.status, "incomplete")
                    self.assertTrue(result.error)
                    save.assert_not_called()
                    self.assertEqual(self.snapshot(), before)
                    path.write_bytes(original)

    def test_invalid_keymap_set_is_incomplete(self):
        self.path.parent.mkdir(parents=True)
        for content in (b"{broken", b"null", b"{}"):
            with self.subTest(content=content):
                self.path.write_bytes(content)
                before = self.snapshot()
                self.assertEqual(self.install().status, "incomplete")
                self.assertEqual(self.snapshot(), before)

    def test_reachable_sequence_outside_sample_is_checked(self):
        self.assertEqual(self.install().status, "written")
        trigger_path = self.root / SAMPLE_DIR / "trigger_sets/shortcuts.json"
        payload = self.service.repository.load_json(str(trigger_path))
        payload["triggers"][0]["sequence_path"] = "custom/edited.json"
        self.service.repository.save_json(str(trigger_path), payload)
        self.assertEqual(self.install().status, "incomplete")
        self.service.repository.save_json(str(self.root / "custom/edited.json"), {"actions": []})
        self.assertEqual(self.install().status, "existing")

    def test_leftover_children_are_overwritten(self):
        child = self.root / SAMPLE_DIR / "sequences/copy.json"
        child.parent.mkdir(parents=True)
        child.write_text("broken leftover", encoding="utf-8")
        self.assertEqual(self.install().status, "written")
        self.assertIsInstance(self.service.repository.load_json(str(child)), dict)
        self.assertTrue(self.service.check_sample_complete(config_root=str(self.root)))

    def test_failure_leaves_no_keymap_set_and_retry_succeeds(self):
        save_json = self.service.repository.save_json
        calls = []

        def fail_keymap_set(path, payload):
            calls.append(Path(path).relative_to(self.root).as_posix())
            if os.path.abspath(path) == str(self.path):
                raise OSError("sample write failed")
            save_json(path, payload)

        with patch.object(self.service.repository, "save_json", side_effect=fail_keymap_set):
            result = self.install()
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error, "OSError: sample write failed")
        self.assertFalse(self.path.exists())
        self.assertEqual(len(calls), 14)
        self.assertTrue(all(path.startswith("sample/sequences/") for path in calls[:7]))
        self.assertTrue(all(path.startswith("sample/trigger_sets/") for path in calls[7:10]))
        self.assertTrue(all(path.startswith("sample/keymaps/") for path in calls[10:13]))
        self.assertEqual(calls[-1], "sample/keymap_sets/sample.json")
        self.assertFalse((self.root / "config.json").exists())
        self.assertEqual(self.install().status, "written")

    def test_startup_entry_default_writes_and_false_preserves_existing(self):
        self.assertEqual(self.install().status, "written")
        data = self.service.new_default_data()
        self.service.save_runtime_data(str(self.path), data, config_root=str(self.root))
        startup_path = self.root / "config.json"
        self.assertTrue(startup_path.is_file())
        before = (startup_path.stat().st_mtime_ns, startup_path.read_bytes())
        self.service.save_runtime_data(
            str(self.path), data, config_root=str(self.root), write_startup_entry=False,
        )
        self.assertEqual((startup_path.stat().st_mtime_ns, startup_path.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
