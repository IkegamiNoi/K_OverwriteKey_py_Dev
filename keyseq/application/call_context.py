from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from keyseq.domain import call_graph, sequence_control
from keyseq.domain.call_graph import CallEntry
from keyseq.application.sequence_steps import (
    LoopFrame,
    MAX_PROCESSED_SYSTEM_ACTIONS,
    PROCESSED_LIMIT_MESSAGE,
    StepResume,
    StepOutcome,
    advance,
    after_normal_action,
    apply_deferred_counters,
    settle_after_normal,
)


@dataclass
class CallFrame:
    key: str
    position: int = 0
    frames: list[LoopFrame] = field(default_factory=list)
    deferred: list[tuple[str, str]] = field(default_factory=list)
    resume: StepResume | None = None
    step: bool = False


@dataclass
class CallContext:
    trigger_set_id: str
    root_key: str
    first_target: str
    snapshot: dict[str, CallEntry | None]
    stack: list[CallFrame] = field(default_factory=list)
    started: bool = False
    processed_before_action: int = 0
    first_step: bool = False
    sent: bool = False

    def top_is_step(self) -> bool:
        return bool(self.stack and self.stack[-1].step)

    def is_step_context(self) -> bool:
        """呼び出しの行がステップの文脈か（最初の段の印。入れ子の一括の実行中も真）。"""
        return self.first_step


@dataclass(frozen=True)
class CallStep:
    kind: Literal["action", "wait", "next", "done", "stopped", "error"]
    action: dict[str, Any] | None = None
    wait_ms: int | None = None
    message: str | None = None
    chain: tuple[str, ...] = ()
    counter_deltas: tuple[tuple[str, int], ...] = ()
    interval_ms: int | None = None
    call_done: bool = False


def start_call(
    trigger_set_id: str,
    root_key: str,
    target_key: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None],
    *, step: bool = False,
) -> CallContext:
    """Capture the reachable call targets before beginning a call."""
    return CallContext(
        trigger_set_id=trigger_set_id,
        root_key=root_key,
        first_target=target_key,
        snapshot=call_graph.collect_call_snapshot(target_key, find_trigger),
        first_step=step,
    )


def chain_text(chain: tuple[str, ...]) -> str:
    return f"呼び出し: {' > '.join(key for key in chain if key)}"


def top_interval(ctx: CallContext) -> int:
    if not ctx.stack:
        return 0
    entry = ctx.snapshot.get(ctx.stack[-1].key)
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
    if len(ctx.stack) + 1 > sequence_control.MAX_CALL_DEPTH:
        return _error(
            f"呼び出しの深さが {sequence_control.MAX_CALL_DEPTH} を超えます", chain, deltas,
        )
    if key == ctx.root_key or any(frame.key == key for frame in ctx.stack):
        return _error(f"呼び出しが循環します（{key}）", chain, deltas)
    entry = ctx.snapshot.get(key) if key else None
    if key and (key not in ctx.snapshot or entry is None):
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
    ctx.stack.append(CallFrame(key, step=step and parent_step))
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
    return apply_deferred_counters(frame.deferred, counters)


def _stop_enabled(ctx: CallContext, run_to_end: bool) -> bool:
    return ctx.top_is_step() and run_to_end and ctx.sent


def _advance_call(ctx: CallContext, counters: dict[str, int], run_to_end: bool) -> CallStep:
    deltas: list[tuple[str, int]] = []
    processed = [0]
    if not ctx.started:
        ctx.started = True
        failure = _push_frame(ctx, ctx.first_target, deltas, ctx.first_step)
        if failure is not None:
            ctx.started = False
            return failure
    while ctx.stack:
        result = _advance_frame(ctx, counters, deltas, processed, run_to_end)
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
    entry = ctx.snapshot.get(frame.key)
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
        deltas.extend(_pop_frame(ctx, counters))
        if not ctx.stack:
            return CallStep("done", chain=(), counter_deltas=tuple(deltas))
        return _finish_returned_call(ctx, counters, deltas, processed, run_to_end)
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
) -> CallStep | None:
    """Resume the parent after a nested frame ends; return on an error."""
    while ctx.stack:
        frame = ctx.stack[-1]
        entry = ctx.snapshot[frame.key]
        call_index = frame.position
        if call_index + 1 >= len(entry.actions):
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
        frame.position, frame.frames = settled.position, settled.frames
        deltas.extend(settled.counter_deltas)
        frame.deferred.extend(settled.deferred_counters)
        if processed[0] > MAX_PROCESSED_SYSTEM_ACTIONS:
            return _error(PROCESSED_LIMIT_MESSAGE, _chain(ctx), deltas)
        if settled.stopped:
            return _settle_stopped_call(ctx, counters, deltas, processed)
        if frame.position != 0 or not entry.actions:
            return None
        deltas.extend(_pop_frame(ctx, counters))
    return None


