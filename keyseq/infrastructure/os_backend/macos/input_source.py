"""遅延ロードする Carbon/CoreFoundation の入力ソース API。"""
from __future__ import annotations

import ctypes
import ctypes.util


class InputSourceAPI:
    def __init__(self) -> None:
        carbon_path = ctypes.util.find_library("Carbon") or "/System/Library/Frameworks/Carbon.framework/Carbon"
        cf_path = ctypes.util.find_library("CoreFoundation") or "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        self._carbon = ctypes.CDLL(carbon_path)
        self._cf = ctypes.CDLL(cf_path)
        self._bind_functions()

    def _bind_functions(self) -> None:
        c, f = self._carbon, self._cf
        c.TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
        c.TISCopyCurrentKeyboardInputSource.argtypes = []
        c.TISCopyCurrentASCIICapableKeyboardInputSource.restype = ctypes.c_void_p
        c.TISCopyCurrentASCIICapableKeyboardInputSource.argtypes = []
        c.TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        c.TISGetInputSourceProperty.restype = ctypes.c_void_p
        c.TISSelectInputSource.argtypes = [ctypes.c_void_p]
        c.TISSelectInputSource.restype = ctypes.c_int32
        f.CFBooleanGetValue.argtypes = [ctypes.c_void_p]
        f.CFBooleanGetValue.restype = ctypes.c_bool
        f.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
        f.CFStringGetCString.restype = ctypes.c_bool
        f.CFRelease.argtypes = [ctypes.c_void_p]
        f.CFRelease.restype = None
        self._ascii_property = ctypes.c_void_p.in_dll(c, "kTISPropertyInputSourceIsASCIICapable")
        self._id_property = ctypes.c_void_p.in_dll(c, "kTISPropertyInputSourceID")

    def current(self): return self._carbon.TISCopyCurrentKeyboardInputSource()
    def ascii_source(self): return self._carbon.TISCopyCurrentASCIICapableKeyboardInputSource()
    def select(self, source) -> int: return int(self._carbon.TISSelectInputSource(source))
    def release(self, source) -> None:
        if source: self._cf.CFRelease(source)

    def is_ascii_capable(self, source) -> bool | None:
        value = self._carbon.TISGetInputSourceProperty(source, self._ascii_property)
        return None if not value else bool(self._cf.CFBooleanGetValue(value))

    def source_id(self, source) -> str | None:
        value = self._carbon.TISGetInputSourceProperty(source, self._id_property)
        if not value: return None
        buffer = ctypes.create_string_buffer(1024)
        if not self._cf.CFStringGetCString(value, buffer, len(buffer), 0x08000100): return None
        return buffer.value.decode("utf-8")
