from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from keyseq.domain import call_graph, sequence_control
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int
from keyseq.application.sequence_history import StepSnapshot, snapshot_for
from keyseq.application.sequence_steps import (
    LoopFrame,
    MAX_PROCESSED_SYSTEM_ACTIONS,
    PROCESSED_LIMIT_MESSAGE,
    StepResume,
    StepOutcome,
    advance,
    after_normal_action,
    apply_deferred_counters,
    reset_frames,
    settle_after_normal,
)


@dataclass(frozen=True)
class CallSequence:
    """A live action list and its trigger's current interval."""
    actions: list[dict[str, Any]]
    interval_ms: int


@dataclass
class CallFrame:
    key: str
    position: int = 0
    frames: list[LoopFrame] = field(default_factory=list)
    deferred: list[tuple[str, str]] = field(default_factory=list)
    resume: StepResume | None = None
    step: bool = False
    sent: bool = False  # Step-return boundary only; stops use the run-level gate.


@dataclass
class CallContext:
    trigger_set_id: str
    root_key: str
    first_target: str
    state: Any
    find_trigger: Callable[[str], Mapping[str, Any] | None]
    stack: list[CallFrame] = field(default_factory=list)
    started: bool = False
    processed_before_action: int = 0
    first_step: bool = False
    before: dict[str, StepSnapshot] = field(default_factory=dict)
    changed_frames: dict[str, CallFrame] = field(default_factory=dict)
    completed: list[str] = field(default_factory=list)
    deltas_by_key: dict[str, list[tuple[str, int]]] = field(default_factory=dict)
    ancestors: tuple[str, ...] = ()
    ancestor_depth: int = 0
    root_continuation: int | None = None
    sent_action: bool = False
    performing: bool = False
    failed: bool = False
    press_processed: int = 0
    stop_gate: Callable[[], bool] = field(default=lambda: False)
    on_call_success: Callable[[], None] | None = None

    def entry_for(self, key: str) -> CallSequence | None:
        trigger = self.find_trigger(key)
        if trigger is None:
            return None
        return CallSequence(trigger.get("actions", []), coerce_nonnegative_int(
            trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        ))

    def record_deltas(self, key: str, deltas: Iterable[tuple[str, int]]) -> None:
        self.deltas_by_key.setdefault(key, []).extend(deltas)

    def top_is_step(self) -> bool:
        return bool(self.stack and self.stack[-1].step)

    def is_step_context(self) -> bool:
        """呼び出しの行がステップの文脈か（最初の段の印。入れ子の一括の実行中も真）。"""
        return self.first_step


@dataclass(frozen=True)
class CallStep:
    kind: Literal["action", "wait", "next", "done", "stopped", "error", "ignored", "paused_callee"]
    action: dict[str, Any] | None = None
    wait_ms: int | None = None
    message: str | None = None
    chain: tuple[str, ...] = ()
    counter_deltas: tuple[tuple[str, int], ...] = ()
    interval_ms: int | None = None
    call_done: bool = False


def start_linked_call(
    trigger_set_id: str, root_key: str, target_key: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None], state: Any,
    *, step: bool, ancestors: tuple[str, ...] = (), ancestor_depth: int = 0,
) -> CallContext:
    """Build a linked call from live trigger states, without copying actions."""
    ctx = CallContext(trigger_set_id, root_key, target_key, first_step=step,
                      state=state, find_trigger=find_trigger, ancestors=ancestors,
                      ancestor_depth=ancestor_depth)
    ctx.before[root_key] = snapshot_for(state, trigger_set_id, root_key)
    return ctx


def chain_text(chain: tuple[str, ...]) -> str:
    return f"呼び出し: {' > '.join(key for key in chain if key)}"


def top_interval(ctx: CallContext) -> int:
    if not ctx.stack:
        return 0
    entry = ctx.entry_for(ctx.stack[-1].key)
    return entry.interval_ms if entry is not None else 0


def _chain(ctx: CallContext, attempted: str | None = None) -> tuple[str, ...]:
    keys = tuple(frame.key for frame in ctx.stack)
    return (*keys, attempted) if attempted is not None else keys


def _error(message: str, chain: tuple[str, ...], deltas: list[tuple[str, int]]) -> CallStep:
    return CallStep("error", message=message, chain=chain, counter_deltas=tuple(deltas))


