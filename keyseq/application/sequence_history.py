"""Runtime history helpers for undoing sequence steps and controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence

from keyseq.application.call_chain import chain_top


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
    deferred_counters: list[tuple[str, str]] = field(default_factory=list)
    press_id: int = field(default=0, compare=False)
    call_ref: bool = field(default=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", list(self.frames))
        object.__setattr__(self, "counter_deltas", list(self.counter_deltas))
        object.__setattr__(self, "deferred_counters", list(self.deferred_counters))


@dataclass(frozen=True)
class StepSnapshot:
    """State captured at the start of a trigger step."""

    trigger_set_id: str
    key: str
    position: int
    frames: list[Any]
    deferred_counters: list[tuple[str, str]] = field(default_factory=list)
    call_ref: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", list(self.frames))
        object.__setattr__(self, "deferred_counters", list(self.deferred_counters))


def snapshot_for(state: Any, trigger_set_id: str, key: str) -> StepSnapshot:
    """Capture the current position and loop stack for one trigger."""
    with state.lock:
        position = state.indices_for(trigger_set_id).get(key, 0)
        frames = state.loop_frames_for(trigger_set_id).get(key, [])
        deferred = state.deferred_counters_for(trigger_set_id).get(key, [])
        call_ref = key in state.call_refs_for(trigger_set_id)
        return StepSnapshot(trigger_set_id, key, position, list(frames), list(deferred), call_ref)


def push_history(
    history: list[HistoryEntry],
    snapshot: StepSnapshot,
    position: int,
    frames: Sequence[Any],
    counter_deltas: Iterable[CounterDelta],
    deferred_counters: Sequence[tuple[str, str]] = (),
    press_id: int = 0,
    call_ref: bool | None = None,
) -> bool:
    """Append a changed step's start state, keeping only the newest 100 entries."""
    deltas = list(counter_deltas)
    current_frames = list(frames)
    current_deferred = list(deferred_counters)
    current_call_ref = snapshot.call_ref if call_ref is None else call_ref
    if (snapshot.position == position and snapshot.frames == current_frames
            and snapshot.deferred_counters == current_deferred
            and snapshot.call_ref == current_call_ref and not deltas):
        return False

    history.append(
        HistoryEntry(
            position=snapshot.position,
            frames=list(snapshot.frames),
            counter_deltas=deltas,
            deferred_counters=list(snapshot.deferred_counters),
            press_id=press_id,
            call_ref=snapshot.call_ref,
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
    state: Any, snapshot: StepSnapshot, deltas: Iterable[CounterDelta], press_id: int | None = None
) -> bool:
    """Record the start state when the completed step changed runtime state."""
    trigger_set_id, key = snapshot.trigger_set_id, snapshot.key
    with state.lock:
        if press_id is None:
            press_id = state.next_press_id()
        position = state.indices_for(trigger_set_id).get(key, snapshot.position)
        frames = state.loop_frames_for(trigger_set_id).get(key, [])
        deferred = state.deferred_counters_for(trigger_set_id).get(key, [])
        call_ref = key in state.call_refs_for(trigger_set_id)
        histories = state.history_for(trigger_set_id)
        history = histories.get(key)
        pending_history = history if history is not None else []
        if not push_history(pending_history, snapshot, position, frames, deltas,
                            deferred_counters=deferred, press_id=press_id, call_ref=call_ref):
            return False
        if history is None:
            histories[key] = pending_history
        state.last_trigger = (trigger_set_id, key)
        return True


def commit_press(
    state: Any,
    snapshots: Sequence[StepSnapshot],
    deltas_by_key: Mapping[str, Sequence[CounterDelta]],
    *,
    pressed_key: str,
) -> bool:
    """Commit one press across changed triggers, sharing one press identifier."""
    with state.lock:
        press_id = state.next_press_id()
        committed = False
        for snapshot in snapshots:
            trigger_set_id, key = snapshot.trigger_set_id, snapshot.key
            position = state.indices_for(trigger_set_id).get(key, snapshot.position)
            frames = state.loop_frames_for(trigger_set_id).get(key, [])
            deferred = state.deferred_counters_for(trigger_set_id).get(key, [])
            call_ref = key in state.call_refs_for(trigger_set_id)
            histories = state.history_for(trigger_set_id)
            history = histories.get(key)
            pending_history = history if history is not None else []
            if not push_history(
                pending_history, snapshot, position, frames, deltas_by_key.get(key, ()),
                deferred_counters=deferred, press_id=press_id, call_ref=call_ref,
            ):
                continue
            if history is None:
                histories[key] = pending_history
            committed = True
        if committed:
            state.last_trigger = (snapshots[0].trigger_set_id, pressed_key)
        return committed


def cancel_pending_steps(
    state: Any,
    after_cancel: Callable[[Any], None],
    identity: tuple[str, str] | None = None,
) -> None:
    """Commit and cancel one or all pending waits under the runtime state."""
    with state.lock:
        if identity is None:
            pending_steps = tuple(state.pending_steps.values())
            state.pending_steps.clear()
        else:
            pending = state.pending_steps.pop(identity, None)
            pending_steps = (pending,) if pending is not None else ()
    for pending in pending_steps:
        commit_step(state, pending.snapshot, pending.resume.counter_deltas)
        if pending.after_id is not None:
            try:
                after_cancel(pending.after_id)
            except Exception:
                pass


def apply_control(
    state: Any,
    source: tuple[str, str],
    op: str,
    find_trigger: Callable[[str], object | None],
    prepare_targets: Callable[[tuple[tuple[str, str], ...]], bool] | None = None,
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
    restore_key = target_key
    histories: MutableMapping[str, list[HistoryEntry]]
    grouped_keys: tuple[str, ...] = ()
    if op == "back":
        with state.lock:
            target_has_call_ref = target_key in state.call_refs_for(target_id)
        if target_has_call_ref:
            candidate = chain_top(state, target_id, target_key, find_trigger)
            with state.lock:
                candidate_history = state.history_for(target_id).get(candidate)
                if candidate_history:
                    restore_key = candidate
    with state.lock:
        histories = state.history_for(target_id)
        top_entry = None
        if op == "back":
            origin_history = histories.get(restore_key)
            top_entry = origin_history[-1] if origin_history else None
            if top_entry is not None:
                press_id = top_entry.press_id
                grouped_keys = tuple(
                    key for key, trigger_history in histories.items()
                    if trigger_history and trigger_history[-1].press_id == press_id
                    and (press_id != 0 or key == restore_key)
                )
        control_keys = tuple(dict.fromkeys((target_key, *grouped_keys)))
        control_identities = tuple((target_id, key) for key in control_keys)
        pending_steps = state.pending_steps
        for pending_identity in control_identities:
            pending = pending_steps.get(pending_identity)
            if pending is None:
                continue
            paused_call = (getattr(pending, "call", None) is not None
                           and bool(getattr(pending, "call_paused", False)))
            if not paused_call:
                return None, PENDING_TARGET_MESSAGE

    if prepare_targets is not None:
        if not prepare_targets(control_identities):
            return None, None

    with state.lock:
        if op == "back":
            # Re-read the selected history after preparation: a paused call may
            # have been discarded by the two-press control flow.
            history = histories.get(restore_key)
            top_entry = history[-1] if history else None
            if top_entry is None:
                return None, None
            press_id = top_entry.press_id
            restored = False
            for key, trigger_history in tuple(histories.items()):
                if (not trigger_history or trigger_history[-1].press_id != press_id
                        or (press_id == 0 and key != restore_key)):
                    continue
                entry = pop_history(trigger_history)
                if entry is None:
                    continue
                state.indices_for(target_id)[key] = entry.position
                state.loop_frames_for(target_id)[key] = list(entry.frames)
                state.deferred_counters_for(target_id)[key] = list(entry.deferred_counters)
                call_refs = state.call_refs_for(target_id)
                if entry.call_ref:
                    call_refs.add(key)
                else:
                    call_refs.discard(key)
                undo_counter_deltas(state.counters, entry.counter_deltas)
                restored = True
            return (restore_key, None) if restored else (None, None)

        history = histories.get(restore_key)
        if op == "rewind":
            state.indices_for(target_id)[target_key] = 0
            state.loop_frames_for(target_id)[target_key] = []
            state.deferred_counters_for(target_id).pop(target_key, None)
            state.call_refs_for(target_id).discard(target_key)
            if history is not None:
                clear_history(history)
            return target_key, None

    return None, None
