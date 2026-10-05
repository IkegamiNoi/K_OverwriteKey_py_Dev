from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable


ACTION_TYPE_SYSTEM: str = "system"
ACTION_TYPE_FILE_LINE: str = "file_line"

OP_LOOP_START: str = "loop_start"
OP_LOOP_END: str = "loop_end"
OP_COUNTER_INC: str = "counter_inc"
OP_COUNTER_RESET: str = "counter_reset"
OP_WAIT: str = "wait"
OP_BACK: str = "back"
OP_REWIND: str = "rewind"
OP_STOP: str = "stop"
OP_CALL: str = "call"

MAX_LOOP_DEPTH: int = 9
MAX_CALL_DEPTH: int = 9

ENCODING_UTF_8: str = "utf-8"
ENCODING_SHIFT_JIS: str = "shift_jis"
OUT_OF_RANGE_ERROR: str = "error"
OUT_OF_RANGE_EMPTY: str = "empty"
OUT_OF_RANGE_WRAP: str = "wrap"
DEFAULT_ENCODING: str = ENCODING_UTF_8
DEFAULT_OUT_OF_RANGE: str = OUT_OF_RANGE_ERROR


def action_type(action: Mapping[str, Any]) -> str:
    value = action.get("type")
    return value.strip().lower() if isinstance(value, str) else ""


def system_op(action: Mapping[str, Any]) -> str:
    value = action.get("op")
    return value.strip().lower() if isinstance(value, str) else ""


def control_target(action: Mapping[str, Any]) -> str | None:
    if action_type(action) != ACTION_TYPE_SYSTEM or system_op(action) not in (OP_BACK, OP_REWIND):
        return None
    if "target" not in action:
        return None
    target = action.get("target")
    # config imports this module, so keep key normalization inline to avoid a cycle.
    return target.strip().lower() if isinstance(target, str) else ""


def is_step_call(action: Mapping[str, Any]) -> bool:
    return (
        action_type(action) == ACTION_TYPE_SYSTEM
        and system_op(action) == OP_CALL
        and not bool(action.get("all"))
    )


def is_all_call(action: Mapping[str, Any]) -> bool:
    return (
        action_type(action) == ACTION_TYPE_SYSTEM
        and system_op(action) == OP_CALL
        and bool(action.get("all"))
    )


@dataclass(frozen=True)
class LoopStructure:
    pairs: Mapping[int, int]
    reverse_pairs: Mapping[int, int]
    depth: tuple[int, ...]
    unmatched: frozenset[int]
    too_deep: frozenset[int]


def analyze_loops(actions: Sequence[Any]) -> LoopStructure:
    stack: list[int] = []
    pairs: dict[int, int] = {}
    unmatched: set[int] = set()
    starts: set[int] = set()
    ends: set[int] = set()

    for position, action in enumerate(actions):
        if not isinstance(action, Mapping) or action_type(action) != ACTION_TYPE_SYSTEM:
            continue
        op = system_op(action)
        if op == OP_LOOP_START:
            stack.append(position)
            starts.add(position)
        elif op == OP_LOOP_END:
            ends.add(position)
            if stack:
                pairs[stack.pop()] = position
            else:
                unmatched.add(position)

    unmatched.update(stack)
    return _build_loop_structure(len(actions), pairs, unmatched, starts, ends)


def _build_loop_structure(
    length: int,
    pairs: dict[int, int],
    unmatched: set[int],
    starts: set[int],
    ends: set[int],
) -> LoopStructure:
    reverse_pairs = {end: start for start, end in pairs.items()}
    depths = [0] * length
    too_deep: set[int] = set()
    active: list[int] = []

    for position in range(length):
        if position in pairs:
            depth = len(active) + 1
            depths[position] = depth
            active.append(position)
            if depth > MAX_LOOP_DEPTH:
                too_deep.add(position)
        elif position in reverse_pairs:
            depths[position] = len(active)
            active.pop()
        elif position not in starts and position not in ends:
            depths[position] = len(active)

    return LoopStructure(
        pairs=MappingProxyType(dict(pairs)),
        reverse_pairs=MappingProxyType(reverse_pairs),
        depth=tuple(depths),
        unmatched=frozenset(unmatched),
        too_deep=frozenset(too_deep),
    )