def _push_frame(
    ctx: CallContext, key: str, deltas: list[tuple[str, int]], step: bool,
) -> CallStep | None:
    chain = _chain(ctx, key)
    if ctx.ancestor_depth + len(ctx.stack) + 1 > sequence_control.MAX_CALL_DEPTH:
        return _error(
            f"呼び出しの深さが {sequence_control.MAX_CALL_DEPTH} を超えます", chain, deltas,
        )
    if key in ctx.ancestors or key == ctx.root_key or any(frame.key == key for frame in ctx.stack):
        return _error(f"呼び出しが循環します（{key}）", chain, deltas)
    entry = ctx.entry_for(key) if key else None
    if key and entry is None:
        return _error(f"呼び出し先のトリガーがありません（{key}）", chain, deltas)
    if entry is not None and len(entry.actions) == 1:
        action = entry.actions[0]
        if (
            isinstance(action, Mapping)
            and sequence_control.action_type(action) == sequence_control.ACTION_TYPE_SYSTEM
            and sequence_control.system_op(action)
            in (sequence_control.OP_BACK, sequence_control.OP_REWIND)
        ):
            return _error("戻す・先頭へのトリガーは呼び出せません", chain, deltas)
    if not key:
        return _error("呼び出し先が指定されていません", chain, deltas)
    parent_step = ctx.top_is_step() if ctx.stack else True
    frame = CallFrame(key, step=step and parent_step)
    # Keep this even for a busy target so rollback can restore its press-start state.
    saved = ctx.before.setdefault(key, snapshot_for(ctx.state, ctx.trigger_set_id, key))
    previous = ctx.changed_frames.get(key)
    frame.position = previous.position if previous is not None else saved.position
    frame.frames = list(previous.frames if previous is not None else saved.frames)
    frame.deferred = list(previous.deferred if previous is not None else saved.deferred_counters)
    if entry is not None and any(
        bool(entry.actions[loop.start].get("infinite"))
        for loop in reset_frames(entry.actions, frame.position)
    ):
        return _error("呼び出し先に無限ループがあります", chain, deltas)
    if (key not in ctx.ancestors and key != ctx.root_key
            and (ctx.trigger_set_id, key) in ctx.state.pending_steps):
        pending = ctx.state.pending_steps[(ctx.trigger_set_id, key)]
        if isinstance(pending.call, CallContext) and pending.call_paused:
            return CallStep("paused_callee", chain=chain, counter_deltas=tuple(deltas))
        # This ends call_step before it can return an action to the sender.
        return CallStep("ignored", chain=chain)
    ctx.changed_frames[key] = frame
    ctx.stack.append(frame)
    return None


def _is_call(action: Any) -> bool:
    return (
        isinstance(action, Mapping)
        and sequence_control.action_type(action) == sequence_control.ACTION_TYPE_SYSTEM
        and sequence_control.system_op(action) == sequence_control.OP_CALL
    )


def _new_deltas(
    outcome: StepOutcome, resume: StepResume | None,
) -> tuple[tuple[str, int], ...]:
    prior = len(resume.counter_deltas) if resume is not None else 0
    return outcome.counter_deltas[prior:]


def _pop_frame(ctx: CallContext, counters: dict[str, int]) -> tuple[tuple[str, int], ...]:
    frame = ctx.stack.pop()
    if ctx.on_call_success is not None:
        ctx.on_call_success()
    deltas = apply_deferred_counters(frame.deferred, counters)
    ctx.record_deltas(frame.key, deltas)
    frame.position, frame.frames, frame.deferred = 0, [], []
    ctx.completed.append(frame.key)
    return deltas


def _clear_step_frame_sent(ctx: CallContext) -> None:
    if ctx.top_is_step():
        for frame in ctx.stack:
            frame.sent = False


def _stop_enabled(ctx: CallContext, run_to_end: bool) -> bool:
    return ctx.top_is_step() and run_to_end and ctx.stop_gate()


def _advance_call(ctx: CallContext, counters: dict[str, int], run_to_end: bool) -> CallStep:
    deltas: list[tuple[str, int]] = []
    processed = [ctx.press_processed]
    if not ctx.started:
        ctx.started = True
        failure = _push_frame(ctx, ctx.first_target, deltas, ctx.first_step)
        if failure is not None:
            ctx.started = False
            return failure
    while ctx.stack:
        result = _advance_frame(ctx, counters, deltas, processed, run_to_end)
        ctx.press_processed = processed[0]
        if result is not None:
            ctx.processed_before_action = (
                processed[0] if result.kind == "action" else 0
            )
            return result
    return CallStep("done", counter_deltas=tuple(deltas))


