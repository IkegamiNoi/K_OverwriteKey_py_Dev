from __future__ import annotations

import builtins
import importlib
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend.macos import backend, event_tap
from keyseq.infrastructure.os_backend.macos.event_tap import EventTap, KeyEvent, OWN_EVENT_MARK


def key_event(kind="down"):
    return KeyEvent(kind, 30, "a", False)


class MacKeyboardBackendTests(unittest.TestCase):
    def setUp(self):
        self.factory = patch.object(backend, "EventTap")
        self.tap_class = self.factory.start()
        self.addCleanup(self.factory.stop)
        self.keyboard = backend.MacKeyboardBackend()

    def test_lazy_single_tap_and_last_removal(self):
        self.tap_class.assert_not_called()
        one = self.keyboard.register_global_hook(lambda e: True)
        two = self.keyboard.register_key_hook("a", lambda e: None, suppress=False)
        self.tap_class.assert_called_once()
        self.tap_class.return_value.start.assert_called_once()
        self.keyboard.unregister_hook(object())
        self.keyboard.unregister_hook(one)
        self.tap_class.return_value.stop.assert_not_called()
        self.keyboard.unregister_hook(two)
        self.tap_class.return_value.stop.assert_called_once()
        self.keyboard.unregister_hook(two)
        self.keyboard.register_global_hook(lambda e: True)
        self.assertEqual(self.tap_class.call_count, 1)
        self.assertEqual(self.tap_class.return_value.start.call_count, 2)

    def test_failed_start_removes_registration_and_can_retry(self):
        self.tap_class.return_value.start.side_effect = [OSError("denied"), None]
        with self.assertRaises(OSError):
            self.keyboard.register_global_hook(lambda e: False, suppress=True)
        self.keyboard.register_global_hook(lambda e: True, suppress=True)
        self.assertTrue(self.keyboard._dispatch(0, key_event()))

    def test_suppressing_globals_short_circuit_in_order(self):
        for decision in (False, None):
            with self.subTest(decision=decision):
                keyboard = backend.MacKeyboardBackend()
                seen = []
                keyboard.register_global_hook(lambda e: seen.append(1) or True, suppress=True)
                keyboard.register_global_hook(lambda e: seen.append(2) or decision, suppress=True)
                keyboard.register_global_hook(lambda e: seen.append(3) or True, suppress=True)
                self.assertFalse(keyboard._dispatch(0, key_event()))
                self.assertEqual(seen, [1, 2])

    def test_globals_precede_key_hooks_and_key_return_is_ignored(self):
        seen = []
        self.keyboard.register_key_hook("a", lambda e: seen.append("key") or True, suppress=True)
        self.keyboard.register_global_hook(lambda e: seen.append("global") or True, suppress=True)
        self.keyboard.register_key_hook("a", lambda e: seen.append("later"), suppress=True)
        self.assertFalse(self.keyboard._dispatch(0, key_event()))
        self.assertEqual(seen, ["global", "key"])
        seen.clear()
        self.assertFalse(self.keyboard._dispatch(0, key_event("up")))
        self.assertEqual(seen, ["global"])

    def test_observers_do_not_suppress_and_key_observer_only_sees_down(self):
        global_hook, key_hook = Mock(return_value=False), Mock(return_value=None)
        self.keyboard.register_global_hook(global_hook)
        self.keyboard.register_key_hook("a", key_hook, suppress=False)
        for vk, kind in ((0, "down"), (0, "up"), (1, "down")):
            self.assertTrue(self.keyboard._dispatch(vk, key_event(kind)))
        self.assertEqual(global_hook.call_count, 3)
        key_hook.assert_called_once_with(key_event())

    def test_suppressing_global_skips_keys_and_observers(self):
        observer, key_hook = Mock(), Mock()
        self.keyboard.register_global_hook(observer)
        self.keyboard.register_key_hook("a", key_hook, suppress=True)
        self.keyboard.register_global_hook(lambda e: False, suppress=True)
        self.assertFalse(self.keyboard._dispatch(0, key_event()))
        observer.assert_not_called()
        key_hook.assert_not_called()

    def test_unknown_key_fails_without_starting_tap(self):
        for name in ("unknown", "caps lock", "fn", "num 0"):
            with self.assertRaises(ValueError):
                self.keyboard.register_key_hook(name, Mock(), suppress=True)
        self.tap_class.assert_not_called()

    def test_import_does_not_load_pyobjc(self):
        original_import = builtins.__import__

        def guarded(name, *args, **kwargs):
            if name.split(".")[0] in {"Quartz", "objc", "Foundation", "CoreFoundation"}:
                raise AssertionError("Native imports must be delayed")
            return original_import(name, *args, **kwargs)

        module_names = (
            "keyseq.infrastructure.os_backend.macos.event_tap",
            "keyseq.infrastructure.os_backend.macos.backend",
        )
        originals = {name: sys.modules.pop(name) for name in module_names}
        try:
            with patch("builtins.__import__", side_effect=guarded):
                importlib.import_module(module_names[0])
                importlib.import_module(module_names[1])
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
            sys.modules.update(originals)


