from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call

from keyseq.application.make_only_keys import MakeOnlyResult

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
            make_only_keys=SimpleNamespace(handle=Mock(return_value=None), generation=0),
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

    def test_make_only_event_returns_filter_accept_and_reserves_all_routes(self) -> None:
        actions = (SendKeyAction("muhenkan", "a"), StopHookAction())
        routes = tuple(
            SimpleNamespace(actions=(action,), shadowed=(index,))
            for index, action in enumerate(actions)
        )
        self.app.make_only_keys.handle.return_value = MakeOnlyResult(False, routes, 0)
        event = SimpleNamespace(scan_code=241, event_type="down")
        self.app.layout.should_debug_special_key_event.return_value = True
        self.app.layout.debug_special_key_event = Mock()
        order = []
        self.app.layout.debug_special_key_event.side_effect = lambda *_: order.append("debug")
        self.app.make_only_keys.handle.side_effect = lambda _event: (
            order.append("filter") or MakeOnlyResult(False, routes, 0)
        )

        self.assertFalse(self.controller.on_input_event(event))

        self.assertEqual(order, ["debug", "filter"])
        self.app.make_only_keys.handle.assert_called_once_with(event)
        self.app.layout.debug_special_key_event.assert_called_once_with(event, "a")
        self.app.input_router.handle.assert_not_called()
        self.assertEqual(len(self.callbacks), 2)
        for callback in self.callbacks:
            callback()
        self.assertEqual(
            self.execute_router_action.call_args_list,
            [call(action, shadowed=(index,)) for index, action in enumerate(actions)],
        )

    def test_other_keys_use_existing_router_path_and_accept(self) -> None:
        action = StopHookAction()
        event = SimpleNamespace(scan_code=30, event_type="down")
        self.app.input_router.handle.return_value = SimpleNamespace(
            actions=(action,), shadowed=(), accept=False,
        )
        self.assertFalse(self.controller.on_input_event(event))
        self.app.make_only_keys.handle.assert_called_once_with(event)
        self.app.input_router.handle.assert_called_once_with(event)
        self.callbacks.pop()()
        self.execute_router_action.assert_called_once_with(action, shadowed=())

    def test_stale_generation_is_discarded_at_ui_execution(self) -> None:
        route = SimpleNamespace(actions=(StopHookAction(),), shadowed=())
        for source in ("hook", "timer"):
            with self.subTest(source=source):
                self.app.make_only_keys.generation = 0
                if source == "hook":
                    self.app.make_only_keys.handle.return_value = MakeOnlyResult(
                        False, (route,), 0,
                    )
                    self.controller.on_input_event(SimpleNamespace(scan_code=241))
                else:
                    self.controller.schedule_make_only_routes((route,), 0)
                self.assertEqual(len(self.callbacks), 1)
                self.app.make_only_keys.generation = 1
                self.callbacks.pop()()
                self.execute_router_action.assert_not_called()

    def test_current_timer_generation_executes(self) -> None:
        action = SendKeyAction("muhenkan", "a")
        route = SimpleNamespace(actions=(action,), shadowed=())
        self.controller.schedule_make_only_routes((route,), 0)
        self.callbacks.pop()()
        self.execute_router_action.assert_called_once_with(action, shadowed=())

    def test_timer_after_failure_is_logged_and_discarded(self) -> None:
        route = SimpleNamespace(actions=(StopHookAction(),), shadowed=())
        self.app.after = Mock(side_effect=RuntimeError("main loop has ended"))
        with self.assertLogs("keyseq.presentation.controllers.hook_controller", level="ERROR"):
            self.controller.schedule_make_only_routes((route,), 0)
        self.execute_router_action.assert_not_called()

    def test_start_and_stop_clear_filter_immediately_after_key_state(self) -> None:
        trace = Mock()
        self.app.key_state_manager = SimpleNamespace(clear=trace.key_state_clear)
        self.app.make_only_keys.clear = trace.filter_clear
        self.app.hook_coordinator = SimpleNamespace(start=trace.start, stop=trace.stop)
        self.app.sequence_runner = Mock()
        self.app.held_inputs = SimpleNamespace(release_all=Mock(return_value=[]))
        self.app.layout.refresh_keyboard_window = Mock()
        self.app.trigger_panel = Mock()
        self.app.data = {"triggers": []}
        self.controller = HookController(self.app)

        self.controller.start_hook()

        self.assertEqual(trace.mock_calls[:2], [call.key_state_clear(), call.filter_clear()])
        self.assertEqual(trace.mock_calls[2][0], "start")
        trace.reset_mock()
        self.controller.stop_hook()
        self.assertEqual(
            trace.mock_calls, [call.stop(), call.key_state_clear(), call.filter_clear()],
        )

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
