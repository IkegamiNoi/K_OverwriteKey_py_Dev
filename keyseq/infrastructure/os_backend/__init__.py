from __future__ import annotations

import sys
import threading

from .contracts import AppIdentity, Capabilities, ImeBackend, OsBackend, TkKeyTranslator, WindowBackend

__all__ = ["AppIdentity", "Capabilities", "ImeBackend", "OsBackend", "TkKeyTranslator", "WindowBackend", "get_backend"]

_backend: OsBackend | None = None
_backend_lock = threading.Lock()


def get_backend() -> OsBackend:
    global _backend
    with _backend_lock:
        if _backend is None:
            if sys.platform == "win32":
                from keyseq.infrastructure.os_backend.windows.backend import create_backend
                _backend = create_backend()
            else:
                raise RuntimeError(f"Unsupported operating system: {sys.platform}")
        return _backend
