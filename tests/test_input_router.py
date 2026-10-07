import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.application.action_executor import ActionExecutor
from keyseq.application.key_overlap import analyze_key_overlaps
from keyseq.application.input_router import (
    InputRoute,
    InputRouter,
    SelectKeymapAction,
    SendKeyAction,
    StopHookAction,
    ToggleModeAction,
    TriggerAction,
)
from keyseq.application.key_state_manager import KeyStateManager
from keyseq.application.trigger_service import TriggerService


def make_router(
    *,
    send_guard=0,
    pause=0,
    stop_key="",
    toggle_key="",
    custom_enabled=True,
    switch_target="",
    trigger=None,
    keymap_target="",
    runtime_data=None,
    switching_event=None,
):
    if runtime_data is None:
        runtime_data = {
            "keymaps": [{"id": "km1", "triggers": [], "mappings": {}}],
            "active_keymap_id": "km1",
        }
    return InputRouter(
        key_state_manager=KeyStateManager(),
        get_send_guard_count=lambda: send_guard,
        get_hook_pause_count=lambda: pause,
        get_stop_key=lambda: stop_key,
        get_toggle_key=lambda: toggle_key,
        get_key_overlap_report=lambda: analyze_key_overlaps(runtime_data, stop_key, toggle_key),
        get_custom_input_enabled=lambda: custom_enabled,
        find_keymap_switch_target=lambda key: switch_target(key) if callable(switch_target) else switch_target,
        find_trigger=lambda key: trigger(key) if callable(trigger) else trigger,
        find_keymap_target=lambda key: keymap_target(key) if callable(keymap_target) else keymap_target,
        keymap_switch_in_progress=switching_event,
    )


def down(name):
    return SimpleNamespace(event_type="down", name=name, scan_code=None)


