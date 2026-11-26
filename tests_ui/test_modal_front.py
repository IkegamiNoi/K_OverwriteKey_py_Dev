"""モーダル台帳の前面窓・入力先・grab 委譲の補助 API。"""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation import modal


class ModalFrontTest(unittest.TestCase):
    def setUp(self):
        for name, value in (
            ("_active_modals", []),
            ("_opened_while_minimized", []),
            ("_hidden_by_minimize", []),
            ("_custody_window", None),
            ("_app_minimized", False),
            ("_message_boxes", 0),
            ("_modal_presence_listener", None),
            ("_modal_front_listener", None),
            ("_modal_help_follow", {}),
            ("_modal_last_inputs", {}),
        ):
            patcher = patch.object(modal, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.root.report_callback_exception = Mock()
        self.addCleanup(self.root.report_callback_exception.assert_not_called)
        self.root.update_idletasks()
        self.root.focus_force()
        self.root.update()
        self.root.grab_release()
        self.addCleanup(self.root.deiconify)

    def make_window(self, parent=None):
        window = tk.Toplevel(self.root if parent is None else parent)
        self.addCleanup(self.cleanup_window, window)
        window.update_idletasks()
        self.assertTrue(window.winfo_exists())
        return window

    @staticmethod
    def cleanup_window(window):
        if window.winfo_exists():
            window.grab_release()
            window.destroy()

    def test_front_listener_runs_after_presence_on_grab(self):
        window = self.make_window()
        events = []
        modal.set_modal_presence_listener(lambda: events.append("presence"))
        modal.set_modal_front_listener(
            lambda: events.append(("front", modal.is_modal_active()))
        )

        modal.grab_modal(window)

        self.assertEqual(events, ["presence", ("front", True)])

    def test_front_listener_fires_once_on_destroy_for_each_restore_path(self):
        # 前の保持者へ戻す経路
        first = self.make_window()
        second = self.make_window()
        listener = Mock()
        modal.set_modal_front_listener(listener)
        modal.grab_modal(first)
        modal.grab_modal(second)
        listener.reset_mock()
        second.destroy()
        listener.assert_called_once_with()
        self.assertIs(self.root.grab_current(), first)

        # previous is None の経路
        listener.reset_mock()
        first.destroy()
        third = self.make_window()
        modal.grab_modal(third)
        self.assertIs(self.root.grab_current(), third)
        listener.reset_mock()
        third.destroy()
        listener.assert_called_once_with()

    def test_front_listener_fires_on_non_lifo_destroy_and_can_be_cleared(self):
        first, second, third = (self.make_window() for _ in range(3))
        listener = Mock()
        modal.set_modal_front_listener(listener)
        for window in (first, second, third):
            modal.grab_modal(window)

        listener.reset_mock()
        second.destroy()
        listener.assert_called_once_with()
        self.assertIs(self.root.grab_current(), third)
        listener.reset_mock()
        first.destroy()
        listener.assert_called_once_with()
        self.assertIs(self.root.grab_current(), third)
        listener.reset_mock()
        third.destroy()
        listener.assert_called_once_with()

        listener.reset_mock()
        modal.set_modal_front_listener(None)
        fourth = self.make_window()
        modal.grab_modal(fourth)
        fourth.destroy()
        listener.assert_not_called()
        self.assertNotIn(fourth, modal._active_modals)

    def test_front_listener_exceptions_do_not_stop_grab_or_destroy(self):
        window = self.make_window()
        modal.set_modal_front_listener(Mock(side_effect=RuntimeError("front failed")))
        with self.assertLogs("keyseq.presentation.modal", level="ERROR"):
            modal.grab_modal(window)
        self.assertIn(window, modal._active_modals)
        with self.assertLogs("keyseq.presentation.modal", level="ERROR"):
            window.destroy()
        self.assertNotIn(window, modal._active_modals)

    def test_front_modal_uses_last_eligible_live_window(self):
        first, second, ignored = (self.make_window() for _ in range(3))
        modal.grab_modal(first)
        modal.grab_modal(second)
        self.assertIs(modal.front_modal(), second)
        modal.grab_modal(ignored, help_follow=False)
        self.assertIs(modal.front_modal(), second)
        second.destroy()
        self.assertIs(modal.front_modal(), first)
        first.destroy()
        self.assertIsNone(modal.front_modal())

    def test_front_modal_skips_destroyed_and_empty_registry(self):
        window = self.make_window()
        window.destroy()
        modal._active_modals.append(window)
        self.assertIsNone(modal.front_modal())
        modal._active_modals.clear()
        self.assertIsNone(modal.front_modal())

    def test_front_modal_skips_a_window_raising_tcl_error(self):
        live = self.make_window()
        broken = self.make_window()
        modal.grab_modal(live)
        modal.grab_modal(broken)
        with patch.object(broken, "winfo_exists", side_effect=tk.TclError("gone")):
            self.assertIs(modal.front_modal(), live)

    def test_last_input_tracks_focus_within_window_only(self):
        window = self.make_window()
        first_child = tk.Entry(window)
        first_child.pack()
        second_child = tk.Entry(window)
        second_child.pack()
        other = self.make_window()
        other_child = tk.Entry(other)
        other_child.pack()

        existing_focus_handler = Mock()
        window.bind("<FocusIn>", existing_focus_handler)
        with patch.object(window, "bind", wraps=window.bind) as bind:
            modal.grab_modal(window, focus=first_child)
        focus_binding = next(
            call for call in bind.call_args_list if call.args[0] == "<FocusIn>"
        )
        self.assertEqual(focus_binding.kwargs.get("add"), "+")
        remember_input = focus_binding.args[1]
        self.assertIs(modal.last_input(window), first_child)
        second_child.focus_set()
        self.root.update()
        self.assertIs(self.root.focus_get(), second_child)
        self.assertIs(modal.last_input(window), second_child)
        existing_focus_handler.assert_called()

        # Toplevel 自身と別窓の FocusIn は現在の入力先を上書きしない。
        remember_input(Mock(widget=window))
        remember_input(Mock(widget=other_child))
        window.focus_set()
        self.root.update()
        self.assertIs(modal.last_input(window), second_child)
        other_child.focus_set()
        self.root.update()
        self.assertIs(modal.last_input(window), second_child)
        second_child.destroy()
        self.assertIsNone(modal.last_input(window))

    def test_last_input_defaults_to_window_and_clears_on_destroy(self):
        window = self.make_window()
        modal.grab_modal(window)
        self.assertIs(modal.last_input(window), window)
        window.destroy()
        self.assertIsNone(modal.last_input(window))

    def test_resolve_grab_holder_follows_marked_windows_to_first_unmarked(self):
        parent = self.make_window()
        delegate = self.make_window(parent)
        nested_delegate = self.make_window(delegate)
        self.assertIs(modal.resolve_grab_holder(parent), parent)
        self.assertIs(modal.resolve_grab_holder(None), None)

        modal.mark_grab_delegate(delegate)
        self.assertIs(modal.resolve_grab_holder(delegate), parent)
        modal.mark_grab_delegate(nested_delegate)
        self.assertIs(modal.resolve_grab_holder(nested_delegate), parent)
        parent.destroy()
        self.assertIsNone(modal.resolve_grab_holder(nested_delegate))

    def test_grab_restores_to_dialog_when_delegate_was_previous_holder(self):
        dialog = self.make_window()
        delegate = self.make_window(dialog)
        new_modal = self.make_window()
        modal.grab_modal(dialog, self.root)
        modal.mark_grab_delegate(delegate)
        delegate.grab_set()

        modal.grab_modal(new_modal, self.root)
        new_modal.destroy()

        self.assertIs(self.root.grab_current(), dialog)


if __name__ == "__main__":
    unittest.main()
