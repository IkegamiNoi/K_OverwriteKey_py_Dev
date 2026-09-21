"""構成セット履歴の遅延作成、破損退避、記録を担当する。"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from keyseq.domain import keymap_set_history as domain
from . import contracts

if TYPE_CHECKING:
    from . import ConfigService


def history_absolute_path(service: ConfigService, *, config_root: str) -> str:
    return service.resolve_config_path(service.KEYMAP_SET_HISTORY_RELATIVE_PATH, config_root)


def _recover_history(path: str) -> str:
    """空いている退避先へ移し、退避できない場合は書き込みを禁止する。"""
    for suffix in ("", "2", "3", "4", "5"):
        destination = os.path.join(
            os.path.dirname(path), f"keymap_set_history.broken{suffix}.json",
        )
        if os.path.exists(destination):
            continue
        try:
            os.replace(path, destination)
        except Exception:
            return contracts.HISTORY_READ_ONLY
        return contracts.HISTORY_RECOVERED
    return contracts.HISTORY_READ_ONLY


def load_history(
    service: ConfigService, *, config_root: str,
) -> tuple[dict[str, Any], str]:
    """不在と破損を区別し、読み込みだけではファイルを作らない。"""
    path = history_absolute_path(service, config_root=config_root)
    if not os.path.exists(path):
        return domain.normalize_history({}), contracts.HISTORY_OK
    try:
        raw = service.repository.load_json(path)
    except Exception:
        return domain.normalize_history({}), _recover_history(path)
    if isinstance(raw, dict):
        return domain.normalize_history(raw), contracts.HISTORY_OK
    return domain.normalize_history({}), _recover_history(path)


def save_history(
    service: ConfigService, history: dict[str, Any], *, config_root: str,
) -> tuple[bool, str]:
    """正規化した履歴を原子的に保存し、失敗理由を返す。"""
    try:
        service.repository.save_json(
            history_absolute_path(service, config_root=config_root),
            domain.normalize_history(history),
        )
    except Exception as exc:
        return False, f"履歴ファイルを保存できませんでした: {exc}"
    return True, ""


def record(
    service: ConfigService, path: str, *, config_root: str,
) -> tuple[bool, str]:
    """永続化済みの先頭と比較し、変更があるときだけ記録する。"""
    history, status = load_history(service, config_root=config_root)
    if status == contracts.HISTORY_READ_ONLY:
        return False, "履歴ファイルを読み込めず、退避もできないため記録できません。"
    if not path.strip():
        return False, "構成セットのパスが空のため履歴を記録できません。"
    stored = service.to_config_relative_or_absolute(path, config_root)
    key_of = lambda p: service.canonical_path(p, config_root)
    if domain.is_recent_head(history, stored, key_of=key_of):
        return True, ""
    return save_history(
        service, domain.push_recent(history, stored, key_of=key_of),
        config_root=config_root,
    )
