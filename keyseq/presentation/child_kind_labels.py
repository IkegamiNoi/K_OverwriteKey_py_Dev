"""子ファイルの種類と親の表示名を返す純関数。"""

from keyseq.application.config_service.contracts import (
    KIND_KEYMAP,
    KIND_SEQUENCE,
    KIND_TRIGGER_SET,
)
from keyseq.shared.i18n import tr


KIND_LABELS: dict[str, str] = {
    KIND_KEYMAP: "child_kind.keymap",
    KIND_TRIGGER_SET: "child_kind.trigger_set",
    KIND_SEQUENCE: "child_kind.sequence",
}


def kind_label(kind: str) -> str:
    key = KIND_LABELS.get(kind)
    return tr(key) if key is not None else kind


def parent_kind_label(kind: str) -> str:
    key = {
        KIND_KEYMAP: "child_kind.parent_keymap",
        KIND_TRIGGER_SET: "child_kind.parent_trigger_set",
        KIND_SEQUENCE: "child_kind.parent_sequence",
    }[kind]
    return tr(key)
