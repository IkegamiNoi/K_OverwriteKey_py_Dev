from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from keyseq.infrastructure.os_backend.macos import backend
from keyseq.infrastructure.os_backend.macos.event_tap import OWN_EVENT_MARK
from keyseq.infrastructure.os_backend.macos.mouse_hold_tap import MouseHoldTap


def fake_quartz(*, event_results=None, button_states=None):
    quartz = SimpleNamespace(
        kCGScrollEventUnitPixel=77,
        kCGEventSourceUserData=99,
        kCGHIDEventTap=88,
        kCGEventSourceStateHIDSystemState=66,
        kCGMouseButtonLeft=0,
        kCGMouseButtonRight=1,
        CGEventCreateScrollWheelEvent=Mock(side_effect=event_results),
        CGEventSetIntegerValueField=Mock(),
        CGEventPost=Mock(),
        CGEventSourceButtonState=Mock(side_effect=button_states),
    )
    return quartz


class MacMouseBackendTests(unittest.TestCase):
    def test_scroll_maps_axes_and_marks_posts(self) -> None:
        events = [object(), object()]
        quartz = fake_quartz(event_results=events)
        mouse = backend.MacMouseBackend(quartz=quartz)
        mouse.scroll_mouse(vertical=True, deltas=(120,), position=None)
        mouse.scroll_mouse(vertical=False, deltas=(-120,), position=None)
        self.assertEqual(quartz.CGEventCreateScrollWheelEvent.call_args_list, [
            call(None, 77, 2, 10, 0), call(None, 77, 2, 0, 10),
        ])
        self.assertEqual(quartz.CGEventSetIntegerValueField.call_args_list, [
            call(events[0], 99, OWN_EVENT_MARK), call(events[1], 99, OWN_EVENT_MARK),
        ])
        self.assertEqual(quartz.CGEventPost.call_args_list, [call(88, events[0]), call(88, events[1])])

    def test_scroll_rounds_preserving_sign_and_skips_zero(self) -> None:
        values = (120, -120, 60, 6, -6, 1, 0)
        events = [object() for _ in values[:-1]]
        quartz = fake_quartz(event_results=events)
        backend.MacMouseBackend(quartz=quartz).scroll_mouse(
            vertical=True, deltas=values, position=None,
        )
        self.assertEqual([args.args[3] for args in quartz.CGEventCreateScrollWheelEvent.call_args_list],
                         [10, -10, 5, 1, -1, 1])
        self.assertEqual(quartz.CGEventPost.call_count, 6)

    def test_empty_deltas_and_position(self) -> None:
        quartz = fake_quartz()
        mouse = backend.MacMouseBackend(quartz=quartz)
        with patch.object(mouse, "move_cursor") as move:
            mouse.scroll_mouse(vertical=True, deltas=(), position=(4, 5))
        move.assert_called_once_with(4, 5)
        quartz.CGEventPost.assert_not_called()

    def test_none_event_raises_oserror(self) -> None:
        quartz = fake_quartz(event_results=[None])
        with self.assertRaises(OSError):
            backend.MacMouseBackend(quartz=quartz).scroll_mouse(
                vertical=True, deltas=(120,), position=None,
            )


class MacMouseButtonStateTests(unittest.TestCase):
    def test_left_right_and_neither(self) -> None:
        for states, expected in (((True, False), True), ((False, True), True), ((False, False), False)):
            with self.subTest(states=states):
                quartz = fake_quartz(button_states=states)
                self.assertEqual(backend.MacWindowBackend(quartz=quartz).is_mouse_button_down(), expected)

    def test_exception_returns_false_and_logs_once_per_instance(self) -> None:
        quartz = fake_quartz(button_states=[RuntimeError("failed"), RuntimeError("failed")])
        window = backend.MacWindowBackend(quartz=quartz)
        with self.assertLogs(backend._LOG, level="ERROR") as logs:
            self.assertFalse(window.is_mouse_button_down())
            self.assertFalse(window.is_mouse_button_down())
        self.assertEqual(len(logs.records), 1)


if __name__ == "__main__":
    unittest.main()

