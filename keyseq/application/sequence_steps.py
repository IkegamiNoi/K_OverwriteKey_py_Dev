from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from keyseq.domain.sequence_control import (
    ACTION_TYPE_SYSTEM, OP_BACK, OP_CALL, OP_COUNTER_INC, OP_COUNTER_RESET,
    MAX_LOOP_DEPTH, OP_LOOP_END, OP_LOOP_START, OP_REWIND, OP_STOP, OP_WAIT, action_type,
    analyze_loops, control_target, enclosing_loop_starts, system_op,
)

MAX_PROCESSED_SYSTEM_ACTIONS = 10000
PROCESSED_LIMIT_MESSAGE = (
    "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）"
)


@dataclass(frozen=True)
class LoopFrame:
    start: int
    iteration: int


@dataclass(frozen=True)
class StepResume:
    initial_position: int
    wrapped: bool
    processed: int
    counter_deltas: tuple[tuple[str, int], ...] = ()
    deferred_counters: tuple[tuple[str, str], ...] = ()


def continue_resume(resume: StepResume, settled: SettleOutcome) -> StepResume:
    """先行処理（待機をまたぐ）の結果を足した続きの StepResume。"""
    return StepResume(resume.initial_position, settled.wrapped, settled.processed,
                      resume.counter_deltas + settled.counter_deltas, settled.deferred_counters)


def format_system_error_notification(
    action: dict[str, Any], message: str,
) -> tuple[dict[str, Any], str]:
    """Copy a system action and add its readable operation value for notification."""
    notified = action.copy()
    op = str(action.get("op") or "(なし)")
    normalized_op = system_op(action)
    if normalized_op == "loop_start":
        value = "無限" if action.get("infinite") else f"回数={action.get('count', '(なし)')}"
    elif normalized_op == "wait":
        value = f"{action.get('ms', '(なし)')}ms"
    elif normalized_op in ("counter_inc", "counter_reset"):
        value = f"カウンター={action.get('counter', '(なし)')}"
    elif normalized_op == "call":
        target = action.get("target")
        target = target.strip() if isinstance(target, str) else ""
        value = f"呼び出し先={target or '(なし)'}"
    else:
        value = ""
    detail = f"{op} {value}".rstrip()
    notified["value"] = detail
    label = action.get("label")
    if isinstance(label, str) and label.strip():
        detail += f" / ラベル: {label.strip()}"
    return notified, f"system 実行エラー（{detail}）: {message}"


def apply_deferred_counters(
    deferred: Sequence[tuple[str, str]], counters: dict[str, int],
) -> tuple[tuple[str, int], ...]:
    """Apply queued counter operations and return their reversible deltas."""
    deltas: list[tuple[str, int]] = []
    for op, name in deferred:
        error = _counter({"counter": name}, op, counters, deltas)
        if error:
            continue
    return tuple(deltas)


@dataclass
class StepOutcome:
    normal_index: int | None
    position: int
    frames: list[LoopFrame]
    error: tuple[int, str] | None = None
    reached_end: bool = False
    wait_ms: int | None = None
    resume_position: int | None = None
    resume: StepResume | None = None
    counter_deltas: tuple[tuple[str, int], ...] = ()
    wrapped: bool = False
    processed: int = 0
    stopped: bool = False


def resume_for_pending(outcome: StepOutcome, initial_position: int) -> StepResume:
    return StepResume(
        initial_position, outcome.wrapped, outcome.processed, outcome.counter_deltas,
    )


@dataclass
class SettleOutcome:
    position: int
    frames: list[LoopFrame]
    counter_deltas: tuple[tuple[str, int], ...]
    wrapped: bool = False
    deferred_counters: tuple[tuple[str, str], ...] = ()
    stopped: bool = False
    processed: int = 0
    wait_ms: int | None = None


def reset_frames(actions: Sequence[Any], position: int) -> list[LoopFrame]:
    structure = analyze_loops(actions)
    if structure.unmatched:
        return []
    return [LoopFrame(start, 1) for start in enclosing_loop_starts(structure, position)]


def _loop_count(action: Mapping[str, Any]) -> int | None:
    if bool(action.get("infinite")):
        return None
    try:
        count = int(action.get("count"))
    except (TypeError, ValueError, OverflowError):
        return 0
    return count if count >= 1 else 0


def _loop_start(action: Mapping[str, Any], position: int, frames: list[LoopFrame], structure: Any) -> tuple[int, str | None]:
    if position in structure.unmatched:
        return position, "ループの始まりに対応する終わりがありません"
    if position in structure.too_deep:
        return position, f"ループの入れ子が {MAX_LOOP_DEPTH} 段を超えています"
    if _loop_count(action) == 0:
        return position, "ループの回数が不正です（1 以上の整数）"
    frames.append(LoopFrame(position, 1))
    return position + 1, None


