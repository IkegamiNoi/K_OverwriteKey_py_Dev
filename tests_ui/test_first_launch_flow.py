import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.application.config_service.sample_install import SampleInstallResult
from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.welcome import JIS_LAYOUT_PATH, WelcomeResult
from keyseq.shared.i18n import catalog, fix_language, tr_in

# モジュールの既定は日本語に固定し、各テストの setUp で固定を一時的に外して言語の切り替えを確かめる。
fix_language("ja")


class FirstLaunchFlowUiTest(unittest.TestCase):
    def setUp(self):
        self._patch(catalog, "_fixed", False)
        self._patch(catalog, "_language", "en")
        self._patch(ConfigService, "ensure_split_config_dirs")
        self._patch(app_module, "load_startup_settings", return_value={})
        self.install_sample = self._patch(
            ConfigService, "install_sample",
            return_value=SampleInstallResult("written", "unused"),
        )
        self.write_startup = self._patch(StartupIo, "write_startup", return_value=True)
        self.welcome = self._patch(
            app_module, "run_first_launch_welcome",
            return_value=WelcomeResult("en", "us_tkl", "sample"),
        )
        self.first_launch = self._patch(app_module, "is_first_launch", return_value=True)
        self.warning = self._patch(app_module.messagebox, "showwarning")
        self.withdraw = self._patch(app_module.App, "withdraw", autospec=True)
        self.deiconify = self._patch(app_module.App, "deiconify", autospec=True)
        self.loaded_startup = None

        def load_empty(io):
            app = io._app
            self.loaded_startup = dict(app._startup_settings)
            app.data = app.config_service.new_empty_data()
            app.keymap_set_path = ""
            app.keymap_set_io.apply_loaded_data_to_ui()

        self._patch(StartupIo, "load_startup_and_config", autospec=True, side_effect=load_empty)
        self.start_empty = self._patch(
            KeymapSetIo, "start_empty", autospec=True, side_effect=KeymapSetIo.start_empty,
        )

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def _create_app(self, **kwargs):
        app = app_module.App(**kwargs)
        self.addCleanup(app.destroy)
        return app

    def _assert_no_welcome(self):
        self.welcome.assert_not_called()
        self.install_sample.assert_not_called()
        self.start_empty.assert_not_called()
        self.write_startup.assert_not_called()
        self.withdraw.assert_not_called()
        self.deiconify.assert_not_called()

    def test_default_constructor_does_not_check_first_launch(self):
        self._create_app()
        self.first_launch.assert_not_called()
        self._assert_no_welcome()

    def test_existing_startup_does_not_run_welcome(self):
        self.first_launch.return_value = False
        self._create_app(first_launch_welcome=True)
        self.first_launch.assert_called_once()
        self._assert_no_welcome()

    def _assert_sample_status(self, status):
        self.install_sample.return_value = SampleInstallResult(status, "unused")
        app = self._create_app(first_launch_welcome=True)
        expected = {"ui_language": "en", "keymap_set_path": "sample/keymap_sets/sample.json"}
        self.assertEqual(app._startup_settings, expected)
        self.assertEqual(self.loaded_startup, expected)
        self.write_startup.assert_called_once_with(expected)
        self.install_sample.assert_called_once_with(
            config_root=app.config_root, keyboard_layout_id="us_tkl", external_layout_path="",
        )
        self.start_empty.assert_not_called()
        self.warning.assert_not_called()
        self.withdraw.assert_called_once_with(app)
        self.deiconify.assert_called_once_with(app)

    def test_sample_written_records_relative_path(self):
        self._assert_sample_status("written")

    def test_existing_sample_records_relative_path(self):
        self._assert_sample_status("existing")

    def _assert_empty_jis(self, app):
        self.start_empty.assert_called_once_with(
            app.keymap_set_io, layout_id="jis", external_layout_path=JIS_LAYOUT_PATH,
        )
        self.assertEqual(len(app.data["keymaps"]), 1)
        self.assertEqual(get_active_triggers(app.data), [])
        self.assertEqual(app.data["keyboard_layout"], "jis")
        self.assertEqual(app.data["external_keyboard_layouts"], [{"path": JIS_LAYOUT_PATH}])
        self.assertEqual(app.keymap_set_path, "")
        self.assertTrue(app.dirty_tracker.is_dirty)
        self.assertNotIn("keymap_set_path", app._startup_settings)
        self.write_startup.assert_called_once_with({"ui_language": "ja"})

    def test_empty_start_uses_selected_layout_without_installing_sample(self):
        self.welcome.return_value = WelcomeResult("ja", "jis", "empty")
        app = self._create_app(first_launch_welcome=True)
        self._assert_empty_jis(app)
        self.install_sample.assert_not_called()
        self.warning.assert_not_called()

    def _assert_sample_failure(self, status):
        calls = []
        self.deiconify.side_effect = lambda _app: calls.append("deiconify")
        self.warning.side_effect = lambda *_args: calls.append("warning")
        self.welcome.return_value = WelcomeResult("ja", "jis", "sample")
        self.install_sample.return_value = SampleInstallResult(status, "unused", "disk error")
        app = self._create_app(first_launch_welcome=True)
        self._assert_empty_jis(app)
        self.install_sample.assert_called_once_with(
            config_root=app.config_root, keyboard_layout_id="jis",
            external_layout_path=JIS_LAYOUT_PATH,
        )
        self.warning.assert_called_once_with(
            tr_in("ja", "welcome.sample_failed.title"),
            tr_in("ja", "welcome.sample_failed.body", status=status, error="disk error"),
        )
        self.assertEqual(calls, ["deiconify", "warning"])

    def test_failed_sample_starts_empty_and_warns(self):
        self._assert_sample_failure("failed")

    def test_incomplete_sample_starts_empty_and_warns(self):
        self._assert_sample_failure("incomplete")

    def test_welcome_language_is_applied_before_building_widgets(self):
        self.welcome.return_value = WelcomeResult("ja", "jis", "empty")
        app = self._create_app(first_launch_welcome=True)
        self.assertEqual(app.ui_vars.ui_language_var.get(), "ja")
        file_index = next(
            index for index in range(app.menubar.index("end") + 1)
            if app.menubar.type(index) == "cascade"
        )
        file_menu = app.nametowidget(app.menubar.entrycget(file_index, "menu"))
        self.assertEqual(file_menu.entrycget(0, "label"), tr_in("ja", "menu.file.new"))

    def test_start_empty_preserves_clipboard_without_dialog_or_flash(self):
        app = self._create_app()
        with patch.object(app.list_clipboard, "clear") as clear, patch.object(
            app.keymap_set_io, "confirm_save_if_dirty",
        ) as confirm, patch.object(app, "_set_flash_message") as flash:
            app.keymap_set_io.start_empty(layout_id="us_tkl")
        clear.assert_not_called()
        confirm.assert_not_called()
        flash.assert_not_called()
        self.assertEqual(len(app.data["keymaps"]), 1)
        self.assertEqual(get_active_triggers(app.data), [])
        self.assertEqual(app.data["keyboard_layout"], "us_tkl")
        self.assertTrue(app.dirty_tracker.is_dirty)
