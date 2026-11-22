from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import tkinter as tk

from keyseq.presentation.views.menu_bar import _toggle_physical_labels, build_menu_bar
from keyseq.shared.i18n import available_languages


class MenuBarDeferralTests(unittest.TestCase):
    def test_menu_commands_and_language_radios_are_deferred_only(self):
        menus = []
        class FakeMenu:
            def __init__(self, *args, **kwargs):
                self.entries = []
                menus.append(self)
            def add_command(self, **kwargs): self.entries.append(("command", kwargs))
            def add_checkbutton(self, **kwargs): self.entries.append(("checkbutton", kwargs))
            def add_radiobutton(self, **kwargs): self.entries.append(("radiobutton", kwargs))
            def add_separator(self): self.entries.append(("separator", {}))
            def add_cascade(self, **kwargs): self.entries.append(("cascade", kwargs))

        deferred = []
        app = SimpleNamespace(
            menu_commands=SimpleNamespace(defer=lambda callback: deferred.append(callback) or (lambda: None)),
            keymap_set_io=SimpleNamespace(**{name: Mock() for name in ("new_config", "save_keymap_set", "save_as", "load_keymap_set_from", "import_config", "export_config", "set_startup_keymap_set", "restore_default")}),
            keymap_set_history_io=SimpleNamespace(open_history_dialog=Mock()),
            reference_cleanup_io=SimpleNamespace(run_cleanup=Mock()),
            orphan_sweep_io=SimpleNamespace(run_sweep=Mock()),
            quarantine_manage_io=SimpleNamespace(manage_quarantine=Mock()),
            layout=SimpleNamespace(**{name: Mock() for name in ("open_keyboard_window", "add_external_keyboard_layout", "delete_keyboard_layout")}),
            ui_vars=SimpleNamespace(keyboard_show_physical_key_labels_var=Mock(), ui_font_delta_var=Mock(), ui_language_var=Mock()),
            open_preset_manager=Mock(), on_close=Mock(), set_ui_font_delta=Mock(), set_ui_language=Mock(),
            help=SimpleNamespace(open=Mock()), license=SimpleNamespace(open=Mock()),
            config=Mock(), tk=Mock(),
        )
        with patch.object(tk, "Menu", FakeMenu):
            build_menu_bar(app)

        entries = [entry for menu in menus for entry in menu.entries]
        commands = [options for kind, options in entries if kind == "command"]
        language_radios = [options for menu in menus for kind, options in menu.entries
                           if kind == "radiobutton" and options["variable"] is app.ui_vars.ui_language_var]
        font_radios = [options for menu in menus for kind, options in menu.entries
                       if kind == "radiobutton" and options["variable"] is app.ui_vars.ui_font_delta_var]
        physical_checks = [options for kind, options in entries if kind == "checkbutton"]
        self.assertEqual(len(deferred), len(commands) + len(language_radios))
        self.assertEqual(len(language_radios), len(available_languages()))
        self.assertEqual(len(font_radios), 7)
        self.assertEqual(len(physical_checks), 1)
        self.assertEqual(len(deferred), 22 + len(available_languages()))

    def test_physical_label_apply_is_immediate_and_save_skips_changed_path(self):
        scheduled = []
        app = SimpleNamespace(
            keymap_set_path="first.json",
            layout=SimpleNamespace(
                apply_keyboard_show_physical_key_labels=Mock(),
                persist_keyboard_layout_selection=Mock(),
            ),
            menu_commands=SimpleNamespace(defer=lambda callback: lambda: scheduled.append(callback)),
        )
        _toggle_physical_labels(app)
        app.layout.apply_keyboard_show_physical_key_labels.assert_called_once_with()
        app.layout.persist_keyboard_layout_selection.assert_not_called()
        app.keymap_set_path = "second.json"
        scheduled[0]()
        app.layout.persist_keyboard_layout_selection.assert_not_called()

    def test_physical_label_save_runs_when_path_is_unchanged(self):
        scheduled = []
        app = SimpleNamespace(
            keymap_set_path="same.json",
            layout=SimpleNamespace(apply_keyboard_show_physical_key_labels=Mock(), persist_keyboard_layout_selection=Mock()),
            menu_commands=SimpleNamespace(defer=lambda callback: lambda: scheduled.append(callback)),
        )
        _toggle_physical_labels(app)
        scheduled[0]()
        app.layout.persist_keyboard_layout_selection.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
