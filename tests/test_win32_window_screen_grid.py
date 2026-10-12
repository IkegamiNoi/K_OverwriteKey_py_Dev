from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure import win32_window


class Win32ScreenGridTests(unittest.TestCase):
    def setUp(self) -> None:
        win32_window._logged_errors.clear()
        win32_window._user32.cache_clear()
        win32_window._kernel32.cache_clear()
        self.addCleanup(win32_window._user32.cache_clear)
        self.addCleanup(win32_window._kernel32.cache_clear)

    def _run_win32(self, user32, operation):
        with patch.object(win32_window.sys, "platform", "win32"), patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ):
            win32_window._user32.cache_clear()
            return operation()

    def test_list_monitor_rects_returns_bounds_and_primary_flag(self) -> None:
        user32 = Mock()

        def get_monitor_info(_handle, info_pointer):
            info = info_pointer._obj
            info.rcMonitor.left = -1920
            info.rcMonitor.top = 0
            info.rcMonitor.right = 0
            info.rcMonitor.bottom = 1080
            info.dwFlags = win32_window.MONITORINFOF_PRIMARY
            return 1

        def enumerate(_hdc, _clip, callback, _data):
            self.assertTrue(callback(100, None, None, 0))
            return 1

        user32.GetMonitorInfoW.side_effect = get_monitor_info
        user32.EnumDisplayMonitors.side_effect = enumerate
        result = self._run_win32(user32, win32_window.list_monitor_rects)

        self.assertEqual(result, [((-1920, 0, 0, 1080), True)])
        self.assertEqual(
            user32.EnumDisplayMonitors.argtypes,
            [
                win32_window.wintypes.HDC,
                win32_window.ctypes.POINTER(win32_window.wintypes.RECT),
                user32.EnumDisplayMonitors.argtypes[2],
                win32_window.ctypes.c_ssize_t,
            ],
        )

    def test_monitor_enumeration_api_failure_returns_empty(self) -> None:
        user32 = Mock()
        user32.EnumDisplayMonitors.return_value = 0
        self.assertEqual(
            self._run_win32(user32, win32_window.list_monitor_rects), []
        )

    def test_monitor_info_failure_returns_empty(self) -> None:
        user32 = Mock()

        def enumerate(_hdc, _clip, callback, _data):
            callback(100, None, None, 0)
            return 1

        user32.EnumDisplayMonitors.side_effect = enumerate
        user32.GetMonitorInfoW.return_value = 0
        self.assertEqual(
            self._run_win32(user32, win32_window.list_monitor_rects), []
        )

    def test_monitor_info_exception_returns_empty_and_logs(self) -> None:
        user32 = Mock()

        def enumerate(_hdc, _clip, callback, _data):
            callback(100, None, None, 0)
            return 1

        user32.EnumDisplayMonitors.side_effect = enumerate
        user32.GetMonitorInfoW.side_effect = OSError("monitor info failed")
        with self.assertLogs("keyseq.infrastructure.win32_window", level="ERROR"):
            self.assertEqual(
                self._run_win32(user32, win32_window.list_monitor_rects), []
            )

    def test_monitor_api_exception_returns_empty(self) -> None:
        user32 = Mock()
        user32.EnumDisplayMonitors.side_effect = OSError("enumeration failed")
        with self.assertLogs("keyseq.infrastructure.win32_window", level="ERROR"):
            self.assertEqual(
                self._run_win32(user32, win32_window.list_monitor_rects), []
            )

    def test_non_windows_does_not_load_user32(self) -> None:
        with patch.object(win32_window.sys, "platform", "linux"), patch.object(
            win32_window.ctypes, "WinDLL", create=True
        ) as load_user32:
            self.assertEqual(win32_window.list_monitor_rects(), [])
            self.assertFalse(win32_window.make_click_through_overlay(10))
        load_user32.assert_not_called()

    def test_vk_to_scan_code_uses_map_virtual_key_and_returns_none_on_failure(self) -> None:
        user32 = Mock()
        user32.MapVirtualKeyW.return_value = 0x1E
        self.assertEqual(self._run_win32(user32, lambda: win32_window.vk_to_scan_code(0x41)), 0x1E)
        user32.MapVirtualKeyW.assert_called_once_with(0x41, win32_window.MAPVK_VK_TO_VSC)

        user32.MapVirtualKeyW.return_value = 0
        self.assertIsNone(self._run_win32(user32, lambda: win32_window.vk_to_scan_code(0x41)))

        broken = Mock()
        broken.MapVirtualKeyW.side_effect = OSError("mapping failed")
        with self.assertLogs("keyseq.infrastructure.win32_window", level="ERROR"):
            self.assertIsNone(self._run_win32(broken, lambda: win32_window.vk_to_scan_code(0x41)))

    def test_vk_to_char_returns_unshifted_char_and_empty_on_failure(self) -> None:
        user32 = Mock()
        user32.MapVirtualKeyW.return_value = ord(".")
        self.assertEqual(self._run_win32(user32, lambda: win32_window.vk_to_char(0xBE)), ".")
        user32.MapVirtualKeyW.assert_called_once_with(0xBE, win32_window.MAPVK_VK_TO_CHAR)

        user32.MapVirtualKeyW.return_value = 0x80000000 | ord("^")
        self.assertEqual(self._run_win32(user32, lambda: win32_window.vk_to_char(0xDE)), "^")

        for code in (0, 0x20):
            user32.MapVirtualKeyW.return_value = code
            self.assertEqual(self._run_win32(user32, lambda: win32_window.vk_to_char(0x74)), "")

        broken = Mock()
        broken.MapVirtualKeyW.side_effect = OSError("mapping failed")
        with self.assertLogs("keyseq.infrastructure.win32_window", level="ERROR"):
            self.assertEqual(self._run_win32(broken, lambda: win32_window.vk_to_char(0xBE)), "")

    def test_click_through_overlay_adds_extended_styles(self) -> None:
        user32 = Mock()
        user32.GetParent.return_value = 200
        user32.GetWindowLongPtrW.return_value = 0
        user32.SetWindowLongPtrW.return_value = 0
        with patch.object(win32_window, "_clear_last_error"), patch.object(
            win32_window, "_last_error", return_value=0
        ):
            result = self._run_win32(
                user32, lambda: win32_window.make_click_through_overlay(100)
            )

        styles = (
            win32_window.WS_EX_LAYERED
            | win32_window.WS_EX_TRANSPARENT
            | win32_window.WS_EX_NOACTIVATE
            | win32_window.WS_EX_TOOLWINDOW
        )
        self.assertTrue(result)
        user32.GetParent.assert_called_once_with(100)
        user32.GetWindowLongPtrW.assert_called_once_with(200, win32_window.GWL_EXSTYLE)
        user32.SetWindowLongPtrW.assert_called_once_with(
            200, win32_window.GWL_EXSTYLE, styles
        )

    def test_click_through_false_return_and_exception_return_false(self) -> None:
        failed = Mock()
        failed.GetParent.return_value = 200
        failed.GetWindowLongPtrW.return_value = 16
        failed.SetWindowLongPtrW.return_value = 0
        with patch.object(win32_window, "_clear_last_error"), patch.object(
            win32_window, "_last_error", return_value=5
        ):
            self.assertFalse(self._run_win32(
                failed, lambda: win32_window.make_click_through_overlay(100)
            ))

        broken = Mock()
        broken.GetParent.side_effect = OSError("parent failed")
        with self.assertLogs("keyseq.infrastructure.win32_window", level="ERROR"):
            self.assertFalse(self._run_win32(
                broken, lambda: win32_window.make_click_through_overlay(100)
            ))

    def test_click_through_zero_get_style_with_error_returns_false(self) -> None:
        user32 = Mock()
        user32.GetParent.return_value = 200
        user32.GetWindowLongPtrW.return_value = 0
        with patch.object(win32_window, "_clear_last_error"), patch.object(
            win32_window, "_last_error", return_value=5
        ):
            self.assertFalse(self._run_win32(
                user32, lambda: win32_window.make_click_through_overlay(100)
            ))
        user32.SetWindowLongPtrW.assert_not_called()

    def test_click_through_without_parent_returns_false(self) -> None:
        user32 = Mock()
        user32.GetParent.return_value = 0
        self.assertFalse(self._run_win32(
            user32, lambda: win32_window.make_click_through_overlay(100)
        ))
        user32.GetWindowLongPtrW.assert_not_called()
        user32.SetWindowLongPtrW.assert_not_called()
