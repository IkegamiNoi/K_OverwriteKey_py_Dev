"""Read the currently marked call chain for one trigger set."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from keyseq.domain import call_graph, sequence_control


def chain_from(
    state: Any,
    trigger_set_id: str,
    key: str,
    find_trigger: Callable[[str], object | None],
    *, positions: Mapping[str, int] | None = None, call_refs: set[str] | None = None,
) -> tuple[str, ...]:
    """Follow active marks, optionally using in-flight positions and marks."""
    with state.lock:
        chain: list[str] = []
        current = key
        while current not in chain:
            chain.append(current)
            if current not in (state.call_refs_for(trigger_set_id) if call_refs is None else call_refs):
                break
            if len(chain) - 1 >= sequence_control.MAX_CALL_DEPTH:
                break
            trigger = find_trigger(current)
            actions = _actions_for(trigger)
            position = (state.indices_for(trigger_set_id) if positions is None else positions).get(current, 0)
            if actions is None or position < 0 or position >= len(actions):
                break
            target = call_graph.call_target(actions[position])
            if not target or target in chain or find_trigger(target) is None:
                break
            current = target
        return tuple(chain)


def chain_top(
    state: Any,
    trigger_set_id: str,
    key: str,
    find_trigger: Callable[[str], object | None],
) -> str:
    """Return the deepest reachable trigger in the current marked chain."""
    return chain_from(state, trigger_set_id, key, find_trigger)[-1]


def _actions_for(trigger: object | None) -> Any:
    if isinstance(trigger, Mapping):
        return trigger.get("actions")
    return getattr(trigger, "actions", None) if trigger is not None else None