def enclosing_loop_starts(structure: LoopStructure, position: int) -> tuple[int, ...]:
    if position < 0 or position >= len(structure.depth):
        return ()
    return tuple(
        start
        for start in sorted(structure.pairs)
        if start < position <= structure.pairs[start]
    )


def loop_depth_style(depth: int) -> tuple[str, str] | None:
    if not isinstance(depth, int) or isinstance(depth, bool) or not 1 <= depth <= MAX_LOOP_DEPTH:
        return None
    colors = ("blue", "green", "orange")
    shades = ("light", "medium", "dark")
    return colors[(depth - 1) % len(colors)], shades[(depth - 1) // len(colors)]


def format_control_value(
    action: Mapping[str, Any],
    *,
    loop_iteration: int | None = None,
    counters: Mapping[str, Any] | None = None,
    resolve_call: Callable[[Any], tuple[str, str | None]] | None = None,
) -> str:
    kind = action_type(action)
    if kind == ACTION_TYPE_SYSTEM:
        return _format_system_value(action, loop_iteration, counters, resolve_call)
    if kind == ACTION_TYPE_FILE_LINE:
        return _format_file_line_value(action, counters)
    return ""


def _format_system_value(
    action: Mapping[str, Any],
    loop_iteration: int | None,
    counters: Mapping[str, Any] | None,
    resolve_call: Callable[[Any], tuple[str, str | None]] | None,
) -> str:
    op = system_op(action)
    if op == OP_LOOP_START:
        count = "∞" if bool(action.get("infinite")) else str(action.get("count", ""))
        if loop_iteration is None:
            return f"[loop] ×{count}"
        return f"[loop] {loop_iteration}/{count}"
    if op == OP_LOOP_END:
        return "[loop_end]"
    if op == OP_COUNTER_INC:
        return _format_counter_value("[count+1]", action, counters)
    if op == OP_COUNTER_RESET:
        return _format_counter_value("[count=0]", action, counters)
    if op == OP_WAIT:
        return f"[wait] {action.get('ms', '')}ms"
    if op == OP_BACK:
        return _format_control_target("[back]", action, resolve_call)
    if op == OP_REWIND:
        return _format_control_target("[rewind]", action, resolve_call)
    if op == OP_STOP:
        return "[stop]"
    if op == OP_CALL:
        display_name = "[call all]" if is_all_call(action) else "[call]"
        target = action.get("target")
        if resolve_call is None:
            if not isinstance(target, str) or not target.strip():
                return f"{display_name} （呼び出し先なし）"
            return f"{display_name} {target.strip()}"
        key, label = resolve_call(target)
        if label is None:
            return f"{display_name} {key}（参照先なし）"
        if label:
            return f"{display_name} {key}（{label}）"
        return f"{display_name} {key}"
    return f"[system] {action.get('op', '')}"


def _format_control_target(
    display_name: str,
    action: Mapping[str, Any],
    resolve_call: Callable[[Any], tuple[str, str | None]] | None,
) -> str:
    target = control_target(action)
    if target is None:
        return display_name
    if not target:
        return f"{display_name} → （参照先なし）"
    if resolve_call is None:
        return f"{display_name} → {target}"
    key, label = resolve_call(action.get("target"))
    if label is None:
        return f"{display_name} → {key}（参照先なし）"
    return f"{display_name} → {key}"


def _format_counter_value(
    display_name: str,
    action: Mapping[str, Any],
    counters: Mapping[str, Any] | None,
) -> str:
    counter_name = str(action.get("counter", ""))
    value = counters.get(counter_name, 0) if counters is not None else 0
    return f"{display_name} {counter_name} (={value})"


def _format_file_line_value(action: Mapping[str, Any], counters: Mapping[str, Any] | None) -> str:
    path = str(action.get("path", ""))
    filename = path.replace("\\", "/").rsplit("/", 1)[-1]
    counter_name = str(action.get("counter", ""))
    value = counters.get(counter_name, 0) if counters is not None else 0
    return f"[file_line] {filename} #{counter_name} (={value})"
