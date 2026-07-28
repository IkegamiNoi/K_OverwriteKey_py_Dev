from __future__ import annotations

from dataclasses import dataclass


CHILD_KEYMAP = "keymap"
CHILD_TRIGGER_SET = "trigger_set"
CHILD_SEQUENCE = "sequence"

ACTION_SAVE = "save"
ACTION_SAVE_AS = "save_as"
ACTION_SKIP = "skip"


@dataclass(frozen=True)
class ChildSaveEntry:
    kind: str
    key: str
    action: str
    target_path: str = ""


@dataclass(frozen=True)
class SavePlan:
    entries: tuple[ChildSaveEntry, ...] = ()

    def entry_for(self, kind: str, key: str = "") -> ChildSaveEntry | None:
        for entry in self.entries:
            if entry.kind == kind and entry.key == key:
                return entry
        return None


class SavePlanError(ValueError):
    """保存計画の事前検証に失敗した（この例外が出たときは 1 バイトも書いていない）。"""