def fake_quartz():
    q = SimpleNamespace(
        kCGEventKeyDown=10, kCGEventKeyUp=11, kCGEventFlagsChanged=12,
        kCGEventTapDisabledByTimeout=0xFFFFFFFE, kCGEventTapDisabledByUserInput=0xFFFFFFFF,
        kCGEventSourceUserData="mark", kCGKeyboardEventKeycode="vk",
        kCGSessionEventTap=1, kCGHeadInsertEventTap=0, kCGEventTapOptionDefault=0,
        kCFRunLoopCommonModes="common", kCFRunLoopDefaultMode="default",
    )
    q.CGEventGetIntegerValueField = lambda event, field: event.get(field, 0)
    q.CGEventGetFlags = lambda event: event.get("flags", 0)
    q.CGEventSetFlags = Mock(side_effect=lambda event, flags: event.update(flags=flags))
    for name in ("CGEventTapCreate", "CGEventTapEnable", "CFRunLoopGetCurrent",
                 "CFRunLoopStop", "CFMachPortInvalidate", "CFRunLoopAddSource",
                 "CFRunLoopRemoveSource", "CFMachPortCreateRunLoopSource", "CFRunLoopRunInMode"):
        setattr(q, name, Mock())
    return q


class EventTapTests(unittest.TestCase):
    def setUp(self):
        self.q = fake_quartz()
        self.callback = Mock(return_value=True)
        self.tap = EventTap(self.callback, quartz=self.q)
        self.native_tap = object()
        self.tap._tap = self.native_tap

    def deliver(self, vk=0, kind=None, flags=0, **fields):
        event = dict(vk=vk, flags=flags, **fields)
        result = self.tap._handle_event(None, kind or self.q.kCGEventKeyDown, event, None)
        return event, result

    def test_down_up_repeat_unknown_and_immutable_event(self):
        for kind in (self.q.kCGEventKeyDown, self.q.kCGEventKeyDown, self.q.kCGEventKeyUp):
            event, result = self.deliver(kind=kind, autorepeat=1)
            self.assertIs(result, event)
        self.assertEqual([call.args[1].event_type for call in self.callback.call_args_list],
                         ["down", "down", "up"])
        translated = self.callback.call_args.args[1]
        self.assertEqual((translated.scan_code, translated.name, translated.is_keypad), (30, "a", False))
        with self.assertRaises(AttributeError):
            translated.name = "changed"
        self.callback.return_value = False
        event, result = self.deliver(vk=179)
        self.assertIsNone(result)
        self.assertEqual(self.callback.call_args.args[1].name, "")
        self.assertEqual(self.callback.call_args.args[1].scan_code, 0)

    def test_own_event_bypasses_callbacks_and_flag_rewrite(self):
        event, result = self.deliver(mark=OWN_EVENT_MARK, flags=0x100008)
        self.assertIs(result, event)
        self.callback.assert_not_called()
        self.q.CGEventSetFlags.assert_not_called()

    def test_disabled_tap_recovers_and_clears_records(self):
        for kind in (self.q.kCGEventTapDisabledByTimeout, self.q.kCGEventTapDisabledByUserInput):
            self.tap._modifiers.on_flags_changed(55, 0x100008)
            self.tap._modifiers.mark_suppressed(55, True)
            event, result = self.deliver(kind=kind)
            self.assertIs(result, event)
            self.assertEqual(self.tap._modifiers.rewrite_flags(0x100008), 0x100008)
        self.assertEqual(self.q.CGEventTapEnable.call_count, 2)
        self.q.CGEventTapEnable.assert_called_with(self.native_tap, True)
        self.callback.assert_not_called()

    def test_detached_tap_does_nothing_even_for_disable_notification(self):
        self.tap._tap = None
        for kind in (self.q.kCGEventKeyDown, self.q.kCGEventTapDisabledByUserInput):
            event, result = self.deliver(kind=kind)
            self.assertIs(result, event)
        self.q.CGEventTapEnable.assert_not_called()
        self.callback.assert_not_called()

    def test_capslock_and_fn_always_pass_and_derive_down_up(self):
        self.callback.return_value = False
        for vk, bit in ((57, 0x10000), (63, 0x800000)):
            for flags, kind in ((bit, "down"), (0, "up")):
                event, result = self.deliver(vk=vk, kind=self.q.kCGEventFlagsChanged, flags=flags)
                self.assertIs(result, event)
                translated = self.callback.call_args.args[1]
                self.assertEqual((translated.event_type, translated.scan_code, translated.name), (kind, 0, ""))

    def test_modifier_pairs_and_subsequent_flags(self):
        self.callback.return_value = False
        self.assertIsNone(self.deliver(vk=55, kind=self.q.kCGEventFlagsChanged, flags=0x100008)[1])
        self.callback.return_value = True
        event, result = self.deliver(flags=0x110008)
        self.assertIs(result, event)
        self.assertEqual(event["flags"], 0x10000)
        self.assertIsNone(self.deliver(vk=55, kind=self.q.kCGEventFlagsChanged)[1])
        self.deliver(vk=56, kind=self.q.kCGEventFlagsChanged, flags=0x20002)
        self.callback.return_value = False
        event, result = self.deliver(vk=56, kind=self.q.kCGEventFlagsChanged)
        self.assertIs(result, event)

    def test_forwarded_right_shift_change_removes_suppressed_left_shift(self):
        self.callback.return_value = False
        self.deliver(vk=56, kind=self.q.kCGEventFlagsChanged, flags=0x20002)
        self.callback.return_value = True
        event, result = self.deliver(vk=60, kind=self.q.kCGEventFlagsChanged, flags=0x20006)
        self.assertIs(result, event)
        self.assertEqual(event["flags"], 0x20004)
        self.assertEqual(self.callback.call_count, 2)

    def test_callback_detaching_tap_cannot_suppress_or_rewrite_event(self):
        def detach(_vk, _event):
            self.tap.stop()
            return False

        self.callback.side_effect = detach
        event, result = self.deliver()
        self.assertIs(result, event)
        self.q.CGEventSetFlags.assert_not_called()

    def test_callback_and_quartz_failures_are_logged_and_pass_through(self):
        self.tap._modifiers.on_flags_changed(55, 0x100008)
        self.tap._modifiers.mark_suppressed(55, True)
        for native_failure in (False, True):
            if native_failure:
                self.callback.side_effect = None
                self.q.CGEventSetFlags.side_effect = RuntimeError("native failure")
            else:
                self.callback.side_effect = RuntimeError("consumer failure")
            with self.assertLogs(event_tap.__name__, level="ERROR"):
                event, result = self.deliver()
            self.assertIs(result, event)
            self.assertEqual(self.tap._modifiers.rewrite_flags(0x100008), 0)

    def test_create_failure_and_successful_start_are_lazy(self):
        tap = EventTap(self.callback, quartz=self.q)
        self.q.CGEventTapCreate.return_value = None
        with self.assertRaises(OSError):
            tap.start()
        self.assertIsNone(tap._tap)
        self.q.CGEventTapCreate.return_value = self.native_tap
        with patch.object(event_tap, "Thread") as thread:
            tap.start()
            tap.start()
            thread.return_value.start.assert_called_once()
        args = self.q.CGEventTapCreate.call_args.args
        self.assertEqual(args[2:4], (0, (1 << 10) | (1 << 11) | (1 << 12)))

    def test_stop_detaches_before_disable_stops_loop_and_joins(self):
        thread = Mock()
        self.tap._thread = thread
        self.tap._run_loop = object()
        self.tap._modifiers.on_flags_changed(55, 0x100008)
        self.tap._modifiers.mark_suppressed(55, True)

        def disable(tap, enabled):
            self.assertIsNone(self.tap._tap)
            self.deliver(kind=self.q.kCGEventTapDisabledByUserInput)

        self.q.CGEventTapEnable.side_effect = disable
        self.tap.stop()
        self.q.CGEventTapEnable.assert_called_once_with(self.native_tap, False)
        self.q.CFRunLoopStop.assert_called_once()
        thread.join.assert_called_once_with(timeout=1.0)
        self.assertEqual(self.tap._modifiers.rewrite_flags(0x100008), 0x100008)

    def test_unknown_flags_changed_key_is_not_sent_to_callback(self):
        event, result = self.deliver(vk=179, kind=self.q.kCGEventFlagsChanged, flags=0x800000)
        self.assertIs(result, event)
        self.callback.assert_not_called()

    def test_run_loop_installs_source_and_disposes_native_tap(self):
        self.q.CFRunLoopRunInMode.side_effect = lambda *args: setattr(self.tap, "_tap", None)
        self.tap._run(self.native_tap, object())
        self.q.CFRunLoopAddSource.assert_called_once()
        self.q.CFRunLoopRunInMode.assert_called_once()
        self.q.CFRunLoopRemoveSource.assert_called_once()
        self.q.CFMachPortInvalidate.assert_called_once_with(self.native_tap)

    def test_source_creation_failure_disposes_tap_and_raises_at_start(self):
        tap = EventTap(self.callback, quartz=self.q)
        self.q.CGEventTapCreate.return_value = self.native_tap
        self.q.CFMachPortCreateRunLoopSource.return_value = None
        with self.assertRaises(OSError):
            tap.start()
        self.assertIsNone(tap._tap)
        self.q.CFMachPortInvalidate.assert_called_once_with(self.native_tap)

    def test_stop_from_worker_skips_self_join(self):
        with patch.object(event_tap, "current_thread", return_value=Mock()) as current:
            self.tap._thread = current.return_value
            self.tap.stop()
            current.return_value.join.assert_not_called()

    def test_stop_still_joins_when_native_disable_raises(self):
        self.tap._thread = Mock()
        self.tap._run_loop = object()
        self.q.CGEventTapEnable.side_effect = RuntimeError("disable failed")
        with self.assertLogs(event_tap.__name__, level="ERROR"):
            self.tap.stop()
        self.q.CFRunLoopStop.assert_called_once()
        self.tap._thread.join.assert_called_once_with(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