def _advance_frame(
    ctx: CallContext, counters: dict[str, int], deltas: list[tuple[str, int]],
    processed: list[int],
    run_to_end: bool,
) -> CallStep | None:
    frame = ctx.stack[-1]
    entry = ctx.entry_for(frame.key)
    if entry is None:
        return _error(f"呼び出し先のトリガーがありません（{frame.key}）", _chain(ctx), deltas)
    resume = frame.resume
    deferred = () if resume is not None else tuple(frame.deferred)
    if resume is None:
        frame.deferred.clear()
    outcome = advance(
        entry.actions, frame.position, frame.frames, counters,
        wrap_once=False, resume=resume, deferred_counters=deferred,
        on_control=None, stop_ends_run=_stop_enabled(ctx, run_to_end), in_call=True,
    )
    processed[0] += max(0, outcome.processed - (resume.processed if resume else 0))
    deltas.extend(_new_deltas(outcome, resume))
    ctx.record_deltas(frame.key, _new_deltas(outcome, resume))
    frame.resume = None
    frame.frames = outcome.frames
    if processed[0] > MAX_PROCESSED_SYSTEM_ACTIONS:
        return _error(PROCESSED_LIMIT_MESSAGE, _chain(ctx), deltas)
    if outcome.error is not None:
        frame.position = outcome.position
        return _error(outcome.error[1], _chain(ctx), deltas)
    if outcome.stopped:
        frame.position = outcome.position
        return _settle_stopped_call(ctx, counters, deltas, processed)
    if outcome.wait_ms is not None:
        frame.position = outcome.resume_position or 0
        frame.resume = outcome.resume
        return CallStep("wait", wait_ms=outcome.wait_ms, chain=_chain(ctx),
                        counter_deltas=tuple(deltas))
    if outcome.reached_end:
        returned_sent = frame.sent
        deltas.extend(_pop_frame(ctx, counters))
        if not ctx.stack:
            return CallStep("done", chain=(), counter_deltas=tuple(deltas))
        return _finish_returned_call(
            ctx, counters, deltas, processed, run_to_end,
            returned_sent=returned_sent,
        )
    if outcome.normal_index is None:
        return _error("呼び出し先のステップを進められません", _chain(ctx), deltas)
    action = entry.actions[outcome.normal_index]
    frame.position = outcome.normal_index
    if _is_call(action):
        return _push_frame(
            ctx, call_graph.call_target(action), deltas, sequence_control.is_step_call(action),
        )
    return CallStep("action", action=dict(action), chain=_chain(ctx),
                    counter_deltas=tuple(deltas))


def _finish_returned_call(
    ctx: CallContext, counters: dict[str, int], deltas: list[tuple[str, int]],
    processed: list[int],
    run_to_end: bool = False,
    *, returned_sent: bool = False,
) -> CallStep | None:
    """Resume a parent frame, returning when a boundary or control outcome is reached."""
    while ctx.stack:
        frame = ctx.stack[-1]
        entry = ctx.entry_for(frame.key)
        if entry is None:
            return _error(f"呼び出し先のトリガーがありません（{frame.key}）", _chain(ctx), deltas)
        call_index = frame.position
        if call_index + 1 >= len(entry.actions):
            returned_sent = returned_sent or frame.sent
            deltas.extend(_pop_frame(ctx, counters))
            continue
        frame.position, frame.frames = after_normal_action(
            entry.actions, call_index, frame.frames,
        )
        settled = settle_after_normal(
            entry.actions, frame.position, frame.frames, counters,
            allow_wrap=False, stop_ends_run=_stop_enabled(ctx, run_to_end), in_call=True,
        )
        processed[0] += settled.processed
        ctx.press_processed = processed[0]
        frame.position, frame.frames = settled.position, settled.frames
        deltas.extend(settled.counter_deltas)
        ctx.record_deltas(frame.key, settled.counter_deltas)
        frame.deferred.extend(settled.deferred_counters)
        if processed[0] > MAX_PROCESSED_SYSTEM_ACTIONS:
            return _error(PROCESSED_LIMIT_MESSAGE, _chain(ctx), deltas)
        if settled.stopped:
            return _settle_stopped_call(ctx, counters, deltas, processed)
        if frame.position != 0 or not entry.actions:
            if frame.step and returned_sent:
                _clear_step_frame_sent(ctx)
                return CallStep("next", chain=_chain(ctx), counter_deltas=tuple(deltas),
                                interval_ms=top_interval(ctx))
            return None
        returned_sent = returned_sent or frame.sent
        deltas.extend(_pop_frame(ctx, counters))
    return None


