from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend.windows import win32_window


class OwnProcessForegroundTests(unittest.TestCase):
    def setUp(self) -> None:
        win32_window._logged_errors.clear()
        win32_window._user32.cache_clear()
        self.addCleanup(win32_window._user32.cache_clear)

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
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ), patch.object(win32_window.os, "getpid", return_value=42):
            win32_window._user32.cache_clear()
            return win32_window.is_own_process_foreground()

    def test_own_and_other_process_foreground(self):
        own = self._user32(100, 42)
        self.assertTrue(self._check_with_user32(own))
        own.GetForegroundWindow.assert_called_once_with()
        own.GetWindowThreadProcessId.assert_called_once()
        self.assertEqual(own.GetForegroundWindow.argtypes, [])
        self.assertIs(own.GetForegroundWindow.restype, win32_window.wintypes.HWND)
        self.assertEqual(
            own.GetWindowThreadProcessId.argtypes,
            [win32_window.wintypes.HWND, win32_window.ctypes.POINTER(win32_window.wintypes.DWORD)],
        )
        self.assertIs(
            own.GetWindowThreadProcessId.restype, win32_window.wintypes.DWORD,
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
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ), self.assertLogs("keyseq.infrastructure.os_backend.windows.win32_window", level="ERROR") as logs:
            win32_window._user32.cache_clear()
            self.assertFalse(win32_window.is_own_process_foreground())
            self.assertFalse(win32_window.is_own_process_foreground())
        self.assertEqual(len(logs.records), 1)

    def test_unavailable_windll_returns_false(self):
        with patch.object(
            win32_window.ctypes, "WinDLL", side_effect=OSError("unavailable"), create=True
        ):
            self.assertFalse(win32_window.is_own_process_foreground())


class ForegroundOwnWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        win32_window._logged_errors.clear()
        win32_window._user32.cache_clear()
        self.addCleanup(win32_window._user32.cache_clear)

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

    def _check_with_user32(self, user32):
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ), patch.object(win32_window.os, "getpid", return_value=42):
            win32_window._user32.cache_clear()
            return win32_window.foreground_own_window()

    def test_own_process_foreground_returns_handle(self):
        user32 = self._user32(100, 42)
        self.assertEqual(self._check_with_user32(user32), 100)
        user32.GetForegroundWindow.assert_called_once_with()
        user32.GetWindowThreadProcessId.assert_called_once()

    def test_other_process_foreground_returns_none(self):
        self.assertIsNone(self._check_with_user32(self._user32(101, 43)))

    def test_no_foreground_window_returns_none(self):
        for foreground in (None, 0):
            user32 = self._user32(foreground)
            with self.subTest(foreground=foreground):
                self.assertIsNone(self._check_with_user32(user32))
                user32.GetWindowThreadProcessId.assert_not_called()

    def test_exception_returns_none_and_logs_only_once(self):
        user32 = self._user32(100, error=OSError("foreground failed"))
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ), patch.object(win32_window.os, "getpid", return_value=42), self.assertLogs(
            "keyseq.infrastructure.os_backend.windows.win32_window", level="ERROR"
        ) as logs:
            win32_window._user32.cache_clear()
            self.assertIsNone(win32_window.foreground_own_window())
            self.assertIsNone(win32_window.foreground_own_window())
        self.assertEqual(len(logs.records), 1)


class PlaceWindowBelowTests(unittest.TestCase):
    def setUp(self) -> None:
        win32_window._logged_errors.clear()
        win32_window._user32.cache_clear()
        self.addCleanup(win32_window._user32.cache_clear)

    def _check_with_user32(self, user32, hwnd=100, above_hwnd=200):
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ):
            win32_window._user32.cache_clear()
            return win32_window.place_window_below(hwnd, above_hwnd)

    def test_success_passes_handles_and_flags(self):
        user32 = Mock()
        user32.SetWindowPos.return_value = 1
        self.assertTrue(self._check_with_user32(user32))
        self.assertEqual(
            user32.SetWindowPos.call_args.args,
            (100, 200, 0, 0, 0, 0, 0x0013),
        )
        self.assertEqual(
            user32.SetWindowPos.argtypes,
            [
                win32_window.wintypes.HWND, win32_window.wintypes.HWND,
                win32_window.ctypes.c_int, win32_window.ctypes.c_int,
                win32_window.ctypes.c_int, win32_window.ctypes.c_int,
                win32_window.ctypes.c_uint,
            ],
        )
        self.assertIs(user32.SetWindowPos.restype, win32_window.wintypes.BOOL)

    def test_api_false_returns_false(self):
        user32 = Mock()
        user32.SetWindowPos.return_value = 0
        self.assertFalse(self._check_with_user32(user32))

    def test_exception_returns_false_and_logs_only_once(self):
        user32 = Mock()
        user32.SetWindowPos.side_effect = OSError("window placement failed")
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ), self.assertLogs(
            "keyseq.infrastructure.os_backend.windows.win32_window", level="ERROR"
        ) as logs:
            win32_window._user32.cache_clear()
            self.assertFalse(win32_window.place_window_below(100, 200))
            self.assertFalse(win32_window.place_window_below(100, 200))
        self.assertEqual(len(logs.records), 1)

    def test_unavailable_windll_returns_false(self):
        with patch.object(
            win32_window.ctypes, "WinDLL", side_effect=OSError("unavailable"), create=True
        ):
            self.assertFalse(win32_window.place_window_below(100, 200))