def _loop_end(actions: Sequence[Any], position: int, frames: list[LoopFrame], structure: Any) -> tuple[int, str | None]:
    start = structure.reverse_pairs.get(position)
    if start is None or not frames or frames[-1].start != start:
        return position, "ループの終わりに対応する始まりがありません"
    count = _loop_count(actions[start])
    if count == 0:
        return position, "ループの回数が不正です（1 以上の整数）"
    frame = frames[-1]
    if count is None or frame.iteration < count:
        frames[-1] = LoopFrame(start, frame.iteration + 1)
        return start + 1, None
    frames.pop()
    return position + 1, None


def _counter(action: Mapping[str, Any], op: str, counters: dict[str, int],
             counter_deltas: list[tuple[str, int]]) -> str | None:
    value = action.get("counter", "")
    name = value.strip() if isinstance(value, str) else ""
    if not name:
        return "カウンター名が空です"
    current = counters.get(name, 0)
    if op == OP_COUNTER_INC:
        counters[name] = current + 1
        counter_deltas.append((name, 1))
    else:
        counters[name] = 0
        if current:
            counter_deltas.append((name, -current))
    return None


def _system_step(actions: Sequence[Any], position: int, frames: list[LoopFrame],
                 counters: dict[str, int], structure: Any,
                 counter_deltas: list[tuple[str, int]]) -> tuple[int, str | None]:
    action = actions[position]
    op = system_op(action)
    if op == OP_LOOP_START:
        return _loop_start(action, position, frames, structure)
    if op == OP_LOOP_END:
        return _loop_end(actions, position, frames, structure)
    if op in (OP_COUNTER_INC, OP_COUNTER_RESET):
        return position + 1, _counter(action, op, counters, counter_deltas)
    if op in (OP_BACK, OP_REWIND):
        return position + 1, None
    if op == OP_STOP:
        return position + 1, None
    return position, f"system の操作が不正です。操作: {op}"


def advance(actions: Sequence[Any], position: int, frames: list[LoopFrame],
            counters: dict[str, int], *, wrap_once: bool,
            resume: StepResume | None = None,
            deferred_counters: Sequence[tuple[str, str]] = (),
            on_control: Callable[[str, str | None], None] | None = None,
            stop_ends_run: bool = False,
            in_call: bool = False) -> StepOutcome:
    structure = analyze_loops(actions)
    if resume is None:
        position = position if 0 <= position < len(actions) else 0
    initial_position = resume.initial_position if resume else position
    current = list(frames)
    if resume is None:
        expected = enclosing_loop_starts(structure, position)
        if not structure.unmatched and tuple(frame.start for frame in current) != expected:
            current = [LoopFrame(start, 1) for start in expected]
    processed = resume.processed if resume else 0
    wrapped = resume.wrapped if resume else False
    counter_deltas = list(resume.counter_deltas) if resume else []
    if resume is None:
        for op, name in deferred_counters:
            _counter({"counter": name}, op, counters, counter_deltas)
    while True:
        if position == len(actions):
            position, current = 0, []
            if not wrap_once or wrapped:
                return StepOutcome(None, position, current, reached_end=True,
                                   counter_deltas=tuple(counter_deltas), processed=processed)
            wrapped = True
        if wrapped and position == initial_position:
            return StepOutcome(None, position, current, reached_end=True,
                               counter_deltas=tuple(counter_deltas), processed=processed)
        if not actions:
            return StepOutcome(None, 0, [], reached_end=True,
                               counter_deltas=tuple(counter_deltas), processed=processed)
        action = actions[position]
        if not isinstance(action, Mapping) or action_type(action) != ACTION_TYPE_SYSTEM:
            return StepOutcome(position, position, current,
                               counter_deltas=tuple(counter_deltas),
                               wrapped=wrapped, processed=processed)
        if system_op(action) == OP_CALL:
            return StepOutcome(position, position, current,
                               counter_deltas=tuple(counter_deltas),
                               wrapped=wrapped, processed=processed)
        if processed >= MAX_PROCESSED_SYSTEM_ACTIONS:
            return StepOutcome(
                None, position, current,
                (position, PROCESSED_LIMIT_MESSAGE),
                counter_deltas=tuple(counter_deltas), processed=processed,
            )
        if (in_call and system_op(action) == OP_LOOP_START
                and bool(action.get("infinite"))):
            return StepOutcome(
                None, position, current,
                (position, "呼び出し先に無限ループがあります"),
                counter_deltas=tuple(counter_deltas), wrapped=wrapped,
                processed=processed,
            )
        processed += 1
        if system_op(action) == OP_STOP and stop_ends_run:
            position += 1
            if position == len(actions):
                position, current = 0, []
            return StepOutcome(
                None, position, current, stopped=True,
                counter_deltas=tuple(counter_deltas), wrapped=wrapped,
                processed=processed,
            )
        if system_op(action) == OP_WAIT:
            try:
                wait_ms = int(action.get("ms"))
            except (TypeError, ValueError, OverflowError):
                wait_ms = 0
            if wait_ms < 1:
                return StepOutcome(
                    None, position, current,
                    (position, "待機時間が不正です（1 以上の整数・ミリ秒）"),
                    counter_deltas=tuple(counter_deltas), processed=processed,
                )
            if in_call:
                return StepOutcome(None, position, current, wait_ms=wait_ms,
                                   resume_position=position + 1,
                                   resume=StepResume(
                                       initial_position, wrapped, processed,
                                       tuple(counter_deltas),
                                   ),
                                   counter_deltas=tuple(counter_deltas), processed=processed)
            position += 1
            continue
        op = system_op(action)
        if op in (OP_BACK, OP_REWIND) and len(actions) > 1:
            return StepOutcome(None, position, current,
                               (position, "戻す・先頭へは単独で登録してください"),
                               counter_deltas=tuple(counter_deltas), processed=processed)
        if op in (OP_BACK, OP_REWIND) and on_control is not None:
            on_control(op, control_target(action))
        next_position, error = _system_step(
            actions, position, current, counters, structure, counter_deltas,
        )
        if error:
            return StepOutcome(None, position, current, (position, error),
                               counter_deltas=tuple(counter_deltas), processed=processed)
        position = next_position


