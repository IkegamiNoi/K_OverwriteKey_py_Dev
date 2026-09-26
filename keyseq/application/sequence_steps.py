from __future__ import annotations

from collections.abc import Mapping, Sequence
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


@dataclass
class StepOutcome:
    normal_index: int | None
    position: int
    frames: list[LoopFrame]
    error: tuple[int, str] | None = None
    reached_end: bool = False


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


def _counter(action: Mapping[str, Any], op: str, counters: dict[str, int]) -> str | None:
    value = action.get("counter", "")
    name = value.strip() if isinstance(value, str) else ""
    if not name:
        return "カウンター名が空です"
    counters[name] = counters.get(name, 0) + 1 if op == OP_COUNTER_INC else 0
    return None


def _system_step(actions: Sequence[Any], position: int, frames: list[LoopFrame],
                 counters: dict[str, int], structure: Any) -> tuple[int, str | None]:
    action = actions[position]
    op = system_op(action)
    if op == OP_LOOP_START:
        return _loop_start(action, position, frames, structure)
    if op == OP_LOOP_END:
        return _loop_end(actions, position, frames, structure)
    if op in (OP_COUNTER_INC, OP_COUNTER_RESET):
        return position + 1, _counter(action, op, counters)
    # wait / back / rewind are handled by later execution-core tasks.
    if op in (OP_WAIT, OP_BACK, OP_REWIND):
        return position + 1, None
    return position, f"system の操作が不正です。操作: {op}"


def advance(actions: Sequence[Any], position: int, frames: list[LoopFrame],
            counters: dict[str, int], *, wrap_once: bool) -> StepOutcome:
    structure = analyze_loops(actions)
    position = position if 0 <= position < len(actions) else 0
    initial_position = position
    current = list(frames)
    expected = enclosing_loop_starts(structure, position)
    if not structure.unmatched and tuple(frame.start for frame in current) != expected:
        current = [LoopFrame(start, 1) for start in expected]
    processed = 0
    wrapped = False
    while True:
        if position == len(actions):
            position, current = 0, []
            if not wrap_once or wrapped:
                return StepOutcome(None, position, current, reached_end=True)
            wrapped = True
        if wrapped and position == initial_position:
            return StepOutcome(None, position, current, reached_end=True)
        if not actions:
            return StepOutcome(None, 0, [], reached_end=True)
        action = actions[position]
        if not isinstance(action, Mapping) or action_type(action) != ACTION_TYPE_SYSTEM:
            return StepOutcome(position, position, current)
        if processed >= 10000:
            return StepOutcome(None, position, current, (position, "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）"))
        processed += 1
        next_position, error = _system_step(actions, position, current, counters, structure)
        if error:
            return StepOutcome(None, position, current, (position, error))
        position = next_position


def after_normal_action(actions: Sequence[Any], index: int,
                        frames: list[LoopFrame]) -> tuple[int, list[LoopFrame]]:
    if index + 1 >= len(actions):
        return 0, []
    return index + 1, list(frames)
