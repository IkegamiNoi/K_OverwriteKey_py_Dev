import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation import modal
from keyseq.presentation.modal import grab_modal, install_minimize_grab_custody


class ModalGrabTest(unittest.TestCase):
    def setUp(self):
        registry_patch = patch.object(modal, "_active_modals", [])
        registry_patch.start()
        self.addCleanup(registry_patch.stop)
        custody_patch = patch.object(modal, "_custody_window", None)
        custody_patch.start()
        self.addCleanup(custody_patch.stop)
        minimized_patch = patch.object(modal, "_app_minimized", False)
        minimized_patch.start()
        self.addCleanup(minimized_patch.stop)
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.root.report_callback_exception = Mock()
        self.root.update_idletasks()
        self.root.grab_release()
        # cleanup 中の Destroy コールバック例外も失敗として検出する。
        self.addCleanup(self.root.report_callback_exception.assert_not_called)
        self.addCleanup(self.root.deiconify)

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

    def test_initial_focus_defaults_to_window(self):
        window = self.make_window()
        with patch.object(window, "focus_set") as focus_set:
            grab_modal(window, self.root)
        focus_set.assert_called_once_with()

    def test_initial_focus_uses_explicit_child(self):
        window = self.make_window()
        child = tk.Entry(window)
        with (
            patch.object(window, "focus_set") as window_focus,
            patch.object(child, "focus_set") as child_focus,
        ):
            grab_modal(window, self.root, focus=child)
        child_focus.assert_called_once_with()
        window_focus.assert_not_called()

    def test_duplicate_grab_does_not_repeat_initial_focus(self):
        window = self.make_window()
        with patch.object(window, "focus_set") as focus_set:
            grab_modal(window, self.root)
            focus_set.assert_called_once_with()
            focus_set.reset_mock()
            grab_modal(window, self.root)
            focus_set.assert_not_called()

    def test_custody_grab_does_not_repeat_initial_focus(self):
        window = self.make_window()
        with (
            patch.object(modal, "_custody_window", window),
            patch.object(window, "grab_current", return_value=None),
            patch.object(window, "focus_set") as focus_set,
        ):
            grab_modal(window, self.root)
        focus_set.assert_not_called()

    def test_initial_focus_does_not_force_or_lift_window(self):
        window = self.make_window()
        with (
            patch.object(window, "focus_set") as focus_set,
            patch.object(window, "focus_force") as focus_force,
            patch.object(window, "lift") as lift,
        ):
            grab_modal(window, self.root)
        focus_set.assert_called_once_with()
        focus_force.assert_not_called()
        lift.assert_not_called()

    def test_restores_previous_holder_independent_of_transient_parent(self):
        a = self.make_window()
        b = self.make_window()
        grab_modal(a, self.root)
        grab_modal(b, self.root)
        self.assertIs(self.root.grab_current(), b)
        b.destroy()
        self.assertIs(self.root.grab_current(), a)

    def test_iconify_releases_hidden_grab_holder(self):
        window = self.make_window()
        grab_modal(window, self.root)
        install_minimize_grab_custody(self.root)
        self.root.update()

        self.root.iconify()
        self.root.update()

        self.assertFalse(window.winfo_viewable())
        self.assertIsNone(self.root.grab_current())
        self.assertIs(modal._custody_window, window)

    def test_deiconify_restores_same_grab_holder(self):
        window = self.make_window()
        grab_modal(window, self.root)
        install_minimize_grab_custody(self.root)
        self.root.update()
        self.root.iconify()
        self.root.update()
        self.assertIsNone(self.root.grab_current())
        self.assertIs(modal._custody_window, window)

        self.root.deiconify()
        self.root.update()

        self.assertTrue(window.winfo_viewable())
        self.assertIs(self.root.grab_current(), window)
        self.assertIsNone(modal._custody_window)

    def test_repeated_grab_modal_in_custody_restores_same_holder(self):
        window = self.make_window()
        grab_modal(window, self.root)
        install_minimize_grab_custody(self.root)
        self.root.update()
        self.root.iconify()
        self.root.update()
        self.assertIsNone(self.root.grab_current())
        self.assertIs(modal._custody_window, window)

        with patch.object(window, "bind", wraps=window.bind) as bind:
            grab_modal(window, self.root)
            bind.assert_not_called()

        self.assertIs(modal._custody_window, window)
        self.assertIsNone(self.root.grab_current())
        self.assertEqual(modal._active_modals, [window])
        self.root.deiconify()
        self.root.update()

        self.assertTrue(window.winfo_viewable())
        self.assertIs(self.root.grab_current(), window)
        self.assertIsNone(modal._custody_window)

    def test_unmap_preserves_visible_grab_holder(self):
        window = self.make_window()
        grab_modal(window)
        install_minimize_grab_custody(self.root)
        self.root.update()
        self.assertTrue(window.winfo_viewable())

        self.root.event_generate("<Unmap>")

        self.assertIs(self.root.grab_current(), window)
        self.assertIsNone(modal._custody_window)

    def test_child_unmap_does_not_take_custody(self):
        window = self.make_window()
        frame = tk.Frame(self.root)
        frame.pack()
        grab_modal(window)
        install_minimize_grab_custody(self.root)
        self.root.update()
        window.withdraw()
        self.root.update()
        self.assertFalse(window.winfo_viewable())
        self.assertIs(self.root.grab_current(), window)

        frame.pack_forget()
        self.root.update()

        self.assertIs(self.root.grab_current(), window)
        self.assertIsNone(modal._custody_window)

    def test_new_modal_restores_holder_taken_into_custody(self):
        previous = self.make_window()
        grab_modal(previous, self.root)
        install_minimize_grab_custody(self.root)
        self.root.update()
        self.root.iconify()
        self.root.update()
        self.assertIsNone(self.root.grab_current())
        self.assertIs(modal._custody_window, previous)

        window = self.make_window()
        grab_modal(window)
        self.assertIsNone(modal._custody_window)
        self.assertIs(self.root.grab_current(), window)
        self.root.deiconify()
        self.root.update()
        self.assertTrue(previous.winfo_viewable())
        self.assertIs(self.root.grab_current(), window)
        window.destroy()

        self.assertIs(self.root.grab_current(), previous)

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

    def test_hidden_previous_holder_is_not_taken_into_custody_when_not_minimized(self):
        with patch.object(modal, "_app_minimized", False):
            a = self.make_window()
            b = self.make_window()
            grab_modal(a)
            a.withdraw()
            self.assertTrue(a.winfo_exists())
            self.assertFalse(a.winfo_viewable())
            self.assertIs(self.root.grab_current(), a)
            grab_modal(b)
            self.assertIsNone(modal._custody_window)
            with patch.object(a, "grab_set", wraps=a.grab_set) as restore:
                b.destroy()
                restore.assert_not_called()
            self.assertIsNone(self.root.grab_current())
            self.assertIsNone(modal._custody_window)

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

    def test_registry_records_opening_order_with_innermost_last(self):
        a = self.make_window()
        b = self.make_window()
        c = self.make_window()
        grab_modal(a)
        self.assertEqual(modal._active_modals, [a])
        grab_modal(b)
        self.assertEqual(modal._active_modals, [a, b])
        grab_modal(c)
        self.assertEqual(modal._active_modals, [a, b, c])
        self.assertIs(modal._active_modals[-1], c)

    def test_registry_removes_destroyed_windows_in_lifo_order(self):
        a = self.make_window()
        b = self.make_window()
        grab_modal(a)
        grab_modal(b)
        self.assertEqual(modal._active_modals, [a, b])
        b.destroy()
        self.assertEqual(modal._active_modals, [a])
        a.destroy()
        self.assertEqual(modal._active_modals, [])

    def test_registry_non_lifo_destroy_preserves_remaining_order(self):
        a = self.make_window()
        b = self.make_window()
        c = self.make_window()
        grab_modal(a)
        grab_modal(b)
        grab_modal(c)
        self.assertEqual(modal._active_modals, [a, b, c])
        b.destroy()
        self.assertEqual(modal._active_modals, [a, c])
        self.assertIs(self.root.grab_current(), c)

    def test_registry_repeated_grab_modal_does_not_duplicate_window(self):
        a = self.make_window()
        grab_modal(a)
        grab_modal(a)
        self.assertEqual(modal._active_modals, [a])
        a.destroy()
        self.assertEqual(modal._active_modals, [])

    def test_registry_child_widget_destroy_keeps_modal_registered(self):
        a = self.make_window()
        b = self.make_window()
        child = tk.Label(b, text="child")
        child.pack()
        grab_modal(a)
        grab_modal(b)
        child.destroy()
        self.assertEqual(modal._active_modals, [a, b])
        b.destroy()
        self.assertEqual(modal._active_modals, [a])

    def test_registry_excludes_windows_without_grab_modal(self):
        a = self.make_window()
        b = self.make_window()
        self.assertEqual(modal._active_modals, [])
        grab_modal(a)
        self.assertEqual(modal._active_modals, [a])
        b.destroy()
        self.assertEqual(modal._active_modals, [a])

    def test_registry_removes_window_when_previous_holder_cannot_restore(self):
        for state in ("destroyed", "withdrawn"):
            with self.subTest(previous_holder=state):
                a = self.make_window()
                b = self.make_window()
                grab_modal(a)
                grab_modal(b)
                self.assertEqual(modal._active_modals, [a, b])
                if state == "destroyed":
                    a.destroy()
                    self.assertFalse(a.winfo_exists())
                    self.assertEqual(modal._active_modals, [b])
                else:
                    a.withdraw()
                    self.assertFalse(a.winfo_viewable())
                    self.assertEqual(modal._active_modals, [a, b])
                with patch.object(a, "grab_set", wraps=a.grab_set) as restore:
                    b.destroy()
                    restore.assert_not_called()
                self.assertEqual(
                    modal._active_modals, [] if state == "destroyed" else [a]
                )
                self.assertIsNone(self.root.grab_current())
                self.cleanup_window(a)
                self.assertEqual(modal._active_modals, [])
