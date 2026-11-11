import ast
import os
import tempfile
import unittest
from pathlib import Path

from keyseq.application.config_service import ConfigService
from keyseq.domain.config import (
    build_base_config,
    build_sample_config,
    ensure_config_compatibility,
)
from keyseq.domain.default_profile import (
    MACOS_DEFAULT_PROFILE,
    WINDOWS_DEFAULT_PROFILE,
)
from keyseq.infrastructure.json_repository import JsonRepository


class DefaultProfileTest(unittest.TestCase):
    def test_windows_profile_keeps_existing_values(self):
        self.assertEqual(WINDOWS_DEFAULT_PROFILE.hotkey_presets, (
            ("Alt+Tab", "alt+tab"),
            ("Win+D", "windows+d"),
            ("Win+E", "windows+e"),
            ("Ctrl+Shift+Esc", "ctrl+shift+esc"),
            ("Win+R", "windows+r"),
            ("Win+Tab", "windows+tab"),
            ("Win+X", "windows+x"),
            ("Alt+F4", "alt+f4"),
        ))
        self.assertEqual(len(WINDOWS_DEFAULT_PROFILE.hotkey_presets), 8)
        self.assertEqual(WINDOWS_DEFAULT_PROFILE.select_line, ("home", "shift+end"))
        self.assertEqual(WINDOWS_DEFAULT_PROFILE.copy, "ctrl+c")
        self.assertEqual(WINDOWS_DEFAULT_PROFILE.paste, "ctrl+v")
        self.assertEqual(WINDOWS_DEFAULT_PROFILE.switch_app, "alt+tab")

    def test_macos_profile_values(self):
        self.assertEqual(MACOS_DEFAULT_PROFILE.hotkey_presets, (
            ("Command+Tab", "windows+tab"),
            ("Command+Space", "windows+space"),
            ("Command+Q", "windows+q"),
            ("Command+W", "windows+w"),
            ("Command+H", "windows+h"),
            ("Command+M", "windows+m"),
            ("Option+Command+Esc", "alt+windows+esc"),
            ("Ctrl+↑", "ctrl+up"),
        ))
        self.assertEqual(len(MACOS_DEFAULT_PROFILE.hotkey_presets), 8)
        self.assertEqual(MACOS_DEFAULT_PROFILE.select_line, ("windows+left", "windows+shift+right"))
        self.assertEqual(MACOS_DEFAULT_PROFILE.copy, "windows+c")
        self.assertEqual(MACOS_DEFAULT_PROFILE.paste, "windows+v")
        self.assertEqual(MACOS_DEFAULT_PROFILE.switch_app, "windows+tab")

    def test_profile_module_has_no_os_detection_or_ui_dependency(self):
        path = Path(__file__).resolve().parents[1] / "keyseq/domain/default_profile.py"
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        forbidden_roots = {"os", "sys", "tkinter"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                self.assertFalse(imported & forbidden_roots)
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], forbidden_roots)
            elif isinstance(node, ast.Attribute):
                self.assertFalse(
                    isinstance(node.value, ast.Name)
                    and node.value.id in {"os", "sys"}
                    and node.attr in {"name", "platform"}
                )


class ProfiledConfigTest(unittest.TestCase):
    def test_base_config_uses_profile_preset_order_and_labels(self):
        self.assertEqual(
            build_base_config(MACOS_DEFAULT_PROFILE)["hotkey_presets"],
            [
                {"label": label, "value": value}
                for label, value in MACOS_DEFAULT_PROFILE.hotkey_presets
            ],
        )
        self.assertEqual(
            build_base_config()["hotkey_presets"],
            build_base_config(WINDOWS_DEFAULT_PROFILE)["hotkey_presets"],
        )

    def test_sample_config_uses_profile_actions_and_combined_sequence_order(self):
        triggers = build_sample_config(MACOS_DEFAULT_PROFILE)["keymaps"][0]["triggers"]
        self.assertEqual(
            [[action["value"] for action in trigger["actions"]] for trigger in triggers],
            [
                ["windows+left", "windows+shift+right"],
                ["windows+c"],
                ["windows+v"],
                ["windows+tab"],
                [
                    "windows+left", "windows+shift+right", "windows+c",
                    "windows+tab", "windows+v", "windows+tab",
                ],
            ],
        )

    def test_compatibility_uses_profile_only_for_missing_defaults(self):
        self.assertEqual(
            ensure_config_compatibility({}, profile=MACOS_DEFAULT_PROFILE)["hotkey_presets"],
            build_base_config(MACOS_DEFAULT_PROFILE)["hotkey_presets"],
        )
        self.assertEqual(
            ensure_config_compatibility({})["hotkey_presets"],
            build_base_config(WINDOWS_DEFAULT_PROFILE)["hotkey_presets"],
        )
        existing = [{"label": "User", "value": "ctrl+u"}]
        self.assertEqual(
            ensure_config_compatibility(
                {"hotkey_presets": existing}, profile=MACOS_DEFAULT_PROFILE
            )["hotkey_presets"],
            existing,
        )

    def test_config_service_new_and_load_data_use_macos_profile(self):
        service = ConfigService(JsonRepository(), default_profile=MACOS_DEFAULT_PROFILE)
        expected = build_base_config(MACOS_DEFAULT_PROFILE)["hotkey_presets"]
        self.assertEqual(service.new_base_data()["hotkey_presets"], expected)
        sample = service.new_default_data()
        self.assertEqual(sample["hotkey_presets"], expected)
        self.assertEqual(
            [
                [action["value"] for action in trigger["actions"]]
                for trigger in sample["keymaps"][0]["triggers"]
            ],
            [
                ["windows+left", "windows+shift+right"], ["windows+c"],
                ["windows+v"], ["windows+tab"],
                [
                    "windows+left", "windows+shift+right", "windows+c",
                    "windows+tab", "windows+v", "windows+tab",
                ],
            ],
        )

        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "user", "keymap_sets", "empty.json")
            service.repository.save_json(path, {})
            loaded = service.load_runtime_data_from_keymap_set_path(path, config_root=root)
            legacy_path = os.path.join(root, "legacy.json")
            service.repository.save_json(legacy_path, {})
            legacy_loaded = service.load(legacy_path)
        self.assertEqual(loaded["hotkey_presets"], expected)
        self.assertEqual(legacy_loaded["hotkey_presets"], expected)

    def test_save_uses_profile_defaults_and_preserves_custom_presets(self):
        service = ConfigService(JsonRepository(), default_profile=MACOS_DEFAULT_PROFILE)
        expected = build_base_config(MACOS_DEFAULT_PROFILE)["hotkey_presets"]
        with tempfile.TemporaryDirectory() as root:
            saved, _ = service.save_runtime_data("", {}, config_root=root)
            self.assertEqual(saved["hotkey_presets"], expected)

            custom_presets = [{"label": "Personal", "value": "ctrl+u"}]
            saved_custom, _ = service.save_runtime_data(
                "", {"hotkey_presets": custom_presets}, config_root=root
            )
        self.assertEqual(saved_custom["hotkey_presets"], custom_presets)


if __name__ == "__main__":
    unittest.main()
