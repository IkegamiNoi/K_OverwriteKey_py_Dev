"""In-memory clipboard shared by presentation list views."""

from __future__ import annotations

from collections.abc import Sequence

from keyseq.domain.config import safe_deepcopy


CLIP_ACTIONS = "actions"
CLIP_TRIGGERS = "trigger_rows"
CLIP_KEYMAPS = "keymap_rows"


class ListClipboard:
    """Keep a detached copy of items from one kind of list."""

    def __init__(self) -> None:
        self._kind: str | None = None
        self._items: list[dict] | None = None

    def copy(self, kind: str, items: Sequence[dict]) -> None:
        self._kind = kind
        self._items = safe_deepcopy(list(items))

    def paste(self, kind: str) -> list[dict] | None:
        if kind != self._kind or self._items is None:
            return None
        return safe_deepcopy(self._items)

    def clear(self) -> None:
        self._kind = None
        self._items = None
