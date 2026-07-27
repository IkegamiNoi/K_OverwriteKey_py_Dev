import unittest

from keyseq.presentation.startup_settings import load_startup_settings


class FakeConfigService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def load_startup(self, startup_path):
        self.calls.append(startup_path)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class StartupSettingsTest(unittest.TestCase):
    startup_path = "fake/startup.json"

    def test_empty_dict_uses_defaults_without_read_error(self):
        config_service = FakeConfigService({})
        read_errors = []

        result = load_startup_settings(
            config_service,
            self.startup_path,
            on_read_error=read_errors.append,
        )

        self.assertEqual(result, {"ui_font_delta_pt": 0})
        self.assertEqual(config_service.calls, [self.startup_path])
        self.assertEqual(read_errors, [])

    def test_read_exception_reports_same_exception_and_uses_defaults(self):
        read_error = ValueError("broken json")
        config_service = FakeConfigService(read_error)
        read_errors = []

        result = load_startup_settings(
            config_service,
            self.startup_path,
            on_read_error=read_errors.append,
        )

        self.assertEqual(result, {"ui_font_delta_pt": 0})
        self.assertEqual(config_service.calls, [self.startup_path])
        self.assertEqual(read_errors, [read_error])
        self.assertIs(read_errors[0], read_error)

    def test_non_dict_uses_defaults_without_read_error(self):
        config_service = FakeConfigService(["not", "a", "dict"])
        read_errors = []

        result = load_startup_settings(
            config_service,
            self.startup_path,
            on_read_error=read_errors.append,
        )

        self.assertEqual(result, {"ui_font_delta_pt": 0})
        self.assertEqual(config_service.calls, [self.startup_path])
        self.assertEqual(read_errors, [])

    def test_normal_dict_preserves_unknown_keys_and_normalizes_values(self):
        startup = {
            "keymap_set_path": "X.json",
            "last_used_directory": "D",
            "custom_setting": {"enabled": True},
            "ui_font_delta_pt": "5",
            "prompt_if_missing": 0,
        }
        config_service = FakeConfigService(startup)
        read_errors = []

        result = load_startup_settings(
            config_service,
            self.startup_path,
            on_read_error=read_errors.append,
        )

        self.assertIs(result, startup)
        self.assertEqual(
            result,
            {
                "keymap_set_path": "X.json",
                "last_used_directory": "D",
                "custom_setting": {"enabled": True},
                "ui_font_delta_pt": 3,
                "prompt_if_missing": 0,
            },
        )
        self.assertEqual(config_service.calls, [self.startup_path])
        self.assertEqual(read_errors, [])
