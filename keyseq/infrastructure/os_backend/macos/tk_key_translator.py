from __future__ import annotations

import logging

from .key_table import MacKey, key_for_vk
from .keyboard_backend import MacKeyboardBackend


_LOG = logging.getLogger(__name__)


class MacTkKeyTranslator:
    def __init__(self, keyboard: MacKeyboardBackend) -> None:
        self._keyboard = keyboard

    def _key(self, keycode: object) -> MacKey | None:
        if not isinstance(keycode, int) or isinstance(keycode, bool):
            return None
        vk = (keycode >> 24) & 0xFF
        if vk == 0xFF:
            return None
        return key_for_vk(vk, jis=self._keyboard._jis)

    def numpad_name(self, keycode: object, state: object) -> str:
        key = self._key(keycode)
        return key.name if key is not None and key.is_keypad else ""

    def vk_to_scan_code(self, vk: int) -> int | None:
        key = self._key(vk)
        return key.scan_code if key is not None else None

    def vk_to_char(self, vk: int) -> str:
        key = self._key(vk)
        return key.name if key is not None and len(key.name) == 1 else ""

    def modifier_name(self, keysym: str, *, sided: bool) -> str | None:
        key = (keysym or "").lower()
        if key in {"super_l", "super_r"}:
            return "??"
        names = {
            "control_l": ("ctrl", "left ctrl"),
            "control_r": ("ctrl", "right ctrl"),
            "shift_l": ("shift", "left shift"),
            "shift_r": ("shift", "right shift"),
            "meta_l": ("command", "left command"),
            "meta_r": ("command", "right command"),
            "alt_l": ("option", "left option"),
            "alt_r": ("option", "right option"),
        }
        result = names.get(key)
        return result[1 if sided else 0] if result is not None else None
