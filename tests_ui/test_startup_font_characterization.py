"""起動設定とフォント設定の現行 App 挙動を固定する特性テスト。"""
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation import app as app_module


class StartupFontCharacterizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_startup_patch = patch.object(
            app_module.ConfigService,
            "load_startup",
            return_value={},
        )
        cls._makedirs_patch = patch.object(app_module.os, "makedirs")
        cls._load_startup_patch.start()
        cls._makedirs_patch.start()
        try:
            cls.app = app_module.App()
            cls.app.update_idletasks()
        finally:
            cls._makedirs_patch.stop()
            cls._load_startup_patch.stop()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def test_coerce_font_delta_value_table(self):
        cases = (
            ("x", 0),
            (None, 0),
            (object(), 0),
            (-100, -3),
            (-4, -3),
            (-3, -3),
            (-1, -1),
            (0, 0),
            (2, 2),
            (3, 3),
            (4, 3),
            (100, 3),
            ("2", 2),
            ("-3", -3),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(self.app._coerce_font_delta(value), expected)

    def test_load_startup_settings_truth_table(self):
        read_error = ValueError("broken json")
        cases = (
            ("missing", {}, {"ui_font_delta_pt": 0, "prompt_if_missing": True}, None),
            ("read_error", read_error, {"ui_font_delta_pt": 0, "prompt_if_missing": True}, read_error),
            ("non_dict_string", "not a dict", {"ui_font_delta_pt": 0, "prompt_if_missing": True}, None),
            ("non_dict_list", [], {"ui_font_delta_pt": 0, "prompt_if_missing": True}, None),
            ("valid_dict", {"ui_font_delta_pt": "5", "prompt_if_missing": 0}, {"ui_font_delta_pt": 3, "prompt_if_missing": False}, None),
        )

        for name, startup, expected, expected_error in cases:
            with self.subTest(case=name):
                showwarning = Mock()
                with patch.object(self.app.config_service, "load_startup") as load_startup, patch.object(
                    app_module.messagebox,
                    "showwarning",
                    showwarning,
                ):
                    if isinstance(startup, Exception):
                        load_startup.side_effect = startup
                    else:
                        load_startup.return_value = startup
                    result = self.app._load_startup_settings()

                self.assertEqual(result, expected)
                load_startup.assert_called_once_with(self.app.startup_path)
                if expected_error is None:
                    showwarning.assert_not_called()
                else:
                    showwarning.assert_called_once_with(
                        "startup.json 読込失敗",
                        f"startup.json の読込に失敗しました。\n{expected_error}\n\n既定設定で起動します。",
                    )

    def test_load_startup_settings_preserves_unknown_keys_through_save(self):
        startup = {
            "keymap_set_path": "X.json",
            "last_used_directory": "D",
            "ui_font_delta_pt": "1",
        }
        with patch.object(self.app.config_service, "load_startup", return_value=startup), patch.object(
            app_module.messagebox,
            "showwarning",
        ) as showwarning:
            result = self.app._load_startup_settings()

        self.assertEqual(
            result,
            {
                "keymap_set_path": "X.json",
                "last_used_directory": "D",
                "ui_font_delta_pt": 1,
                "prompt_if_missing": True,
            },
        )
        showwarning.assert_not_called()

        self.app._startup_settings = result
        with patch.object(self.app.config_service, "save_startup") as save_startup:
            self.app.config_io.write_startup({"ui_font_delta_pt": 2})

        save_startup.assert_called_once()
        self.assertEqual(
            save_startup.call_args.args[1],
            {
                "prompt_if_missing": True,
                "ui_font_delta_pt": 2,
                "last_used_directory": "D",
                "keymap_set_path": "X.json",
            },
        )
        self.assertEqual(self.app._startup_settings["keymap_set_path"], "X.json")
        self.assertEqual(self.app._startup_settings["last_used_directory"], "D")

    def test_set_ui_font_delta_applies_only_real_changes(self):
        self.app._ui_font_delta_pt = 0
        self.app.ui_vars.ui_font_delta_var.set(0)
        self.app.ui_vars.flash_message_var.set("unchanged")

        with patch.object(self.app.config_io, "write_startup") as write_startup, patch.object(
            app_module,
            "apply_global_theme",
        ) as apply_global_theme, patch.object(app_module, "build_menu_bar") as build_menu_bar, patch.object(
            app_module,
            "bind_menu_shortcuts",
        ) as bind_menu_shortcuts:
            self.app.set_ui_font_delta(0)

            self.assertEqual(self.app._ui_font_delta_pt, 0)
            self.assertEqual(self.app.ui_vars.ui_font_delta_var.get(), 0)
            self.assertEqual(self.app.ui_vars.flash_message_var.get(), "unchanged")
            write_startup.assert_not_called()
            apply_global_theme.assert_not_called()
            build_menu_bar.assert_not_called()
            bind_menu_shortcuts.assert_not_called()

            self.app.set_ui_font_delta(2)

            self.assertEqual(self.app._ui_font_delta_pt, 2)
            self.assertEqual(self.app.ui_vars.ui_font_delta_var.get(), 2)
            self.assertEqual(self.app.ui_vars.flash_message_var.get(), "フォントサイズを +2 にしました。")
            apply_global_theme.assert_called_once_with(self.app, font_delta_pt=2)
            write_startup.assert_called_once_with({"ui_font_delta_pt": 2})
            build_menu_bar.assert_called_once_with(self.app)
            bind_menu_shortcuts.assert_not_called()


if __name__ == "__main__":
    unittest.main()
