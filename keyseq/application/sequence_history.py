"""Runtime history helpers for undoing sequence steps and controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, MutableMapping, Sequence


MAX_HISTORY_ENTRIES = 100
CounterDelta = tuple[str, int]
NO_TARGET_MESSAGE = "戻す対象のトリガーがありません"
PENDING_TARGET_MESSAGE = "対象のトリガーが待機中のため操作できません"


@dataclass(frozen=True)
class HistoryEntry:
    """State to restore before a step, plus the counter operations it made."""

    position: int
    frames: list[Any]
    counter_deltas: list[CounterDelta]

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", list(self.frames))
        object.__setattr__(self, "counter_deltas", list(self.counter_deltas))


@dataclass(frozen=True)
class StepSnapshot:
    """State captured at the start of a trigger step."""

    trigger_set_id: str
    key: str
    position: int
    frames: list[Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", list(self.frames))


def snapshot_for(state: Any, trigger_set_id: str, key: str) -> StepSnapshot:
    """Capture the current position and loop stack for one trigger."""
    with state.lock:
        position = state.indices_for(trigger_set_id).get(key, 0)
        frames = state.loop_frames_for(trigger_set_id).get(key, [])
        return StepSnapshot(trigger_set_id, key, position, list(frames))


def push_history(
    history: list[HistoryEntry],
    snapshot: StepSnapshot,
    position: int,
    frames: Sequence[Any],
    counter_deltas: Iterable[CounterDelta],
) -> bool:
    """Append a changed step's start state, keeping only the newest 100 entries."""
    deltas = list(counter_deltas)
    current_frames = list(frames)
    if snapshot.position == position and snapshot.frames == current_frames and not deltas:
        return False

    history.append(
        HistoryEntry(
            position=snapshot.position,
            frames=list(snapshot.frames),
            counter_deltas=deltas,
        )
    )
    overflow = len(history) - MAX_HISTORY_ENTRIES
    if overflow > 0:
        del history[:overflow]
    return True


def pop_history(history: list[HistoryEntry]) -> HistoryEntry | None:
    """Remove and return the newest history entry, if one exists."""
    return history.pop() if history else None


def clear_history(history: list[HistoryEntry]) -> None:
    """Remove all entries from a trigger's history in place."""
    history.clear()


def undo_counter_deltas(
    counters: MutableMapping[str, int], deltas: Iterable[CounterDelta]
) -> None:
    """Reverse counter operations in reverse order without clamping values."""
    for name, delta in reversed(tuple(deltas)):
        counters[name] -= delta


def commit_step(
    state: Any, snapshot: StepSnapshot, deltas: Iterable[CounterDelta]
) -> bool:
    """Record the start state when the completed step changed runtime state."""
    trigger_set_id, key = snapshot.trigger_set_id, snapshot.key
    with state.lock:
        position = state.indices_for(trigger_set_id).get(key, snapshot.position)
        frames = state.loop_frames_for(trigger_set_id).get(key, [])
        histories = state.history_for(trigger_set_id)
        history = histories.get(key)
        pending_history = history if history is not None else []
        if not push_history(pending_history, snapshot, position, frames, deltas):
            return False
        if history is None:
            histories[key] = pending_history
        state.last_trigger = (trigger_set_id, key)
        return True


def apply_control(
    state: Any,
    source: tuple[str, str],
    op: str,
    find_trigger: Callable[[str], object | None],
) -> tuple[str | None, str | None]:
    """Apply a back/rewind control to the most recently recorded trigger.

    The caller performs any selection after the triggering key's normal selection
    work.  A returned key requests selecting the restored target; a returned
    message reports why no target could be operated on.
    """
    target = state.last_trigger
    if (
        target is None
        or target == source
        or target[0] != source[0]
        or find_trigger(target[1]) is None
    ):
        return None, NO_TARGET_MESSAGE

    target_id, target_key = target
    identity = (target_id, target_key)
    with state.lock:
        if identity in state.pending_steps:
            return None, PENDING_TARGET_MESSAGE

        histories = state.history_for(target_id)
        history = histories.get(target_key)
        if op == "back":
            if history is None:
                return None, None
            entry = pop_history(history)
            if entry is None:
                return None, None
            state.indices_for(target_id)[target_key] = entry.position
            state.loop_frames_for(target_id)[target_key] = list(entry.frames)
            undo_counter_deltas(state.counters, entry.counter_deltas)
            return target_key, None

        if op == "rewind":
            state.indices_for(target_id)[target_key] = 0
            state.loop_frames_for(target_id)[target_key] = []
            if history is not None:
                clear_history(history)
            return target_key, None

    return None, None
