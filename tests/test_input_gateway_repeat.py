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
