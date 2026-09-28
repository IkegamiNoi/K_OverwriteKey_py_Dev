from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from keyseq.application.sequence_steps import LoopFrame, StepResume
from keyseq.application.sequence_history import HistoryEntry, StepSnapshot, commit_step


@dataclass
class PendingStep:
    generation: int
    after_id: Any
    position: int
    resume: StepResume
    snapshot: StepSnapshot
    file_line: object | None = None
    call: object | None = None
    call_file_line: object | None = None
    call_paused: bool = False


@dataclass
class AppState:
    selected_trigger_idx: int = 0
    selected_trigger_indices: dict[str, int] = field(default_factory=dict)
    indices: dict[str, int] = field(default_factory=dict)
    keymap_indices: dict[str, dict[str, int]] = field(default_factory=dict)
    loop_frames: dict[str, list[LoopFrame]] = field(default_factory=dict)
    keymap_loop_frames: dict[str, dict[str, list[LoopFrame]]] = field(default_factory=dict)
    deferred_counters: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    keymap_deferred_counters: dict[str, dict[str, list[tuple[str, str]]]] = field(default_factory=dict)
    history: dict[str, list[HistoryEntry]] = field(default_factory=dict)
    keymap_history: dict[str, dict[str, list[HistoryEntry]]] = field(default_factory=dict)
    last_trigger: tuple[str, str] | None = None
    counters: dict[str, int] = field(default_factory=dict)
    pending_steps: dict[tuple[str, str], PendingStep] = field(default_factory=dict)
    pending_step_generation: int = 0
    reset_listeners: list[Callable[[], None]] = field(default_factory=list, compare=False, repr=False)

    run_to_end_key: str | None = None
    run_to_end_paused: bool = False
    run_to_end_after_id: Any = None

    lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    reentry_guard: set[str] = field(default_factory=set, init=False)

    def reset_indices(self) -> None:
        self.pending_steps.clear()
        self.indices = {}
        self.keymap_indices = {}
        self.loop_frames = {}
        self.keymap_loop_frames = {}
        self.deferred_counters = {}
        self.keymap_deferred_counters = {}
        self.history = {}
        self.keymap_history = {}
        self.last_trigger = None
        self.selected_trigger_indices = {}
        self.selected_trigger_idx = 0
        for listener in self.reset_listeners:
            listener()

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

    def loop_frames_for(self, trigger_set_id: str | None = None) -> dict[str, list[LoopFrame]]:
        if not trigger_set_id:
            return self.loop_frames
        return self.keymap_loop_frames.setdefault(trigger_set_id, {})

    def deferred_counters_for(self, trigger_set_id: str | None = None) -> dict[str, list[tuple[str, str]]]:
        if not trigger_set_id:
            return self.deferred_counters
        return self.keymap_deferred_counters.setdefault(trigger_set_id, {})

    def loop_iterations_for(self, trigger_set_id: str, key: str) -> dict[int, int]:
        """指定トリガーの周回フレームを開始位置から周回数への対応表で返す。"""
        with self.lock:
            if trigger_set_id:
                frames = self.keymap_loop_frames.get(trigger_set_id, {}).get(key, ())
            else:
                frames = self.loop_frames.get(key, ())
            return {frame.start: frame.iteration for frame in tuple(frames)}

    def history_for(self, trigger_set_id: str | None = None) -> dict[str, list[HistoryEntry]]:
        if not trigger_set_id:
            return self.history
        return self.keymap_history.setdefault(trigger_set_id, {})

    def forget_trigger(self, trigger_set_id: str, key: str) -> None:
        self.history_for(trigger_set_id).pop(key, None)
        self.deferred_counters_for(trigger_set_id).pop(key, None)
        if self.last_trigger == (trigger_set_id, key):
            self.last_trigger = None

    def rekey_trigger(self, trigger_set_id: str, previous_key: str, current_key: str) -> None:
        history = self.history_for(trigger_set_id)
        if previous_key in history:
            history.setdefault(current_key, history[previous_key])
            del history[previous_key]
        deferred = self.deferred_counters_for(trigger_set_id)
        if previous_key in deferred:
            deferred.setdefault(current_key, deferred[previous_key])
            del deferred[previous_key]
        if self.last_trigger == (trigger_set_id, previous_key):
            self.last_trigger = (trigger_set_id, current_key)

    def forget_trigger_set(self, trigger_set_id: str) -> None:
        for identity in tuple(self.pending_steps):
            if identity[0] == trigger_set_id:
                del self.pending_steps[identity]
        self.keymap_indices.pop(trigger_set_id, None)
        self.keymap_loop_frames.pop(trigger_set_id, None)
        self.keymap_deferred_counters.pop(trigger_set_id, None)
        self.keymap_history.pop(trigger_set_id, None)
        if self.last_trigger is not None and self.last_trigger[0] == trigger_set_id:
            self.last_trigger = None
        self.selected_trigger_indices.pop(trigger_set_id, None)

    def rekey_trigger_set(self, previous_id: str, current_id: str) -> None:
        if not previous_id or not current_id or previous_id == current_id:
            return
        for identity in tuple(self.pending_steps):
            if identity[0] in (previous_id, current_id):
                pending = self.pending_steps.pop(identity)
                if identity[0] == previous_id and isinstance(pending, PendingStep):
                    commit_step(self, pending.snapshot, pending.resume.counter_deltas)
        if previous_id in self.keymap_indices:
            self.keymap_indices[current_id] = self.keymap_indices.pop(previous_id)
        if previous_id in self.keymap_loop_frames:
            self.keymap_loop_frames[current_id] = self.keymap_loop_frames.pop(previous_id)
        if previous_id in self.keymap_deferred_counters:
            self.keymap_deferred_counters[current_id] = self.keymap_deferred_counters.pop(previous_id)
        if previous_id in self.keymap_history:
            self.keymap_history[current_id] = self.keymap_history.pop(previous_id)
        if self.last_trigger is not None and self.last_trigger[0] == previous_id:
            self.last_trigger = (current_id, self.last_trigger[1])
        if previous_id in self.selected_trigger_indices:
            self.selected_trigger_indices[current_id] = self.selected_trigger_indices.pop(previous_id)

    def can_switch_keymap(
        self, target_keymap_id: str = "", active_keymap_id: str = "", *, changes_active: bool = False
    ) -> bool:
        """連続実行が実行中かどうかを共有する。"""
        same_target = target_keymap_id and target_keymap_id == active_keymap_id
        return (self.run_to_end_key is None or self.run_to_end_paused
                or (bool(same_target) and not changes_active))
