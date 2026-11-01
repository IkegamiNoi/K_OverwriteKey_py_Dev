"""言語メニューと設定保存の UI 挙動を固定する。"""
import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.ui_vars import UiVars
from keyseq.shared.i18n import available_languages, current_language, fix_language, tr_in

fix_language("ja")


class UiLanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_startup_patch = patch.object(
            app_module.ConfigService,
            "load_startup",
            return_value={"ui_language": "ja"},
        )
        cls._ensure_dirs_patch = patch.object(
            app_module.ConfigService,
            "ensure_split_config_dirs",
        )
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

    def _settings_menu(self):
        menubar = self.app.menubar
        settings_index = next(
            index
            for index in range(menubar.index("end") + 1)
            if menubar.type(index) == "cascade" and menubar.entrycget(index, "label") == "設定"
        )
        return self.app.nametowidget(menubar.entrycget(settings_index, "menu"))

    def setUp(self):
        self.app._startup_settings = {"ui_language": "ja"}
        self.app.ui_vars.ui_language_var.set("ja")

    def test_language_cascade_follows_font_size_and_has_available_radio_items(self):
        settings = self._settings_menu()
        labels = [
            settings.entrycget(index, "label") if settings.type(index) == "cascade" else ""
            for index in range(settings.index("end") + 1)
        ]
        font_index = labels.index("フォントサイズ")
        language_index = labels.index("言語 / Language")
        self.assertEqual(language_index, font_index + 1)

        language_menu = self.app.nametowidget(settings.entrycget(language_index, "menu"))
        items = [
            (
                language_menu.entrycget(index, "label"),
                language_menu.entrycget(index, "value"),
            )
            for index in range(language_menu.index("end") + 1)
        ]
        self.assertEqual(items, [(name, code) for code, name in available_languages()])
        self.assertEqual([label for label, _code in items], ["日本語", "English"])
        self.assertTrue(all(language_menu.type(index) == "radiobutton"
                            for index in range(language_menu.index("end") + 1)))
        self.assertEqual(self.app.ui_vars.ui_language_var.get(), "ja")
        self.assertEqual(
            str(language_menu.entrycget(0, "variable")),
            str(self.app.ui_vars.ui_language_var),
        )

    def test_language_radio_command_passes_selected_code_to_app(self):
        settings = self._settings_menu()
        language_index = next(
            index
            for index in range(settings.index("end") + 1)
            if settings.type(index) == "cascade"
            and settings.entrycget(index, "label") == "言語 / Language"
        )
        language_menu = self.app.nametowidget(settings.entrycget(language_index, "menu"))
        english_index = next(
            index
            for index in range(language_menu.index("end") + 1)
            if language_menu.entrycget(index, "value") == "en"
        )

        with patch.object(self.app, "set_ui_language") as set_ui_language:
            language_menu.invoke(english_index)

        set_ui_language.assert_called_once_with("en")

    def test_selecting_different_language_saves_and_announces_without_changing_current_language(self):
        self.app._startup_settings = {"ui_language": "ja"}
        starting_language = current_language()
        with patch.object(self.app.startup_io, "write_startup", return_value=True) as write_startup, patch.object(
            app_module.messagebox,
            "showinfo",
        ) as showinfo:
            self.app.set_ui_language("en")

        write_startup.assert_called_once_with({"ui_language": "en"})
        showinfo.assert_called_once_with(
            tr_in("en", "dialog.language_restart.title"),
            tr_in("en", "dialog.language_restart.body"),
            parent=self.app,
        )
        self.assertEqual(self.app.ui_vars.ui_language_var.get(), "en")
        self.assertEqual(current_language(), starting_language)

    def test_radio_selection_uses_saved_language_while_current_language_stays_japanese(self):
        variables = UiVars(self.app, ui_font_delta_pt=0, ui_language="en")
        self.assertEqual(variables.ui_language_var.get(), "en")
        self.assertEqual(current_language(), "ja")

    def test_selecting_current_saved_language_does_not_save_or_announce(self):
        self.app._startup_settings = {"ui_language": "ja"}
        self.app.ui_vars.ui_language_var.set("ja")
        with patch.object(self.app.startup_io, "write_startup") as write_startup, patch.object(
            app_module.messagebox,
            "showinfo",
        ) as showinfo:
            self.app.set_ui_language("ja")

        write_startup.assert_not_called()
        showinfo.assert_not_called()
        self.assertEqual(self.app.ui_vars.ui_language_var.get(), "ja")

    def test_failed_save_does_not_update_selected_language_or_announce(self):
        self.app._startup_settings = {"ui_language": "ja"}
        self.app.ui_vars.ui_language_var.set("en")
        with patch.object(self.app.startup_io, "write_startup", return_value=False) as write_startup, patch.object(
            app_module.messagebox,
            "showinfo",
        ) as showinfo:
            self.app.set_ui_language("en")

        write_startup.assert_called_once_with({"ui_language": "en"})
        showinfo.assert_not_called()
        self.assertEqual(self.app.ui_vars.ui_language_var.get(), "ja")


if __name__ == "__main__":
    unittest.main()

