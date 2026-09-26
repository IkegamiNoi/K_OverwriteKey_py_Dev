from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor


class ActionExecutorFileLineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "lines.txt"
        self.path.write_text("first\nsecond\n", encoding="utf-8")
        self.gateway = Mock()
        self.on_action_error = Mock()
        self.resolve_path = Mock(side_effect=lambda path: path)
        self.get_counter = Mock(return_value=1)
        self.executor = self._executor()

    def _executor(self, *, resolve_path=..., get_counter=...) -> ActionExecutor:
        return ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=Mock(return_value=("", "ctrl+c")),
            on_action_error=self.on_action_error,
            on_runtime_error=Mock(),
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
            resolve_file_line_path=self.resolve_path if resolve_path is ... else resolve_path,
            get_counter=self.get_counter if get_counter is ... else get_counter,
        )

    def test_success_writes_once_and_releases_send_guard(self) -> None:
        action = {"type": "file_line", "path": str(self.path), "counter": "rows"}
        self.assertIs(self.executor.execute(action), True)
        self.gateway.write_text.assert_called_once_with("first")
        self.assertEqual(self.executor.send_guard_count, 0)
        self.get_counter.assert_called_once_with("rows")
        self.on_action_error.assert_not_called()

    def test_empty_line_and_empty_out_of_range_do_not_send(self) -> None:
        self.path.write_text("\nsecond", encoding="utf-8")
        self.get_counter.return_value = 1
        self.assertIs(self.executor.execute({"type": "file_line", "path": str(self.path), "counter": "rows"}), True)
        self.get_counter.return_value = 3
        action = {
            "type": "file_line", "path": str(self.path), "counter": "rows", "out_of_range": "empty"
        }
        self.assertIs(self.executor.execute(action), True)
        self.gateway.write_text.assert_not_called()

    def test_errors_notify_and_return_false(self) -> None:
        action = {"type": "file_line", "path": "missing.txt", "counter": "rows", "label": "sample"}
        self.assertIs(self.executor.execute(action), False)
        self.on_action_error.assert_called_once()
        self.assertIs(self.on_action_error.call_args.args[0], action)
        self.assertIn("sample", self.on_action_error.call_args.args[1])

    def test_empty_counter_name_is_an_error(self) -> None:
        action = {"type": "file_line", "path": str(self.path), "counter": "  "}
        self.assertIs(self.executor.execute(action), False)
        self.on_action_error.assert_called_once()
        self.get_counter.assert_not_called()

    def test_missing_callbacks_are_errors(self) -> None:
        for resolve_path, get_counter in ((None, self.get_counter), (self.resolve_path, None)):
            with self.subTest(resolve_path=resolve_path, get_counter=get_counter):
                self.on_action_error.reset_mock()
                executor = self._executor(resolve_path=resolve_path, get_counter=get_counter)
                result = executor.execute(
                    {"type": "file_line", "path": str(self.path), "counter": "rows"}
                )
                self.assertIs(result, False)
                self.on_action_error.assert_called_once()
        self.gateway.write_text.assert_not_called()

    def test_existing_action_types_keep_their_behavior(self) -> None:
        text_executor = self.executor
        self.assertIs(text_executor.execute({"type": "text", "value": "hello"}), True)
        self.gateway.write_text.assert_called_once_with("hello")
        self.assertIs(text_executor.execute({"type": "hotkey", "value": "ctrl+c"}), True)
        self.gateway.send_hotkey.assert_called_once_with("ctrl+c")
        self.assertIs(text_executor.execute({"type": "mouse_click", "x": 4, "y": 5}), True)
        self.gateway.click_mouse.assert_called_once_with(x=4, y=5, button="left", clicks=1)
        self.on_action_error.reset_mock()
        self.assertIs(text_executor.execute({"type": "unknown"}), False)
        self.on_action_error.assert_called_once()
        self.assertIn("hotkey / text / mouse_click", self.on_action_error.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
