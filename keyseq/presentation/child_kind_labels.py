"""子ファイルの種類と親の表示名を返す純関数。"""

from keyseq.application.config_service.contracts import (
    KIND_KEYMAP,
    KIND_SEQUENCE,
    KIND_TRIGGER_SET,
)


KIND_LABELS: dict[str, str] = {
    KIND_KEYMAP: "キーマップ",
    KIND_TRIGGER_SET: "トリガーセット",
    KIND_SEQUENCE: "出力シーケンス",
}


def kind_label(kind: str) -> str:
    return KIND_LABELS.get(kind, kind)


def parent_kind_label(kind: str) -> str:
    return {
        KIND_KEYMAP: "構成セット",
        KIND_TRIGGER_SET: KIND_LABELS[KIND_KEYMAP],
        KIND_SEQUENCE: KIND_LABELS[KIND_TRIGGER_SET],
    }[kind]
