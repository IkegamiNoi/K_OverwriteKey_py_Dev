from __future__ import annotations

import unittest
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor


class MouseScrollExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = Mock()
        self.held_inputs = Mock()
        self.held_inputs.release_owner.return_value = []
        self.on_action_error = Mock()
        self.executor = ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=Mock(return_value=("", "")),
            on_action_error=self.on_action_error,
            on_runtime_error=Mock(),
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
            held_inputs=self.held_inputs,
        )

    def test_success_passes_axis_deltas_and_position(self) -> None:
        action = {"type": "mouse_scroll", "direction": "right", "unit": "delta",
                  "amount": 300, "x": 10, "y": 20}
        self.assertIs(self.executor.execute(action, owner="f8"), True)
        self.gateway.scroll_mouse.assert_called_once_with(
            vertical=False, deltas=(120, 120, 60), position=(10, 20),
        )
        self.on_action_error.assert_not_called()

    def test_invalid_action_reports_reason_description_label_and_releases_owner(self) -> None:
        action = {"type": "mouse_scroll", "direction": "bad", "unit": "notch",
                  "amount": 1, "label": "memo"}
        self.assertIs(self.executor.execute(action, owner="f8"), False)
        self.gateway.scroll_mouse.assert_not_called()
        self.held_inputs.release_owner.assert_called_once_with("f8")
        message = self.on_action_error.call_args.args[1]
        self.assertIn("向きはup / down / left / right", message)
        self.assertIn("direction=bad unit=notch amount=1 ラベル: memo", message)

    def test_gateway_error_reports_details_and_releases_owner(self) -> None:
        self.gateway.scroll_mouse.side_effect = OSError(5, "SendInput failed")
        action = {"type": "mouse_scroll", "direction": "up", "amount": 1}
        self.assertIs(self.executor.execute(action, owner="f8"), False)
        self.held_inputs.release_owner.assert_called_once_with("f8")
        message = self.on_action_error.call_args.args[1]
        self.assertIn("mouse_scrollの送信に失敗しました: [Errno 5", message)
        self.assertIn("direction=up unit=（なし） amount=1", message)

    def test_unknown_type_message_lists_mouse_scroll(self) -> None:
        self.assertIs(self.executor.execute({"type": "unknown"}), False)
        self.assertIn("mouse_scroll", self.on_action_error.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
