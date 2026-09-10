import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.modal import grab_modal


class ModalGrabTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.root.report_callback_exception = Mock()
        self.root.update_idletasks()
        self.root.grab_release()
        # cleanup 中の Destroy コールバック例外も失敗として検出する。
        self.addCleanup(self.root.report_callback_exception.assert_not_called)

    def make_window(self):
        # 非 LIFO 終了で連鎖破棄されないよう、すべて root の直接の子にする。
        window = tk.Toplevel(self.root)
        self.addCleanup(self.cleanup_window, window)
        window.update_idletasks()
        self.assertTrue(window.winfo_viewable())
        return window

    @staticmethod
    def cleanup_window(window):
        if window.winfo_exists():
            window.grab_release()
            window.destroy()

    def test_restores_previous_holder_independent_of_transient_parent(self):
        a = self.make_window()
        b = self.make_window()
        grab_modal(a, self.root)
        grab_modal(b, self.root)
        self.assertIs(self.root.grab_current(), b)
        b.destroy()
        self.assertIs(self.root.grab_current(), a)

    def test_no_previous_holder_does_not_modalize_parent(self):
        b = self.make_window()
        self.assertIsNone(self.root.grab_current())
        grab_modal(b, self.root)
        b.destroy()
        self.assertIsNone(self.root.grab_current())

    def test_withdrawn_previous_holder_is_not_restored(self):
        a = self.make_window()
        b = self.make_window()
        grab_modal(a)
        a.withdraw()
        self.assertTrue(a.winfo_exists())
        self.assertFalse(a.winfo_viewable())
        self.assertIs(self.root.grab_current(), a)
        grab_modal(b)
        with patch.object(a, "grab_set", wraps=a.grab_set) as restore:
            b.destroy()
            restore.assert_not_called()
        self.assertIsNone(self.root.grab_current())

    def test_destroyed_previous_holder_is_not_restored(self):
        a = self.make_window()
        b = self.make_window()
        grab_modal(a)
        grab_modal(b)
        a.destroy()
        self.assertFalse(a.winfo_exists())
        self.assertIs(self.root.grab_current(), b)
        with patch.object(a, "grab_set", wraps=a.grab_set) as restore:
            b.destroy()
            restore.assert_not_called()
        self.assertIsNone(self.root.grab_current())

    def test_non_lifo_destroy_preserves_innermost_grab(self):
        a = self.make_window()
        b = self.make_window()
        c = self.make_window()
        grab_modal(a)
        grab_modal(b)
        grab_modal(c)
        with patch.object(a, "grab_set", wraps=a.grab_set) as restore:
            b.destroy()
            restore.assert_not_called()
        self.assertIs(self.root.grab_current(), c)

    def test_child_widget_destroy_does_not_restore_grab(self):
        a = self.make_window()
        b = self.make_window()
        child = tk.Label(b, text="child")
        child.pack()
        grab_modal(a)
        grab_modal(b)
        child.destroy()
        self.assertIs(self.root.grab_current(), b)
        b.destroy()
        self.assertIs(self.root.grab_current(), a)

    def test_repeated_grab_modal_restores_exactly_once(self):
        a = self.make_window()
        b = self.make_window()
        grab_modal(a)
        grab_modal(b)
        grab_modal(b)
        self.assertIs(self.root.grab_current(), b)
        with patch.object(a, "grab_set", wraps=a.grab_set) as restore:
            b.destroy()
            restore.assert_called_once_with()
        self.assertIs(self.root.grab_current(), a)
