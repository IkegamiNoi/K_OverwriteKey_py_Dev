from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure import input_gateway


class RepeatTimingConversionTests(unittest.TestCase):
    def test_delay_conversion(self):
        for value, expected in ((0, 250), (1, 500), (3, 1000)):
            with self.subTest(value=value):
                self.assertEqual(input_gateway.repeat_delay_ms(value), expected)
        for value in (-1, 4):
            with self.subTest(value=value):
                self.assertIsNone(input_gateway.repeat_delay_ms(value))

    def test_interval_conversion(self):
        for value, expected in ((0, 400), (15, 63), (31, 33)):
            with self.subTest(value=value):
                self.assertEqual(input_gateway.repeat_interval_ms(value), expected)
        for value in (-1, 32):
            with self.subTest(value=value):
                self.assertIsNone(input_gateway.repeat_interval_ms(value))


class KeyboardRepeatTimingTests(unittest.TestCase):
    def _user32(self, delay: int, speed: int, *, delay_result: int = 1, speed_result: int = 1):
        user32 = Mock()

        def read_setting(action, _parameter, value_pointer, _flags):
            if action == input_gateway._SPI_GETKEYBOARDDELAY:
                if delay_result:
                    value_pointer._obj.value = delay
                return delay_result
            if speed_result:
                value_pointer._obj.value = speed
            return speed_result

        user32.SystemParametersInfoW.side_effect = read_setting
        return user32

    def test_reads_and_converts_windows_settings(self):
        user32 = self._user32(2, 15)
        with patch.object(input_gateway.sys, "platform", "win32"), patch.object(
            input_gateway.ctypes, "windll", Mock(user32=user32), create=True
        ):
            self.assertEqual(input_gateway.keyboard_repeat_timing(), (750, 63))
        self.assertEqual(user32.SystemParametersInfoW.call_count, 2)

    def test_failed_setting_uses_its_default_independently(self):
        cases = (
            (0, 15, (500, 63)),
            (2, 0, (750, 33)),
        )
        for delay_result, speed_result, expected in cases:
            user32 = self._user32(
                2, 15, delay_result=delay_result, speed_result=speed_result
            )
            with self.subTest(expected=expected), patch.object(
                input_gateway.sys, "platform", "win32"
            ), patch.object(input_gateway.ctypes, "windll", Mock(user32=user32), create=True):
                self.assertEqual(input_gateway.keyboard_repeat_timing(), expected)

    def test_out_of_range_setting_uses_default(self):
        user32 = self._user32(4, 32)
        with patch.object(input_gateway.sys, "platform", "win32"), patch.object(
            input_gateway.ctypes, "windll", Mock(user32=user32), create=True
        ):
            self.assertEqual(input_gateway.keyboard_repeat_timing(), (500, 33))

    def test_api_exception_uses_defaults(self):
        user32 = Mock()

        def read_setting(action, _parameter, value_pointer, _flags):
            if action == input_gateway._SPI_GETKEYBOARDDELAY:
                raise OSError("delay failed")
            value_pointer._obj.value = 15
            return 1

        user32.SystemParametersInfoW.side_effect = read_setting
        with patch.object(input_gateway.sys, "platform", "win32"), patch.object(
            input_gateway.ctypes, "windll", Mock(user32=user32), create=True
        ):
            self.assertEqual(input_gateway.keyboard_repeat_timing(), (500, 63))

    def test_non_windows_uses_defaults_without_calling_api(self):
        user32 = self._user32(0, 0)
        with patch.object(input_gateway.sys, "platform", "linux"), patch.object(
            input_gateway.ctypes, "windll", Mock(user32=user32), create=True
        ):
            self.assertEqual(input_gateway.keyboard_repeat_timing(), (500, 33))
        user32.SystemParametersInfoW.assert_not_called()


class OwnProcessForegroundTests(unittest.TestCase):
    def setUp(self) -> None:
        input_gateway._foreground_error_logged = False
        input_gateway._foreground_process_api.cache_clear()
        self.addCleanup(input_gateway._foreground_process_api.cache_clear)

    def _user32(self, foreground, process_id: int = 42, *, error=None):
        user32 = Mock()
        user32.GetForegroundWindow.return_value = foreground

        def get_process_id(_window, process_id_pointer):
            if error is not None:
                raise error
            process_id_pointer._obj.value = process_id
            return 1

        user32.GetWindowThreadProcessId.side_effect = get_process_id
        return user32

    def _check_with_user32(self, user32) -> bool:
        with patch.object(input_gateway.sys, "platform", "win32"), patch.object(
            input_gateway.ctypes, "WinDLL", return_value=user32, create=True
        ), patch.object(input_gateway.os, "getpid", return_value=42):
            input_gateway._foreground_process_api.cache_clear()
            return input_gateway.is_own_process_foreground()

    def test_own_and_other_process_foreground(self):
        own = self._user32(100, 42)
        self.assertTrue(self._check_with_user32(own))
        own.GetForegroundWindow.assert_called_once_with()
        own.GetWindowThreadProcessId.assert_called_once()
        self.assertEqual(own.GetForegroundWindow.argtypes, [])
        self.assertIs(own.GetForegroundWindow.restype, input_gateway.wintypes.HWND)
        self.assertEqual(
            own.GetWindowThreadProcessId.argtypes,
            [input_gateway.wintypes.HWND, input_gateway.ctypes.POINTER(input_gateway.wintypes.DWORD)],
        )
        self.assertIs(
            own.GetWindowThreadProcessId.restype, input_gateway.wintypes.DWORD,
        )
        self.assertFalse(self._check_with_user32(self._user32(101, 43)))

    def test_null_foreground_window_blocks(self):
        for foreground in (None, 0):
            user32 = self._user32(foreground)
            with self.subTest(foreground=foreground):
                self.assertTrue(self._check_with_user32(user32))
                user32.GetWindowThreadProcessId.assert_not_called()

    def test_zero_process_id_does_not_block(self):
        self.assertFalse(self._check_with_user32(self._user32(100, 0)))

    def test_win32_exception_returns_false_and_logs_only_once(self):
        user32 = self._user32(100, error=OSError("foreground failed"))
        with patch.object(input_gateway.sys, "platform", "win32"), patch.object(
            input_gateway.ctypes, "WinDLL", return_value=user32, create=True
        ), self.assertLogs("keyseq.infrastructure.input_gateway", level="ERROR") as logs:
            input_gateway._foreground_process_api.cache_clear()
            self.assertFalse(input_gateway.is_own_process_foreground())
            self.assertFalse(input_gateway.is_own_process_foreground())
        self.assertEqual(len(logs.records), 1)

    def test_non_windows_does_not_load_user32(self):
        with patch.object(input_gateway.sys, "platform", "linux"), patch.object(
            input_gateway.ctypes, "WinDLL", create=True
        ) as load_user32:
            self.assertFalse(input_gateway.is_own_process_foreground())
        load_user32.assert_not_called()
