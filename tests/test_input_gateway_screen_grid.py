from __future__ import annotations

import unittest
from unittest.mock import Mock, call, patch

from keyseq.infrastructure import input_gateway


class InputGatewayScreenGridTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = input_gateway.InputGateway()
        self.mouse = Mock(FAILSAFE=True)
        patcher = patch.object(input_gateway, "pyautogui", self.mouse)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_cursor_position_returns_integer_coordinates(self) -> None:
        self.mouse.position.return_value = Mock(x=12.8, y=-34.2)
        self.assertEqual(self.gateway.cursor_position(), (12, -34))
        self.mouse.position.assert_called_once_with()

    def test_move_cursor_disables_pause_and_restores_failsafe(self) -> None:
        self.mouse.moveTo.side_effect = lambda *args, **kwargs: self.assertFalse(
            self.mouse.FAILSAFE
        )
        self.gateway.move_cursor(12, -34)
        self.mouse.moveTo.assert_called_once_with(12, -34, _pause=False)
        self.assertTrue(self.mouse.FAILSAFE)

    def test_click_at_moves_then_clicks_without_pause(self) -> None:
        events = Mock()
        events.attach_mock(self.mouse.moveTo, "moveTo")
        events.attach_mock(self.mouse.click, "click")
        for method in (self.mouse.moveTo, self.mouse.click):
            method.side_effect = lambda *args, **kwargs: self.assertFalse(
                self.mouse.FAILSAFE
            )

        self.gateway.click_at(120, 340, "right")

        self.assertEqual(events.mock_calls, [
            call.moveTo(120, 340, _pause=False),
            call.click(button="right", _pause=False),
        ])
        self.assertTrue(self.mouse.FAILSAFE)

    def test_cursor_actions_restore_failsafe_after_error(self) -> None:
        self.mouse.moveTo.side_effect = RuntimeError("move failed")
        with self.assertRaisesRegex(RuntimeError, "move failed"):
            self.gateway.move_cursor(1, 2)
        self.assertTrue(self.mouse.FAILSAFE)

        self.mouse.moveTo.side_effect = None
        self.mouse.click.side_effect = RuntimeError("click failed")
        with self.assertRaisesRegex(RuntimeError, "click failed"):
            self.gateway.click_at(1, 2, "left")
        self.assertTrue(self.mouse.FAILSAFE)
