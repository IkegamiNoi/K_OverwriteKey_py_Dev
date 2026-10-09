from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor


class FakeGateway:
    """Record input commands without sending real keyboard or mouse events."""

    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.invalid_keys: set[str] = set()
        self.fail_press: set[str] = set()
        self.fail_press_once: set[str] = set()
        self.fail_release_once: set[str] = set()
        self.fail_mouse_down: set[str] = set()
        self.fail_text = False
        self.guard_probe = None

    def validate_key_name(self, key: str) -> None:
        self.events.append(("validate", key))
        if key in self.invalid_keys:
            raise ValueError(f"invalid key: {key}")

    def key_identity(self, key: str) -> tuple[int, bool]:
        scan_code = {"shift": 42, "ctrl": 29, "left ctrl": 29, "right ctrl": 29}.get(key, 30)
        return scan_code, key == "right ctrl"

    def press_key(self, key: str) -> None:
        self.events.append(("key_down", key))
        if self.guard_probe is not None:
            self.events.append(("guard_count", self.guard_probe()))
        if key in self.fail_press_once:
            self.fail_press_once.remove(key)
            raise RuntimeError(f"press failed once: {key}")
        if key in self.fail_press:
            raise RuntimeError(f"press failed: {key}")

    def release_key(self, key: str) -> None:
        self.events.append(("key_up", key))
        if self.guard_probe is not None:
            self.events.append(("guard_count", self.guard_probe()))
        if key in self.fail_release_once:
            self.fail_release_once.remove(key)
            raise RuntimeError(f"release failed once: {key}")

    def mouse_down(self, button: str, x: int | None = None, y: int | None = None) -> None:
        self.events.append(("mouse_down", button, x, y))
        if button in self.fail_mouse_down:
            raise RuntimeError(f"mouse down failed: {button}")

    def mouse_up(self, button: str, x: int | None = None, y: int | None = None) -> None:
        self.events.append(("mouse_up", button, x, y))

    def write_text(self, text: str) -> None:
        self.events.append(("text", text))
        if self.fail_text:
            raise RuntimeError("text failed")

    def send_hotkey(self, _hotkey: str) -> None:
        raise AssertionError("unexpected hotkey send")


class FakeLoader:
    def request(self, path: str, encoding: str) -> object:
        return (path, encoding)

    def poll(self, _request: object) -> SimpleNamespace:
        return SimpleNamespace(status="done", lines=["loaded text"], error=None)


class ActionExecutorKeyHoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = FakeGateway()
        self.events = self.gateway.events
        self.on_action_error = Mock(side_effect=lambda *_args: self.events.append(("action_error",)))
        self.on_runtime_error = Mock(side_effect=lambda *_args: self.events.append(("runtime_error",)))
        self.executor = self._executor()

    def _executor(self, *, loader=None, held_inputs=None) -> ActionExecutor:
        return ActionExecutor(
            input_gateway=self.gateway,
            validate_hotkey=Mock(return_value=("", "ctrl+c")),
            on_action_error=self.on_action_error,
            on_runtime_error=self.on_runtime_error,
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
            resolve_file_line_path=lambda path: path,
            get_counter=lambda _name: 1,
            file_line_loader=loader,
            held_inputs=held_inputs,
        )

    def _press_shift(self, owner: str = "f8") -> None:
        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "value": "shift"}, owner=owner
            ),
            True,
        )

    def test_key_hold_sends_key_down_and_up(self) -> None:
        down = {"type": "key_hold", "edge": "down", "value": "shift"}
        up = {"type": "key_hold", "edge": "up", "value": "shift"}

        self.assertIs(self.executor.execute(down, owner="f8"), True)
        self.assertEqual(self.events[-1], ("key_down", "shift"))
        self.assertEqual(self.executor.held_inputs.display_names, ("shift",))
        self.assertIs(self.executor.execute(up, owner="f8"), True)
        self.assertEqual(self.events[-1], ("key_up", "shift"))
        self.assertEqual(self.executor.held_inputs.display_names, ())

    def test_key_hold_sends_mouse_down_and_up_with_positions(self) -> None:
        down = {"type": "key_hold", "edge": "down", "button": "left", "x": 12, "y": 34}
        up = {"type": "key_hold", "edge": "up", "button": "left", "x": 56, "y": 78}

        self.assertIs(self.executor.execute(down, owner="f8"), True)
        self.assertEqual(self.events[-1], ("mouse_down", "left", 12, 34))
        self.assertEqual(self.executor.held_inputs.display_names, ("マウス左",))
        self.assertIs(self.executor.execute(up, owner="f8"), True)
        self.assertEqual(self.events[-1], ("mouse_up", "left", 56, 78))
        self.assertEqual(self.executor.held_inputs.display_names, ())

    def test_parse_error_releases_owner_before_notification_and_returns_false(self) -> None:
        self._press_shift()
        self.events.clear()
        action = {"type": "key_hold", "edge": "sideways", "value": "a"}

        self.assertIs(self.executor.execute(action, owner="f8"), False)

        self.assertEqual(self.events, [("key_up", "shift"), ("action_error",)])
        self.on_action_error.assert_called_once()

    def test_key_validation_error_releases_owner_before_notification(self) -> None:
        self._press_shift()
        self.events.clear()
        self.gateway.invalid_keys.add("no such key")
        action = {"type": "key_hold", "edge": "down", "value": "no such key"}

        self.assertIs(self.executor.execute(action, owner="f8"), False)

        self.assertEqual(
            self.events,
            [("validate", "no such key"), ("key_up", "shift"), ("action_error",)],
        )
        self.on_action_error.assert_called_once()

    def test_send_error_compensates_then_releases_owner_before_notification(self) -> None:
        self._press_shift()
        self.events.clear()
        self.gateway.fail_press.add("ctrl")

        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "value": "ctrl"}, owner="f8"
            ),
            False,
        )

        self.assertEqual(
            self.events,
            [
                ("validate", "ctrl"),
                ("key_down", "ctrl"),
                ("key_up", "ctrl"),
                ("key_up", "shift"),
                ("action_error",),
            ],
        )
        self.on_action_error.assert_called_once()

    def test_mouse_down_error_compensates_then_releases_owner_before_notification(self) -> None:
        self._press_shift()
        self.events.clear()
        self.gateway.fail_mouse_down.add("left")

        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "button": "left", "x": 10, "y": 20},
                owner="f8",
            ),
            False,
        )

        self.assertEqual(
            self.events,
            [
                ("mouse_down", "left", 10, 20),
                ("mouse_up", "left", None, None),
                ("key_up", "shift"),
                ("action_error",),
            ],
        )
        self.on_action_error.assert_called_once()

    def test_explicit_key_up_error_is_retried_by_owner_release_before_notification(self) -> None:
        self._press_shift()
        self.events.clear()
        self.gateway.fail_release_once.add("shift")

        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "up", "value": "shift"}, owner="f8"
            ),
            False,
        )

        self.assertEqual(
            self.events,
            [
                ("validate", "shift"),
                ("key_up", "shift"),
                ("key_up", "shift"),
                ("action_error",),
            ],
        )
        self.assertEqual(self.executor.held_inputs.display_names, ())

    def test_omitted_owner_is_recorded_and_released_as_empty_owner(self) -> None:
        self.assertIs(
            self.executor.execute({"type": "key_hold", "edge": "down", "value": "shift"}),
            True,
        )
        self.events.clear()

        self.assertIs(
            self.executor.execute({"type": "key_hold", "edge": "bad", "value": "a"}), False
        )

        self.assertEqual(self.events, [("key_up", "shift"), ("action_error",)])

    def test_injected_held_inputs_uses_executor_send_guard(self) -> None:
        from keyseq.application.held_inputs import HeldInputs

        held_inputs = HeldInputs(self.gateway)
        executor = self._executor(held_inputs=held_inputs)
        self.gateway.guard_probe = lambda: executor.send_guard_count

        self.assertIs(
            executor.execute({"type": "key_hold", "edge": "down", "value": "shift"}), True
        )
        self.assertEqual(self.events[-2:], [("key_down", "shift"), ("guard_count", 1)])
        self.assertEqual(executor.send_guard_count, 0)
        self.events.clear()
        self.assertIs(
            executor.execute({"type": "key_hold", "edge": "up", "value": "shift"}), True
        )
        self.assertEqual(self.events[-2:], [("key_up", "shift"), ("guard_count", 1)])
        self.assertEqual(executor.send_guard_count, 0)

    def test_text_temporarily_releases_and_restores_held_keyboard_key(self) -> None:
        self._press_shift()
        self.events.clear()

        self.assertIs(
            self.executor.execute({"type": "text", "value": "hello"}, owner="f8"), True
        )

        self.assertEqual(
            self.events,
            [("key_up", "shift"), ("text", "hello"), ("key_down", "shift")],
        )
        self.assertEqual(self.executor.held_inputs.display_names, ("shift",))
        self.on_action_error.assert_not_called()

    def test_text_suspends_all_owners_keyboard_keys_and_keeps_mouse_held(self) -> None:
        self._press_shift("f8")
        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "value": "ctrl"}, owner="f9"
            ),
            True,
        )
        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "button": "left"}, owner="f10"
            ),
            True,
        )
        self.events.clear()

        self.assertIs(self.executor.execute({"type": "text", "value": "hello"}, owner="f8"), True)

        self.assertEqual(
            self.events,
            [
                ("key_up", "shift"),
                ("key_up", "ctrl"),
                ("text", "hello"),
                ("key_down", "shift"),
                ("key_down", "ctrl"),
            ],
        )
        self.assertEqual(
            self.executor.held_inputs.display_names, ("shift", "ctrl", "マウス左")
        )

    def test_text_error_does_not_restore_and_releases_owner_before_notification(self) -> None:
        self._press_shift()
        self.events.clear()
        self.gateway.fail_text = True

        self.assertIs(
            self.executor.execute({"type": "text", "value": "hello"}, owner="f8"), False
        )

        self.assertEqual(
            self.events,
            [("key_up", "shift"), ("text", "hello"), ("key_up", "shift"), ("action_error",)],
        )
        self.assertEqual(self.executor.held_inputs.display_names, ())
        self.on_action_error.assert_called_once()

    def test_text_error_releases_other_owners_keyboard_keys_and_keeps_mouse(self) -> None:
        self._press_shift("f8")
        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "value": "ctrl"}, owner="f9"
            ),
            True,
        )
        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "button": "left"}, owner="f9"
            ),
            True,
        )
        self.events.clear()
        self.gateway.fail_text = True

        self.assertIs(
            self.executor.execute({"type": "text", "value": "hello"}, owner="f8"), False
        )

        self.assertNotIn(("key_down", "ctrl"), self.events)
        self.assertEqual(self.events[-1], ("action_error",))
        self.assertEqual(self.executor.held_inputs.display_names, ("マウス左",))

    def test_text_resume_error_compensates_failed_press_then_releases_owner_before_notice(self) -> None:
        self._press_shift()
        self.assertIs(
            self.executor.execute(
                {"type": "key_hold", "edge": "down", "value": "ctrl"}, owner="f8"
            ),
            True,
        )
        self.events.clear()
        self.gateway.fail_press_once.add("ctrl")

        self.assertIs(self.executor.execute({"type": "text", "value": "hello"}, owner="f8"), False)

        self.assertEqual(
            self.events,
            [
                ("key_up", "shift"),
                ("key_up", "ctrl"),
                ("text", "hello"),
                ("key_down", "shift"),
                ("key_down", "ctrl"),
                ("key_up", "ctrl"),
                ("key_up", "shift"),
                ("action_error",),
            ],
        )
        self.assertEqual(self.executor.held_inputs.display_names, ())
        self.on_action_error.assert_called_once()

    def test_file_line_temporarily_releases_and_restores_held_key(self) -> None:
        self.executor = self._executor(loader=FakeLoader())
        self._press_shift()
        self.events.clear()
        handle = self.executor.begin_file_line(
            {"type": "file_line", "path": "lines.txt", "counter": "rows"}
        )
        self.assertIsNotNone(handle)

        self.assertIs(self.executor.poll_file_line(handle, owner="f8"), True)

        self.assertEqual(
            self.events,
            [("key_up", "shift"), ("text", "loaded text"), ("key_down", "shift")],
        )
        self.assertEqual(self.executor.held_inputs.display_names, ("shift",))

    def test_file_line_send_error_does_not_restore_and_releases_before_notification(self) -> None:
        self.executor = self._executor(loader=FakeLoader())
        self._press_shift()
        self.events.clear()
        self.gateway.fail_text = True
        handle = self.executor.begin_file_line(
            {"type": "file_line", "path": "lines.txt", "counter": "rows"}
        )
        self.assertIsNotNone(handle)

        self.assertIs(self.executor.poll_file_line(handle, owner="f8"), False)

        self.assertEqual(
            self.events,
            [
                ("key_up", "shift"),
                ("text", "loaded text"),
                ("key_up", "shift"),
                ("action_error",),
            ],
        )
        self.assertEqual(self.executor.held_inputs.display_names, ())
        self.on_action_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
