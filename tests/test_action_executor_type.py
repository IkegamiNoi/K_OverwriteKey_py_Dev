from __future__ import annotations

import unittest
from copy import deepcopy
from functools import partial
from unittest.mock import Mock, call, patch

from keyseq.application.action_executor import ActionExecutor
from keyseq.domain.config import normalize_actions
from keyseq.presentation.controllers import hook_controller


class ActionExecutorTypeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = Mock()
        self.validate_hotkey = Mock(return_value=("", "ctrl+c"))
        self.on_action_error = Mock()
        self.on_runtime_error = Mock()
        self.executor = ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=self.validate_hotkey,
            on_action_error=self.on_action_error,
            on_runtime_error=self.on_runtime_error,
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
        )

    def test_invalid_types_do_not_send_and_notify_once(self) -> None:
        actions = [
            {"value": "alt+f4"},
            *(
                {"type": raw, "value": "alt+f4"}
                for raw in ("", "   ", "hotky", ["hotkey"], 1, None)
            ),
            normalize_actions([{"type": ["hotkey"], "value": "alt+f4"}])[0],
        ]
        for action in actions:
            with self.subTest(action=action):
                self.on_action_error.reset_mock()
                with patch.object(self.executor, "_enter_send_guard") as enter_guard:
                    self.assertIs(self.executor.execute(action), False)
                    enter_guard.assert_not_called()
                self.assertEqual(self.gateway.method_calls, [])
                self.assertEqual(self.executor.send_guard_count, 0)
                self.on_action_error.assert_called_once()
                self.on_runtime_error.assert_not_called()
                self.validate_hotkey.assert_not_called()

    def test_invalid_type_error_message_matches_exactly(self) -> None:
        cases = [
            (
                {"type": "hotky", "label": " 保存 "},
                "種類が不正です（hotkey / text / mouse_click のいずれか）。種類: hotky / ラベル: 保存",
            ),
            ({}, "種類が不正です（hotkey / text / mouse_click のいずれか）。種類: (なし)"),
            *(
                (
                    {"type": "hotky", "label": label},
                    "種類が不正です（hotkey / text / mouse_click のいずれか）。種類: hotky",
                )
                for label in (1, ["保存"], None, "", "   ")
            ),
            (
                {"type": " HoTkY ", "label": " 保存 "},
                "種類が不正です（hotkey / text / mouse_click のいずれか）。種類: HoTkY / ラベル: 保存",
            ),
        ]
        for action, expected in cases:
            with self.subTest(action=action):
                self.on_action_error.reset_mock()
                self.assertIs(self.executor.execute(action), False)
                self.on_action_error.assert_called_once()
                self.assertEqual(self.on_action_error.call_args.args[1], expected)

    def test_notification_uses_shallow_copy_without_mutating_action(self) -> None:
        for raw, expected_type in (
            (["hotkey"], ""), (1, ""), (None, ""), (" HoTkY ", "HoTkY"),
        ):
            with self.subTest(raw=raw):
                self.on_action_error.reset_mock()
                action = {"type": raw, "value": "alt+f4", "metadata": {"keep": True}}
                original = deepcopy(action)
                self.assertIs(self.executor.execute(action), False)
                self.on_action_error.assert_called_once()
                notified_action = self.on_action_error.call_args.args[0]
                self.assertIsNot(notified_action, action)
                self.assertIsInstance(notified_action["type"], str)
                self.assertEqual(notified_action["type"], expected_type)
                self.assertEqual(notified_action, {**action, "type": expected_type})
                self.assertIs(notified_action["metadata"], action["metadata"])
                self.assertEqual(action, original)
                self.assertIs(action["type"], raw)

    def test_non_string_type_can_reach_real_error_dialog(self) -> None:
        controller = hook_controller.HookController(Mock())
        self.on_action_error.side_effect = partial(controller.show_action_error, "f8")
        with patch.object(hook_controller.messagebox, "showerror") as showerror:
            self.assertIs(
                self.executor.execute({"type": ["hotkey"], "value": "alt+f4"}),
                False,
            )
            showerror.assert_called_once()
        self.on_action_error.assert_called_once()
        self.assertEqual(self.gateway.method_calls, [])
        self.on_runtime_error.assert_not_called()

    def test_known_types_keep_existing_dispatch_and_return_true(self) -> None:
        cases = [
            ({"type": "hotkey", "value": "ctrl+c"}, call.send_hotkey("ctrl+c")),
            ({"type": " TEXT ", "value": "hello"}, call.write_text("hello")),
            (
                {"type": "Mouse_Click", "x": "100", "y": 200},
                call.click_mouse(x=100, y=200, button="left", clicks=1),
            ),
        ]
        for action, expected_call in cases:
            with self.subTest(action=action):
                self.gateway.reset_mock()
                self.validate_hotkey.reset_mock()
                self.assertIs(self.executor.execute(action), True)
                self.assertEqual(self.gateway.method_calls, [expected_call])
                if action["type"] == "hotkey":
                    self.validate_hotkey.assert_called_once_with("ctrl+c")
                else:
                    self.validate_hotkey.assert_not_called()
                self.assertEqual(self.executor.send_guard_count, 0)
                self.on_action_error.assert_not_called()
                self.on_runtime_error.assert_not_called()

    def test_known_type_internal_errors_still_return_true(self) -> None:
        with self.subTest(error="hotkey validation"):
            self.validate_hotkey.return_value = ("エラー", "")
            action = {"type": "hotkey", "value": "bad"}
            self.assertIs(self.executor.execute(action), True)
            self.on_action_error.assert_called_once_with(action, "エラー")
            self.on_runtime_error.assert_not_called()
            self.assertEqual(self.gateway.method_calls, [])

        self.on_action_error.reset_mock()
        with self.subTest(error="invalid mouse x"):
            self.assertIs(
                self.executor.execute({"type": "mouse_click", "x": "bad", "y": 200}),
                True,
            )
            self.on_runtime_error.assert_called_once_with(
                "送信エラー", "mouse_click の x/y が不正です（整数で指定してください）。"
            )
            self.on_action_error.assert_not_called()
            self.assertEqual(self.gateway.method_calls, [])
        self.assertEqual(self.executor.send_guard_count, 0)


if __name__ == "__main__":
    unittest.main()
