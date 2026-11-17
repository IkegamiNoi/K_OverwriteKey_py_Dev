import unittest
from unittest.mock import Mock, patch
import tkinter

from keyseq.presentation import message_box, modal


class MessageBoxTests(unittest.TestCase):
    def setUp(self):
        self.active = patch.object(modal, "_active_modals", [])
        self.active.start()
        self.addCleanup(self.active.stop)
        self.boxes = patch.object(modal, "_message_boxes", 0)
        self.boxes.start()
        self.addCleanup(self.boxes.stop)
        self.backend = Mock()
        self.backend.window = Mock()
        self.backend_patch = patch("keyseq.presentation.message_box.get_backend", return_value=self.backend)
        self.backend_patch.start()
        self.addCleanup(self.backend_patch.stop)

    def test_parent_prefers_innermost_viewable_modal(self):
        outer, inner = Mock(), Mock()
        for window in (outer, inner):
            window.winfo_exists.return_value = True
            window.winfo_viewable.return_value = True
        modal._active_modals.extend((outer, inner))
        with patch.object(tkinter.messagebox, "showinfo", return_value="ok") as call:
            self.assertEqual(message_box.showinfo("t", "m"), "ok")
        self.assertIs(call.call_args.kwargs["parent"], inner)

    def test_parent_uses_viewable_default_root_or_none(self):
        root = Mock()
        root.winfo_viewable.return_value = True
        with patch.object(tkinter, "_default_root", root), patch.object(tkinter.messagebox, "showinfo") as call:
            message_box.showinfo("t", "m")
        self.assertIs(call.call_args.kwargs["parent"], root)
        with patch.object(tkinter, "_default_root", None), patch.object(tkinter.messagebox, "showinfo") as call:
            message_box.showinfo("t", "m")
        self.assertNotIn("parent", call.call_args.kwargs)

    def test_explicit_parent_and_front_activation_policy(self):
        parent = object()
        with patch.object(tkinter.messagebox, "showinfo") as info:
            message_box.showinfo("t", "m", parent=parent)
        self.assertIs(info.call_args.kwargs["parent"], parent)
        with patch.object(tkinter.messagebox, "showerror"):
            message_box.showerror("t", "m")
        self.backend.window.bring_app_to_front.assert_called_once_with()
        self.backend.window.reset_mock()
        with patch.object(tkinter.messagebox, "showwarning"):
            message_box.showwarning("t", "m")
        self.backend.window.bring_app_to_front.assert_called_once_with()
        self.backend.window.reset_mock()
        with patch.object(tkinter.messagebox, "askyesno"):
            message_box.askyesno("t", "m")
        self.backend.window.bring_app_to_front.assert_not_called()

    def test_leave_runs_when_callable_raises_and_callable_is_late_bound(self):
        with patch.object(modal, "enter_message_box") as enter, patch.object(modal, "leave_message_box") as leave:
            with patch.object(tkinter.messagebox, "showinfo", side_effect=RuntimeError):
                with self.assertRaises(RuntimeError):
                    message_box.showinfo("t", "m")
        enter.assert_called_once_with()
        leave.assert_called_once_with()
        replacement = Mock(return_value="patched")
        with patch.object(tkinter.messagebox, "showinfo", replacement):
            self.assertEqual(message_box.showinfo("t", "m"), "patched")


if __name__ == "__main__":
    unittest.main()
