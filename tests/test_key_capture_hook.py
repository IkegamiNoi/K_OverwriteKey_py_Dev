from __future__ import annotations

import unittest
from types import SimpleNamespace

from keyseq.presentation.key_capture_hook import KeyCaptureHook


class KeyCaptureHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 0.0
        self.events: list[tuple[int, object]] = []
        self.registered: list[object] = []
        self.unregistered: list[object] = []
        self.delivered: list[tuple[str, int]] = []
        self.generation = 4
        self.foreground = True
        self.names = {41: "zenkaku_hankaku", 42: "kana", 43: "esc", 44: "left ctrl"}
        self.target_checks: list[str] = []
        self.hook = KeyCaptureHook(
            register_hook=self._register,
            unregister_hook=self.unregistered.append,
            resolve_name=self._resolve_name,
            numpad_name=self._numpad_name,
            is_foreground=self._is_foreground,
            after=self._after,
            repeat_delay_ms=lambda: 500,
            deliver=lambda name, generation: self.delivered.append((name, generation)),
            get_generation=lambda: self.generation,
            clock=lambda: self.now,
        )

    def _register(self, callback):
        handle = object()
        self.registered.append((callback, handle))
        return handle

    def _after(self, delay: int, callback) -> None:
        self.events.append((delay, callback))

    def _resolve_name(self, scan_code: int) -> str:
        self.target_checks.append("name")
        return self.names.get(scan_code, "")

    def _numpad_name(self, scan_code: int, is_keypad: bool) -> str | None:
        self.target_checks.append("numpad")
        return "numpad 1" if is_keypad else None

    def _is_foreground(self) -> bool:
        self.target_checks.append("foreground")
        return self.foreground

    def _event(self, scan_code: int, event_type: str = "down", is_keypad: bool = False):
        return SimpleNamespace(
            scan_code=scan_code,
            event_type=event_type,
            is_keypad=is_keypad,
        )

    def _dispatch(self, event) -> bool:
        return self.registered[-1][0](event)

    def _run_timer(self, delay: int) -> None:
        for index, (queued_delay, callback) in enumerate(self.events):
            if queued_delay == delay:
                self.events.pop(index)
                callback()
                return
        self.fail(f"No {delay} ms timer queued")

    def test_registers_once_reuses_hook_and_unregisters(self) -> None:
        self.hook.activate()
        first = self.registered[0][1]
        self.hook.activate()
        self.assertEqual(len(self.registered), 1)
        self.hook.deactivate()
        self.assertEqual(self.unregistered, [])
        self.hook.deactivate()
        self.assertEqual(self.unregistered, [first])

    def test_non_target_checks_are_ordered_and_pass_through(self) -> None:
        self.hook.activate()
        self.foreground = False
        self.assertIs(self._dispatch(self._event(99)), True)
        self.assertEqual(self.target_checks, ["foreground"])
        self.foreground = True
        self.target_checks.clear()
        self.assertIs(self._dispatch(self._event(41, is_keypad=True)), True)
        self.assertEqual(self.target_checks, ["foreground", "numpad"])
        self.target_checks.clear()
        self.assertIs(self._dispatch(self._event(99)), True)
        self.assertEqual(self.target_checks, ["foreground", "numpad", "name"])
        self.assertIs(self._dispatch(self._event(43)), True)
        self.assertIs(self._dispatch(self._event(44)), True)
        self.assertIs(self._dispatch(self._event(41, "other")), True)

    def test_target_down_and_up_are_suppressed_but_only_new_down_is_delivered(self) -> None:
        self.hook.activate()
        self.assertIs(self._dispatch(self._event(41)), False)
        self.assertIs(self._dispatch(self._event(41, "up")), False)
        self.assertEqual(self.delivered, [])
        delay, scheduled = self.events.pop(0)
        self.assertEqual(delay, 0)
        scheduled()
        self.assertEqual(self.delivered, [("zenkaku_hankaku", 4)])

        self.now = 0.3
        self.assertIs(self._dispatch(self._event(41)), False)
        self.assertEqual(len(self.events), 0)
        self.now = 0.9
        self.assertIs(self._dispatch(self._event(41)), False)
        self.assertEqual(len(self.events), 0)
        self.now = 1.61
        self.assertIs(self._dispatch(self._event(41)), False)
        self.events.pop(0)[1]()
        self.assertEqual(self.delivered[-1], ("zenkaku_hankaku", 4))

    def test_up_does_not_clear_pressed_entry_or_extend_repeat_window(self) -> None:
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.now = 0.6
        self._dispatch(self._event(41, "up"))
        self.now = 0.69
        self._dispatch(self._event(41))
        self.assertEqual(len(self.events), 0)
        self.now = 1.3
        self._dispatch(self._event(41, "up"))
        self.now = 1.39
        self._dispatch(self._event(41))
        self.assertEqual(len(self.events), 0)
        self.now = 2.1
        self._dispatch(self._event(41))
        self.assertEqual(len(self.events), 1)

    def test_deactivated_hook_suppresses_pressed_key_until_release_timeout(self) -> None:
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.hook.deactivate()
        self.assertIs(self._dispatch(self._event(41, "up")), False)
        self.assertIs(self._dispatch(self._event(42)), True)
        self.now = 0.71
        self._run_timer(100)
        self.assertEqual(self.unregistered, [self.registered[0][1]])

    def test_layout_name_that_is_numpad_name_passes_through(self) -> None:
        self.names[45] = "num 0"
        self.hook.activate()
        self.assertIs(self._dispatch(self._event(45)), True)
        self.assertEqual(self.events, [])

    def test_generation_is_read_before_resolving_the_name(self) -> None:
        def resolve_and_switch(scan_code: int) -> str:
            self.generation = 5
            return self.names.get(scan_code, "")

        self.hook._resolve_name = resolve_and_switch
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.assertEqual(self.delivered, [("zenkaku_hankaku", 4)])

    def test_up_during_idle_does_not_extend_pressed_entry(self) -> None:
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.hook.deactivate()
        self.now = 0.6
        self.assertIs(self._dispatch(self._event(41, "up")), False)
        self.now = 0.71
        self.assertIs(self._dispatch(self._event(41, "up")), True)

    def test_idle_timeout_and_reactivation(self) -> None:
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.hook.deactivate()
        self.now = 5.0
        self._run_timer(100)
        self.assertEqual(len(self.unregistered), 1)

        self.now = 10.0
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.hook.deactivate()
        self.hook.activate()
        self._run_timer(100)
        self.assertEqual(len(self.registered), 2)
        self.assertEqual(len(self.unregistered), 1)

    def test_after_failure_still_suppresses_and_callback_failure_passes_through(self) -> None:
        self.hook.activate()
        self._after = lambda delay, callback: (_ for _ in ()).throw(RuntimeError("closing"))
        self.hook._after = self._after
        self.assertIs(self._dispatch(self._event(41)), False)
        broken = KeyCaptureHook(
            register_hook=lambda callback: callback,
            unregister_hook=lambda handle: None,
            resolve_name=lambda scan_code: (_ for _ in ()).throw(RuntimeError("bad layout")),
            numpad_name=lambda scan_code, is_keypad: None,
            is_foreground=lambda: True,
            after=lambda delay, callback: None,
            repeat_delay_ms=lambda: 500,
            deliver=lambda name, generation: None,
            get_generation=lambda: 0,
        )
        broken.activate()
        self.assertIs(broken._callback(self._event(41)), True)

    def test_shutdown_unregisters_immediately_and_invalidates_idle_timer(self) -> None:
        self.hook.activate()
        self._dispatch(self._event(41))
        self.events.pop(0)[1]()
        self.hook.deactivate()
        self.hook.shutdown()
        self.assertEqual(len(self.unregistered), 1)
        self._run_timer(100)
        self.assertEqual(len(self.unregistered), 1)


if __name__ == "__main__":
    unittest.main()
