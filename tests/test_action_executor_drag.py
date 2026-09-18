from __future__ import annotations

import unittest
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor


class ActionExecutorDragTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = Mock()
        self.on_runtime_error = Mock()
        self.executor = ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=Mock(),
            on_action_error=Mock(),
            on_runtime_error=self.on_runtime_error,
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
        )

    def test_without_drag_uses_existing_click(self) -> None:
        for extra in ({}, {"drag": False, "to_x": "bad", "drag_speed": 0}):
            with self.subTest(extra=extra):
                self.gateway.reset_mock()
                self.executor._execute_mouse_click({
                    "x": "100", "y": 200, "button": " RIGHT ", "clicks": "3", **extra,
                })
                self.gateway.click_mouse.assert_called_once_with(
                    x=100, y=200, button="right", clicks=3
                )
                self.gateway.drag_mouse.assert_not_called()
        self.on_runtime_error.assert_not_called()

    def test_drag_converts_coordinates_and_ignores_clicks(self) -> None:
        self.executor._execute_mouse_click({
            "x": "100", "y": 200, "to_x": "400", "to_y": 600.9,
            "drag": True, "button": " RIGHT ", "clicks": 3, "drag_speed": "2000",
        })
        self.gateway.drag_mouse.assert_called_once_with(
            x=100, y=200, to_x=400, to_y=600, button="right", duration_sec=0.25
        )
        self.gateway.click_mouse.assert_not_called()
        self.on_runtime_error.assert_not_called()
        self.assertEqual(self.executor.send_guard_count, 0)

    def test_duration_and_clamp_boundaries(self) -> None:
        for to_x, to_y, duration in (
            (300, 400, 0.5), (50, 0, 0.15), (10000, 0, 5.0),
            (150, 0, 0.15), (5000, 0, 5.0), (0, 0, 0.15),
        ):
            with self.subTest(to_x=to_x, to_y=to_y):
                self.gateway.reset_mock()
                self.executor._execute_mouse_click({
                    "x": 0, "y": 0, "to_x": to_x, "to_y": to_y,
                    "drag": True, "drag_speed": 1000,
                })
                self.gateway.drag_mouse.assert_called_once_with(
                    x=0, y=0, to_x=to_x, to_y=to_y, button="left", duration_sec=duration
                )
                self.gateway.click_mouse.assert_not_called()
        self.on_runtime_error.assert_not_called()

    def test_missing_or_invalid_speed_uses_default(self) -> None:
        for extra in ({}, *({"drag_speed": value} for value in ("", "abc", 0, -1, None, float("nan"), "nan"))):
            with self.subTest(extra=extra):
                self.gateway.reset_mock()
                self.executor._execute_mouse_click({
                    "x": 0, "y": 0, "to_x": 300, "to_y": 400, "drag": True, **extra,
                })
                self.gateway.drag_mouse.assert_called_once_with(
                    x=0, y=0, to_x=300, to_y=400, button="left", duration_sec=0.5
                )
                self.gateway.click_mouse.assert_not_called()
        self.on_runtime_error.assert_not_called()

    def test_missing_or_invalid_destination_sends_nothing(self) -> None:
        for destination in (
            {}, {"to_x": 300}, {"to_y": 400},
            {"to_x": "abc", "to_y": 400}, {"to_x": 300, "to_y": ""},
            {"to_x": None, "to_y": 400},
        ):
            with self.subTest(destination=destination):
                self.on_runtime_error.reset_mock()
                self.executor._execute_mouse_click({
                    "x": 0, "y": 0, "drag": True, **destination,
                })
                self.on_runtime_error.assert_called_once_with(
                    "送信エラー",
                    "mouse_click の to_x/to_y が不正です（ドラッグの離す位置を整数で指定してください）。",
                )
                self.gateway.drag_mouse.assert_not_called()
                self.gateway.click_mouse.assert_not_called()

    def test_invalid_start_sends_nothing(self) -> None:
        self.executor._execute_mouse_click({
            "x": "bad", "y": 0, "to_x": 300, "to_y": 400, "drag": True,
        })
        self.on_runtime_error.assert_called_once_with(
            "送信エラー", "mouse_click の x/y が不正です（整数で指定してください）。"
        )
        self.gateway.drag_mouse.assert_not_called()
        self.gateway.click_mouse.assert_not_called()

    def test_drag_failure_is_reported(self) -> None:
        self.gateway.drag_mouse.side_effect = RuntimeError("drag failed")
        self.executor._execute_mouse_click({
            "x": 0, "y": 0, "to_x": 300, "to_y": 400, "drag": True,
        })
        self.gateway.drag_mouse.assert_called_once_with(
            x=0, y=0, to_x=300, to_y=400, button="left", duration_sec=0.5
        )
        self.gateway.click_mouse.assert_not_called()
        self.on_runtime_error.assert_called_once_with(
            "送信エラー", "mouse_click の実行に失敗しました。\nRuntimeError: drag failed"
        )
