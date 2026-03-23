from __future__ import annotations

import threading
from typing import Iterable

from keyseq.domain.config import normalize_key_name


_MODIFIER_ALIASES = {
    "shift": "shift",
    "shift_l": "shift",
    "shift_r": "shift",
    "left shift": "shift",
    "right shift": "shift",
    "ctrl": "ctrl",
    "control": "ctrl",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "control_l": "ctrl",
    "control_r": "ctrl",
    "left ctrl": "ctrl",
    "right ctrl": "ctrl",
    "left control": "ctrl",
    "right control": "ctrl",
    "alt": "alt",
    "alt_l": "alt",
    "alt_r": "alt",
    "left alt": "alt",
    "right alt": "alt",
    "alt gr": "alt",
    "windows": "windows",
    "win": "windows",
    "left windows": "windows",
    "right windows": "windows",
    "left win": "windows",
    "right win": "windows",
    "super": "windows",
    "super_l": "windows",
    "super_r": "windows",
    "left super": "windows",
    "right super": "windows",
    "command": "windows",
    "cmd": "windows",
}

class KeyStateManager:
    def __init__(self, *, resolve_scan_code=None) -> None:
        self._pressed_keys: set[str] = set()
        self._lock = threading.RLock()
        self._resolve_scan_code = resolve_scan_code

    @property
    def pressed_keys(self) -> frozenset[str]:
        with self._lock:
            return frozenset(self._pressed_keys)

    def clear(self) -> None:
        with self._lock:
            self._pressed_keys.clear()

    def handle_event(self, event: object) -> None:
        key = self._extract_key_name(event)
        if not key:
            return

        event_type = normalize_key_name(str(getattr(event, "event_type", "")))
        if event_type == "down":
            self.key_down(key)
        elif event_type == "up":
            self.key_up(key)

    def key_down(self, key: str) -> None:
        normalized = self._normalize_key(key)
        if not normalized:
            return
        with self._lock:
            self._pressed_keys.add(normalized)

    def key_up(self, key: str) -> None:
        normalized = self._normalize_key(key)
        if not normalized:
            return
        with self._lock:
            self._pressed_keys.discard(normalized)

    def is_pressed(self, key: str) -> bool:
        normalized = self._normalize_key(key)
        if not normalized:
            return False
        with self._lock:
            return normalized in self._pressed_keys

    def _extract_key_name(self, event: object) -> str:
        candidates: Iterable[object] = (
            getattr(event, "name", ""),
            getattr(event, "key", ""),
        )
        for candidate in candidates:
            normalized = self._normalize_key(candidate)
            if normalized:
                return normalized
        if callable(self._resolve_scan_code):
            normalized = self._normalize_key(self._resolve_scan_code(getattr(event, "scan_code", None)))
            if normalized:
                return normalized
        return ""

    def _normalize_key(self, key: object) -> str:
        normalized = normalize_key_name(str(key or ""))
        if not normalized:
            return ""
        return _MODIFIER_ALIASES.get(normalized, normalized)
