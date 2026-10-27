"""ダイアログから開く子ヘルプと12箇所の導線を検査する。"""

from __future__ import annotations

import ast
from contextlib import ExitStack
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.child_save_dialog import ChildSaveDialog
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs.orphan_sweep_dialog import OrphanSweepDialog
from keyseq.presentation.dialogs.trigger_dialog import TriggerDialog
from keyseq.presentation.help.help_button import add_help_button
from keyseq.presentation.help.help_content import (
    HelpBlock, HelpCategory, HelpContent, HelpItem, HelpLoadResult,
)
from keyseq.presentation.help.help_targets import DIALOG_TARGETS
from keyseq.presentation.help.help_window import HelpWindow
from tests_ui.escape_delivery import send_escape


def sample_content() -> HelpContent:
    categories = tuple(HelpCategory(target, target, (
        HelpItem(f"{target}.one", "使い方", (HelpBlock("p", text="説明\n" * 40),)),
    )) for target in DIALOG_TARGETS)
    return HelpContent(categories, (HelpCategory("faq", "QA", ()),))


def buttons_in(widget: tk.Misc) -> list[ttk.Button]:
    return [child for child in widget.winfo_children() if isinstance(child, ttk.Button)] + [
        button for child in widget.winfo_children() for button in buttons_in(child)
    ]


class DialogHelpPlacementTest(unittest.TestCase):
    def test_exactly_twelve_calls_with_expected_targets_and_scopes(self) -> None:
        expected = {
            "dialogs/action_dialog.py": ("__init__", "SEQUENCE"),
            "dialogs/keymap_edit_dialog.py": ("__init__", "KEYMAP"),
            "dialogs/trigger_dialog.py": ("__init__", "TRIGGER"),
            "dialogs/preset_manager.py": ("_build_preset_manager_widgets", "PRESET"),
            "dialogs/preset_dialog.py": ("__init__", "PRESET"),
            "dialogs/keymap_switch_batch_dialog.py": ("_build_buttons", "KEYMAP"),
            "dialogs/keymap_set_history_dialog.py": ("_build_actions", "KEYMAP_SET"),
            "dialogs/orphan_sweep_dialog.py": ("_build_widgets", "CLEANUP"),
            "dialogs/quarantine_manage_dialog.py": ("_build_widgets", "CLEANUP"),
            "dialogs/reference_cleanup_dialog.py": ("__init__", "CLEANUP"),
            "dialogs/layout_delete_dialog.py": ("__init__", "KEYBOARD_UI"),
            "controllers/config_io/child_save_dialog.py": ("_create_action_dialog", "KEYMAP_SET"),
        }
        root = Path(__file__).resolve().parents[1] / "keyseq/presentation"
        for relative, (scope, target) in expected.items():
            with self.subTest(file=relative):
                tree = ast.parse((root / relative).read_text(encoding="utf-8-sig"))
                calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Name) and node.func.id == "add_help_button"]
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].args[2].id, target)
                owners = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                          and calls[0] in ast.walk(node)]
                self.assertEqual(owners, [scope])


class DialogHelpButtonsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(app_module, "load_startup_settings", return_value={}))
        stack.enter_context(patch.object(StartupIo, "load_startup_and_config"))
        stack.enter_context(patch.object(StartupIo, "write_startup", return_value=True))
        stack.enter_context(patch.object(ConfigService, "load_keymap_set_history",
                                        return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK)))
        try:
            cls.app = app_module.App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls.app.destroy)
        cls.app.update_idletasks()

    def setUp(self) -> None:
        self.app.help.close()
        self.app.help.load_content = lambda: HelpLoadResult(sample_content())
        self.addCleanup(self.app.help.close)
        self.addCleanup(self._release_grab)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def _release_grab(self) -> None:
        current = self.app.grab_current()
        if current is not None:
            current.grab_release()

    def _close_dialog(self, dialog: tk.Toplevel) -> None:
        if dialog.winfo_exists():
            dialog.destroy()
        self.app.update()

    def _dialog(self, kind: str = "trigger") -> tk.Toplevel:
        dialog = (TriggerDialog(self.app, title="導線の検査") if kind == "trigger" else
                  OrphanSweepDialog(self.app, scan_dirs=(), initial_dir=""))
        self.addCleanup(self._close_dialog, dialog)
        self.app.update_idletasks()
        return dialog

    def _help_button(self, dialog: tk.Toplevel) -> ttk.Button:
        buttons = [button for button in buttons_in(dialog) if button.cget("text") == "?"]
        self.assertEqual(len(buttons), 1)
        button = buttons[0]
        self.assertIs(button.master.pack_slaves()[0], button)
        self.app.update_idletasks()
        self.assertTrue(all(button.winfo_x() <= peer.winfo_x()
                            for peer in button.master.pack_slaves()))
        return button

    def _open_help(self, dialog: tk.Toplevel, target: str) -> HelpWindow:
        self._help_button(dialog).invoke()
        self.app.update_idletasks()
        window = self.app.help.window
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window.winfo_parent(), str(dialog))
        self.assertIs(self.app.grab_current(), dialog)
        self.assertEqual(window.filter_text, "")
        self.assertEqual(window.notebook.select(), str(window.tabs["guide"]))
        self.assertTrue(window.tabs["guide"].is_category_open(target))
        self.assertEqual(len([child for child in dialog.winfo_children()
                              if isinstance(child, HelpWindow)]), 1)
        return window

    def test_representative_dialogs_replace_main_help_and_close_children(self) -> None:
        for kind, target, close_label in (("trigger", "trigger", "キャンセル"),
                                           ("orphan", "cleanup", "閉じる")):
            with self.subTest(dialog=kind):
                self.app.grab_set()
                self.app.help.open("faq")
                old = self.app.help.window
                old.filter_var.set("入力済み")
                dialog = self._dialog(kind)
                window = self._open_help(dialog, target)
                self.assertFalse(old.winfo_exists())
                window.filter_var.set("再入力")
                self.assertIs(self._open_help(dialog, target), window)
                next(button for button in buttons_in(dialog)
                     if button.cget("text") == close_label).invoke()
                self.app.update()
                self.assertFalse(window.winfo_exists())
                self.assertIsNone(self.app.help.window)
                self.assertIs(self.app.grab_current(), self.app)
                self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
                self.app.grab_release()

    def test_child_save_public_flow_opens_child_and_cancels(self) -> None:
        windows: list[HelpWindow] = []

        def exercise(dialog: tk.Toplevel) -> None:
            self.addCleanup(self._close_dialog, dialog)
            windows.append(self._open_help(dialog, "keymap_set"))
            next(button for button in buttons_in(dialog)
                 if button.cget("text") == "キャンセル").invoke()

        self.app.grab_set()
        self.app.help.open("guide")
        old = self.app.help.window
        old.filter_var.set("入力済み")
        # 作成・grab 完了後の待機点で操作し、初期化中の idle 配送には依存しない。
        with patch.object(tk.Toplevel, "wait_window", exercise):
            self.assertIsNone(ChildSaveDialog(self.app).ask_child_save_actions([]))
        self.app.update()
        self.assertFalse(old.winfo_exists())
        self.assertEqual(len(windows), 1)
        self.assertFalse(windows[0].winfo_exists())
        self.assertIsNone(self.app.help.window)
        self.assertIs(self.app.grab_current(), self.app)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_nested_hook_focus_and_escape_restore_main_grab(self) -> None:
        self.app.grab_set()
        dialog = self._dialog()
        window = self._open_help(dialog, "trigger")
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        with patch.object(self.app.hook, "suspend_hook_for_dialog",
                          wraps=self.app.hook.suspend_hook_for_dialog) as suspend:
            window.filter_entry.event_generate("<FocusIn>")
            suspend.assert_called_once_with()
        self.assertEqual(self.app.hook.get_hook_pause_count(), 2)
        window.filter_entry.event_generate("<FocusOut>")
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        window.filter_entry.event_generate("<FocusIn>")
        self.assertEqual(self.app.hook.get_hook_pause_count(), 2)
        send_escape(self, self.app, dialog)
        self.assertFalse(window.winfo_exists())
        self.assertIsNone(self.app.help.window)
        self.assertIs(self.app.grab_current(), self.app)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_switching_dialog_parent_destroys_previous_help(self) -> None:
        first = self._dialog()
        old = self._open_help(first, "trigger")
        second = self._dialog("orphan")
        new = self._open_help(second, "cleanup")
        self.assertFalse(old.winfo_exists())
        self._close_dialog(second)
        self.assertFalse(new.winfo_exists())
        self.assertIs(self.app.grab_current(), first)

    def test_dialog_help_applies_topmost_on_creation_and_reuse(self) -> None:
        dialog = self._dialog()
        with patch.object(self.app.help, "_always_on_top", return_value=True):
            window = self._open_help(dialog, "trigger")
            self.assertTrue(bool(window.attributes("-topmost")))
        with patch.object(self.app.help, "_always_on_top", return_value=False):
            self.assertIs(self._open_help(dialog, "trigger"), window)
            self.assertFalse(bool(window.attributes("-topmost")))

    def test_item_and_empty_category_targets_are_revealed_and_scrolled(self) -> None:
        dialog = self._dialog()
        self.app.help.open_for_dialog(dialog, "guide", "cleanup.one")
        self.app.update_idletasks()
        view = self.app.help.window.tabs["guide"]
        self.assertTrue(view.is_category_open("cleanup"))
        self.assertTrue(view.is_item_open("cleanup.one"))
        self.assertIsNotNone(view.text.dlineinfo(view._headings["cleanup.one"][0]))
        self.app.help.open_for_dialog(dialog, "faq", "faq")
        self.assertTrue(self.app.help.window.tabs["faq"].is_category_open("faq"))
        self.assertEqual(self.app.help.window.tabs["faq"].text.tag_cget("heading:faq", "elide"), "0")

    def test_missing_target_and_failed_content_are_safe(self) -> None:
        dialog = self._dialog()
        self.app.help.open_for_dialog(dialog, "faq", "missing")
        window = self.app.help.window
        self.assertEqual(window.notebook.select(), str(window.tabs["faq"]))
        self.assertFalse(window.reveal("faq", "missing"))
        self.app.help.close()
        self.app.help.load_content = lambda: HelpLoadResult(None, "読込失敗")
        self._help_button(dialog).invoke()
        window = self.app.help.window
        self.assertEqual(window.winfo_parent(), str(dialog))
        self.assertEqual(window.filter_text, "")
        self.assertIsNone(window.notebook)
        self.assertIn("読込失敗", window.error_label.cget("text"))
        self.assertIs(self.app.grab_current(), dialog)

    def test_plain_root_button_and_existing_left_or_right_buttons(self) -> None:
        root = tk.Tk()
        self.addCleanup(root.destroy)
        dialog = tk.Toplevel(root)
        for side in ("left", "right"):
            row = ttk.Frame(dialog)
            row.pack()
            existing = ttk.Button(row, text="OK")
            existing.pack(side=side)
            button = add_help_button(row, dialog, "trigger")
            # 位置は窓が地図化されるまで決まらないため update まで回す。
            root.update()
            self.assertIs(row.pack_slaves()[0], button)
            self.assertLess(button.winfo_x(), existing.winfo_x())
            button.invoke()