def _settle_stopped_call(
    ctx: CallContext, counters: dict[str, int], deltas: list[tuple[str, int]],
    processed: list[int],
) -> CallStep:
    """Settle past a stop, unwinding completed frames without starting actions."""
    frame = ctx.stack[-1]
    deltas.extend(apply_deferred_counters(frame.deferred, counters))
    frame.deferred.clear()
    while ctx.stack:
        frame = ctx.stack[-1]
        entry = ctx.snapshot[frame.key]
        if frame.position != 0:
            settled = settle_after_normal(
                entry.actions, frame.position, frame.frames, counters,
                allow_wrap=False, processed=processed[0], in_call=True, wait_mode="skip",
            )
            processed[0] = settled.processed
            frame.position, frame.frames = settled.position, settled.frames
            frame.deferred.extend(settled.deferred_counters)
            deltas.extend(settled.counter_deltas)
            if frame.position != 0:
                break
        deltas.extend(_pop_frame(ctx, counters))
        if ctx.stack:
            parent = ctx.stack[-1]
            parent.position, parent.frames = after_normal_action(
                ctx.snapshot[parent.key].actions, parent.position, parent.frames,
            )
    return CallStep("stopped", chain=_chain(ctx), counter_deltas=tuple(deltas),
                    call_done=not ctx.stack)


def call_step(
    ctx: CallContext, counters: dict[str, int], *, run_to_end: bool = False,
) -> CallStep:
    """Advance the call context to its next action, wait, completion, or error."""
    return _advance_call(ctx, counters, run_to_end)


def finish_call_action(
    ctx: CallContext, counters: dict[str, int], *, run_to_end: bool = False,
) -> CallStep:
    """Complete the delivered action and prepare the next call-context step."""
    if not ctx.stack:
        return CallStep("done")
    # A nested batch delivers actions within the enclosing step context too.
    if ctx.is_step_context():
        ctx.sent = True
    deltas: list[tuple[str, int]] = []
    processed = [ctx.processed_before_action]
    ctx.processed_before_action = 0
    frame = ctx.stack[-1]
    entry = ctx.snapshot.get(frame.key)
    if entry is None:
        return _error(f"呼び出し先のトリガーがありません（{frame.key}）", _chain(ctx), deltas)
    if frame.position + 1 >= len(entry.actions):
        deltas.extend(_pop_frame(ctx, counters))
        failure = _finish_returned_call(ctx, counters, deltas, processed, run_to_end)
        if failure is not None:
            return failure
        if not ctx.stack:
            return CallStep("done", counter_deltas=tuple(deltas))
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
    frame.position, frame.frames = settled.position, settled.frames
    frame.deferred.extend(settled.deferred_counters)
    deltas.extend(settled.counter_deltas)
    if processed[0] > MAX_PROCESSED_SYSTEM_ACTIONS:
        return _error(PROCESSED_LIMIT_MESSAGE, _chain(ctx), deltas)
    if settled.stopped:
        return _settle_stopped_call(ctx, counters, deltas, processed)
    if frame.position == 0:
        deltas.extend(_pop_frame(ctx, counters))
        failure = _finish_returned_call(ctx, counters, deltas, processed, run_to_end)
        if failure is not None:
            return failure
    if not ctx.stack:
        return CallStep("done", counter_deltas=tuple(deltas))
    return CallStep("next", chain=_chain(ctx), counter_deltas=tuple(deltas),
                    interval_ms=top_interval(ctx))
