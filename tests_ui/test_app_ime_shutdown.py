"""Verify shutdown ordering without creating a Tk window."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call

from keyseq.presentation.app import App


class AppImeShutdownTests(unittest.TestCase):
    def test_close_restores_after_hook_stop_before_destroy(self) -> None:
        trace = Mock()
        app = SimpleNamespace(
            keymap_set_io=SimpleNamespace(confirm_save_if_dirty=trace.confirm),
            pane_layout=SimpleNamespace(cancel_window_width_save=trace.cancel),
            compact_window=SimpleNamespace(cancel_save=trace.cancel),
            hook=SimpleNamespace(begin_shutdown=trace.begin, stop_hook=trace.stop),
            layout=SimpleNamespace(keyboard_window=None),
            input_gateway=SimpleNamespace(restore_ime_now=trace.restore),
            held_inputs=SimpleNamespace(release_all=trace.release),
            destroy=trace.destroy,
        )
        trace.confirm.return_value = True
        trace.release.return_value = []
        App.on_close(app)
        self.assertEqual(trace.mock_calls, [
            call.confirm("終了"), call.cancel(), call.cancel(), call.begin(), call.stop(),
            call.release(), call.restore(), call.destroy(),
        ])

    def test_restore_runs_if_hook_stop_raises(self) -> None:
        trace = Mock()
        app = SimpleNamespace(
            keymap_set_io=SimpleNamespace(confirm_save_if_dirty=trace.confirm),
            pane_layout=SimpleNamespace(cancel_window_width_save=trace.cancel),
            compact_window=SimpleNamespace(cancel_save=trace.cancel),
            hook=SimpleNamespace(begin_shutdown=trace.begin, stop_hook=trace.stop),
            layout=SimpleNamespace(keyboard_window=None),
            input_gateway=SimpleNamespace(restore_ime_now=trace.restore),
            held_inputs=SimpleNamespace(release_all=trace.release),
            destroy=trace.destroy,
        )
        trace.confirm.return_value = True
        trace.release.return_value = []
        trace.stop.side_effect = RuntimeError("stop failed")
        with self.assertRaisesRegex(RuntimeError, "stop failed"):
            App.on_close(app)
        self.assertEqual(trace.mock_calls[-3:], [call.release(), call.restore(), call.destroy()])
