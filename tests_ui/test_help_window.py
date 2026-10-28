"""UI coverage for the help window, its filter, and the Help menu."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
import keyseq
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.help.help_window import HelpWindow
from keyseq.presentation.help import version_dialog
from keyseq.presentation.help.third_party import load_license_text, load_third_party
from keyseq.presentation.help.help_content import (
    HelpBlock,
    HelpCategory,
    HelpContent,
    HelpItem,
    HelpLoadResult,
)
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from tests_ui.escape_delivery import acquire_focus


def _item(identifier: str, title: str, text: str) -> HelpItem:
    return HelpItem(identifier, title, (HelpBlock("p", text=text),))


def sample_content() -> HelpContent:
    """Return small content with Unicode expansion and both block kinds."""
    street = HelpItem(
        "guide-street",
        "Straße の設定",
        (
            HelpBlock("p", text="Straße を使う。ガイドを確認する。"),
            HelpBlock("list", items=("項目を選ぶ", "ガイドを開く")),
        ),
    )
    return HelpContent(
        guide=(
            HelpCategory(
                "guide-basics",
                "基本操作",
                (street, _item("guide-save", "保存する", "設定を保存します。")),
            ),
            HelpCategory(
                "guide-advanced",
                "詳細",
                (_item("guide-advanced-one", "詳細項目", "追加情報"),),
            ),
        ),
        faq=(
            HelpCategory(
                "faq-common",
                "よくある質問",
                (_item("faq-font", "文字サイズ", "フォントを変更します。"),),
            ),
        ),
    )


class HelpWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(app_module, "load_startup_settings", return_value={}))
        stack.enter_context(patch.object(StartupIo, "load_startup_and_config"))
        stack.enter_context(patch.object(StartupIo, "write_startup", return_value=True))
        stack.enter_context(patch.object(
            ConfigService,
            "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        try:
            cls.app = App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update_idletasks()

    @classmethod
    def _destroy_app(cls) -> None:
        if cls.app.help.window is not None:
            cls.app.help.close()
        if cls.app.license.window is not None:
            cls.app.license.close()
        cls.app.destroy()

    def setUp(self) -> None:
        self.app = type(self).app
        if self.app.help.window is not None:
            self.app.help.close()
        if self.app.license.window is not None:
            self.app.license.close()
        self.app.help.load_content = lambda: HelpLoadResult(sample_content())
        self.addCleanup(self._close_help)
        self.addCleanup(self._reset_font_delta)

    def _reset_font_delta(self) -> None:
        if int(getattr(self.app, "_ui_font_delta_pt", 0)) != 0:
            self.app.set_ui_font_delta(0)

    def _close_help(self) -> None:
        if self.app.help.window is not None:
            self.app.help.close()
            self.app.update_idletasks()

    def _open(self, tab: str = "guide") -> HelpWindow:
        self.app.help.open(tab)
        self.app.update_idletasks()
        window = self.app.help.window
        assert window is not None
        return window

    @staticmethod
    def _menu_labels(menu: tk.Menu) -> list[str]:
        labels = []
        for index in range(menu.index("end") + 1):
            kind = menu.type(index)
            labels.append("separator" if kind == "separator" else menu.entrycget(index, "label"))
        return labels

    def _help_menu(self) -> tk.Menu:
        for index in range(self.app.menubar.index("end") + 1):
            if self.app.menubar.type(index) != "cascade":
                continue
            if self.app.menubar.entrycget(index, "label") == "ヘルプ":
                path = self.app.menubar.entrycget(index, "menu")
                return self.app.nametowidget(path)
        self.fail("ヘルプ menu is missing")

    def test_help_menu_survives_font_menu_rebuild(self) -> None:
        expected = ["使い方", "よくある質問", "separator", "バージョン情報", "ライセンス"]
        self.assertEqual(self._menu_labels(self._help_menu()), expected)
        menu = self._help_menu()
        menu.invoke(0)
        self.app.update_idletasks()
        self.assertIsNotNone(self.app.help.window)
        menu.invoke(1)
        self.app.update_idletasks()
        self.assertEqual(
            self.app.help.window.notebook.tab(
                self.app.help.window.notebook.select(), "text",
            ),
            "QA",
        )
        self.app.help.close()

        self.app.set_ui_font_delta(1)
        self.assertEqual(self._menu_labels(self._help_menu()), expected)

    def test_help_menu_commands_use_dynamic_window_entry_points(self) -> None:
        menu = self._help_menu()
        with patch.object(version_dialog, "open_version_dialog") as version_spy:
            menu.invoke(3)
            version_spy.assert_called_once_with(self.app)
        with patch.object(self.app.license, "open") as license_spy:
            menu.invoke(4)
            license_spy.assert_called_once_with()

    def test_version_dialog_content_and_modal_hook_pause(self) -> None:
        dialog = version_dialog.open_version_dialog(self.app)
        try:
            self.app.update_idletasks()
            self.assertEqual(dialog.title(), "バージョン情報")
            self.assertIs(self.app.grab_current(), dialog)
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            content = "\n".join(
                child.get("1.0", "end-1c")
                for child in dialog.winfo_children()
                if isinstance(child, tk.Text)
            )
            self.assertIn(f"バージョン {keyseq.__version__}", content)
            self.assertIn("Copyright (C) 2026 池上ノイ (Ikegami Noi)", content)
            self.assertIn("GNU General Public License v3", content)
            self.assertIn("実行環境: Python ", content)
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
            # 破棄の後に after(0) で予約されるフックの再開まで進め、次へ持ち越さない。
            self.app.update()

    def test_version_dialog_escape_and_close_button_resume_hook(self) -> None:
        dialog = version_dialog.open_version_dialog(self.app)
        try:
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            acquire_focus(self.app, dialog)
            self.app.focus_get().event_generate("<Escape>")
            self.app.update()
            self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
            # 破棄の後に after(0) で予約されるフックの再開まで進め、次へ持ち越さない。
            self.app.update()
        dialog = version_dialog.open_version_dialog(self.app)
        try:
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            close_button = next(
                child for child in dialog.winfo_children()
                if isinstance(child, tk.Button) or child.winfo_class() == "TButton"
            )
            close_button.invoke()
            self.app.update()
            self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
            # 破棄の後に after(0) で予約されるフックの再開まで進め、次へ持ち越さない。
            self.app.update()

    def test_license_window_reuses_and_displays_all_notices(self) -> None:
        window = self.app.license.open()
        try:
            self.app.update_idletasks()
            self.assertIs(self.app.license.open(), window)
            content = window.text.get("1.0", "end-1c")
            self.assertTrue(content.startswith("Key Replacer Sequencer\n"))
            self.assertEqual(content.count(" — "), 14)
            notices, error = load_third_party()
            self.assertEqual(error, "")
            for notice in notices:
                heading = f"\n{notice.entry.name} {notice.entry.version}\n"
                self.assertIn(heading, content)
            license_text = load_license_text()
            assert license_text is not None
            self.assertIn(license_text.splitlines()[0], content)
            self.assertIsNot(self.app.grab_current(), window)
            self.assertEqual(window.transient(), "")
        finally:
            if self.app.license.window is not None:
                self.app.license.close()

    def test_license_window_tracks_topmost_and_app_close(self) -> None:
        variable = self.app.ui_vars.always_on_top_var
        variable.set(True)
        window = self.app.license.open()
        self.addCleanup(setattr, self.app.hook, "_shutting_down", False)
        try:
            self.assertTrue(bool(window.attributes("-topmost")))
            variable.set(False)
            self.app._apply_always_on_top()
            self.assertFalse(bool(window.attributes("-topmost")))

            with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), \
                    patch.object(self.app, "destroy"), \
                    patch.object(app_module, "shutdown_capture_hook"), \
                    patch.object(self.app.delayed_calls, "stop"), \
                    patch.object(self.app.held_inputs, "release_all", return_value=[]), \
                    patch.object(self.app.input_gateway, "restore_ime_now"), \
                    patch.object(self.app.screen_grid, "shutdown"), \
                    patch.object(self.app.hook, "stop_hook"):
                self.app.on_close()
            self.assertIsNone(self.app.license.window)
        finally:
            self.app.ui_vars.always_on_top_var.set(False)
            if self.app.license.window is not None:
                self.app.license.close()

    def test_open_reuses_window_switches_tab_and_preserves_filter(self) -> None:
        window = self._open("guide")
        self.assertEqual(window.title(), "ヘルプ")
        self.assertEqual(window.notebook.tab(window.notebook.select(), "text"), "主要機能")
        window.filter_var.set("ガイド")
        self.app.update_idletasks()

        self.app.help.open("faq")
        self.app.update_idletasks()
        self.assertIs(self.app.help.window, window)
        self.assertEqual(window.notebook.tab(window.notebook.select(), "text"), "QA (0)")
        self.assertEqual(window.filter_text, "ガイド")

    def test_window_is_nonmodal_and_initial_focus_is_not_filter(self) -> None:
        window = self._open()
        self.assertIsNot(self.app.grab_current(), window)
        self.assertEqual(window.transient(), "")
        self.assertNotEqual(self.app.focus_get(), window.filter_entry)

    def test_initial_expanders_and_keyboard_controls(self) -> None:
        window = self._open()
        view = window.tabs["guide"]
        for category in ("guide-basics", "guide-advanced"):
            self.assertFalse(view.is_category_open(category))
        for item in ("guide-street", "guide-save", "guide-advanced-one"):
            self.assertFalse(view.is_item_open(item))

        view.toggle("guide-basics")
        self.assertTrue(view.is_category_open("guide-basics"))
        acquire_focus(self.app, view.text)
        view.text.event_generate("<Down>")
        # Windows の Tk ではテンキーの Enter も Return として届く。
        view.text.event_generate("<Return>")
        self.app.update_idletasks()
        self.assertTrue(view.is_item_open("guide-street"))
        view.text.event_generate("<space>")
        self.app.update_idletasks()
        self.assertFalse(view.is_item_open("guide-street"))
        view.text.event_generate("<Up>")
        view.text.event_generate("<Return>")
        self.app.update_idletasks()
        self.assertFalse(view.is_category_open("guide-basics"))

    def _highlight_text_ranges(self, text: tk.Text) -> list[tuple[str, str]]:
        ranges: list[tuple[str, str]] = []
        for tag in text.tag_names():
            if tag == "sel" or not text.tag_cget(tag, "background"):
                continue
            positions = text.tag_ranges(tag)
            for start, end in zip(positions[::2], positions[1::2]):
                ranges.append((str(start), str(end)))
        return ranges

    def test_filter_counts_visibility_no_matches_and_empty_reset(self) -> None:
        window = self._open()
        view = window.tabs["guide"]
        self.assertFalse(view.is_category_open("guide-basics"))

        window.filter_var.set("ss ガイド")
        self.app.update_idletasks()
        self.assertEqual(window.notebook.tab(window.notebook.tabs()[0], "text"), "主要機能 (1)")
        self.assertEqual(window.notebook.tab(window.notebook.tabs()[1], "text"), "QA (0)")
        self.assertTrue(view.is_category_open("guide-basics"))
        self.assertTrue(view.is_item_open("guide-street"))
        self.assertTrue(view.is_item_visible("guide-street"))
        self.assertFalse(view.is_item_visible("guide-save"))
        self.assertFalse(view.no_matches)
        self.assertTrue(window.tabs["faq"].no_matches)

    def test_zero_matches_and_clear_reset(self) -> None:
        window = self._open()
        view = window.tabs["guide"]
        window.filter_var.set("ss 保存")
        self.app.update_idletasks()
        self.assertTrue(view.no_matches)
        self.assertEqual(window.notebook.tab(window.notebook.tabs()[0], "text"), "主要機能 (0)")
        window.filter_var.set("ガイド")
        self.assertTrue(view.is_item_open("guide-street"))
        window.clear_button.invoke()
        self.app.update_idletasks()
        self.assertEqual(window.filter_text, "")
        self.assertEqual(window.notebook.tab(window.notebook.tabs()[0], "text"), "主要機能")
        for item in ("guide-street", "guide-save", "guide-advanced-one"):
            self.assertTrue(view.is_item_visible(item))
        self.assertFalse(view.is_category_open("guide-basics"))
        for item in ("guide-street", "guide-save", "guide-advanced-one"):
            self.assertFalse(view.is_item_open(item))

    def test_whitespace_only_filter_is_treated_as_empty(self) -> None:
        window = self._open()
        window.filter_var.set("   ")
        self.app.update_idletasks()
        self.assertEqual(window.notebook.tab(window.notebook.tabs()[0], "text"), "主要機能")
        self.assertEqual(window.notebook.tab(window.notebook.tabs()[1], "text"), "QA")

    def _copied(self, view) -> str:
        view.text.tag_add("sel", "1.0", "end-1c")
        with patch.object(view.text, "clipboard_clear"),                 patch.object(view.text, "clipboard_append") as append:
            view._copy()
        view.text.tag_remove("sel", "1.0", "end")
        return append.call_args.args[0]

    def test_copy_skips_collapsed_and_filtered_out_text(self) -> None:
        window = self._open()
        view = window.tabs["guide"]
        copied = self._copied(view)
        self.assertIn("基本操作", copied)
        self.assertNotIn("設定を保存します。", copied)
        self.assertNotIn("一致する項目はありません。", copied)
        view.toggle("guide-basics")
        view.toggle("guide-save")
        self.assertIn("設定を保存します。", self._copied(view))
        window.filter_var.set("詳細項目")
        self.app.update_idletasks()
        copied = self._copied(view)
        self.assertIn("追加情報", copied)
        self.assertNotIn("基本操作", copied)

    def test_unicode_highlight_positions_and_rendered_list_marker(self) -> None:
        window = self._open()
        window.filter_var.set("ss ガイド")
        self.app.update_idletasks()
        view = window.tabs["guide"]
        spans = view.highlight_spans("guide-street")
        self.assertIn(("title", 4, 5), spans)
        body = "Straße を使う。ガイドを確認する。\n項目を選ぶ\nガイドを開く"
        for offset in (body.index("ガイド"), body.rindex("ガイド")):
            self.assertIn(("body", offset, offset + 3), spans)
        ranges = self._highlight_text_ranges(view.text)
        self.assertTrue(any("ガイド" in view.text.get(start, end) for start, end in ranges))
        self.assertTrue(any(
            view.text.get(start, end) == "ガイド"
            and view.text.get(f"{start} - 1 chars", start) == "・"
            for start, end in ranges
        ))

    def test_escape_clears_filter_or_closes_and_next_open_is_fresh(self) -> None:
        window = self._open()
        window.filter_var.set("保存")
        acquire_focus(self.app, window.filter_entry)
        window.event_generate("<Escape>")
        self.app.update_idletasks()
        self.assertEqual(window.filter_text, "")
        self.assertIs(self.app.help.window, window)

        window.filter_var.set("保存")
        acquire_focus(self.app, window.tabs["guide"].text)
        window.event_generate("<Escape>")
        self.app.update_idletasks()
        self.assertIsNone(self.app.help.window)
        recreated = self._open()
        self.assertIsNot(recreated, window)
        self.assertEqual(recreated.filter_text, "")
        self.assertFalse(recreated.tabs["guide"].is_category_open("guide-basics"))

    def test_load_failure_is_shown_and_content_reloads_for_new_window(self) -> None:
        loader = patch.object(
            self.app.help,
            "load_content",
            side_effect=[HelpLoadResult(None, "理由"), HelpLoadResult(sample_content())],
        )
        with loader as load_content:
            window = self._open()
            self.assertIn("ヘルプを読み込めませんでした。（理由）", window.error_label.cget("text"))
            self.app.help.close()
            reopened = self._open()
            self.assertIsNotNone(reopened.notebook)
            self.assertEqual(load_content.call_count, 2)

    def test_filter_focus_suspends_and_resumes_hook_once(self) -> None:
        suspend = patch.object(
            self.app.hook, "suspend_hook_for_dialog",
            wraps=self.app.hook.suspend_hook_for_dialog,
        )
        resume = patch.object(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        )
        with suspend as suspend_hook, resume as resume_hook:
            window = self._open()
            self.assertEqual(suspend_hook.call_count, 0)
            window.filter_entry.event_generate("<FocusIn>")
            window.filter_entry.event_generate("<FocusIn>")
            self.assertEqual(suspend_hook.call_count, 1)
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            window.filter_entry.event_generate("<FocusOut>")
            self.assertEqual(resume_hook.call_count, 1)
            self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

            window.tabs["guide"].text.event_generate("<FocusIn>")
            window.notebook.event_generate("<FocusIn>")
            self.assertEqual(suspend_hook.call_count, 1)
            self.assertEqual(resume_hook.call_count, 1)

    def test_destroying_focused_filter_resumes_once(self) -> None:
        window = self._open()
        with patch.object(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        ) as resume_hook:
            window.filter_entry.event_generate("<FocusIn>")
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            self.app.help.close()
            self.assertEqual(resume_hook.call_count, 1)
            self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_font_change_tracks_named_font_and_preserves_view_state(self) -> None:
        window = self._open()
        view = window.tabs["guide"]
        window.filter_var.set("ガイド")
        self.app.update_idletasks()
        view.toggle("guide-basics")
        spans = view.highlight_spans("guide-street")
        named_font = tkfont.nametofont("TkDefaultFont")
        original_size = int(named_font.cget("size"))

        self.app.set_ui_font_delta(2)
        self.app.update_idletasks()

        self.assertEqual(int(named_font.cget("size")), original_size + 2)
        self.assertEqual(view.text.cget("font"), "TkDefaultFont")
        self.assertEqual(window.filter_text, "ガイド")
        self.assertFalse(view.is_category_open("guide-basics"))
        self.assertEqual(view.highlight_spans("guide-street"), spans)

    def test_help_topmost_tracks_main_setting_on_open_and_toggle(self) -> None:
        variable = self.app.ui_vars.always_on_top_var
        variable.set(True)
        window = self._open()
        self.assertTrue(bool(window.attributes("-topmost")))

        variable.set(False)
        self.app._apply_always_on_top()
        self.assertFalse(bool(window.attributes("-topmost")))

        variable.set(True)
        self.app.help.open("faq")
        self.assertTrue(bool(window.attributes("-topmost")))

        self.app.help.close()
        variable.set(False)
        reopened = self._open()
        self.assertFalse(bool(reopened.attributes("-topmost")))

    def test_main_topmost_change_resyncs_keyboard_watch_around_help_window(self) -> None:
        layout = self.app.layout
        main_topmost = self.app.ui_vars.always_on_top_var
        keyboard_topmost = self.app.ui_vars.keyboard_always_on_top_var
        keyboard = None
        foreground = self.app.foreground_own_window
        place_below = self.app.place_window_below
        main_topmost.set(True)
        keyboard_topmost.set(True)
        try:
            help_window = self._open()
            with patch.object(self.app, "after", return_value="watch-job"):
                layout.open_keyboard_window()
            keyboard = layout.keyboard_window
            self.assertTrue(bool(help_window.attributes("-topmost")))
            self.assertTrue(bool(keyboard.attributes("-topmost")))

            layout._topmost_released = True
            layout.apply_keyboard_topmost()
            self.assertFalse(bool(keyboard.attributes("-topmost")))
            main_topmost.set(False)
            self.app.foreground_own_window = Mock(
                return_value=int(help_window.wm_frame(), 16)
            )
            self.app.place_window_below = Mock(return_value=True)
            with patch.object(self.app, "after", return_value="watch-job"):
                with patch.object(
                    layout, "resync_keyboard_topmost",
                    wraps=layout.resync_keyboard_topmost,
                ) as resync:
                    self.app._apply_always_on_top()
                resync.assert_called_once_with()
                self.assertFalse(bool(help_window.attributes("-topmost")))
                self.assertFalse(layout._topmost_released)
                self.assertTrue(bool(keyboard.attributes("-topmost")))

                layout._watch_topmost_tick()
            self.assertTrue(layout._topmost_released)
            self.assertFalse(bool(keyboard.attributes("-topmost")))
            self.app.place_window_below.assert_called_once_with(
                int(keyboard.wm_frame(), 16), int(help_window.wm_frame(), 16)
            )
        finally:
            main_topmost.set(False)
            keyboard_topmost.set(False)
            layout.on_keyboard_topmost_changed()
            self.app.foreground_own_window = foreground
            self.app.place_window_below = place_below
            if keyboard is not None:
                keyboard._handle_close()
            self._close_help()

    def test_keyboard_topmost_resync_is_noop_when_closed_or_disabled(self) -> None:
        layout = self.app.layout
        keyboard_topmost = self.app.ui_vars.keyboard_always_on_top_var
        if layout.keyboard_window is not None:
            layout.keyboard_window._handle_close()
        self.assertIsNone(layout.keyboard_window)
        layout._topmost_released = True
        layout.resync_keyboard_topmost()
        self.assertTrue(layout._topmost_released)

        keyboard_topmost.set(False)
        layout.open_keyboard_window()
        keyboard = layout.keyboard_window
        try:
            layout._topmost_released = True
            layout.resync_keyboard_topmost()
            self.assertTrue(layout._topmost_released)
        finally:
            keyboard._handle_close()

    def test_app_close_closes_help_without_resuming_hook(self) -> None:
        self.addCleanup(setattr, self.app.hook, "_shutting_down", False)
        window = self._open()
        window.filter_entry.event_generate("<FocusIn>")
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), \
                patch.object(self.app, "destroy"), \
                patch.object(app_module, "shutdown_capture_hook"), \
                patch.object(self.app.delayed_calls, "stop"), \
                patch.object(self.app.held_inputs, "release_all", return_value=[]), \
                patch.object(self.app.input_gateway, "restore_ime_now"), \
                patch.object(self.app.screen_grid, "shutdown"), \
                patch.object(self.app.hook, "stop_hook"), \
                patch.object(self.app.hook, "start_hook") as start_hook, \
                patch.object(
                    self.app.hook, "resume_hook_after_dialog",
                    wraps=self.app.hook.resume_hook_after_dialog,
                ) as resume_hook:
            self.app.on_close()
        self.assertIsNone(self.app.help.window)
        self.assertEqual(resume_hook.call_count, 1)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        start_hook.assert_not_called()
        self.app.hook._shutting_down = False

    def test_destroy_and_wm_delete_clear_controller_reference(self) -> None:
        window = self._open()
        window.destroy()
        self.app.update_idletasks()
        self.assertIsNone(self.app.help.window)

        window = self._open()
        protocol = window.protocol("WM_DELETE_WINDOW")
        self.app.tk.call(protocol)
        self.app.update_idletasks()
        self.assertIsNone(self.app.help.window)

