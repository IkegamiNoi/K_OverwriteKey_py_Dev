from __future__ import annotations

import unittest
from collections.abc import Callable
from types import SimpleNamespace

from keyseq.application.input_router import (
    InputRoute,
    InputRouter,
    SendKeyAction,
)
from keyseq.application.key_overlap import analyze_key_overlaps
from keyseq.application.key_state_manager import KeyStateManager
from keyseq.application.make_only_keys import MakeOnlyKeyFilter
from keyseq.presentation.keyboard_layouts import (
    KeyboardLayout,
    KeySpec,
    resolve_layout_key_id_from_scan_code,
)


class FakeClockAndScheduler:
    def __init__(self) -> None:
        self.now = 0.0
        self.scheduled: list[tuple[float, Callable[[], None]]] = []

    def clock(self) -> float:
        return self.now

    def schedule(self, delay_s: float, callback: Callable[[], None]) -> None:
        self.scheduled.append((self.now + delay_s, callback))

    def advance_and_fire(self, at: float) -> None:
        self.now = at
        due = [item for item in self.scheduled if item[0] < at]
        self.scheduled = [item for item in self.scheduled if item[0] >= at]
        for _deadline, callback in due:
            callback()


class MakeOnlyKeysIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.time = FakeClockAndScheduler()
        self.layout = KeyboardLayout(
            layout_id="test-jis",
            display_name="Test JIS",
            keys=(
                KeySpec(
                    id="muhenkan",
                    label="無変換",
                    x=0,
                    y=0,
                    scan_code=123,
                    extra_scan_codes=(241,),
                ),
            ),
        )
        resolve_scan_code = lambda scan_code: resolve_layout_key_id_from_scan_code(
            self.layout, scan_code
        )
        self.key_state_manager = KeyStateManager(resolve_scan_code=resolve_scan_code)
        runtime_data = {
            "keymaps": [{"id": "km1", "triggers": [], "mappings": {"muhenkan": "a"}}],
            "active_keymap_id": "km1",
        }
        self.router = InputRouter(
            key_state_manager=self.key_state_manager,
            get_send_guard_count=lambda: 0,
            get_hook_pause_count=lambda: 0,
            get_stop_key=lambda: "",
            get_toggle_key=lambda: "",
            get_key_overlap_report=lambda: analyze_key_overlaps(runtime_data, "", ""),
            get_custom_input_enabled=lambda: True,
            find_keymap_switch_target=lambda _key: "",
            find_trigger=lambda _key: None,
            find_keymap_target=lambda key: runtime_data["keymaps"][0]["mappings"].get(key, ""),
            resolve_scan_code=resolve_scan_code,
        )
        self.routes: list[InputRoute] = []
        self.filter = MakeOnlyKeyFilter(
            route=self.router.handle,
            release_state=self.key_state_manager.handle_event,
            clock=self.time.clock,
            schedule=self.time.schedule,
            get_hook_pause_count=lambda: 0,
            get_repeat_delay_ms=lambda: 500,
            on_routes=lambda routes, _generation: self.routes.extend(routes),
        )

    def send_down(self, at: float) -> None:
        self.time.now = at
        result = self.filter.handle(
            SimpleNamespace(
                event_type="down",
                scan_code=241,
                name=None,
                is_keypad=False,
            )
        )
        self.assertIsNotNone(result)
        self.routes.extend(result.routes)

    def assert_send_actions(self, expected_count: int) -> None:
        actions = [
            action
            for route in self.routes
            for action in route.actions
            if isinstance(action, SendKeyAction)
        ]
        self.assertEqual(
            actions,
            [SendKeyAction(source_key="muhenkan", target_key="a")]
            * expected_count,
        )

    def test_press_and_release_pair_sends_replacement_once(self) -> None:
        self.send_down(0.0)
        self.assertTrue(self.key_state_manager.is_pressed("muhenkan"))
        self.send_down(0.045)
        self.send_down(0.056)
        self.time.advance_and_fire(0.080)

        self.assert_send_actions(1)
        self.assertFalse(self.key_state_manager.is_pressed("muhenkan"))

    def test_hold_repeats_replacement_then_release_clears_pressed_state(self) -> None:
        self.send_down(0.0)
        self.send_down(0.500)
        self.time.advance_and_fire(0.5161)
        self.send_down(0.533)
        self.time.advance_and_fire(0.5491)
        self.send_down(0.588)
        self.send_down(0.601)
        self.time.advance_and_fire(0.650)

        self.assert_send_actions(3)
        self.assertFalse(self.key_state_manager.is_pressed("muhenkan"))


if __name__ == "__main__":
    unittest.main()
