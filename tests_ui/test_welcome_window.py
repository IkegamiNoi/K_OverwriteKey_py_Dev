"""First-launch window choices, translation preview, and child help lifecycle."""

import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.presentation.help.help_content import HelpContent, HelpLoadResult
from keyseq.presentation.welcome.first_launch import run_first_launch_welcome
from keyseq.presentation.welcome.welcome_result import WelcomeResult, estimate_layout_id
from keyseq.presentation.welcome.welcome_window import WelcomeWindow
from keyseq.shared.i18n import catalog, current_language, fix_language, tr_in
from tests_ui.escape_delivery import send_escape

fix_language("ja")


class WelcomeWindowUiTest(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(catalog, "_language", "en")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)

    def _window(self, language="ja"):
        window = WelcomeWindow(self.root, language=language)
        self.root.update()
        self.addCleanup(lambda: window.destroy() if window.winfo_exists() else None)
        return window

    def _language(self, window, language):
        codes = [code for code, _ in window._languages]
        window.language_combo.current(codes.index(language))
        window.language_combo.event_generate("<<ComboboxSelected>>")
        self.root.update()

    def test_initial_choices_and_modal_visibility_with_withdrawn_root(self):
        for language in ("ja", "en"):
            with self.subTest(language=language):
                window = self._window(language)
                self.assertEqual(window.language, language)
                self.assertEqual(window.layout_var.get(), estimate_layout_id(language))
                self.assertEqual(window.start_var.get(), "sample")
                self.assertEqual(window.language_combo.get(), dict(window._languages)[language])
                self.assertEqual(str(window.transient()), "")
                self.assertTrue(window.winfo_viewable())
                self.assertIs(window.grab_current(), window)
                window.start_button.invoke()

    def test_language_preview_updates_all_text_without_changing_global_language(self):
        window = self._window()
        window.start_choices["empty"].invoke()
        for language in ("en", "ja"):
            self._language(window, language)
            with self.subTest(language=language):
                self.assertEqual(current_language(), "en")
                self.assertEqual(window.title(), tr_in(language, "welcome.title"))
                widgets = (
                    (window.layout_section, "layout"), (window.usage_section, "usage"),
                    (window.start_section, "start"), (window.help_button, "open_help"),
                    (window.start_button, "begin"),
                    (window.sample_description, "sample_description"),
                    (window.start_choices["sample"], "start.sample"),
                    (window.start_choices["empty"], "start.empty"),
                )
                for widget, key in widgets:
                    self.assertEqual(widget.cget("text"), tr_in(language, f"welcome.{key}"))
                for label, key in zip(window.usage_labels, ("trigger", "sequence", "hook")):
                    self.assertEqual(label.cget("text"), tr_in(language, f"welcome.usage.{key}"))
                self.assertEqual(window.start_var.get(), "empty")

    def test_layout_follows_language_until_user_touches_it(self):
        window = self._window()
        self._language(window, "en")
        self.assertEqual(window.layout_var.get(), "us_tkl")
        self._language(window, "ja")
        self.assertEqual(window.layout_var.get(), "jis")
        # Even selecting the already selected layout counts as touching it.
        window.layout_buttons["jis"].invoke()
        self._language(window, "en")
        self.assertEqual(window.layout_var.get(), "jis")
        window.layout_buttons["us_tkl"].invoke()
        self._language(window, "ja")
        self.assertEqual(window.layout_var.get(), "us_tkl")

    def test_all_close_routes_confirm_current_choices(self):
        for close in ("button", "protocol", "escape"):
            with self.subTest(close=close):
                window = self._window()
                self._language(window, "en")
                window.layout_buttons["jis"].invoke()
                window.start_choices["empty"].invoke()
                if close == "button":
                    window.start_button.invoke()
                elif close == "protocol":
                    window.tk.call(window.protocol("WM_DELETE_WINDOW"))
                else:
                    send_escape(self, self.root, window)
                self.assertFalse(window.winfo_exists())
                self.assertEqual(window.result, WelcomeResult("en", "jis", "empty"))

    def test_help_is_single_child_on_guide_tab_and_closes_with_welcome(self):
        content = HelpLoadResult(HelpContent(guide=(), faq=()))
        window = self._window()
        with patch("keyseq.presentation.welcome.welcome_window.load_help_content",
                   return_value=content) as load:
            window.help_button.invoke()
            self.root.update()
            help_window = window._help_window
            self.assertIs(help_window.master, window)
            self.assertIs(window.grab_current(), window)
            self.assertEqual(help_window.notebook.select(), str(help_window.tabs["guide"]))
            self.assertEqual(help_window.title(), tr_in("en", "help.window.title"))
            help_window.select_tab("faq")
            window.help_button.invoke()
            self.assertIs(window._help_window, help_window)
            load.assert_called_once_with()
            self.assertEqual(help_window.notebook.select(), str(help_window.tabs["guide"]))
            window.start_button.invoke()
            self.assertFalse(help_window.winfo_exists())

    def test_help_can_reopen_after_being_closed(self):
        content = HelpLoadResult(HelpContent(guide=(), faq=()))
        window = self._window()
        with patch("keyseq.presentation.welcome.welcome_window.load_help_content",
                   return_value=content):
            window.help_button.invoke()
            first = window._help_window
            first.destroy()
            window.help_button.invoke()
            self.assertIsNot(window._help_window, first)
            self.assertTrue(window._help_window.winfo_exists())

    def test_runner_waits_and_returns_window_result(self):
        failures = []

        def choose():
            try:
                window = next(child for child in self.root.winfo_children()
                              if isinstance(child, WelcomeWindow))
                self._language(window, "ja")
                window.layout_buttons["us_tkl"].invoke()
                window.start_choices["empty"].invoke()
                window.start_button.invoke()
            except Exception as exc:
                failures.append(exc)
                for child in self.root.winfo_children():
                    child.destroy()

        self.root.after(0, choose)
        result = run_first_launch_welcome(self.root)
        self.assertEqual(failures, [])
        self.assertEqual(result, WelcomeResult("ja", "us_tkl", "empty"))

    def test_reopen_window_hides_first_launch_sections(self):
        self.root.deiconify()
        window = WelcomeWindow(self.root, language="ja", reopen=True)
        self.root.update()
        self.addCleanup(lambda: window.destroy() if window.winfo_exists() else None)
        self.assertEqual(str(window.transient()), str(self.root))
        self.assertTrue(window.winfo_viewable())
        self.assertIs(window.grab_current(), window)
        self.assertFalse(hasattr(window, "layout_section"))
        self.assertFalse(hasattr(window, "start_section"))
        self.assertIn(tr_in("ja", "menu.file.restore_sample"),
                      window.sample_restore_notice.cget("text"))
        self.assertIn(tr_in("ja", "menu.file.title"),
                      window.sample_restore_notice.cget("text"))
        self.assertEqual(window.start_button.cget("text"), tr_in("ja", "welcome.close"))
        initial = self._window("ja")
        self.assertTrue(hasattr(initial, "layout_section"))
        self.assertTrue(hasattr(initial, "start_section"))

    def test_reopen_help_uses_app_controller(self):
        window = WelcomeWindow(self.root, language="ja", reopen=True)
        with patch.object(self.root, "help", create=True) as help_controller:
            window._open_help()
        help_controller.open_for_dialog.assert_called_once_with(window, "guide", "")

    @patch("keyseq.presentation.welcome.first_launch.WelcomeWindow")
    def test_open_welcome_again_resumes_hook_and_only_saves_changed_language(self, _window_class):
        from keyseq.presentation.welcome.first_launch import open_welcome_again

        app = unittest.mock.Mock()
        app.hook = unittest.mock.Mock()

        def wait_window(window):
            window.result = WelcomeResult("en", "jis", "empty")

        app.wait_window.side_effect = wait_window
        with patch("keyseq.presentation.welcome.first_launch.current_language", return_value="ja"):
            open_welcome_again(app)
        app.hook.suspend_hook_for_dialog.assert_called_once_with()
        app.hook.resume_hook_after_dialog.assert_called_once_with()
        app.set_ui_language.assert_called_once_with("en")

    @patch("keyseq.presentation.welcome.first_launch.WelcomeWindow")
    def test_open_welcome_again_does_not_save_unchanged_language(self, _window_class):
        from keyseq.presentation.welcome.first_launch import open_welcome_again

        app = unittest.mock.Mock()
        app.hook = unittest.mock.Mock()
        app.wait_window.side_effect = lambda window: setattr(
            window, "result", WelcomeResult("ja", "jis", "empty"),
        )
        with patch("keyseq.presentation.welcome.first_launch.current_language", return_value="ja"):
            open_welcome_again(app)
        app.set_ui_language.assert_not_called()

    @patch("keyseq.presentation.welcome.first_launch.WelcomeWindow")
    def test_open_welcome_again_resumes_hook_after_window_error(self, _window_class):
        from keyseq.presentation.welcome.first_launch import open_welcome_again

        app = unittest.mock.Mock()
        app.hook = unittest.mock.Mock()
        app.wait_window.side_effect = RuntimeError("window failure")
        with patch("keyseq.presentation.welcome.first_launch.current_language", return_value="ja"):
            with self.assertRaises(RuntimeError):
                open_welcome_again(app)
        app.hook.resume_hook_after_dialog.assert_called_once_with()

    def test_usage_terms_match_existing_catalog_labels(self):
        for language in ("ja", "en"):
            with self.subTest(language=language):
                for suffix, existing in (("trigger", "trigger_dialog.trigger"),
                                         ("sequence", "child_kind.sequence"),
                                         ("hook", "hook_button.start")):
                    self.assertIn(tr_in(language, existing),
                                  tr_in(language, f"welcome.usage.{suffix}"))
                self.assertIn(tr_in(language, "hook_button.start"),
                              tr_in(language, "welcome.sample_description"))
