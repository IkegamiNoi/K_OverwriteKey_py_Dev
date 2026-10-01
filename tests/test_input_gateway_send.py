from __future__ import annotations

import unittest
from unittest.mock import Mock, call, patch

from keyseq.infrastructure import input_gateway


class InputGatewaySendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = input_gateway.InputGateway()
        self.events = Mock()
        for name, target in (
            ("send", "keyboard.send"),
            ("press", "keyboard.press"),
            ("release", "keyboard.release"),
            ("ext", "_send_extended_event"),
        ):
            patcher = patch(f"keyseq.infrastructure.input_gateway.{target}")
            mocked = patcher.start()
            self.addCleanup(patcher.stop)
            self.events.attach_mock(mocked, name)

    def test_shift_right(self) -> None:
        self.gateway.send_hotkey("shift+right")
        self.assertEqual(self.events.mock_calls, [
            call.press("shift"),
            call.ext(0x27, 0x4D, key_up=False),
            call.ext(0x27, 0x4D, key_up=True),
            call.release("shift"),
        ])

    def test_ctrl_shift_end(self) -> None:
        self.gateway.send_hotkey("ctrl+shift+end")
        self.assertEqual(self.events.mock_calls, [
            call.press("ctrl"),
            call.press("shift"),
            call.ext(0x23, 0x4F, key_up=False),
            call.ext(0x23, 0x4F, key_up=True),
            call.release("shift"),
            call.release("ctrl"),
        ])

    def test_order_with_leading_extended(self) -> None:
        cases = {
            "right ctrl+c": [
                call.ext(0xA3, 0x1D, key_up=False),
                call.press("c"),
                call.release("c"),
                call.ext(0xA3, 0x1D, key_up=True),
            ],
            "right ctrl+insert": [
                call.ext(0xA3, 0x1D, key_up=False),
                call.ext(0x2D, 0x52, key_up=False),
                call.ext(0x2D, 0x52, key_up=True),
                call.ext(0xA3, 0x1D, key_up=True),
            ],
        }
        for hotkey, expected in cases.items():
            with self.subTest(hotkey=hotkey):
                self.events.reset_mock()
                self.gateway.send_hotkey(hotkey)
                self.assertEqual(self.events.mock_calls, expected)

    def test_non_extended_hotkey(self) -> None:
        for hotkey in ("ctrl+c", "ctrl + c"):
            with self.subTest(hotkey=hotkey):
                self.events.reset_mock()
                self.gateway.send_hotkey(hotkey)
                self.assertEqual(self.events.mock_calls, [call.send(hotkey)])

    def test_individual_keys(self) -> None:
        self.gateway.press_key("right")
        self.gateway.release_key("right")
        self.gateway.press_key("a")
        self.assertEqual(self.events.mock_calls, [
            call.ext(0x27, 0x4D, key_up=False),
            call.ext(0x27, 0x4D, key_up=True),
            call.press("a"),
        ])

    def test_aliases_and_sides(self) -> None:
        cases = {
            "pgup": (0x21, 0x49),
            "del": (0x2E, 0x53),
            "apps": (0x5D, 0x5D),
            "win": (0x5B, 0x5B),
            "windows": (0x5B, 0x5B),
            "left windows": (0x5B, 0x5B),
            "right windows": (0x5C, 0x5C),
            "right ctrl": (0xA3, 0x1D),
            "right alt": (0xA5, 0x38),
            "print screen": (0x2C, 0x37),
            "num lock": (0x90, 0x45),
        }
        for name, (vk, scan) in cases.items():
            with self.subTest(name=name):
                self.events.reset_mock()
                self.assertEqual(input_gateway._resolve_extended_key(name), (vk, scan))
                self.gateway.press_key(name)
                self.gateway.release_key(name)
                self.assertEqual(self.events.mock_calls, [
                    call.ext(vk, scan, key_up=False),
                    call.ext(vk, scan, key_up=True),
                ])

    def test_excluded_keys(self) -> None:
        for name in ("ctrl", "alt", "shift", "enter", "/", "alt gr"):
            with self.subTest(name=name):
                self.events.reset_mock()
                self.assertIsNone(input_gateway._resolve_extended_key(name))
                self.gateway.press_key(name)
                self.gateway.release_key(name)
                self.assertEqual(self.events.mock_calls, [
                    call.press(name), call.release(name),
                ])
        with patch.object(input_gateway.keyboard, "normalize_name", side_effect=ValueError):
            self.assertIsNone(input_gateway._resolve_extended_key("right"))

    def test_cleanup_after_error(self) -> None:
        for fail_on_press, fail_on_release in ((True, False), (True, True), (False, True)):
            with self.subTest(press=fail_on_press, release=fail_on_release):
                self.events.reset_mock(side_effect=True)
                press_error = RuntimeError("press failed")
                release_error = RuntimeError("release failed")
                if fail_on_press:
                    self.events.ext.side_effect = press_error
                if fail_on_release:
                    self.events.release.side_effect = release_error
                with self.assertRaises(RuntimeError) as caught:
                    self.gateway.send_hotkey("ctrl+shift+end")
                self.assertIs(
                    caught.exception, press_error if fail_on_press else release_error
                )
                expected = [
                    call.press("ctrl"),
                    call.press("shift"),
                    call.ext(0x23, 0x4F, key_up=False),
                ]
                if not fail_on_press:
                    expected.append(call.ext(0x23, 0x4F, key_up=True))
                expected.extend([call.release("shift"), call.release("ctrl")])
                self.assertEqual(self.events.mock_calls, expected)

    def test_whitespace(self) -> None:
        self.gateway.send_hotkey("shift + right")
        self.assertEqual(self.events.mock_calls, [
            call.press("shift"),
            call.ext(0x27, 0x4D, key_up=False),
            call.ext(0x27, 0x4D, key_up=True),
            call.release("shift"),
        ])

    def test_write_text_disables_ime_writes_then_schedules_restore(self) -> None:
        reservation = object()
        calls = []
        with patch.object(
            input_gateway.ime_control, "disable_for_text",
            side_effect=lambda: calls.append("disable") or reservation,
        ), patch.object(
            input_gateway.keyboard, "write", side_effect=lambda text: calls.append(("write", text)),
        ), patch.object(
            input_gateway.ime_control, "restore_after_text",
            side_effect=lambda value, count: calls.append(("restore", value, count)),
        ):
            self.gateway.write_text("abc")
        self.assertEqual(calls, [
            "disable", ("write", "abc"), ("restore", reservation, 3),
        ])

    def test_write_text_schedules_restore_when_keyboard_write_raises(self) -> None:
        reservation = object()
        send_error = RuntimeError("keyboard write failed")
        with patch.object(input_gateway.ime_control, "disable_for_text", return_value=reservation), \
             patch.object(input_gateway.keyboard, "write", side_effect=send_error), \
             patch.object(input_gateway.ime_control, "restore_after_text") as restore:
            with self.assertRaisesRegex(RuntimeError, "keyboard write failed"):
                self.gateway.write_text("text")
        restore.assert_called_once_with(reservation, 4)

    def test_write_text_continues_after_ime_timeout_fallback(self) -> None:
        with patch.object(input_gateway.ime_control, "disable_for_text", return_value=None), \
             patch.object(input_gateway.keyboard, "write") as write, \
             patch.object(input_gateway.ime_control, "restore_after_text") as restore:
            self.gateway.write_text("text")
        write.assert_called_once_with("text")
        restore.assert_called_once_with(None, 4)

    def test_empty_write_does_not_touch_ime(self) -> None:
        with patch.object(input_gateway.ime_control, "disable_for_text") as disable, \
             patch.object(input_gateway.ime_control, "restore_after_text") as restore, \
             patch.object(input_gateway.keyboard, "write") as write:
            self.gateway.write_text("")
        write.assert_called_once_with("")
        disable.assert_not_called()
        restore.assert_not_called()

    def test_restore_ime_now_delegates(self) -> None:
        with patch.object(input_gateway.ime_control, "restore_ime_now") as restore:
            self.gateway.restore_ime_now()
        restore.assert_called_once_with()

    def test_restore_ime_now_logs_failure(self) -> None:
        with patch.object(input_gateway.ime_control, "restore_ime_now",
                          side_effect=OSError("restore failed")), self.assertLogs(
            "keyseq.infrastructure.input_gateway", level="ERROR",
        ):
            self.gateway.restore_ime_now()


class InputGatewayExtendedFlagTests(unittest.TestCase):
    def test_extended_key_flags(self) -> None:
        with patch.object(input_gateway, "ctypes") as mock_ctypes:
            gateway = input_gateway.InputGateway()
            gateway.press_key("right")
            gateway.release_key("right")
            self.assertEqual(mock_ctypes.windll.user32.keybd_event.call_args_list, [
                call(0x27, 0x4D, 0x0001, 0),
                call(0x27, 0x4D, 0x0003, 0),
            ])
