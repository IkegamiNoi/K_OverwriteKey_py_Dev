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

    def test_grab_current_key_error_and_restore_tcl_error_are_tolerated(self):
        with self.subTest(branch="grab_current_key_error"):
            window = Mock()
            parent = Mock()
            window.grab_current.side_effect = KeyError("unknown grab holder")

            grab_modal(window, parent)

            window.grab_current.assert_called_once_with()
            window.grab_set.assert_called_once_with()
            window.bind.assert_called_once()
            self.assertEqual(window.bind.call_args.args[0], "<Destroy>")
            restore_grab = window.bind.call_args.args[1]
            restore_grab(Mock(widget=window))
            # 記録した保持者は None なので、復元時の照会や親のモーダル化は行わない。
            window.grab_current.assert_called_once_with()
            parent.grab_set.assert_not_called()

        with self.subTest(branch="restore_grab_set_tcl_error"):
            window = Mock()
            previous = Mock()
            window.grab_current.side_effect = [previous, None]
            previous.winfo_exists.return_value = True
            previous.winfo_viewable.return_value = True
            previous.grab_set.side_effect = tk.TclError("grab holder was destroyed")

            grab_modal(window)

            window.grab_set.assert_called_once_with()
            window.bind.assert_called_once()
            self.assertEqual(window.bind.call_args.args[0], "<Destroy>")
            restore_grab = window.bind.call_args.args[1]
            # 直接呼び出し、例外の吸収がなければ Tk の通知経由にせずテストを失敗させる。
            restore_grab(Mock(widget=window))
            self.assertEqual(window.grab_current.call_count, 2)
            previous.winfo_exists.assert_called_once_with()
            previous.winfo_viewable.assert_called_once_with()
            previous.grab_set.assert_called_once_with()

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