class InputRouterTest(unittest.TestCase):
    def test_send_guard_passes_through(self):
        route = make_router(send_guard=1, stop_key="f12").handle(down("f12"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_pause_passes_through(self):
        route = make_router(pause=1, stop_key="f12").handle(down("f12"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_up_event_ignored(self):
        router = make_router(stop_key="f12")
        route = router.handle(SimpleNamespace(event_type="up", name="f12", scan_code=None))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_stop_key(self):
        route = make_router(stop_key="F12").handle(down("f12"))
        self.assertEqual(route.actions, (StopHookAction(),))
        self.assertFalse(route.accept)

    def test_toggle_key(self):
        route = make_router(toggle_key="f11").handle(down("f11"))
        self.assertEqual(route.actions, (ToggleModeAction(),))
        self.assertFalse(route.accept)

    def test_stop_precedes_toggle_when_runtime_keys_overlap(self):
        route = make_router(stop_key="f12", toggle_key="f12").handle(down("f12"))
        self.assertEqual(route.actions, (StopHookAction(),))

    def test_custom_input_disabled_passes_through(self):
        trigger = {"key": "f1", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        route = make_router(custom_enabled=False, trigger=trigger).handle(down("f1"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_keymap_switch_key(self):
        route = make_router(switch_target="km1").handle(down("1"))
        self.assertEqual(route.actions, (SelectKeymapAction(keymap_id="km1"),))
        self.assertFalse(route.accept)

    def test_trigger_suppress_true(self):
        trigger = {"key": "f1", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        route = make_router(trigger=trigger).handle(down("f1"))
        self.assertEqual(route.actions, (TriggerAction(key="f1"),))
        self.assertFalse(route.accept)

    def test_trigger_suppress_false(self):
        trigger = {"key": "f1", "suppress": False, "actions": [{"type": "text", "value": "x"}]}
        route = make_router(trigger=trigger).handle(down("f1"))
        self.assertEqual(route.actions, (TriggerAction(key="f1"),))
        self.assertTrue(route.accept)

    def test_trigger_without_actions_falls_through_to_keymap(self):
        trigger = {"key": "a", "suppress": True, "actions": []}
        route = make_router(trigger=trigger, keymap_target="b").handle(down("a"))
        self.assertEqual(route.actions, (SendKeyAction(source_key="a", target_key="b"),))
        self.assertFalse(route.accept)

    def test_empty_action_trigger_still_executes_keymap_replacement(self):
        trigger = {"key": "a", "suppress": True, "actions": []}
        route = make_router(trigger=trigger, keymap_target="b").handle(down("a"))
        self.assertEqual(route.actions, (SendKeyAction(source_key="a", target_key="b"),))
        gateway = Mock()
        executor = ActionExecutor(
            input_gateway=gateway,
            validate_hotkey=lambda _hotkey: ("", ""),
            on_action_error=Mock(),
            on_runtime_error=Mock(),
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=Mock(),
        )

        executor.execute_router_action(route.actions[0])

        gateway.press_key.assert_called_once_with("b")
        gateway.release_key.assert_called_once_with("b")

    def test_duplicate_key_uses_first_row_and_empty_first_row_falls_through(self):
        first = {"key": "a", "suppress": True, "actions": []}
        second = {"key": "A", "suppress": True, "actions": [{"type": "text", "value": "lower"}]}
        runtime = {
            "keymaps": [{"id": "km1", "triggers": [first, second], "mappings": {"a": "b"}}],
            "active_keymap_id": "km1",
        }
        router = make_router(
            trigger=lambda key: TriggerService.find_trigger_by_key(runtime, key),
            keymap_target="b",
            runtime_data=runtime,
        )

        route = router.handle(down("a"))

        self.assertEqual(route.actions, (SendKeyAction(source_key="a", target_key="b"),))

    def test_trigger_precedes_keymap_replacement_without_shadow_notice(self):
        trigger = {"key": "a", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        runtime = {
            "keymaps": [{"id": "km1", "triggers": [trigger], "mappings": {"a": "b"}}],
            "active_keymap_id": "km1",
        }
        route = make_router(trigger=trigger, keymap_target="b", runtime_data=runtime).handle(down("a"))
        self.assertEqual(route.actions, (TriggerAction(key="a"),))
        self.assertEqual(route.shadowed, ())

    def test_direct_switch_precedes_replacement_and_trigger(self):
        trigger = {"key": "a", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        runtime = {
            "keymaps": [
                {"id": "km1", "triggers": [trigger], "mappings": {"a": "b"}},
                {"id": "km2", "triggers": [], "mappings": {}},
            ],
            "active_keymap_id": "km1",
            "keymap_switch_keys": {"a": "km2"},
        }
        route = make_router(
            switch_target="km2", trigger=trigger, keymap_target="b", runtime_data=runtime
        ).handle(down("a"))
        self.assertEqual(route.actions, (SelectKeymapAction(keymap_id="km2"),))
        self.assertEqual([(item.kind, item.winner) for item in route.shadowed], [("trigger", "switch")])

    def test_switch_pending_passes_through_other_keys_and_clears_after_execution(self):
        trigger = {"key": "f1", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        scenarios = (("completed", True, False), ("rejected", False, False), ("exception", True, True))
        for name, can_switch, raises in scenarios:
            with self.subTest(name=name):
                switching = threading.Event()
                router = make_router(
                    stop_key="f12",
                    toggle_key="f11",
                    switch_target=lambda key: "km2" if key == "f9" else "",
                    trigger=lambda key: trigger if key == "f1" else None,
                    keymap_target=lambda key: "z" if key == "a" else "",
                    switching_event=switching,
                )
                route = router.handle(down("f9"))
                self.assertEqual(route.actions, (SelectKeymapAction(keymap_id="km2"),))
                self.assertTrue(switching.is_set())
                self.assertEqual(router.handle(down("f1")), InputRoute())
                self.assertEqual(router.handle(down("a")), InputRoute())
                self.assertEqual(router.handle(down("f12")).actions, (StopHookAction(),))
                self.assertEqual(router.handle(down("f11")).actions, (ToggleModeAction(),))

                def select_keymap(_keymap_id):
                    self.assertTrue(switching.is_set())
                    if raises:
                        raise RuntimeError("switch failed")

                executor = ActionExecutor(
                    input_gateway=None,
                    validate_hotkey=lambda _hotkey: ("", ""),
                    on_action_error=lambda _action, _error: None,
                    on_runtime_error=lambda _title, _message: None,
                    on_stop_hook=lambda: None,
                    on_toggle_mode=lambda: None,
                    on_select_keymap=select_keymap,
                    on_trigger=lambda _key, _repeat: None,
                    can_switch_keymap=lambda _keymap_id: can_switch,
                    on_keymap_switch_blocked=lambda: self.assertTrue(switching.is_set()),
                    keymap_switch_in_progress=switching,
                )
                if raises:
                    with self.assertRaises(RuntimeError):
                        executor.execute_router_action(route.actions[0])
                else:
                    executor.execute_router_action(route.actions[0])
                self.assertFalse(switching.is_set())
                # f1 は前の押下を離していないため repeat の印が付く（ここでは素通しの種類とキーだけを見る）
                self.assertEqual(
                    [(type(action), action.key) for action in router.handle(down("f1")).actions],
                    [(TriggerAction, "f1")],
                )
                self.assertEqual(
                    router.handle(down("a")).actions,
                    (SendKeyAction(source_key="a", target_key="z"),),
                )

    def test_disabled_custom_input_does_not_attach_shadow_notice(self):
        trigger = {"key": "a", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        runtime = {
            "keymaps": [{"id": "km1", "triggers": [trigger], "mappings": {"a": "b"}}],
            "active_keymap_id": "km1",
        }
        route = make_router(
            custom_enabled=False,
            trigger=trigger,
            keymap_target="b",
            runtime_data=runtime,
        ).handle(down("a"))
        self.assertEqual(route.actions, ())
        self.assertEqual(route.shadowed, ())

    def test_trigger_repeat_tracks_down_up_and_suppress(self):
        for suppress in (True, False):
            with self.subTest(suppress=suppress):
                trigger = {"actions": [{"type": "text", "value": "x"}],
                           "suppress": suppress}
                router = make_router(trigger=trigger)
                first = router.handle(down("F1"))
                repeated = router.handle(down("f1"))
                released = router.handle(
                    SimpleNamespace(event_type="up", name="f1", scan_code=None))
                next_press = router.handle(down("f1"))
                self.assertEqual(first.actions, (TriggerAction("f1", False),))
                self.assertEqual(repeated.actions, (TriggerAction("f1", True),))
                self.assertEqual(released, InputRoute())
                self.assertEqual(next_press.actions, first.actions)
                self.assertEqual(
                    [route.accept for route in (first, repeated, next_press)],
                    [not suppress] * 3,
                )

    def test_repeat_does_not_change_other_router_actions(self):
        cases = (
            ({"stop_key": "f1"}, StopHookAction()),
            ({"toggle_key": "f1"}, ToggleModeAction()),
            ({"switch_target": "km2"}, SelectKeymapAction("km2")),
            ({"keymap_target": "z"}, SendKeyAction("f1", "z")),
        )
        for options, action in cases:
            with self.subTest(options=options):
                router = make_router(**options)
                first = router.handle(down("f1"))
                self.assertEqual(first.actions, (action,))
                self.assertFalse(first.accept)
                self.assertEqual(router.handle(down("f1")), first)

    def test_repeat_uses_resolved_scan_code_before_updating_state(self):
        state = KeyStateManager(resolve_scan_code=lambda _code: "f1")
        router = make_router(trigger={"actions": [{"type": "text", "value": "x"}]})
        router._key_state_manager = state
        router._resolve_scan_code = lambda _code: "F1"
        event = SimpleNamespace(event_type="down", name="unknown", scan_code=59)
        self.assertEqual(router.handle(event).actions, (TriggerAction("f1"),))
        self.assertEqual(router.handle(event).actions, (TriggerAction("f1", True),))

    def test_executor_forwards_repeat(self):
        received = []

        def on_trigger(key, repeat):
            received.append((key, repeat))

        executor = ActionExecutor(
            input_gateway=None,
            validate_hotkey=lambda _key: ("", ""),
            on_action_error=Mock(),
            on_runtime_error=Mock(),
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=on_trigger,
        )
        executor.execute_router_action(TriggerAction("f1"))
        executor.execute_router_action(TriggerAction("f1", True))
        self.assertEqual(received, [("f1", False), ("f1", True)])

    def test_executor_does_not_retry_callback_type_error(self):
        received = []

        def on_trigger(key, repeat=False):
            received.append((key, repeat))
            raise TypeError("callback failed")

        executor = ActionExecutor(
            input_gateway=None,
            validate_hotkey=lambda _key: ("", ""),
            on_action_error=Mock(),
            on_runtime_error=Mock(),
            on_stop_hook=Mock(),
            on_toggle_mode=Mock(),
            on_select_keymap=Mock(),
            on_trigger=on_trigger,
        )
        with self.assertRaisesRegex(TypeError, "callback failed"):
            executor.execute_router_action(TriggerAction("f1", True))
        self.assertEqual(received, [("f1", True)])

    def test_no_match_passes_through(self):
        route = make_router().handle(down("a"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)


if __name__ == "__main__":
    unittest.main()
