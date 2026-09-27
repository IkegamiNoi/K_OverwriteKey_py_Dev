from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from keyseq.domain.sequence_control import (
    ACTION_TYPE_SYSTEM, OP_BACK, OP_COUNTER_INC, OP_COUNTER_RESET,
    OP_LOOP_END, OP_LOOP_START, OP_REWIND, OP_WAIT, action_type,
    analyze_loops, enclosing_loop_starts, system_op,
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


def format_system_error_notification(
    action: dict[str, Any], message: str,
) -> tuple[dict[str, Any], str]:
    """Copy a system action and add its readable operation value for notification."""
    notified = action.copy()
    op = str(action.get("op") or "(なし)")
    if op == "loop_start":
        value = "無限" if action.get("infinite") else f"回数={action.get('count', '(なし)')}"
    elif op == "wait":
        value = f"{action.get('ms', '(なし)')}ms"
    elif op in ("counter_inc", "counter_reset"):
        value = f"カウンター={action.get('counter', '(なし)')}"
    else:
        value = ""
    detail = f"{op} {value}".rstrip()
    notified["value"] = detail
    label = action.get("label")
    if isinstance(label, str) and label.strip():
        detail += f" / ラベル: {label.strip()}"
    return notified, f"system 実行エラー（{detail}）: {message}"


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


@dataclass
class SettleOutcome:
    position: int
    frames: list[LoopFrame]
    counter_deltas: tuple[tuple[str, int], ...]
    wrapped: bool = False


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
        return position, "ループの入れ子が 9 段を超えています"
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
    return position, f"system の操作が不正です。操作: {op}"


def advance(actions: Sequence[Any], position: int, frames: list[LoopFrame],
            counters: dict[str, int], *, wrap_once: bool,
            resume: StepResume | None = None,
            on_control: Callable[[str], None] | None = None) -> StepOutcome:
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
    while True:
        if position == len(actions):
            position, current = 0, []
            if not wrap_once or wrapped:
                return StepOutcome(None, position, current, reached_end=True,
                                   counter_deltas=tuple(counter_deltas))
            wrapped = True
        if wrapped and position == initial_position:
            return StepOutcome(None, position, current, reached_end=True,
                               counter_deltas=tuple(counter_deltas))
        if not actions:
            return StepOutcome(None, 0, [], reached_end=True,
                               counter_deltas=tuple(counter_deltas))
        action = actions[position]
        if not isinstance(action, Mapping) or action_type(action) != ACTION_TYPE_SYSTEM:
            return StepOutcome(position, position, current,
                               counter_deltas=tuple(counter_deltas),
                               wrapped=wrapped, processed=processed)
        if processed >= 10000:
            return StepOutcome(
                None, position, current,
                (position, "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）"),
                counter_deltas=tuple(counter_deltas),
            )
        processed += 1
        if system_op(action) == OP_WAIT:
            try:
                wait_ms = int(action.get("ms"))
            except (TypeError, ValueError, OverflowError):
                wait_ms = 0
            if wait_ms < 1:
                return StepOutcome(
                    None, position, current,
                    (position, "待機時間が不正です（1 以上の整数・ミリ秒）"),
                    counter_deltas=tuple(counter_deltas),
                )
            return StepOutcome(None, position, current, wait_ms=wait_ms,
                               resume_position=position + 1,
                               resume=StepResume(
                                   initial_position, wrapped, processed,
                                   tuple(counter_deltas),
                               ),
                               counter_deltas=tuple(counter_deltas))
        op = system_op(action)
        if op in (OP_BACK, OP_REWIND) and on_control is not None:
            on_control(op)
        next_position, error = _system_step(
            actions, position, current, counters, structure, counter_deltas,
        )
        if error:
            return StepOutcome(None, position, current, (position, error),
                               counter_deltas=tuple(counter_deltas))
        position = next_position


def after_normal_action(actions: Sequence[Any], index: int,
                        frames: list[LoopFrame]) -> tuple[int, list[LoopFrame]]:
    if index + 1 >= len(actions):
        return 0, []
    return index + 1, list(frames)


def settle_after_normal(actions: Sequence[Any], position: int,
                        frames: list[LoopFrame], counters: dict[str, int], *,
                        allow_wrap: bool, processed: int = 0) -> SettleOutcome:
    """Prepare the next step without executing controls or reporting errors."""
    current = list(frames)
    deltas: list[tuple[str, int]] = []
    structure = analyze_loops(actions)
    wrapped = False
    while True:
        if position == len(actions):
            position, current = 0, []
            if not allow_wrap or wrapped:
                break
            wrapped = True
        if not actions or processed >= 10000:
            break
        action = actions[position]
        if not isinstance(action, Mapping) or action_type(action) != ACTION_TYPE_SYSTEM:
            break
        op = system_op(action)
        if op not in (OP_LOOP_START, OP_LOOP_END, OP_COUNTER_INC, OP_COUNTER_RESET):
            break
        next_position, error = _system_step(
            actions, position, current, counters, structure, deltas,
        )
        if error:
            break
        position = next_position
        processed += 1
    return SettleOutcome(position, current, tuple(deltas), wrapped)
