import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.views.menu_command_queue import MenuCommandQueue


class MenuCommandQueueTests(unittest.TestCase):
    def make_queue(self):
        widget = Mock()
        widget.tk.call.return_value = "aqua"
        callbacks = {}
        counter = iter(range(1, 1000))

        def after(delay, callback):
            after_id = f"after#{next(counter)}"
            callbacks[after_id] = (delay, callback)
            return after_id

        widget.after.side_effect = after
        widget.after_cancel.side_effect = lambda after_id: callbacks.pop(after_id, None)
        queue = MenuCommandQueue(widget)

        def run_next():
            # 予約が無ければ何もしない（実行中に次が予約されていないことの確認にも使う）。
            if not callbacks:
                return None
            key = next(iter(callbacks))
            delay, callback = callbacks.pop(key)
            callback()
            return delay
        return queue, widget, callbacks, run_next

    def test_non_aqua_returns_same_command(self):
        widget = Mock()
        widget.tk.call.return_value = "win32"
        queue = MenuCommandQueue(widget)
        command = Mock()
        self.assertIs(queue.defer(command), command)

    def test_commands_run_sequentially_and_errors_do_not_stop_queue(self):
        queue, widget, callbacks, run_next = self.make_queue()
        seen = []
        first = Mock(side_effect=lambda: (seen.append(1), self.assertIsNone(run_next())))
        second = Mock(side_effect=lambda: seen.append(2))
        queue.defer(first)()
        queue.defer(second)()
        with patch("keyseq.presentation.views.menu_command_queue.modal.is_modal_active", return_value=False):
            run_next()
            self.assertEqual(seen, [1])
            run_next()
        self.assertEqual(seen, [1, 2])

        after_error = Mock()
        queue.defer(Mock(side_effect=RuntimeError("failure")))()
        queue.defer(after_error)()
        with patch("keyseq.presentation.views.menu_command_queue.modal.is_modal_active", return_value=False), self.assertLogs("keyseq.presentation.views.menu_command_queue", level="ERROR"):
            run_next()
            run_next()
        after_error.assert_called_once_with()

    def test_modal_waits_and_cancel_all_cancels_reservation(self):
        queue, widget, callbacks, run_next = self.make_queue()
        command = Mock()
        queue.defer(command)()
        with patch("keyseq.presentation.views.menu_command_queue.modal.is_modal_active", side_effect=[True, False]):
            self.assertEqual(run_next(), 0)
            self.assertEqual(run_next(), 100)
            command.assert_called_once_with()
        queue.defer(command)()
        queue.cancel_all()
        widget.after_cancel.assert_called_once()
        self.assertFalse(callbacks)

    def test_cancel_all_cancels_modal_wait_and_discards_command(self):
        queue, widget, callbacks, run_next = self.make_queue()
        command = Mock()
        queue.defer(command)()
        with patch("keyseq.presentation.views.menu_command_queue.modal.is_modal_active", return_value=True):
            self.assertEqual(run_next(), 0)
            self.assertEqual(run_next(), 100)
        wait_id = next(iter(callbacks))
        queue.cancel_all()
        widget.after_cancel.assert_called_with(wait_id)
        self.assertFalse(callbacks)
        command.assert_not_called()

    def test_cancel_all_continues_when_after_cancel_raises_tcl_error(self):
        queue, widget, callbacks, _run_next = self.make_queue()
        queue.defer(Mock())()
        widget.after_cancel.side_effect = __import__("tkinter").TclError("closed")
        queue.cancel_all()
        # 偽の after は取り消しに失敗して予約が残るが、待ち行列の側は空になり予約の ID も手放す。
        self.assertFalse(queue.commands)
        self.assertIsNone(queue.after_id)

    def test_cancel_all_inside_command_finishes_current_and_discards_following(self):
        queue, _widget, _callbacks, run_next = self.make_queue()
        seen = []

        def first():
            seen.append("start")
            queue.cancel_all()
            seen.append("finish")

        queue.defer(first)()
        queue.defer(lambda: seen.append("later"))()
        with patch("keyseq.presentation.views.menu_command_queue.modal.is_modal_active", return_value=False):
            run_next()
        self.assertEqual(seen, ["start", "finish"])


if __name__ == "__main__":
    unittest.main()
