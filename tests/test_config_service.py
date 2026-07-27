import os
import tempfile
import unittest

from keyseq.application.config_service import ConfigService
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
            self.assertTrue(loaded["_sequence_imported"])


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
