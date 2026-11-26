from __future__ import annotations

import unittest
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor
from keyseq.domain.mouse_scroll import NO_SCROLL_INVERT, ScrollInvert


from keyseq.shared.i18n import fix_language

fix_language("ja")


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
        self.assertEqual(
            message,
            "mouse_scrollの指定が正しくありません: "
            "向きはup / down / left / rightのいずれかを指定してください。"
            "（direction=bad unit=notch amount=1 ラベル: memo）",
        )

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

    def test_vertical_invert_only_changes_vertical_rows(self) -> None:
        self.executor._get_scroll_invert = lambda: ScrollInvert(vertical=True)
        self.assertTrue(self.executor.execute({"type": "mouse_scroll", "direction": "down", "amount": 3}))
        self.assertEqual(self.gateway.scroll_mouse.call_args.kwargs["deltas"], (120, 120, 120))
        self.assertTrue(self.executor.execute({"type": "mouse_scroll", "direction": "right", "unit": "delta", "amount": 300}))
        self.assertEqual(self.gateway.scroll_mouse.call_args.kwargs["deltas"], (120, 120, 60))

    def test_horizontal_invert_preserves_position(self) -> None:
        self.executor._get_scroll_invert = lambda: ScrollInvert(horizontal=True)
        self.assertTrue(self.executor.execute({"type": "mouse_scroll", "direction": "right", "unit": "delta", "amount": 300, "x": 10, "y": 20}))
        self.gateway.scroll_mouse.assert_called_once_with(
            vertical=False, deltas=(-120, -120, -60), position=(10, 20),
        )

    def test_invert_callable_is_read_for_each_row(self) -> None:
        get_invert = Mock(side_effect=(NO_SCROLL_INVERT, ScrollInvert(vertical=True)))
        self.executor._get_scroll_invert = get_invert
        action = {"type": "mouse_scroll", "direction": "up", "amount": 1}
        self.assertTrue(self.executor.execute(action))
        self.assertTrue(self.executor.execute(action))
        self.assertEqual(get_invert.call_count, 2)
        self.assertEqual([call.kwargs["deltas"] for call in self.gateway.scroll_mouse.call_args_list],
                         [(120,), (-120,)])

    def test_invert_callable_error_reports_and_does_not_send(self) -> None:
        self.executor._get_scroll_invert = Mock(side_effect=RuntimeError("setting failed"))
        self.assertFalse(self.executor.execute({"type": "mouse_scroll", "direction": "up", "amount": 1}, owner="f8"))
        self.gateway.scroll_mouse.assert_not_called()
        self.assertEqual(self.on_action_error.call_count, 1)


if __name__ == "__main__":
    unittest.main()
