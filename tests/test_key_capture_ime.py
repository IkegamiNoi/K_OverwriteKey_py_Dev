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

    def nametowidget(self, name: str) -> "FakeWindow":
        assert name == "."
        return self.root

    def winfo_id(self) -> int:
        return self.hwnd

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
