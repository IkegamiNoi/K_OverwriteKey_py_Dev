"""⑭: App を生成せず、バックエンド経由の前面判定を検査する。"""

import ctypes
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation import modal


class ModalAppForegroundTest(unittest.TestCase):
    def _window_backend(self, foreground=0x1234, handle=0x1234):
        return Mock(
            foreground_own_window=Mock(return_value=foreground),
            window_handle=Mock(return_value=handle),
        )

    def test_matching_hwnd_is_foreground(self):
        app = Mock()
        window = self._window_backend()
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertTrue(modal._is_app_foreground(app))
        window.foreground_own_window.assert_called_once_with()
        window.window_handle.assert_called_once_with(app)

    def test_different_hwnd_is_not_foreground(self):
        app = Mock()
        window = self._window_backend(foreground=0x5678)
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertFalse(modal._is_app_foreground(app))

    def test_high_bit_hwnd_is_foreground(self):
        app = Mock()
        window = self._window_backend(foreground=0x80001234, handle=0x80001234)
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertTrue(modal._is_app_foreground(app))

    def test_null_hwnd_is_not_foreground(self):
        app = Mock()
        window = self._window_backend(foreground=None)
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertFalse(modal._is_app_foreground(app))
        window.window_handle.assert_not_called()

    def test_foreground_oserror_is_not_foreground(self):
        app = Mock()
        window = self._window_backend()
        window.foreground_own_window.side_effect = OSError
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertFalse(modal._is_app_foreground(app))

    def test_frame_tclerror_is_not_foreground(self):
        app = Mock()
        window = self._window_backend()
        window.window_handle.side_effect = tk.TclError
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertFalse(modal._is_app_foreground(app))

    def test_modal_does_not_call_win32_ffi(self):
        app = Mock()
        window = self._window_backend()
        with patch.object(modal, "get_backend", return_value=Mock(window=window)), patch.object(
            ctypes, "WinDLL", side_effect=AssertionError("modal must use the backend"), create=True
        ):
            self.assertTrue(modal._is_app_foreground(app))

    def test_backend_window_handle_is_used(self):
        app = Mock()
        window = self._window_backend(foreground=0x80001234, handle=0x80001234)
        with patch.object(modal, "get_backend", return_value=Mock(window=window)):
            self.assertTrue(modal._is_app_foreground(app))
        window.window_handle.assert_called_once_with(app)
