from __future__ import annotations

import unittest
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor
from keyseq.shared.i18n import fix_language

fix_language("ja")


class ActionExecutorCounterTextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = Mock()
        self.on_action_error = Mock()
        self.get_counter = Mock(return_value=5)
        self.executor = self._executor()

    def _executor(self, *, get_counter=...):
        return ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=Mock(return_value=("", "ctrl+c")),
            on_action_error=self.on_action_error,
            on_runtime_error=Mock(), on_stop_hook=Mock(), on_toggle_mode=Mock(),
            on_select_keymap=Mock(), on_trigger=Mock(),
            get_counter=self.get_counter if get_counter is ... else get_counter,
        )

    def test_counter_values_are_sent_as_decimal_text(self) -> None:
        for value, expected in ((5, "5"), (-3, "-3"), (0, "0")):
            with self.subTest(value=value):
                self.get_counter.return_value = value
                self.assertIs(self.executor.execute({"type": "counter_text", "counter": " n "}), True)
                self.gateway.write_text.assert_called_with(expected)
        self.get_counter.assert_called_with("n")

    def test_empty_and_invalid_names_notify_with_value_copy(self) -> None:
        for counter in ("", "  ", 3):
            with self.subTest(counter=counter):
                self.on_action_error.reset_mock()
                action = {"type": "counter_text", "counter": counter}
                self.assertIs(self.executor.execute(action), False)
                notified, message = self.on_action_error.call_args.args
                self.assertEqual(notified["value"], counter.strip() if isinstance(counter, str) else "")
                self.assertIn("カウンター名が空です", message)
        self.gateway.write_text.assert_not_called()

    def test_label_is_included_in_empty_name_notification(self) -> None:
        self.executor.execute({"type": "counter_text", "counter": " ", "label": " 数値 "})
        self.assertIn("ラベル: 数値", self.on_action_error.call_args.args[1])

    def test_missing_callback_notifies_and_returns_false(self) -> None:
        executor = self._executor(get_counter=None)
        self.assertIs(executor.execute({"type": "counter_text", "counter": "n"}), False)
        self.assertIn("カウンター取得コールバックが未設定です", self.on_action_error.call_args.args[1])

    def test_send_failure_notifies_and_returns_false(self) -> None:
        self.gateway.write_text.side_effect = RuntimeError("offline")
        self.assertIs(self.executor.execute({"type": "counter_text", "counter": "n"}), False)
        self.assertIn("textの送信に失敗しました", self.on_action_error.call_args.args[1])

    def test_type_is_trimmed_and_case_insensitive(self) -> None:
        self.assertIs(self.executor.execute({"type": " COUNTER_TEXT ", "counter": "n"}), True)
        self.gateway.write_text.assert_called_once_with("5")


if __name__ == "__main__":
    unittest.main()
