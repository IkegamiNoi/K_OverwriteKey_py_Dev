from __future__ import annotations

import ctypes
import logging
import sys
from typing import cast


_logger = logging.getLogger(__name__)
_UNINITIALIZED = object()
_api: _Win32OwnImeApi | None | object = _UNINITIALIZED


class _Win32OwnImeApi:
    """Thin wrapper around the current thread's IMM context APIs."""

    def __init__(self) -> None:
        win_dll = getattr(ctypes, "WinDLL", None)
        if not sys.platform.startswith("win") or win_dll is None:
            raise OSError("Win32 IME APIs are unavailable")
        self._imm32 = win_dll("imm32", use_last_error=True)
        self._imm32.ImmGetContext.argtypes = [ctypes.c_void_p]
        self._imm32.ImmGetContext.restype = ctypes.c_void_p
        self._imm32.ImmReleaseContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._imm32.ImmReleaseContext.restype = ctypes.c_int
        self._imm32.ImmGetOpenStatus.argtypes = [ctypes.c_void_p]
        self._imm32.ImmGetOpenStatus.restype = ctypes.c_int
        self._imm32.ImmSetOpenStatus.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._imm32.ImmSetOpenStatus.restype = ctypes.c_int

    def get_context(self, hwnd: int) -> int | None:
        context = self._imm32.ImmGetContext(hwnd)
        return int(context) if context else None

    def release_context(self, hwnd: int, context: int) -> None:
        self._imm32.ImmReleaseContext(hwnd, context)

    def get_open_status(self, context: int) -> bool:
        return bool(self._imm32.ImmGetOpenStatus(context))

    def set_open_status(self, context: int, is_open: bool) -> bool:
        return bool(self._imm32.ImmSetOpenStatus(context, int(is_open)))


def _get_api() -> _Win32OwnImeApi | None:
    global _api
    if _api is _UNINITIALIZED:
        try:
            _api = _Win32OwnImeApi()
        except OSError as exc:
            _logger.warning("Win32 IME APIs are unavailable: %s", exc)
            _api = None
        except Exception:
            _logger.exception("Failed to initialize Win32 IME APIs")
            _api = None
    return cast(_Win32OwnImeApi | None, _api)


def get_open_status(hwnd: int) -> bool | None:
    api = _get_api()
    if api is None:
        return None
    context: int | None = None
    try:
        context = api.get_context(hwnd)
        if not context:
            return None
        return api.get_open_status(context)
    except Exception:
        _logger.exception("Failed to read the application's IME status")
        return None
    finally:
        if context:
            try:
                api.release_context(hwnd, context)
            except Exception:
                _logger.exception("Failed to release the application's IME context")


def set_open_status(hwnd: int, is_open: bool) -> bool:
    api = _get_api()
    if api is None:
        return False
    context: int | None = None
    try:
        context = api.get_context(hwnd)
        if not context:
            return False
        return api.set_open_status(context, is_open)
    except Exception:
        _logger.exception("Failed to change the application's IME status")
        return False
    finally:
        if context:
            try:
                api.release_context(hwnd, context)
            except Exception:
                _logger.exception("Failed to release the application's IME context")
