"""UI coverage for the help window, its filter, and the Help menu."""

from __future__ import annotations

import tkinter as tk
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.help.help_window import HelpWindow
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
        cls.app.destroy()

    def setUp(self) -> None:
        self.app = type(self).app
        if self.app.help.window is not None:
            self.app.help.close()
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
        expected = ["使い方", "よくある質問", "separator"]
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

