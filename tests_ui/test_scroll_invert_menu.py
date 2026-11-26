"""UI coverage for the scroll direction settings menu and startup value."""
import unittest
from unittest.mock import patch

from keyseq.domain.mouse_scroll import ScrollInvert
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.shared.i18n import fix_language

fix_language("ja")


class ScrollInvertMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_startup_patch = patch.object(
            app_module.ConfigService, "load_startup", return_value={"ui_language": "ja"},
        )
        cls._ensure_dirs_patch = patch.object(app_module.ConfigService, "ensure_split_config_dirs")
        cls._load_config_patch = patch.object(StartupIo, "load_startup_and_config")
        cls._load_startup_patch.start()
        cls._ensure_dirs_patch.start()
        cls._load_config_patch.start()
        try:
            cls.app = app_module.App()
            cls.app.update_idletasks()
        finally:
            cls._load_config_patch.stop()
            cls._ensure_dirs_patch.stop()
            cls._load_startup_patch.stop()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def _make_app_with_startup_settings(self, settings):
        load_startup_patch = patch.object(app_module, "load_startup_settings", return_value=settings)
        load_config_patch = patch.object(app_module.ConfigService, "load_startup", return_value={})
        ensure_dirs_patch = patch.object(app_module.ConfigService, "ensure_split_config_dirs")
        startup_io_patch = patch.object(StartupIo, "load_startup_and_config")
        for active_patch in (load_startup_patch, load_config_patch, ensure_dirs_patch, startup_io_patch):
            active_patch.start()
        try:
            app = app_module.App()
        finally:
            for active_patch in (startup_io_patch, ensure_dirs_patch, load_config_patch, load_startup_patch):
                active_patch.stop()
        return app

    def _settings_menu(self):
        menubar = self.app.menubar
        settings_index = next(
            index
            for index in range(menubar.index("end") + 1)
            if menubar.type(index) == "cascade" and menubar.entrycget(index, "label") == "設定"
        )
        return self.app.nametowidget(menubar.entrycget(settings_index, "menu"))

    def test_scroll_direction_submenu_is_between_physical_names_and_font_size(self):
        settings = self._settings_menu()
        labels = [
            settings.entrycget(index, "label") if settings.type(index) == "cascade" else ""
            for index in range(settings.index("end") + 1)
        ]
        physical_index = next(
            index for index in range(settings.index("end") + 1)
            if settings.type(index) == "checkbutton" and settings.entrycget(index, "label") == "物理キー名を表示"
        )
        scroll_index = labels.index("スクロールの向き")
        font_index = labels.index("フォントサイズ")
        self.assertGreater(scroll_index, physical_index)
        self.assertLess(scroll_index, font_index)
        self.assertEqual(labels.index("Language"), font_index + 1)

        scroll_menu = self.app.nametowidget(settings.entrycget(scroll_index, "menu"))
        self.assertEqual(scroll_menu.index("end"), 1)
        self.assertEqual(
            [scroll_menu.entrycget(index, "label") for index in range(2)],
            ["縦を反転", "横を反転"],
        )
        self.assertTrue(all(scroll_menu.type(index) == "checkbutton" for index in range(2)))
        self.assertEqual(
            [str(scroll_menu.entrycget(index, "variable")) for index in range(2)],
            [str(self.app.ui_vars.scroll_invert_vertical_var), str(self.app.ui_vars.scroll_invert_horizontal_var)],
        )

    def test_startup_settings_initialize_ui_and_executor_scroll_inversion(self):
        cases = (
            ({"scroll_invert": {"vertical": True}}, True, False, ScrollInvert(vertical=True)),
            ({}, False, False, ScrollInvert()),
            ({"scroll_invert": 5}, False, False, ScrollInvert()),
        )
        for settings, vertical, horizontal, expected in cases:
            with self.subTest(settings=settings):
                app = self._make_app_with_startup_settings(settings)
                try:
                    self.assertEqual(app.ui_vars.scroll_invert_vertical_var.get(), vertical)
                    self.assertEqual(app.ui_vars.scroll_invert_horizontal_var.get(), horizontal)
                    self.assertEqual(app.action_executor._get_scroll_invert(), expected)
                finally:
                    app.destroy()

    def test_setting_change_persists_both_values_and_updates_executor(self):
        cases = (
            (True, False, ScrollInvert(vertical=True)),
            (False, True, ScrollInvert(horizontal=True)),
            (True, True, ScrollInvert(vertical=True, horizontal=True)),
        )
        for vertical, horizontal, expected in cases:
            with self.subTest(vertical=vertical, horizontal=horizontal):
                self.app._startup_settings = {"scroll_invert": {"vertical": False, "horizontal": False}}
                self.app.ui_vars.scroll_invert_vertical_var.set(vertical)
                self.app.ui_vars.scroll_invert_horizontal_var.set(horizontal)
                with patch.object(self.app.startup_io, "write_startup", return_value=True) as write_startup:
                    self.app.set_scroll_invert()

                write_startup.assert_called_once_with(
                    {"scroll_invert": {"vertical": vertical, "horizontal": horizontal}},
                )
                self.assertEqual(self.app.action_executor._get_scroll_invert(), expected)

    def test_failed_setting_save_keeps_executor_value(self):
        previous = self.app.action_executor._get_scroll_invert()
        self.app._startup_settings = {"scroll_invert": {"vertical": False, "horizontal": False}}
        self.app.ui_vars.scroll_invert_vertical_var.set(True)
        self.app.ui_vars.scroll_invert_horizontal_var.set(False)
        with patch.object(self.app.startup_io, "write_startup", return_value=False) as write_startup:
            self.app.set_scroll_invert()

        write_startup.assert_called_once_with(
            {"scroll_invert": {"vertical": True, "horizontal": False}},
        )
        self.assertIs(self.app.action_executor._get_scroll_invert(), previous)
        self.assertFalse(self.app.ui_vars.scroll_invert_vertical_var.get())
        self.assertFalse(self.app.ui_vars.scroll_invert_horizontal_var.get())


if __name__ == "__main__":
    unittest.main()
