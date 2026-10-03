from __future__ import annotations

from dataclasses import dataclass

from keyseq.domain.config import normalize_key_name


CHILD_KEYMAP = "keymap"
CHILD_TRIGGER_SET = "trigger_set"
CHILD_SEQUENCE = "sequence"

ACTION_SAVE = "save"
ACTION_SAVE_AS = "save_as"
ACTION_SKIP = "skip"

SEQUENCE_KEY_SEPARATOR = "\x1f"


def sequence_row_token(trigger_key: str, occurrence: int = 1) -> str:
    """同じキーの行を出現順で区別する。最初の行はキーそのもの。"""
    if (
        not trigger_key or SEQUENCE_KEY_SEPARATOR in trigger_key
        or not isinstance(occurrence, int) or isinstance(occurrence, bool)
        or occurrence < 1
    ):
        raise SavePlanError("sequence の行識別子が不正です。")
    if occurrence == 1:
        return trigger_key
    return SEQUENCE_KEY_SEPARATOR.join((trigger_key, str(occurrence)))


def split_sequence_row_token(token: str) -> tuple[str, int]:
    parts = token.split(SEQUENCE_KEY_SEPARATOR)
    if len(parts) not in (1, 2) or not parts[0]:
        raise SavePlanError("sequence の行識別子が不正です。")
    occurrence = 1
    if len(parts) == 2:
        try:
            occurrence = int(parts[1])
        except ValueError as exc:
            raise SavePlanError("sequence の行番号が不正です。") from exc
        if occurrence < 2:
            raise SavePlanError("sequence の行番号が不正です。")
    return parts[0], occurrence


def compose_sequence_key(trigger_set_id: str, trigger_key: str, occurrence: int = 1) -> str:
    """保存計画の sequence 識別子。曖昧になる入力は拒否する。"""
    if not trigger_set_id or not trigger_key or any(
        SEQUENCE_KEY_SEPARATOR in value for value in (trigger_set_id, trigger_key)
    ):
        raise SavePlanError("sequence の識別子が不正です。")
    return SEQUENCE_KEY_SEPARATOR.join((trigger_set_id, sequence_row_token(trigger_key, occurrence)))


def split_sequence_key(key: str) -> tuple[str, str, int]:
    parts = key.split(SEQUENCE_KEY_SEPARATOR)
    if len(parts) not in (2, 3) or not all(parts):
        raise SavePlanError("sequence の合成キーが不正です。")
    trigger_key, occurrence = split_sequence_row_token(SEQUENCE_KEY_SEPARATOR.join(parts[1:]))
    return parts[0], trigger_key, occurrence


def sequence_rows(triggers) -> list[tuple[dict, str, int]]:
    """保存可能な行を正規化キーと同じキーの出現番号付きで返す。"""
    rows: list[tuple[dict, str, int]] = []
    counts: dict[str, int] = {}
    for trigger in triggers:
        if not isinstance(trigger, dict):
            continue
        key = normalize_key_name(str(trigger.get("key") or ""))
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
        rows.append((trigger, key, counts[key]))
    return rows


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
