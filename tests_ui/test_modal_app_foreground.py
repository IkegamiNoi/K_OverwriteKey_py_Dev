"""⑭: App を生成せず、前面判定と専用 Win32 関数の型契約を検査する。"""

import ctypes
import ctypes.wintypes
import sys
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation import modal


class ModalAppForegroundTest(unittest.TestCase):
    def test_matching_hwnd_is_foreground(self):
        app = Mock(wm_frame=Mock(return_value="0x1234"))
        with patch.object(modal, "_foreground_window_fn", return_value=Mock(return_value=0x1234)):
            self.assertTrue(modal._is_app_foreground(app))

    def test_different_hwnd_is_not_foreground(self):
        app = Mock(wm_frame=Mock(return_value="0x1234"))
        with patch.object(modal, "_foreground_window_fn", return_value=Mock(return_value=0x5678)):
            self.assertFalse(modal._is_app_foreground(app))

    def test_high_bit_hwnd_is_foreground(self):
        app = Mock(wm_frame=Mock(return_value="0x80001234"))
        with patch.object(modal, "_foreground_window_fn", return_value=Mock(return_value=0x80001234)):
            self.assertTrue(modal._is_app_foreground(app))

    def test_null_hwnd_is_not_foreground(self):
        app = Mock(wm_frame=Mock(return_value="0x1234"))
        with patch.object(modal, "_foreground_window_fn", return_value=Mock(return_value=None)):
            self.assertFalse(modal._is_app_foreground(app))

    def test_foreground_oserror_is_not_foreground(self):
        app = Mock(wm_frame=Mock(return_value="0x1234"))
        with patch.object(modal, "_foreground_window_fn", return_value=Mock(side_effect=OSError)):
            self.assertFalse(modal._is_app_foreground(app))

    def test_frame_tclerror_is_not_foreground(self):
        app = Mock(wm_frame=Mock(side_effect=tk.TclError))
        with patch.object(modal, "_foreground_window_fn", return_value=Mock(return_value=0x1234)):
            self.assertFalse(modal._is_app_foreground(app))

    @unittest.skipUnless(sys.platform == "win32", "Win32 FFI の型契約")
    def test_function_has_hwnd_signature(self):
        modal._foreground_window_fn.cache_clear()
        self.addCleanup(modal._foreground_window_fn.cache_clear)
        function = modal._foreground_window_fn()
        self.assertIs(function.restype, ctypes.wintypes.HWND)
        self.assertEqual(function.argtypes, [])

    @unittest.skipUnless(sys.platform == "win32", "共有 Win32 関数との分離")
    def test_function_does_not_change_shared_restype(self):
        shared = ctypes.windll.user32.GetForegroundWindow
        original_restype = shared.restype
        modal._foreground_window_fn.cache_clear()
        self.addCleanup(modal._foreground_window_fn.cache_clear)
        function = modal._foreground_window_fn()
        self.assertIs(shared.restype, original_restype)
        self.assertIsNot(function, shared)
