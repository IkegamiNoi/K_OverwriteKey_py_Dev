from __future__ import annotations

import unittest
from unittest.mock import Mock, call, patch

from keyseq.infrastructure import input_gateway


class InputGatewayDragTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = input_gateway.InputGateway()
        self.mouse = Mock(FAILSAFE=True)
        patcher = patch.object(input_gateway, "pyautogui", self.mouse)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.events = Mock()
        for name in ("moveTo", "mouseDown", "mouseUp", "dragTo"):
            self.events.attach_mock(getattr(self.mouse, name), name)

    def test_call_order_and_failsafe(self) -> None:
        def observe(*args: object, **kwargs: object) -> None:
            self.assertIs(self.mouse.FAILSAFE, False)

        for name in ("moveTo", "mouseDown", "mouseUp"):
            getattr(self.mouse, name).side_effect = observe
        self.gateway.drag_mouse(100, 200, 400, 500, "left", 0.3)
        self.assertEqual(self.events.mock_calls, [
            call.moveTo(100, 200),
            call.mouseDown(button="left"),
            call.moveTo(400, 500, duration=0.3),
            call.mouseUp(button="left"),
        ])
        self.assertIs(self.mouse.FAILSAFE, True)
        self.mouse.dragTo.assert_not_called()

    def test_move_failure_releases_and_restores(self) -> None:
        error = RuntimeError("move failed")
        self.mouse.moveTo.side_effect = [None, error]
        with self.assertRaises(RuntimeError) as caught:
            self.gateway.drag_mouse(100, 200, 400, 500, "right", 0.3)
        self.assertIs(caught.exception, error)
        self.mouse.mouseUp.assert_called_once_with(button="right")
        self.assertIs(self.mouse.FAILSAFE, True)
        self.mouse.dragTo.assert_not_called()

    def test_mouse_down_failure_still_releases(self) -> None:
        error = RuntimeError("down failed")
        self.mouse.mouseDown.side_effect = error
        with self.assertRaises(RuntimeError) as caught:
            self.gateway.drag_mouse(100, 200, 400, 500, "left", 0.3)
        self.assertIs(caught.exception, error)
        self.assertEqual(self.events.mock_calls, [
            call.moveTo(100, 200),
            call.mouseDown(button="left"),
            call.mouseUp(button="left"),
        ])
        self.assertIs(self.mouse.FAILSAFE, True)

    def test_initial_move_failure_restores(self) -> None:
        error = RuntimeError("initial move failed")
        self.mouse.moveTo.side_effect = error
        with self.assertRaises(RuntimeError) as caught:
            self.gateway.drag_mouse(100, 200, 400, 500, "left", 0.3)
        self.assertIs(caught.exception, error)
        self.mouse.mouseDown.assert_not_called()
        self.assertIs(self.mouse.FAILSAFE, True)

    def test_mouse_up_failure_restores(self) -> None:
        error = RuntimeError("up failed")
        self.mouse.mouseUp.side_effect = error
        with self.assertRaises(RuntimeError) as caught:
            self.gateway.drag_mouse(100, 200, 400, 500, "left", 0.3)
        self.assertIs(caught.exception, error)
        self.assertIs(self.mouse.FAILSAFE, True)

    def test_original_false_failsafe_is_preserved(self) -> None:
        self.mouse.FAILSAFE = False
        self.gateway.drag_mouse(100, 200, 400, 500, "left", 0.3)
        self.assertIs(self.mouse.FAILSAFE, False)

    def test_click_preserves_failsafe(self) -> None:
        self.gateway.click_mouse(100, 200, "left", 2)
        self.mouse.click.assert_called_once_with(x=100, y=200, button="left", clicks=2)
        self.assertIs(self.mouse.FAILSAFE, True)
