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