class MouseButtonDownTests(unittest.TestCase):
    def setUp(self) -> None:
        win32_window._logged_errors.clear()
        win32_window._user32.cache_clear()
        self.addCleanup(win32_window._user32.cache_clear)

    def _check_with_user32(self, left_state: int, right_state: int) -> bool:
        user32 = Mock()
        user32.GetAsyncKeyState.side_effect = (left_state, right_state)
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ):
            win32_window._user32.cache_clear()
            result = win32_window.is_mouse_button_down()
        self.assertEqual(user32.GetAsyncKeyState.argtypes, [win32_window.ctypes.c_int])
        self.assertIs(user32.GetAsyncKeyState.restype, win32_window.ctypes.c_short)
        return result

    def test_left_button_down(self):
        self.assertTrue(self._check_with_user32(0x8000, 0))

    def test_right_button_down(self):
        self.assertTrue(self._check_with_user32(0, 0x8000))

    def test_no_button_down(self):
        self.assertFalse(self._check_with_user32(0, 0))

    def test_api_exception_returns_false_and_logs_only_once(self):
        user32 = Mock()
        user32.GetAsyncKeyState.side_effect = OSError("mouse state failed")
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=user32, create=True
        ), self.assertLogs("keyseq.infrastructure.os_backend.windows.win32_window", level="ERROR") as logs:
            win32_window._user32.cache_clear()
            self.assertFalse(win32_window.is_mouse_button_down())
            self.assertFalse(win32_window.is_mouse_button_down())
        self.assertEqual(len(logs.records), 1)

    def test_unavailable_windll_returns_false(self):
        with patch.object(
            win32_window.ctypes, "WinDLL", side_effect=OSError("unavailable"), create=True
        ):
            self.assertFalse(win32_window.is_mouse_button_down())


class AppUserModelIdTests(unittest.TestCase):
    def setUp(self) -> None:
        win32_window._logged_errors.clear()

    def _call(self, result=0):
        function = Mock(return_value=result)
        shell32 = Mock(SetCurrentProcessExplicitAppUserModelID=function)
        with patch.object(
            win32_window.ctypes, "WinDLL", return_value=shell32, create=True
        ):
            value = win32_window.set_app_user_model_id("keyseq.app")
        return value, function

    def test_success_and_failure_hresult(self):
        success, function = self._call(0)
        self.assertTrue(success)
        function.assert_called_once_with("keyseq.app")
        self.assertEqual(function.argtypes, [win32_window.wintypes.LPCWSTR])
        self.assertIs(function.restype, win32_window.ctypes.c_long)
        with self.assertLogs("keyseq.infrastructure.os_backend.windows.win32_window", level="WARNING") as logs:
            self.assertFalse(self._call(1)[0])
        self.assertIn("HRESULT=0x00000001", logs.output[0])

    def test_exception_returns_false_and_logs_once(self):
        with patch.object(
            win32_window.ctypes, "WinDLL", side_effect=OSError("failed"), create=True
        ), self.assertLogs("keyseq.infrastructure.os_backend.windows.win32_window", level="ERROR") as logs:
            self.assertFalse(win32_window.set_app_user_model_id("keyseq.app"))
            self.assertFalse(win32_window.set_app_user_model_id("keyseq.app"))
        self.assertEqual(len(logs.records), 1)

    def test_unavailable_windll_returns_false(self):
        with patch.object(
            win32_window.ctypes, "WinDLL", side_effect=OSError("unavailable"), create=True
        ):
            self.assertFalse(win32_window.set_app_user_model_id("keyseq.app"))
