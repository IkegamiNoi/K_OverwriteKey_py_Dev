from __future__ import annotations

import unittest
from types import SimpleNamespace

from keyseq.presentation.key_capture_ime import KeyCaptureImeTracker


class FakeWindow:
    def __init__(self, hwnd: int = 100, root: "FakeWindow | None" = None) -> None:
        self.hwnd = hwnd
        self.root = root or self
        self.bindings: dict[str, object] = {}
        self.unbound: list[tuple[str, str]] = []
        self._next_binding = 0
        self.focus_widget: object | None = None
        self.focus_error = False

    def nametowidget(self, name: str) -> "FakeWindow":
        assert name == "."
        return self.root

    def winfo_id(self) -> int:
        return self.hwnd

    def winfo_toplevel(self) -> "FakeWindow":
        return self.root

    def focus_get(self) -> object | None:
        if self.focus_error:
            raise RuntimeError("focus unavailable")
        return self.focus_widget

    def bind(self, sequence: str, callback, add: str = "") -> str:
        assert sequence == "<Destroy>" and add == "+"
        self._next_binding += 1
        funcid = str(self._next_binding)
        self.bindings[funcid] = callback
        return funcid

    def unbind(self, sequence: str, funcid: str) -> None:
        self.unbound.append((sequence, funcid))
        self.bindings.pop(funcid, None)

    def destroy_event(self, widget: object) -> None:
        event = SimpleNamespace(widget=widget)
        for callback in list(self.bindings.values()):
            callback(event)


class KeyCaptureImeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.is_open = True
        self.get_calls: list[int] = []
        self.set_calls: list[tuple[int, bool]] = []
        self.get_none = False
        self.set_result = True

        def get_open(hwnd: int) -> bool | None:
            self.get_calls.append(hwnd)
            return None if self.get_none else self.is_open

        def set_open(hwnd: int, value: bool) -> bool:
            self.set_calls.append((hwnd, value))
            if self.set_result:
                self.is_open = value
            return self.set_result

        self.tracker = KeyCaptureImeTracker(get_open, set_open)

    def test_generation_advances_for_every_begin_and_actual_end_only(self) -> None:
        window = FakeWindow()
        self.tracker.begin("a", window)
        self.assertEqual(self.tracker.generation, 1)
        self.tracker.begin("a", window, lambda name: None)
        self.assertEqual(self.tracker.generation, 2)
        self.tracker.end("missing")
        self.assertEqual(self.tracker.generation, 2)
        self.tracker.end("a")
        self.assertEqual(self.tracker.generation, 3)

    def test_hook_activates_and_deactivates_only_on_owner_transitions(self) -> None:
        class FakeHook:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def activate(self) -> None:
                self.calls.append("activate")

            def deactivate(self) -> None:
                self.calls.append("deactivate")

        hook = FakeHook()
        self.tracker.set_capture_hook(hook)
        window = FakeWindow()
        self.tracker.begin("a", window)
        self.tracker.begin("a", window)
        self.tracker.begin("b", window)
        self.tracker.end("a")
        self.tracker.end("missing")
        self.tracker.end("b")
        self.assertEqual(hook.calls, ["activate", "deactivate"])

    def test_deliver_checks_generation_focus_and_latest_matching_owner(self) -> None:
        window = FakeWindow()
        focused = FakeWindow(root=window)
        window.focus_widget = focused
        seen: list[tuple[str, str]] = []
        self.tracker.begin("a", window, lambda name: seen.append(("a", name)))
        self.tracker.begin("b", window, lambda name: seen.append(("b", name)))
        self.tracker.deliver("kana", self.tracker.generation - 1)
        self.assertEqual(seen, [])
        self.tracker.deliver("kana", self.tracker.generation)
        self.assertEqual(seen, [("b", "kana")])

        self.tracker.begin("a", window, lambda name: seen.append(("a-new", name)))
        self.tracker.deliver("muhenkan", self.tracker.generation)
        self.assertEqual(seen[-1], ("a-new", "muhenkan"))

    def test_deliver_skips_missing_callback_and_focus_failures(self) -> None:
        window = FakeWindow()
        focused = FakeWindow(root=window)
        window.focus_widget = focused
        self.tracker.begin("a", window)
        self.tracker.deliver("kana", self.tracker.generation)
        self.assertEqual(window.focus_widget, focused)

        window.focus_error = True
        received: list[str] = []
        self.tracker.begin("b", window, received.append)
        self.tracker.deliver("kana", self.tracker.generation)
        self.assertEqual(received, [])

    def test_turns_off_on_begin_and_restores_on_end_only_if_initially_on(self) -> None:
        window = FakeWindow()
        self.tracker.begin("a", window)
        self.assertFalse(self.is_open)
        self.tracker.end("a")
        self.assertTrue(self.is_open)
        self.assertEqual(self.set_calls, [(100, False), (100, True)])

        self.is_open = False
        self.set_calls.clear()
        self.tracker.begin("b", window)
        self.tracker.end("b")
        self.assertEqual(self.set_calls, [])

    def test_uses_root_window_hwnd_not_capturing_window_hwnd(self) -> None:
        root = FakeWindow(hwnd=100)
        child = FakeWindow(hwnd=200, root=root)
        self.tracker.begin("a", child)
        self.tracker.end("a")
        self.assertEqual(self.get_calls, [100, 100])
        self.assertEqual(self.set_calls, [(100, False), (100, True)])
        self.assertEqual(child.unbound, [("<Destroy>", "1")])

    def test_begin_and_end_are_idempotent(self) -> None:
        window = FakeWindow()
        self.tracker.begin("a", window)
        counts = len(self.get_calls), len(self.set_calls)
        self.tracker.begin("a", window)
        self.assertEqual((len(self.get_calls), len(self.set_calls)), counts)
        self.tracker.end("a")
        end_counts = len(self.get_calls), len(self.set_calls)
        self.tracker.end("a")
        self.tracker.end("missing")
        self.assertEqual((len(self.get_calls), len(self.set_calls)), end_counts)

    def test_overlapping_owners_restore_only_after_last_end(self) -> None:
        window = FakeWindow()
        self.tracker.begin("a", window)
        self.tracker.begin("b", window)
        self.tracker.end("a")
        self.assertFalse(self.is_open)
        self.assertEqual(self.set_calls, [(100, False)])
        self.tracker.end("b")
        self.assertTrue(self.is_open)
        self.assertEqual(self.set_calls[-1], (100, True))

    def test_later_begin_turns_ime_off_again_if_user_turned_it_on(self) -> None:
        window = FakeWindow()
        self.tracker.begin("a", window)
        self.is_open = True
        self.tracker.begin("b", window)
        self.assertEqual(self.set_calls, [(100, False), (100, False)])
        self.tracker.end("a")
        self.tracker.end("b")
        self.assertTrue(self.is_open)

    def test_does_not_restore_if_user_turned_ime_on_during_capture(self) -> None:
        window = FakeWindow()
        self.tracker.begin("a", window)
        self.is_open = True
        self.tracker.end("a")
        self.assertEqual(self.set_calls, [(100, False)])

    def test_destroy_handler_ends_only_when_bound_window_is_destroyed(self) -> None:
        root = FakeWindow()
        window = FakeWindow(root=root)
        self.tracker.begin("a", window)
        window.destroy_event(root)
        self.assertTrue(self.tracker.is_capturing("a"))
        window.destroy_event(window)
        self.assertFalse(self.tracker.is_capturing("a"))
        self.assertEqual(window.unbound, [("<Destroy>", "1")])

    def test_get_failure_continues_capture_and_failed_set_does_not_mark(self) -> None:
        window = FakeWindow()
        self.get_none = True
        self.tracker.begin("a", window)
        self.assertTrue(self.tracker.is_capturing("a"))
        self.tracker.end("a")
        self.assertEqual(self.set_calls, [])

        self.get_none = False
        self.set_result = False
        self.tracker.begin("b", window)
        self.tracker.end("b")
        self.assertEqual(self.set_calls, [(100, False)])


if __name__ == "__main__":
    unittest.main()