def after_normal_action(actions: Sequence[Any], index: int,
                        frames: list[LoopFrame]) -> tuple[int, list[LoopFrame]]:
    if index + 1 >= len(actions):
        return 0, []
    return index + 1, list(frames)


def settle_after_normal(actions: Sequence[Any], position: int,
                        frames: list[LoopFrame], counters: dict[str, int], *,
                        allow_wrap: bool, processed: int = 0,
                        stop_ends_run: bool = False,
                        in_call: bool = False, wait_mode: str = "stop",
                        stop_before_stop: bool = False,
                        wrapped: bool = False,
                        deferred_counters: Sequence[tuple[str, str]] = ()) -> SettleOutcome:
    """Prepare the next step without executing controls or reporting errors."""
    current = list(frames)
    deltas: list[tuple[str, int]] = []
    deferred: list[tuple[str, str]] = list(deferred_counters)
    structure = analyze_loops(actions)
    while True:
        if position == len(actions):
            position, current = 0, []
            if not allow_wrap or wrapped:
                break
            wrapped = True
        if not actions:
            break
        action = actions[position]
        if not isinstance(action, Mapping) or action_type(action) != ACTION_TYPE_SYSTEM:
            break
        op = system_op(action)
        if op == OP_CALL:
            break
        if processed >= MAX_PROCESSED_SYSTEM_ACTIONS:
            break
        if in_call and op == OP_LOOP_START and bool(action.get("infinite")):
            break
        if op == OP_STOP:
            if stop_before_stop:
                break
            if stop_ends_run:
                position += 1
                if position == len(actions):
                    position, current = 0, []
                return SettleOutcome(
                    position, current, tuple(deltas), wrapped,
                    tuple(deferred), stopped=True, processed=processed,
                )
            position += 1
            processed += 1
            continue
        if op == OP_WAIT and wait_mode != "stop" and (not in_call or wait_mode == "skip"):
            try:
                wait_ms = int(action.get("ms"))
            except (TypeError, ValueError, OverflowError):
                wait_ms = 0
            if wait_ms < 1:
                break
            processed += 1
            if wait_mode == "wait":
                return SettleOutcome(
                    position, current, tuple(deltas), wrapped,
                    tuple(deferred), processed=processed, wait_ms=wait_ms,
                )
            position += 1
            continue
        if op not in (OP_LOOP_START, OP_LOOP_END, OP_COUNTER_INC, OP_COUNTER_RESET):
            break
        if op in (OP_COUNTER_INC, OP_COUNTER_RESET):
            value = action.get("counter", "")
            name = value.strip() if isinstance(value, str) else ""
            if not name:
                break
            deferred.append((op, name))
            position += 1
            processed += 1
            continue
        next_position, error = _system_step(
            actions, position, current, counters, structure, deltas,
        )
        if error:
            break
        position = next_position
        processed += 1
    return SettleOutcome(position, current, tuple(deltas), wrapped,
                         tuple(deferred), processed=processed)
