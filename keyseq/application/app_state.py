from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    selected_trigger_idx: int = 0
    selected_trigger_indices: dict[str, int] = field(default_factory=dict)
    indices: dict[str, int] = field(default_factory=dict)
    keymap_indices: dict[str, dict[str, int]] = field(default_factory=dict)

    run_to_end_key: str | None = None
    run_to_end_paused: bool = False
    run_to_end_after_id: Any = None

    lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    reentry_guard: set[str] = field(default_factory=set, init=False)

    def reset_indices(self) -> None:
        self.indices = {}
        self.keymap_indices = {}
        self.selected_trigger_indices = {}
        self.selected_trigger_idx = 0

    def update_selected_index(self, value: int, trigger_set_id: str | None = None) -> None:
        value = int(value)
        self.selected_trigger_idx = value
        if trigger_set_id:
            self.selected_trigger_indices[trigger_set_id] = value

    def get_selected_index(self, trigger_set_id: str | None = None) -> int:
        if trigger_set_id:
            return int(self.selected_trigger_indices.get(trigger_set_id, 0))
        return int(self.selected_trigger_idx)

    def indices_for(self, trigger_set_id: str | None = None) -> dict[str, int]:
        if not trigger_set_id:
            return self.indices
        return self.keymap_indices.setdefault(trigger_set_id, {})

    def forget_trigger_set(self, trigger_set_id: str) -> None:
        self.keymap_indices.pop(trigger_set_id, None)
        self.selected_trigger_indices.pop(trigger_set_id, None)

    def rekey_trigger_set(self, previous_id: str, current_id: str) -> None:
        if not previous_id or not current_id or previous_id == current_id:
            return
        if previous_id in self.keymap_indices:
            self.keymap_indices[current_id] = self.keymap_indices.pop(previous_id)
        if previous_id in self.selected_trigger_indices:
            self.selected_trigger_indices[current_id] = self.selected_trigger_indices.pop(previous_id)

    def can_switch_keymap(
        self, target_keymap_id: str = "", active_keymap_id: str = "", *, changes_active: bool = False
    ) -> bool:
        """連続実行中（一時停止中を含む）かどうかを共有する。"""
        same_target = target_keymap_id and target_keymap_id == active_keymap_id
        return self.run_to_end_key is None or (bool(same_target) and not changes_active)
