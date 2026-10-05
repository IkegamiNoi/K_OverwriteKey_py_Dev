from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from . import sequence_control
from .config import normalize_key_name


def edit_control_target_violation(
    owner_key: str,
    target_key: str,
    find_trigger: Callable[[str], Mapping[str, Any] | None],
) -> str | None:
    target = normalize_key_name(target_key)
    if not target:
        return "対象のトリガーを選んでください"

    target_trigger = find_trigger(target)
    if target_trigger is None:
        return f"対象のトリガーがありません（{target}）"
    if target == normalize_key_name(owner_key):
        return "自分自身は指定できません"

    actions = target_trigger.get("actions")
    if (
        isinstance(actions, Sequence)
        and not isinstance(actions, (str, bytes))
        and len(actions) == 1
        and isinstance(actions[0], Mapping)
        and sequence_control.action_type(actions[0]) == sequence_control.ACTION_TYPE_SYSTEM
        and sequence_control.system_op(actions[0])
        in (sequence_control.OP_BACK, sequence_control.OP_REWIND)
    ):
        return "戻す・先頭へのトリガーは指定できません"
    return None


def rename_control_targets(
    actions: Sequence[dict], old_key: str, new_key: str
) -> list[dict] | None:
    old = normalize_key_name(old_key)
    new = normalize_key_name(new_key)
    if not old or old == new:
        return None

    renamed: list[dict] = []
    changed = False
    for action in actions:
        copied = dict(action)
        if sequence_control.control_target(action) == old:
            copied["target"] = new
            changed = True
        renamed.append(copied)
    return renamed if changed else None
