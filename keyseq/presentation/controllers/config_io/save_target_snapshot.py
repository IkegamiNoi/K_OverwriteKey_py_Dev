"""Identity snapshots for trigger sets involved in a save operation."""

from dataclasses import dataclass
from typing import Any

from keyseq.domain.keymap_triggers import (
    iter_trigger_sets,
    keymap_trigger_list,
    trigger_set_owner,
)


SAVE_TARGET_CHANGED_MESSAGE = (
    "保存の準備中にトリガー一覧が変わったため、保存を中止しました。もう一度保存してください。"
)


@dataclass(frozen=True)
class SaveTargetSnapshot:
    """References that identify the trigger sets and row order at plan time."""

    trigger_sets: tuple[
        tuple[
            dict[str, Any],
            list[dict[str, Any]] | None,
            tuple[dict[str, Any], ...],
        ], ...
    ]
    active_representative: dict[str, Any] | None
    active_only: bool


def _snapshot_entry(
    representative: dict[str, Any],
    triggers: list[dict[str, Any]],
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]] | None,
    tuple[dict[str, Any], ...],
]:
    trigger_list = keymap_trigger_list(representative)
    return (
        representative,
        trigger_list,
        tuple(triggers),
    )


def capture_all(data: dict[str, Any]) -> SaveTargetSnapshot:
    """Capture each trigger set and its row order by object reference."""
    entries = tuple(
        _snapshot_entry(representative, triggers)
        for representative, _, triggers in iter_trigger_sets(data)
    )
    return SaveTargetSnapshot(entries, None, False)


def capture_active(data: dict[str, Any]) -> SaveTargetSnapshot:
    """Capture only the active trigger set and its representative."""
    owner = trigger_set_owner(data)
    entry = next(
        (
            _snapshot_entry(representative, triggers)
            for representative, _, triggers in iter_trigger_sets(data)
            if representative is owner
        ),
        None,
    )
    return SaveTargetSnapshot(
        () if entry is None else (entry,),
        owner if entry is not None else None,
        True,
    )


def snapshot_matches(data: dict[str, Any], snapshot: SaveTargetSnapshot) -> bool:
    """Return whether all captured containers, representatives and rows still match."""
    current = capture_active(data) if snapshot.active_only else capture_all(data)
    if snapshot.active_only and current.active_representative is not snapshot.active_representative:
        return False
    if len(current.trigger_sets) != len(snapshot.trigger_sets):
        return False
    for before, after in zip(snapshot.trigger_sets, current.trigger_sets):
        if before[0] is not after[0]:
            return False
        if before[1] is not None and before[1] is not after[1]:
            return False
        if len(before[2]) != len(after[2]) or any(
            left is not right for left, right in zip(before[2], after[2])
        ):
            return False
    return True