def _settle_stopped_call(
    ctx: CallContext, counters: dict[str, int], deltas: list[tuple[str, int]],
    processed: list[int],
) -> CallStep:
    """Settle past a stop, unwinding completed frames without starting actions."""
    frame = ctx.stack[-1]
    applied = apply_deferred_counters(frame.deferred, counters)
    deltas.extend(applied)
    ctx.record_deltas(frame.key, applied)
    frame.deferred.clear()
    while ctx.stack:
        frame = ctx.stack[-1]
        entry = ctx.entry_for(frame.key)
        if frame.position != 0:
            settled = settle_after_normal(
                entry.actions, frame.position, frame.frames, counters,
                allow_wrap=False, processed=processed[0], in_call=True, wait_mode="skip",
            )
            processed[0] = settled.processed
            frame.position, frame.frames = settled.position, settled.frames
            frame.deferred.extend(settled.deferred_counters)
            deltas.extend(settled.counter_deltas)
            ctx.record_deltas(frame.key, settled.counter_deltas)
            if frame.position != 0:
                break
        deltas.extend(_pop_frame(ctx, counters))
        if ctx.stack:
            parent = ctx.stack[-1]
            parent.position, parent.frames = after_normal_action(
                ctx.entry_for(parent.key).actions, parent.position, parent.frames,
            )
    return CallStep("stopped", chain=_chain(ctx), counter_deltas=tuple(deltas),
                    call_done=not ctx.stack)


def call_step(
    ctx: CallContext, counters: dict[str, int], *, run_to_end: bool = False,
    sent: bool | Callable[[], bool] = False,
    on_call_success: Callable[[], None] | None = None,
) -> CallStep:
    """Advance the call context to its next action, wait, completion, or error."""
    ctx.stop_gate = sent if callable(sent) else lambda: sent
    ctx.on_call_success = on_call_success
    result = _advance_call(ctx, counters, run_to_end)
    if result.kind == "next":
        _clear_step_frame_sent(ctx)
    return result


def finish_call_action(
    ctx: CallContext, counters: dict[str, int], *, run_to_end: bool = False,
    sent: bool | Callable[[], bool] = True,
) -> CallStep:
    """Complete the delivered action and prepare the next call-context step."""
    ctx.stop_gate = sent if callable(sent) else lambda: sent
    if not ctx.stack:
        return CallStep("done")
    # A nested batch delivers actions within the enclosing step context too.
    if ctx.is_step_context():
        for active_frame in ctx.stack:
            active_frame.sent = True
    deltas: list[tuple[str, int]] = []
    processed = [ctx.processed_before_action]
    ctx.processed_before_action = 0
    frame = ctx.stack[-1]
    entry = ctx.entry_for(frame.key)
    if entry is None:
        return _error(f"呼び出し先のトリガーがありません（{frame.key}）", _chain(ctx), deltas)
    if frame.position + 1 >= len(entry.actions):
        returned_sent = frame.sent
        deltas.extend(_pop_frame(ctx, counters))
        returned = _finish_returned_call(
            ctx, counters, deltas, processed, run_to_end,
            returned_sent=returned_sent,
        )
        if returned is not None:
            if returned.kind == "next":
                _clear_step_frame_sent(ctx)
            return returned
        if not ctx.stack:
            return CallStep("done", counter_deltas=tuple(deltas))
        _clear_step_frame_sent(ctx)
        return CallStep("next", chain=_chain(ctx), counter_deltas=tuple(deltas),
                        interval_ms=top_interval(ctx))
    frame.position, frame.frames = after_normal_action(
        entry.actions, frame.position, frame.frames,
    )
    settled = settle_after_normal(
        entry.actions, frame.position, frame.frames, counters,
        allow_wrap=False, stop_ends_run=_stop_enabled(ctx, run_to_end), in_call=True,
    )
    processed[0] += settled.processed
    ctx.press_processed = processed[0]
    frame.position, frame.frames = settled.position, settled.frames
    frame.deferred.extend(settled.deferred_counters)
    deltas.extend(settled.counter_deltas)
    ctx.record_deltas(frame.key, settled.counter_deltas)
    if processed[0] > MAX_PROCESSED_SYSTEM_ACTIONS:
        return _error(PROCESSED_LIMIT_MESSAGE, _chain(ctx), deltas)
    if settled.stopped:
        return _settle_stopped_call(ctx, counters, deltas, processed)
    if frame.position == 0:
        returned_sent = frame.sent
        deltas.extend(_pop_frame(ctx, counters))
        returned = _finish_returned_call(
            ctx, counters, deltas, processed, run_to_end,
            returned_sent=returned_sent,
        )
        if returned is not None:
            if returned.kind == "next":
                _clear_step_frame_sent(ctx)
            return returned
    if not ctx.stack:
        return CallStep("done", counter_deltas=tuple(deltas))
    _clear_step_frame_sent(ctx)
    return CallStep("next", chain=_chain(ctx), counter_deltas=tuple(deltas),
                    interval_ms=top_interval(ctx))


def settle_call_wait(ctx: CallContext, counters: dict[str, int]) -> CallStep | None:
    """Cancel a pending call wait and settle without sending another action."""
    if not ctx.stack or ctx.stack[-1].resume is None:
        return None
    frame = ctx.stack[-1]
    frame.deferred.extend(frame.resume.deferred_counters)
    frame.resume = None
    return _settle_stopped_call(ctx, counters, [], [ctx.press_processed])