class MacMouseAddedTests(unittest.TestCase):
    def test_click_twice_and_button_mapping(self):
        q = _extended_quartz()
        mouse = backend.MacMouseBackend(quartz=q)
        with patch.object(mouse, "move_cursor"):
            mouse.click_mouse(3, 4, "left", 2)
        self.assertEqual([call.args[1] for call in q.CGEventCreateMouseEvent.call_args_list], [20, 21, 20, 21])
        self.assertEqual([call.args[-1] for call in q.CGEventSetIntegerValueField.call_args_list if call.args[1] == 101], [1, 1, 2, 2])
        for button, expected in (("left", (20, 21, 22, 0)), ("right", (23, 24, 25, 1)), ("middle", (26, 27, 28, 2))):
            self.assertEqual(mouse._button(button)[1:], expected)
        with self.assertRaises(ValueError):
            mouse._button("unknown")

    def test_drag_steps_last_position_and_releases_after_error(self):
        q = _extended_quartz()
        sleep = Mock()
        mouse = backend.MacMouseBackend(quartz=q, sleep=sleep)
        with patch.object(mouse, "move_cursor"):
            mouse.drag_mouse(0, 0, 5, 10, "left", 0.05)
        self.assertEqual(sum(c.args[1] == 22 for c in q.CGEventCreateMouseEvent.call_args_list), 5)
        self.assertEqual(q.CGEventCreateMouseEvent.call_args_list[-1].args[2], (5, 10))
        self.assertEqual(sleep.call_count, 5)
        q = _extended_quartz()
        mouse = backend.MacMouseBackend(quartz=q, sleep=Mock(side_effect=RuntimeError("stop")))
        with patch.object(mouse, "move_cursor"), self.assertRaises(RuntimeError):
            mouse.drag_mouse(0, 0, 1, 1, "left", 0.05)
        self.assertEqual(q.CGEventCreateMouseEvent.call_args_list[-1].args[1], 21)

    def test_down_up_drive_hold_tap(self):
        q = _extended_quartz()
        mouse = backend.MacMouseBackend(quartz=q)
        mouse._hold_tap = Mock()
        with patch.object(mouse, "cursor_position", return_value=(1, 2)):
            mouse.mouse_down("left")
            mouse.mouse_up("left")
        mouse._hold_tap.start.assert_called_once_with("left")
        mouse._hold_tap.stop.assert_called_once_with()

    def test_hold_callback_rewrites_and_stops_only_on_physical_up(self):
        q = _extended_quartz()
        tap = MouseHoldTap(quartz=q)
        tap._button, tap._up, tap._dragged, tap._number = 20, 21, 22, 0
        event = object()
        tap._callback(None, q.kCGEventMouseMoved, event, None)
        q.CGEventSetType.assert_called_once_with(event, 22)
        q.CGEventSetIntegerValueField.assert_called_with(event, 102, 0)
        q.CGEventGetIntegerValueField.return_value = OWN_EVENT_MARK
        tap.stop = Mock()
        tap._callback(None, 21, event, None)
        tap.stop.assert_not_called()
        q.CGEventGetIntegerValueField.return_value = 0
        with patch("keyseq.infrastructure.os_backend.macos.mouse_hold_tap.Thread") as thread:
            tap._callback(None, 21, event, None)
            thread.assert_called_once()
        tap._button = None
        with patch("keyseq.infrastructure.os_backend.macos.mouse_hold_tap.Thread") as thread:
            tap._callback(None, 21, event, None)
            thread.assert_not_called()

    def test_disabled_reenables_and_missing_tap_logs_once(self):
        q = _extended_quartz()
        tap = MouseHoldTap(quartz=q)
        tap._tap = object()
        event = object()
        tap._callback(None, q.kCGEventTapDisabledByTimeout, event, None)
        q.CGEventTapEnable.assert_called_with(tap._tap, True)
        q.CGEventTapCreate.return_value = None
        with self.assertLogs("keyseq.infrastructure.os_backend.macos.mouse_hold_tap", level="ERROR") as logs:
            tap.start("left")
            tap.start("left")
        self.assertEqual(len(logs.records), 1)


def _extended_quartz():
    names = ("kCGEventLeftMouseDown", "kCGEventLeftMouseUp", "kCGEventLeftMouseDragged",
             "kCGEventRightMouseDown", "kCGEventRightMouseUp", "kCGEventRightMouseDragged",
             "kCGEventOtherMouseDown", "kCGEventOtherMouseUp", "kCGEventOtherMouseDragged")
    q = fake_quartz()
    for i, name in enumerate(names):
        setattr(q, name, i + 20)
    q.kCGMouseButtonCenter = 2
    q.kCGMouseEventClickState = 101
    q.kCGMouseEventButtonNumber = 102
    q.kCGEventMouseMoved = 10
    q.kCGEventTapDisabledByTimeout, q.kCGEventTapDisabledByUserInput = 11, 12
    q.kCGSessionEventTap, q.kCGHeadInsertEventTap, q.kCGEventTapOptionDefault = 13, 14, 15
    q.CGEventCreateMouseEvent = Mock(side_effect=lambda _s, kind, pos, button: SimpleNamespace(kind=kind, pos=pos, button=button))
    q.CGEventSetType = Mock()
    q.CGEventGetIntegerValueField = Mock(return_value=0)
    q.CGEventTapCreate = Mock(return_value=None)
    q.CGEventTapEnable = Mock()
    return q
