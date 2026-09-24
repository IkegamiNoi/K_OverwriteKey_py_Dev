from __future__ import annotations

from dataclasses import dataclass


CHILD_KEYMAP = "keymap"
CHILD_TRIGGER_SET = "trigger_set"
CHILD_SEQUENCE = "sequence"

ACTION_SAVE = "save"
ACTION_SAVE_AS = "save_as"
ACTION_SKIP = "skip"

SEQUENCE_KEY_SEPARATOR = "\x1f"


def compose_sequence_key(trigger_set_id: str, trigger_key: str) -> str:
    """保存計画の sequence 識別子。曖昧になる入力は拒否する。"""
    if not trigger_set_id or not trigger_key or any(
        SEQUENCE_KEY_SEPARATOR in value for value in (trigger_set_id, trigger_key)
    ):
        raise SavePlanError("sequence の識別子が不正です。")
    return SEQUENCE_KEY_SEPARATOR.join((trigger_set_id, trigger_key))


def split_sequence_key(key: str) -> tuple[str, str]:
    parts = key.split(SEQUENCE_KEY_SEPARATOR)
    if len(parts) != 2 or not all(parts):
        raise SavePlanError("sequence の合成キーが不正です。")
    return parts[0], parts[1]


@dataclass(frozen=True)
class ChildSaveEntry:
    kind: str
    key: str
    action: str
    target_path: str = ""


@dataclass(frozen=True)
class SavePlan:
    entries: tuple[ChildSaveEntry, ...] = ()
    allow_deferred_index: bool = False

    def entry_for(self, kind: str, key: str) -> ChildSaveEntry | None:
        for entry in self.entries:
            if entry.kind == kind and entry.key == key:
                return entry
        return None


class SavePlanError(ValueError):
    """保存計画の事前検証に失敗した（この例外が出たときは 1 バイトも書いていない）。"""
