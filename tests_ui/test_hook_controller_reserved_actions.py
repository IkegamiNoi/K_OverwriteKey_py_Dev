from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from keyseq.application.input_router import (
    SelectKeymapAction,
    SendKeyAction,
    StopHookAction,
    ToggleModeAction,
    TriggerAction,
)
from keyseq.presentation.controllers.hook_controller import HookController


class HookControllerReservedActionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.callbacks = []
        self.execute_router_action = Mock()
        self.app = SimpleNamespace(
            layout=SimpleNamespace(
                resolve_key_name_from_scan_code=Mock(return_value="a"),
                should_debug_special_key_event=Mock(return_value=False),
            ),
            input_router=SimpleNamespace(
                handle=Mock(return_value=SimpleNamespace(actions=(), shadowed=(), accept=True)),
            ),
            action_executor=SimpleNamespace(
                execute_router_action=self.execute_router_action,
            ),
            after=lambda _delay, callback: self.callbacks.append(callback),
        )
        self.controller = HookController.__new__(HookController)
        self.controller._app = self.app
        self.controller.hook_active = True
        self.controller.custom_input_enabled = True

    def queue_action(self, action) -> None:
        self.app.input_router.handle.return_value = SimpleNamespace(
            actions=(action,), shadowed=(), accept=True,
        )
        self.controller.on_input_event(SimpleNamespace(scan_code=30))
        self.assertEqual(len(self.callbacks), 1)

    def test_reserved_actions_are_skipped_when_hook_stops_after_scheduling(self) -> None:
        for action in (TriggerAction("a"), SendKeyAction("a", "b")):
            with self.subTest(action=action):
                self.callbacks.clear()
                self.execute_router_action.reset_mock()
                self.controller.hook_active = True
                self.queue_action(action)
                self.controller.hook_active = False

                self.callbacks.pop()()

                self.execute_router_action.assert_not_called()

    def test_reserved_actions_are_skipped_while_custom_input_is_paused(self) -> None:
        for action in (TriggerAction("a"), SendKeyAction("a", "b")):
            with self.subTest(action=action):
                self.callbacks.clear()
                self.execute_router_action.reset_mock()
                self.controller.custom_input_enabled = True
                self.queue_action(action)
                self.controller.custom_input_enabled = False

                self.callbacks.pop()()

                self.execute_router_action.assert_not_called()

    def test_control_actions_still_run_after_hook_stops_or_custom_input_pauses(self) -> None:
        actions = (StopHookAction(), ToggleModeAction(), SelectKeymapAction("target"))
        for action in actions:
            with self.subTest(action=action):
                self.callbacks.clear()
                self.execute_router_action.reset_mock()
                self.controller.hook_active = False
                self.controller.custom_input_enabled = False
                self.queue_action(action)

                self.callbacks.pop()()

                self.execute_router_action.assert_called_once_with(action, shadowed=())


if __name__ == "__main__":
    unittest.main()
