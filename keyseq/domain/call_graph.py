from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from . import sequence_control
from .config import (
    DEFAULT_RUN_TO_END_DELAY_MS,
    coerce_nonnegative_int,
    normalize_key_name,
)


@dataclass(frozen=True)
class CallEntry:
    actions: tuple[dict, ...]
    interval_ms: int


def call_target(action: Any) -> str:
    if not isinstance(action, Mapping):
        return ""
    if (
        sequence_control.action_type(action) != sequence_control.ACTION_TYPE_SYSTEM
        or sequence_control.system_op(action) != sequence_control.OP_CALL
    ):
        return ""
    target = action.get("target")
    return normalize_key_name(target) if isinstance(target, str) else ""


def call_targets(actions: Sequence[Any]) -> list[str]:
    return [target for action in actions if (target := call_target(action))]


def _entry(trigger: Mapping[str, Any] | None) -> CallEntry | None:
    if trigger is None:
        return None
    actions = trigger.get("actions", [])
    if not isinstance(actions, (list, tuple)):
        actions = []
    copied = tuple(deepcopy(action) for action in actions if isinstance(action, dict))
    interval = coerce_nonnegative_int(
        trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
        DEFAULT_RUN_TO_END_DELAY_MS,
    )
    return CallEntry(actions=copied, interval_ms=interval)


def collect_call_snapshot(
    target_key: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None],
) -> dict[str, CallEntry | None]:
    root = normalize_key_name(target_key)
    snapshot: dict[str, CallEntry | None] = {}
    depths = {root: 1}
    pending = deque([root])
    while pending:
        key = pending.popleft()
        depth = depths[key]
        entry = _entry(find_trigger(key))
        snapshot[key] = entry
        if entry is None or depth >= sequence_control.MAX_CALL_DEPTH:
            continue
        for child in call_targets(entry.actions):
            if child in snapshot or child in depths:
                continue
            if depth + 1 <= sequence_control.MAX_CALL_DEPTH:
                depths[child] = depth + 1
                pending.append(child)
    return snapshot


def edit_call_violation(
    owner_key: str,
    target_key: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None],
) -> str | None:
    owner = normalize_key_name(owner_key)
    target = normalize_key_name(target_key)
    if not target:
        return "呼び出し先を選んでください"

    target_trigger = find_trigger(target)
    if target_trigger is None:
        return f"呼び出し先のトリガーがありません（{target}）"
    if target == owner:
        return "自分自身は呼び出せません"

    path = _path_to_owner(target, owner, find_trigger)
    if path is not None:
        return f"呼び出しが循環します（{' > '.join(path)}）"

    if _downstream_depth(target, find_trigger) + 1 > sequence_control.MAX_CALL_DEPTH:
        return f"呼び出しの深さが {sequence_control.MAX_CALL_DEPTH} を超えます"

    actions = target_trigger.get("actions", [])
    if isinstance(actions, (list, tuple)) and len(actions) == 1:
        action = actions[0]
        if (
            isinstance(action, Mapping)
            and sequence_control.action_type(action) == sequence_control.ACTION_TYPE_SYSTEM
            and sequence_control.system_op(action)
            in (sequence_control.OP_BACK, sequence_control.OP_REWIND)
        ):
            return "戻す・先頭へのトリガーは呼び出せません"
    return None


def _path_to_owner(
    start: str,
    owner: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None],
) -> list[str] | None:
    pending: deque[tuple[str, list[str]]] = deque([(start, [start])])
    visited = {start}
    while pending:
        key, path = pending.popleft()
        trigger = find_trigger(key)
        if trigger is None:
            continue
        for child in _trigger_targets(trigger):
            if child == owner:
                return [*path, owner]
            if child not in visited:
                visited.add(child)
                pending.append((child, [*path, child]))
    return None


def _downstream_depth(
    start: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None],
) -> int:
    deepest = 0
    pending: deque[tuple[str, int, frozenset[str]]] = deque([(start, 0, frozenset({start}))])
    while pending:
        key, depth, path = pending.popleft()
        trigger = find_trigger(key)
        if trigger is None:
            continue
        for child in _trigger_targets(trigger):
            child_depth = depth + 1
            deepest = max(deepest, child_depth)
            if child not in path and child_depth < sequence_control.MAX_CALL_DEPTH:
                pending.append((child, child_depth, path | {child}))
    return deepest


def _trigger_targets(trigger: Mapping[str, Any]) -> list[str]:
    actions = trigger.get("actions", [])
    return call_targets(actions) if isinstance(actions, (list, tuple)) else []
