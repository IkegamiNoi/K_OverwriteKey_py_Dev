import unittest
from unittest.mock import Mock, call, patch

from keyseq.presentation.app import App


class AppOnCloseTests(unittest.TestCase):
    def make_app(self, events):
        app = App.__new__(App)
        app._closing = False
        app.keymap_set_io = Mock()
        app.keymap_set_io.confirm_save_if_dirty.return_value = True
        for name in ("pane_layout", "compact_window", "hook", "hook_dispatcher", "layout", "help", "license", "delayed_calls", "held_inputs", "input_gateway", "screen_grid"):
            setattr(app, name, Mock())
        app.held_inputs.release_all.return_value = []
        app.layout.keyboard_window = None
        app.menu_commands = Mock()
        app.menu_commands.cancel_all.side_effect = lambda: events.append("cancel")
        app.destroy = Mock(side_effect=lambda: events.append("destroy"))
        return app

    @patch("keyseq.presentation.app.shutdown_capture_hook")
    def test_confirmed_close_cancels_menu_commands_before_destroy(self, _shutdown):
        events = []
        app = self.make_app(events)
        App.on_close(app)
        self.assertEqual(events, ["cancel", "destroy"])

    @patch("keyseq.presentation.app.shutdown_capture_hook")
    def test_cancelled_close_keeps_menu_commands_and_window(self, _shutdown):
        app = self.make_app([])
        app.keymap_set_io.confirm_save_if_dirty.return_value = False
        App.on_close(app)
        app.menu_commands.cancel_all.assert_not_called()
        app.destroy.assert_not_called()
        self.assertFalse(app._closing)

    def test_confirm_error_resets_closing_and_propagates(self):
        app = self.make_app([])
        error = RuntimeError("confirm failed")
        app.keymap_set_io.confirm_save_if_dirty.side_effect = error
        with self.assertRaisesRegex(RuntimeError, "confirm failed"):
            App.on_close(app)
        self.assertFalse(app._closing)

    def test_reentrant_close_does_not_confirm_twice(self):
        app = App.__new__(App)
        app._closing = False
        app.keymap_set_io = Mock()
        app.keymap_set_io.confirm_save_if_dirty.side_effect = lambda _title: (App.on_close(app), False)[1]

        App.on_close(app)

        app.keymap_set_io.confirm_save_if_dirty.assert_called_once()
        self.assertFalse(app._closing)


if __name__ == "__main__":
    unittest.main()
