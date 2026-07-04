import unittest
from types import SimpleNamespace

from keyseq.application.input_router import (
    InputRouter,
    SelectKeymapAction,
    SendKeyAction,
    StopHookAction,
    ToggleModeAction,
    TriggerAction,
)
from keyseq.application.key_state_manager import KeyStateManager


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
):
    return InputRouter(
        key_state_manager=KeyStateManager(),
        get_send_guard_count=lambda: send_guard,
        get_hook_pause_count=lambda: pause,
        get_stop_key=lambda: stop_key,
        get_toggle_key=lambda: toggle_key,
        get_custom_input_enabled=lambda: custom_enabled,
        find_keymap_switch_target=lambda key: switch_target,
        find_trigger=lambda key: trigger,
        find_keymap_target=lambda key: keymap_target,
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

    def test_no_match_passes_through(self):
        route = make_router().handle(down("a"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)


if __name__ == "__main__":
    unittest.main()
