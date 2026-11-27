"""モーダルの前面に合わせたヘルプ窓の付け替えを実 Tk で検査する。"""

from __future__ import annotations

import copy
from contextlib import ExitStack
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation import modal
from keyseq.infrastructure.os_backend import get_backend
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.help.help_content import (
    HelpBlock, HelpCategory, HelpContent, HelpItem, HelpLoadResult,
)
from keyseq.presentation.help.grab_handoff import install_grab_handoff
from keyseq.presentation.help.help_window import HelpWindow
from keyseq.shared.i18n import fix_language

fix_language("ja")


def sample_content() -> HelpContent:
    def category(name: str) -> HelpCategory:
        items = tuple(
            HelpItem(f"{name}.item{number}", f"見出し {number}", (
                HelpBlock("p", text=(f"本文 {number} " * 40) + "\n"),
            ))
            for number in range(1, 12)
        )
        return HelpCategory(name, name, items)

    return HelpContent((category("guide"),), (category("faq"),))


class HelpFollowTest(unittest.TestCase):
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
            ConfigService, "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        try:
            cls.app = app_module.App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls.app.destroy)
        cls.app.update_idletasks()

    def setUp(self) -> None:
        self.app.help.close()
        self.app.help._following = True
        self.app.help.load_content = lambda: HelpLoadResult(sample_content())
        self.addCleanup(self.app.help.close)
        self.addCleanup(self._release_grab)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def _release_grab(self) -> None:
        current = self.app.grab_current()
        if current is not None:
            current.grab_release()

    def _drain(self) -> None:
        # Controller notifications use after_idle; update() drains them and Tk events.
        self.app.update()

    def _modal(self, parent: tk.Misc, *, help_follow: bool = True) -> tk.Toplevel:
        dialog = tk.Toplevel(parent)
        entry = ttk.Entry(dialog)
        entry.pack()
        dialog._test_focus_target = entry
        self.app.update_idletasks()
        modal.grab_modal(dialog, parent, focus=entry, help_follow=help_follow)
        self.addCleanup(self._close_dialog, dialog)
        return dialog

    def _close_dialog(self, dialog: tk.Toplevel) -> None:
        if dialog.winfo_exists():
            dialog.destroy()
        self._drain()

    def _child_help(self, owner: tk.Misc) -> HelpWindow:
        children = [child for child in owner.winfo_children()
                    if isinstance(child, HelpWindow) and child.winfo_exists()]
        self.assertEqual(len(children), 1)
        return children[0]

    def test_fresh_open_schedules_initial_focus_but_follow_does_not(self) -> None:
        # 新しく開くときは今どおり Notebook へ初期フォーカスを予約する（task_05 の reviewer 指摘 1）。
        with patch.object(HelpWindow, "_initial_focus") as initial_focus:
            self.app.help.open("guide")
            self.app.update()
            initial_focus.assert_called_once_with()
            initial_focus.reset_mock()
            dialog = self._modal(self.app)
            self._drain()
            self.assertIs(self.app.help.window.master, dialog)
            initial_focus.assert_not_called()

    def test_menu_help_follows_modal_and_keeps_one_live_window(self) -> None:
        self.app.deiconify()
        self.app.update()
        self.app.help.open("guide")
        old = self.app.help.window
        self.assertIsNotNone(old)
        self.app.update()
        with patch.object(HelpWindow, "_initial_focus") as initial_focus:
            dialog = self._modal(self.app)
            self._drain()
            initial_focus.assert_not_called()

        current = self.app.help.window
        self.assertIsNotNone(current)
        self.assertIs(current.master, dialog)
        self.assertIs(self._child_help(dialog), current)
        self.assertFalse(old.winfo_exists())
        self.assertEqual(sum(
            isinstance(child, HelpWindow) and child.winfo_exists()
            for owner in (self.app, dialog) for child in owner.winfo_children()
        ), 1)
        self.assertIsNone(current._focus_after_id)

    def test_nested_modal_close_returns_help_to_previous_owner_then_app(self) -> None:
        first = self._modal(self.app)
        self.app.help.open_for_dialog(first, "guide", "")
        first_help = self.app.help.window
        self.assertIs(first_help.master, first)

        second = self._modal(first)
        self._drain()
        nested_help = self.app.help.window
        self.assertIs(nested_help.master, second)
        self.assertFalse(first_help.winfo_exists())

        second.destroy()
        self._drain()
        returned = self.app.help.window
        self.assertIsNotNone(returned)
        self.assertIs(returned.master, first)
        self.assertFalse(nested_help.winfo_exists())

        first.destroy()
        self._drain()
        app_help = self.app.help.window
        self.assertIsNotNone(app_help)
        self.assertIs(app_help.master, self.app)
        self.assertFalse(returned.winfo_exists())

    def test_follow_preserves_filter_tabs_expanders_selection_scroll_and_geometry(self) -> None:
        dialog = self._modal(self.app)
        self.app.help.open_for_dialog(dialog, "guide", "")
        self._drain()
        old = self.app.help.window
        old.geometry("610x470+31+47")
        old_view = old.tabs["guide"]
        old.filter_var.set("見出し")
        old_view.reveal("guide.item8")
        old_view.text.yview_moveto(0.55)
        self.app.update()
        # 保つのは先頭に見えている行（暫定 63 §4.1）。画面に出ている間に控える。
        expected_top = old_view.text.index("@0,0")
        old.select_tab("faq")
        old.geometry("610x470+31+47")
        self.app.update()
        expected_scroll = old_view.text.yview()
        self.assertGreater(expected_scroll[0], 0.0)

        nested = self._modal(dialog)
        self._drain()

        current = self.app.help.window
        self.assertIs(current.master, nested)
        self.assertEqual(current.filter_text, "見出し")
        self.assertEqual(current.notebook.select(), str(current.tabs["faq"]))
        view = current.tabs["guide"]
        self.assertTrue(view.is_category_open("guide"))
        self.assertTrue(view.is_item_open("guide.item8"))
        self.assertEqual(view._selected, "guide.item8")
        # 選ばれていないタブは本文の幅が確定せず折り返しが変わるため、割合（yview）では比べない。
        # タブを画面に出してから、先頭に見えている行が同じかを確かめる。
        current.select_tab("guide")
        self.app.update()
        self.assertEqual(view.text.index("@0,0"), expected_top)
        current.select_tab("faq")
        self.app.update()
        self.assertEqual(current.geometry(), "610x470+31+47")

    def test_iconic_help_state_is_restored_after_follow(self) -> None:
        dialog = self._modal(self.app)
        self.app.help.open_for_dialog(dialog, "guide", "")
        old = self.app.help.window
        old.iconify()
        self.app.update()
        self.assertEqual(old.state(), "iconic")

        nested = self._modal(dialog)
        self._drain()
        self.assertIs(self.app.help.window.master, nested)
        self.assertEqual(self.app.help.window.state(), "iconic")

    def test_ignored_modal_does_not_change_help_owner(self) -> None:
        self.app.help.open("guide")
        old = self.app.help.window
        ignored = self._modal(self.app, help_follow=False)
        self._drain()
        self.assertIs(self.app.help.window, old)
        self.assertIs(old.master, self.app)
        self.assertTrue(old.winfo_exists())
        self.assertTrue(ignored.winfo_exists())

    def test_user_close_paths_disable_following(self) -> None:
        for close_kind in ("controller", "escape", "window-manager"):
            with self.subTest(close_kind=close_kind):
                self.app.help.open("guide")
                window = self.app.help.window
                if close_kind == "controller":
                    self.app.help.close()
                elif close_kind == "escape":
                    window._escape(None)
                else:
                    protocol = window.protocol("WM_DELETE_WINDOW")
                    self.app.tk.call(protocol)
                self._drain()
                dialog = self._modal(self.app)
                self._drain()
                self.assertIsNone(self.app.help.window)
                self.assertEqual([
                    child for child in dialog.winfo_children()
                    if isinstance(child, HelpWindow) and child.winfo_exists()
                ], [])
                self._close_dialog(dialog)

    def test_stop_following_prevents_queued_and_future_reparenting(self) -> None:
        self.app.help.open("guide")
        original = self.app.help.window
        self.app.help.on_modal_front_changed()
        self.assertIsNotNone(self.app.help._follow_id)
        self.app.help.stop_following()
        self.assertIsNone(self.app.help._follow_id)
        dialog = self._modal(self.app)
        self._drain()
        self.assertIs(self.app.help.window, original)
        self.assertIs(original.master, self.app)
        self.assertTrue(original.winfo_exists())
        self.assertEqual([
            child for child in dialog.winfo_children()
            if isinstance(child, HelpWindow) and child.winfo_exists()
        ], [])

    def test_follow_failure_during_creation_keeps_old_window_and_hook_balanced(self) -> None:
        self.app.help.open("guide")
        old = self.app.help.window
        old.filter_var.set("保持")
        self.app.update()
        saved_state = copy.deepcopy(self.app.help._state)
        with patch.object(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        ) as resume_hook:
            with patch(
                "keyseq.presentation.help.help_window_controller.HelpWindow",
                side_effect=RuntimeError("create failed"),
            ) as create_help:
                dialog = self._modal(self.app)
                old.filter_entry.event_generate("<FocusIn>")
                resume_hook.reset_mock()
                self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                self._drain()
                create_help.assert_called_once()
            self.assertIs(self.app.help.window, old)
            self.assertTrue(old.winfo_exists())
            self.assertEqual(old.filter_text, "保持")
            self.assertEqual(self.app.help._state, saved_state)
            self.assertEqual(resume_hook.call_count, 0)
            self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            self.app.help.close()
            self.assertEqual(resume_hook.call_count, 1)
            self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
            self.assertTrue(dialog.winfo_exists())

    def test_follow_failure_restoring_state_discards_partial_window(self) -> None:
        self.app.help.open("guide")
        old = self.app.help.window
        old.filter_var.set("保持")
        self.app.update()
        saved_state = copy.deepcopy(self.app.help._state)
        with patch.object(HelpWindow, "apply_state", side_effect=RuntimeError("restore failed")):
            dialog = self._modal(self.app)
            self._drain()
        self.assertIs(self.app.help.window, old)
        self.assertTrue(old.winfo_exists())
        self.assertEqual(old.filter_text, "保持")
        self.assertEqual(self.app.help._state, saved_state)
        self.assertEqual([
            child for child in dialog.winfo_children()
            if isinstance(child, HelpWindow) and child.winfo_exists()
        ], [])

    def test_follow_reuses_loaded_content_instead_of_reading_again(self) -> None:
        with patch.object(
            self.app.help, "load_content", return_value=HelpLoadResult(sample_content()),
        ) as load_content:
            self.app.help.open("guide")
            original = self.app.help.window
            dialog = self._modal(self.app)
            self._drain()
            nested = self._modal(dialog)
            self._drain()
            nested.destroy()
            self._drain()
            self.assertIs(self.app.help.window.master, dialog)
            dialog.destroy()
            self._drain()
        self.assertEqual(load_content.call_count, 1)
        self.assertTrue(original is not self.app.help.window)
        self.assertIs(self.app.help.window.master, self.app)

    def test_front_notifications_coalesce_and_follow_is_reentrancy_safe(self) -> None:
        controller = self.app.help
        controller.open("guide")
        dialog = self._modal(self.app)
        controller.on_modal_front_changed()
        scheduled = controller._follow_id
        controller.on_modal_front_changed()
        self.assertEqual(controller._follow_id, scheduled)

        build = controller._build
        def reentrant_build(owner: tk.Misc) -> HelpWindow:
            controller.on_modal_front_changed()
            controller._follow()
            return build(owner)

        with patch.object(
            controller, "_build", side_effect=reentrant_build,
        ) as build_help:
            controller._follow()
            self.assertEqual(build_help.call_count, 1)
        self._drain()
        self.assertIs(controller.window.master, dialog)

    def test_failed_content_result_is_reused_when_parent_changes(self) -> None:
        with patch.object(
            self.app.help, "load_content", return_value=HelpLoadResult(None, "読込失敗"),
        ) as load_content:
            self.app.help.open("guide")
            old = self.app.help.window
            old.filter_var.set("検索語")
            old.geometry("590x430+40+50")
            dialog = self._modal(self.app)
            self._drain()
            current = self.app.help.window
            self.assertIs(current.master, dialog)
            self.assertIsNone(current.notebook)
            self.assertIn("読込失敗", current.error_label.cget("text"))
            self.assertEqual(current.filter_text, "検索語")
            self.assertEqual(current.geometry(), "590x430+40+50")
            self.assertFalse(old.winfo_exists())
        self.assertEqual(load_content.call_count, 1)

    def test_hidden_owner_skips_visibility_wait_and_lower(self) -> None:
        dialog = self._modal(self.app)
        self.app.help.open_for_dialog(dialog, "guide", "")
        self._drain()
        window = self.app.help.window
        dialog.withdraw()
        with patch.object(window, "wait_visibility") as wait_visibility, \
                patch.object(window, "lower") as lower, \
                patch.object(modal, "last_input") as last_input, \
                patch.object(self.app.help, "_place_window",
                             wraps=self.app.help._place_window) as place_window:
            self.app.help._place_window(window, dialog)
            place_window.assert_called_once_with(window, dialog)
            wait_visibility.assert_not_called()
            lower.assert_not_called()
            last_input.assert_not_called()

        with patch.object(dialog, "winfo_viewable", return_value=True), \
                patch.object(self.app, "wm_state", return_value="iconic"), \
                patch.object(window, "wait_visibility") as wait_visibility, \
                patch.object(window, "lower") as lower, \
                patch.object(modal, "last_input") as last_input, \
                patch.object(self.app.help, "_place_window",
                             wraps=self.app.help._place_window) as place_window:
            self.app.help._place_window(window, dialog)
            place_window.assert_called_once_with(window, dialog)
            wait_visibility.assert_not_called()
            lower.assert_not_called()
            last_input.assert_not_called()

    def test_follow_returns_focus_to_last_input_only_when_app_is_foreground(self) -> None:
        self.app.help.open("guide")
        dialog = tk.Toplevel(self.app)
        self.addCleanup(self._close_dialog, dialog)
        target = ttk.Entry(dialog)
        target.pack()
        self.app.update_idletasks()
        with patch.object(modal, "last_input", return_value=target), \
                patch.object(modal, "is_app_foreground", return_value=True), \
                patch.object(target, "focus_force") as focus_force:
            modal.grab_modal(dialog, self.app, focus=target)
            self.app.update()
            focus_force.assert_called_once_with()

        self._close_dialog(dialog)
        previous = self._modal(self.app)
        self.app.help.open_for_dialog(previous, "guide", "")
        self._drain()
        previous_target = previous._test_focus_target
        nested = tk.Toplevel(previous)
        self.addCleanup(self._close_dialog, nested)
        target = ttk.Entry(nested)
        target.pack()
        self.app.update_idletasks()
        with patch.object(modal, "last_input", return_value=target), \
                patch.object(modal, "is_app_foreground", return_value=False), \
                patch.object(target, "focus_force") as focus_force:
            modal.grab_modal(nested, previous, focus=target)
            self.app.update()
            self.assertIs(self.app.help.window.master, nested)
            focus_force.assert_not_called()
        with patch.object(modal, "last_input", return_value=previous_target), \
                patch.object(modal, "is_app_foreground", return_value=True), \
                patch.object(previous_target, "focus_force") as focus_force:
            self._close_dialog(nested)
            self.assertIs(self.app.help.window.master, previous)
            focus_force.assert_called_once_with()

    def test_follow_to_app_does_not_force_focus(self) -> None:
        dialog = self._modal(self.app)
        self.app.help.open_for_dialog(dialog, "guide", "")
        self._drain()
        help_window = self.app.help.window
        with patch.object(modal, "last_input") as last_input, \
                patch.object(self.app.help, "_place_window",
                             wraps=self.app.help._place_window) as place_window:
            dialog.destroy()
            self._drain()
            self.assertIs(self.app.help.window.master, self.app)
            self.assertFalse(help_window.winfo_exists())
            place_window.assert_called_once()
            last_input.assert_not_called()

    def test_mac_grab_handoff_is_installed_for_dialog_owner_only(self) -> None:
        self.app.help.open("guide")
        dialog = self._modal(self.app)
        with patch.object(
            get_backend().window, "hands_grab_to_active_child_window", return_value=True,
        ), patch(
            "keyseq.presentation.help.help_window_controller.install_grab_handoff",
            wraps=install_grab_handoff,
        ) as handoff:
            self._drain()
            attached = self.app.help.window
            handoff.assert_called_once_with(attached, dialog)

            handoff.reset_mock()
            dialog.destroy()
            self._drain()
            self.assertIs(self.app.help.window.master, self.app)
            handoff.assert_not_called()


if __name__ == "__main__":
    unittest.main()
