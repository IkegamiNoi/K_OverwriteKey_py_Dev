from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend.windows import mouse_backend


class MouseBackendCaptureTests(unittest.TestCase):
    def test_capture_starts_daemon_listener_without_waiting(self) -> None:
        on_capture = Mock()
        with patch.object(mouse_backend.mouse, "Listener") as listener_factory:
            listener = listener_factory.return_value
            listener.start.side_effect = lambda: self.assertIs(listener.daemon, True)
            result = mouse_backend.WindowsMouseBackend().capture_next_click(on_capture)

        self.assertIsNone(result)
        listener_factory.assert_called_once()
        listener.start.assert_called_once_with()
        listener.join.assert_not_called()
        on_capture.assert_not_called()

    def test_release_continues_and_press_captures_then_stops(self) -> None:
        on_capture = Mock()
        with patch.object(mouse_backend.mouse, "Listener") as listener_factory:
            mouse_backend.WindowsMouseBackend().capture_next_click(on_capture)
        on_click = listener_factory.call_args.kwargs["on_click"]

        self.assertIs(on_click(12.5, -34.5, mouse_backend.mouse.Button.left, False), True)
        on_capture.assert_not_called()
        self.assertIs(on_click(12.5, -34.5, mouse_backend.mouse.Button.left, True), False)
        on_capture.assert_called_once_with(12.5, -34.5)


if __name__ == "__main__":
    unittest.main()
