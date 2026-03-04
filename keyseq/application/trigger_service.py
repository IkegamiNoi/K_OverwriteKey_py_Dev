from __future__ import annotations

from typing import Any

from keyseq.domain.config import normalize_key_name


class TriggerService:
    @staticmethod
    def get_triggers(data: dict[str, Any]) -> list[dict[str, Any]]:
        triggers = data.get("triggers", [])
        if isinstance(triggers, list):
            return triggers
        return []

    @staticmethod
    def find_trigger_by_key(data: dict[str, Any], key: str) -> dict[str, Any] | None:
        normalized = normalize_key_name(key)
        for trigger in TriggerService.get_triggers(data):
            if normalize_key_name(trigger.get("key", "")) == normalized:
                return trigger
        return None

    @staticmethod
    def key_exists(
        data: dict[str, Any],
        key: str,
        exclude_trigger: dict[str, Any] | None = None,
    ) -> bool:
        normalized = normalize_key_name(key)
        for trigger in TriggerService.get_triggers(data):
            if exclude_trigger is not None and trigger is exclude_trigger:
                continue
            if normalize_key_name(trigger.get("key", "")) == normalized:
                return True
        return False

    @staticmethod
    def is_stop_key_conflict(data: dict[str, Any], key: str) -> bool:
        stop_key = normalize_key_name(data.get("hook_stop_key", ""))
        return bool(stop_key) and normalize_key_name(key) == stop_key

