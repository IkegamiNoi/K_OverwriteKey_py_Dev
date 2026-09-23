import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.hook_controller import HookController
from tests_ui.hook_resume_wait import wait_for_hook_pause_count


class HookControllerTeardownTest(unittest.TestCase):
    def setUp(self):
        self.app = tk.Tk()
        self.app.report_callback_exception = Mock()
        self.addCleanup(self.app.report_callback_exception.assert_not_called)
        self.addCleanup(self.app.destroy)
        self.app.update_idletasks()
        self.hook = HookController(self.app)
        # OS フックやアプリ全体を起動せず、実際の開始・停止処理を隔離する。
        self.app.sequence_runner = Mock()
        self.app.hook_coordinator = Mock()
        self.app.key_state_manager = Mock()
        self.app.keymap_service = Mock()
        self.app.layout = Mock()
        self.app.trigger_panel = Mock()
        self.app.data = {"triggers": []}

    def wait_pause_count(self, expected):
        wait_for_hook_pause_count(
            self, SimpleNamespace(update=self.app.update, hook=self.hook), expected,
        )

    def make_window(self):
        window = tk.Toplevel(self.app)
        self.addCleanup(self.cleanup_window, window)
        window.update_idletasks()
        self.assertTrue(window.winfo_viewable())
        return window

    def cleanup_window(self, window):
        if window.winfo_exists():
            window.destroy()
        self.app.update()

    def test_window_destroy_defers_resume_on_app(self):
        window = self.make_window()
        existing_handler = Mock()
        window.bind("<Destroy>", existing_handler)
        self.hook.hook_active = True
        with patch.object(window, "bind", wraps=window.bind) as bind:
            self.hook.suspend_hook_for_dialog(window)
        bind.assert_called_once()
        self.assertEqual(bind.call_args.args[0], "<Destroy>")
        self.assertEqual(bind.call_args.args[2], "+")
        self.app.hook_coordinator.stop.assert_called_once_with()
        with patch.object(self.app, "after", wraps=self.app.after) as after:
            window.destroy()
            after.assert_called_once_with(0, self.hook.resume_hook_after_dialog)
            existing_handler.assert_called_once()
            self.assertEqual(self.hook.get_hook_pause_count(), 1)
            self.app.hook_coordinator.start.assert_not_called()
            self.app.update_idletasks()
            self.assertEqual(self.hook.get_hook_pause_count(), 1)
            self.wait_pause_count(0)
        self.app.hook_coordinator.start.assert_called_once()
        self.assertFalse(self.hook.hook_was_active_before_dialog)

    def test_omitted_window_requires_explicit_resume(self):
        window = self.make_window()
        self.hook.hook_active = True
        with patch.object(window, "bind", wraps=window.bind) as bind:
            self.hook.suspend_hook_for_dialog()
        bind.assert_not_called()
        self.hook.suspend_hook_for_dialog()
        self.app.hook_coordinator.stop.assert_called_once_with()
        window.destroy()
        self.app.update()
        self.assertEqual(self.hook.get_hook_pause_count(), 2)
        self.hook.resume_hook_after_dialog()
        self.assertEqual(self.hook.get_hook_pause_count(), 1)
        self.app.hook_coordinator.start.assert_not_called()
        self.hook.resume_hook_after_dialog()
        self.assertEqual(self.hook.get_hook_pause_count(), 0)
        self.app.hook_coordinator.start.assert_called_once()

    def test_child_destroy_does_not_schedule_resume(self):
        window = self.make_window()
        child = tk.Label(window, text="child")
        child.pack()
        window.update_idletasks()
        self.hook.suspend_hook_for_dialog(window)
        with patch.object(self.app, "after", wraps=self.app.after) as after:
            child.destroy()
            self.app.update()
            after.assert_not_called()
            self.assertEqual(self.hook.get_hook_pause_count(), 1)
            window.destroy()
            self.wait_pause_count(0)

    def test_repeated_destroy_resumes_only_once(self):
        window = self.make_window()
        other = self.make_window()
        with patch.object(window, "bind", wraps=window.bind) as bind:
            self.hook.suspend_hook_for_dialog(window)
        handler = bind.call_args.args[1]
        self.hook.suspend_hook_for_dialog(other)
        with patch.object(self.app, "after", wraps=self.app.after) as after:
            window.destroy()
            handler(Mock(widget=window))
            after.assert_called_once_with(0, self.hook.resume_hook_after_dialog)
            self.assertEqual(self.hook.get_hook_pause_count(), 2)
            self.wait_pause_count(1)
            handler(Mock(widget=window))
            self.app.update()
            self.assertEqual(after.call_count, 1)
        # 別ウィンドウ分まで過剰に decrement していないこと。
        self.assertEqual(self.hook.get_hook_pause_count(), 1)
        other.destroy()
        self.wait_pause_count(0)

    def test_shutdown_guard_blocks_start_but_preserves_resume_bookkeeping(self):
        window = self.make_window()
        self.hook.hook_active = True
        self.hook.suspend_hook_for_dialog(window)
        window.destroy()
        self.hook.begin_shutdown()
        with patch.object(self.hook, "validate_hook_configuration") as validate:
            self.wait_pause_count(0)
            self.assertFalse(self.hook.hook_was_active_before_dialog)
            # 同期解除も、元の active 状態からの停止を再現して確認する。
            self.hook.hook_active = True
            self.hook.suspend_hook_for_dialog()
            self.hook.resume_hook_after_dialog()
            self.assertEqual(self.hook.get_hook_pause_count(), 0)
            self.assertFalse(self.hook.hook_was_active_before_dialog)
            self.hook.start_hook()
            validate.assert_not_called()
        self.app.hook_coordinator.start.assert_not_called()
        self.assertFalse(self.hook.hook_active)
