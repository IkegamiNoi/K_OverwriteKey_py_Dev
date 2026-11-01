"""未知の起動設定キー ui_language が保存経路で保持されることを固定する。"""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.application.config_service.split_payloads import build_startup_payload
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.shared.i18n import fix_language

fix_language("ja")


class StartupLanguagePreservationTest(unittest.TestCase):
    def test_write_startup_keeps_ui_language_when_writing_another_key(self):
        settings = {"ui_language": "ja", "custom_setting": "preserved"}
        app = SimpleNamespace(
            _startup_settings=settings,
            paths=SimpleNamespace(preferred_startup_path=Mock(return_value="startup.json")),
            config_service=SimpleNamespace(save_startup=Mock()),
        )

        self.assertTrue(StartupIo(app).write_startup({"ui_font_delta_pt": 2}))

        saved = app.config_service.save_startup.call_args.args[1]
        self.assertEqual(saved["ui_language"], "ja")
        self.assertEqual(saved["custom_setting"], "preserved")
        self.assertEqual(saved["ui_font_delta_pt"], 2)
        self.assertEqual(app._startup_settings, saved)

    def test_build_startup_payload_keeps_ui_language(self):
        service = SimpleNamespace(
            to_config_relative_or_absolute=Mock(return_value="config/keymaps/main.json"),
            resolve_startup_relative_path=Mock(return_value=""),
        )

        payload = build_startup_payload(
            service,
            {"ui_language": "en", "custom_setting": "preserved"},
            config_root="config",
            keymap_set_path="config/keymaps/main.json",
            legacy_path="",
        )

        self.assertEqual(payload["ui_language"], "en")
        self.assertEqual(payload["custom_setting"], "preserved")


if __name__ == "__main__":
    unittest.main()
