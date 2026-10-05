"""Detached display data for the deepest frame of a call."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType

from keyseq.application.call_context import CallContext
from keyseq.application.sequence_steps import LoopFrame
from keyseq.domain.config import normalize_key_name


@dataclass(frozen=True)
class CallViewSummary:
    path: tuple[str, ...]
    actions: tuple[dict, ...]
    position: int
    loop_frames: tuple[LoopFrame, ...]
    counters: Mapping[str, int]


def build_call_view_summary(
    ctx: CallContext, counters: Mapping[str, int],
) -> CallViewSummary | None:
    """Copy the current actions and progress without changing runtime data."""
    if not ctx.stack:
        return None
    top = ctx.stack[-1]
    entry = ctx.entry_for(top.key)
    return CallViewSummary(
        path=tuple(normalize_key_name(key) for key in
                   (ctx.root_key, *(frame.key for frame in ctx.stack))),
        actions=tuple(deepcopy(entry.actions)) if entry is not None else (),
        position=top.position,
        loop_frames=tuple(deepcopy(top.frames)),
        counters=MappingProxyType(dict(counters)),
    )
