"""Side-specific physical modifier and paired suppression decisions."""
from __future__ import annotations

from .key_table import COMMON_FLAGS, MODIFIERS


class ModifierState:
    def __init__(self) -> None:
        self._pressed: set[int] = set()
        self._suppressed: set[int] = set()

    def on_flags_changed(self, keycode: int, flags: int) -> tuple[str, ...] | None:
        modifier = MODIFIERS.get(keycode)
        if modifier is None:
            return None
        down = bool(flags & modifier[2])
        if down:
            self._pressed.add(keycode)
        else:
            self._pressed.discard(keycode)
        return ("down" if down else "up",)

    def mark_suppressed(self, key: int, suppressed: bool) -> bool:
        """Record a down decision, or consume the paired decision on release."""
        if key in self._pressed:
            if suppressed:
                self._suppressed.add(key)
            else:
                self._suppressed.discard(key)
            return suppressed
        paired = key in self._suppressed
        self._suppressed.discard(key)
        return paired

    def physical_modifiers(self) -> frozenset[int]:
        return frozenset(self._pressed - self._suppressed)

    def rewrite_flags(self, flags: int, physical: set[int] | frozenset[int], sent: set[int] | frozenset[int]) -> int:
        if not self._suppressed and not sent:
            return flags
        return modifier_flags(physical | sent, base=flags)

    def clear(self) -> None:
        self._pressed.clear()
        self._suppressed.clear()


def modifier_flags(keys: set[int] | frozenset[int], base: int = 0) -> int:
    """base の修飾ビットを消し、keys（左右別の修飾 vk）のビットだけを立てる（暫定 57 §5.1）。"""
    flags = base
    for common in COMMON_FLAGS.values():
        flags &= ~common
    for key, (kind, _side, bit) in MODIFIERS.items():
        flags &= ~bit
        if key in keys:
            flags |= bit | COMMON_FLAGS[kind]
    return flags
