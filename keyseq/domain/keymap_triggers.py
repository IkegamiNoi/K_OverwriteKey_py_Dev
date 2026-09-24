"""task_01b でキーマップごとの保持へ差し替える口。

呼び出し側はトップレベル ``triggers`` を直接触らないこと。
"""

from __future__ import annotations

from typing import Any


def get_active_triggers(data: dict[str, Any]) -> list[dict[str, Any]]:
    """トリガー一覧の実体を返す。未設定・非 list なら新しい空 list を返す。"""
    triggers = data.get("triggers")
    if isinstance(triggers, list):
        return triggers
    return []


def ensure_active_triggers(data: dict[str, Any]) -> list[dict[str, Any]]:
    """トリガー一覧を確保し、格納された実体を返す。"""
    triggers = data.get("triggers")
    if not isinstance(triggers, list):
        triggers = []
        data["triggers"] = triggers
    return triggers


def set_active_triggers(data: dict[str, Any], triggers: list[dict[str, Any]]) -> None:
    """渡されたトリガー一覧の実体を格納する。"""
    data["triggers"] = triggers
