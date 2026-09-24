"""アクティブキーマップの保持を読む口。

呼び出し側はトップレベル ``triggers`` を直接触らないこと。
"""

from __future__ import annotations

from typing import Any


def _active_keymap(data: dict[str, Any]) -> dict[str, Any] | None:
    keymaps = data.get("keymaps")
    if data.get("active_keymap_id") and isinstance(keymaps, list):
        for keymap in keymaps:
            if isinstance(keymap, dict) and keymap.get("id") == data.get("active_keymap_id"):
                return keymap
    return None


def ensure_at_least_one_keymap(data: dict[str, Any]) -> dict[str, Any] | None:
    """キーマップがない場合だけ、既存採番規則の最初の要素を作る。"""
    if isinstance(data.get("keymaps"), list) and data["keymaps"]:
        return None
    created = {"id": "keymap_1", "label": "", "mappings": {}}
    data["keymaps"] = [created]
    data["active_keymap_id"] = created["id"]
    return created


def _ensure_active_keymap(data: dict[str, Any]) -> dict[str, Any]:
    ensure_at_least_one_keymap(data)
    current = _active_keymap(data)
    if current is None:
        current = data["keymaps"][0]
        data["active_keymap_id"] = current["id"]
    return current


def migrate_single_json_triggers(data: dict[str, Any]) -> str:
    """正規化済みの単一 JSON の旧一覧を、読込時に一度だけ移行する。"""
    current = _ensure_active_keymap(data)
    legacy = data.get("triggers", [])
    state = "none"
    if legacy:
        state = "unused" if "triggers" in current else "migrated"
        if state == "migrated":
            current["triggers"] = legacy
    for keymap in data["keymaps"]:
        keymap.setdefault("triggers", [])
    data["triggers"] = []
    return state


def get_active_triggers(data: dict[str, Any]) -> list[dict[str, Any]]:
    """トリガー一覧の実体を返す。未設定・非 list なら新しい空 list を返す。"""
    current = _active_keymap(data)
    triggers = current.get("triggers") if current is not None else None
    if isinstance(triggers, list):
        return triggers
    return []


def ensure_active_triggers(data: dict[str, Any]) -> list[dict[str, Any]]:
    """トリガー一覧を確保し、格納された実体を返す。"""
    current = _ensure_active_keymap(data)
    triggers = current.get("triggers")
    if not isinstance(triggers, list):
        triggers = []
        current["triggers"] = triggers
    return triggers


def set_active_triggers(data: dict[str, Any], triggers: list[dict[str, Any]]) -> None:
    """渡されたトリガー一覧の実体を格納する。"""
    _ensure_active_keymap(data)["triggers"] = triggers
