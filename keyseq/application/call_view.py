"""Detached display data for the deepest frame of a call."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType

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
    path: tuple[str, ...], actions: list[dict], position: int,
    frames: list[LoopFrame], counters: Mapping[str, int],
) -> CallViewSummary | None:
    """Copy the current actions and progress without changing runtime data."""
    if len(path) < 2:
        return None
    return CallViewSummary(
        path=tuple(normalize_key_name(key) for key in path),
        actions=tuple(deepcopy(actions)),
        position=position,
        loop_frames=tuple(deepcopy(frames)),
        counters=MappingProxyType(dict(counters)),
    )
