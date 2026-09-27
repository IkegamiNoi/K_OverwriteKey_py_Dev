from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor
from keyseq.application.file_line_loader import FileLineLoader


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

    def _executor(self, *, resolve_path=..., get_counter=..., file_line_loader=None) -> ActionExecutor:
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
            file_line_loader=file_line_loader,
        )

    def _async_executor(self, *, get_counter=None, clock=None):
        workers = []
        loader_options = {"start_worker": workers.append}
        if clock is not None:
            loader_options["clock"] = clock
        loader = FileLineLoader(**loader_options)
        executor = self._executor(
            get_counter=self.get_counter if get_counter is None else get_counter,
            file_line_loader=loader,
        )
        return executor, workers, loader

    def test_begin_and_poll_load_then_send_once(self) -> None:
        executor, workers, _loader = self._async_executor()
        action = {"type": "file_line", "path": str(self.path), "counter": "rows"}
        handle = executor.begin_file_line(action)
        self.assertIsNotNone(handle)
        self.assertIsNone(executor.poll_file_line(handle))
        workers.pop()()
        self.assertIs(executor.poll_file_line(handle), True)
        self.gateway.write_text.assert_called_once_with("first")

    def test_async_empty_line_and_empty_out_of_range_do_not_send(self) -> None:
        self.path.write_text("\nsecond", encoding="utf-8")
        executor, workers, _loader = self._async_executor()
        handle = executor.begin_file_line(
            {"type": "file_line", "path": str(self.path), "counter": "rows"}
        )
        workers.pop()()
        self.assertIs(executor.poll_file_line(handle), True)
        self.get_counter.return_value = 3
        handle = executor.begin_file_line({
            "type": "file_line", "path": str(self.path), "counter": "rows",
            "out_of_range": "empty",
        })
        workers.pop()()
        self.assertIs(executor.poll_file_line(handle), True)
        self.gateway.write_text.assert_not_called()

    def test_async_missing_file_and_range_errors_notify_and_return_false(self) -> None:
        executor, workers, _loader = self._async_executor()
        missing = {"type": "file_line", "path": "missing.txt", "counter": "rows", "label": "x"}
        handle = executor.begin_file_line(missing)
        workers.pop()()
        self.assertIs(executor.poll_file_line(handle), False)
        self.assertIn("file_line 実行エラー（種類: file_line / 値:", self.on_action_error.call_args.args[1])
        self.assertIn("/ ラベル: x", self.on_action_error.call_args.args[1])

        self.on_action_error.reset_mock()
        self.get_counter.return_value = 9
        handle = executor.begin_file_line(
            {"type": "file_line", "path": str(self.path), "counter": "rows"}
        )
        workers.pop()()
        self.assertIs(executor.poll_file_line(handle), False)
        self.assertIn("行番号が範囲外です", self.on_action_error.call_args.args[1])

    def test_begin_validation_errors_and_missing_loader_notify(self) -> None:
        cases = [
            (self.executor, {"type": "file_line", "path": str(self.path), "counter": " "}, "カウンター名が空です"),
            (self._executor(resolve_path=None), {"type": "file_line", "counter": "rows"}, "ファイルパス解決コールバックが未設定です"),
            (self._executor(get_counter=None), {"type": "file_line", "counter": "rows"}, "カウンター取得コールバックが未設定です"),
            (self._executor(file_line_loader=None), {"type": "file_line", "counter": "rows"}, "ファイル読込の仕組みが未設定です"),
        ]
        for executor, action, message in cases:
            with self.subTest(message=message):
                self.on_action_error.reset_mock()
                self.assertIsNone(executor.begin_file_line(action))
                self.assertIn(message, self.on_action_error.call_args.args[1])

    def test_begin_uses_counter_value_captured_at_start(self) -> None:
        self.get_counter.return_value = 1
        executor, workers, _loader = self._async_executor()
        handle = executor.begin_file_line(
            {"type": "file_line", "path": str(self.path), "counter": "rows"}
        )
        self.get_counter.return_value = 2
        workers.pop()()
        self.assertIs(executor.poll_file_line(handle), True)
        self.gateway.write_text.assert_called_once_with("first")

    def test_begin_rejects_previous_timed_out_load(self) -> None:
        now = [0.0]
        executor, workers, _loader = self._async_executor(clock=lambda: now[0])
        action = {"type": "file_line", "path": str(self.path), "counter": "rows"}
        handle = executor.begin_file_line(action)
        now[0] = 5.0
        self.assertIs(executor.poll_file_line(handle), False)
        self.on_action_error.reset_mock()
        self.assertIsNone(executor.begin_file_line(action))
        self.assertIn("前回のファイル読込が終わっていません", self.on_action_error.call_args.args[1])
        self.assertTrue(workers)

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
