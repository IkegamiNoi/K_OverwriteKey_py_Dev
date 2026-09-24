from __future__ import annotations

from collections.abc import Iterable

from keyseq.domain.keymap_triggers import (
    iter_trigger_sets, trigger_set_members, INTERNAL_TRIGGER_SET_DIRTY,
    INTERNAL_TRIGGER_SET_IMPORTED,
)
from keyseq.application.save_plan import compose_sequence_key
from keyseq.domain.config import normalize_key_name


class DirtyStateTracker:
    """構成セット全体・trigger_set・個別 keymap/sequence の未保存状態を一元管理する。"""

    def __init__(self, *, get_data, keymap_service, config_service, on_change) -> None:
        self._get_data = get_data          # lambda: app.data（dict は差し替わるため毎回取得）
        self._keymap_service = keymap_service
        self._config_service = config_service
        self._on_change = on_change        # 表示更新コールバック（app._update_file_status）
        self.is_dirty = False
        self.config_dirty = False

    def _get_trigger_state(self, field: str, default, key: str | None = None):
        members = trigger_set_members(self._get_data(), key)
        return members[0].get(field, default) if members else default

    def _set_trigger_state(self, field: str, value, key: str | None = None) -> None:
        data = self._get_data()
        for member in trigger_set_members(data, key):
            member[field] = value

    @property
    def trigger_set_source_path(self) -> str:
        return self._get_trigger_state(self._config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, "")

    @trigger_set_source_path.setter
    def trigger_set_source_path(self, path: str) -> None:
        self.set_trigger_set_source_path(path)

    @property
    def trigger_set_dirty(self) -> bool:
        return bool(self._get_trigger_state(INTERNAL_TRIGGER_SET_DIRTY, False))

    @trigger_set_dirty.setter
    def trigger_set_dirty(self, value: bool) -> None:
        self._set_trigger_state(INTERNAL_TRIGGER_SET_DIRTY, bool(value))

    @property
    def trigger_set_imported(self) -> bool:
        return bool(self._get_trigger_state(INTERNAL_TRIGGER_SET_IMPORTED, False))

    @trigger_set_imported.setter
    def trigger_set_imported(self, value: bool) -> None:
        self._set_trigger_state(INTERNAL_TRIGGER_SET_IMPORTED, bool(value))

    def set_trigger_set_source_path(self, path: str, key: str | None = None) -> None:
        self._set_trigger_state(self._config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, str(path or "").strip(), key)

    def reset_trigger_set_state(self, key: str | None = None) -> None:
        self.set_trigger_set_source_path("", key)
        self._set_trigger_state(INTERNAL_TRIGGER_SET_DIRTY, False, key)
        self._set_trigger_state(INTERNAL_TRIGGER_SET_IMPORTED, False, key)

    def sync_trigger_set_source_path_from_data(self, key: str | None = None) -> None:
        """実体の代表値を共有要素へ揃える。状態の正は runtime にある。"""
        for field, default in (
            (self._config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, ""),
            (INTERNAL_TRIGGER_SET_DIRTY, False), (INTERNAL_TRIGGER_SET_IMPORTED, False),
        ):
            self._set_trigger_state(field, self._get_trigger_state(field, default, key), key)

    def mark_migrated_keymap_dirty(self) -> None:
        data = self._get_data()
        legacy = data.get(self._config_service.INTERNAL_LEGACY_TRIGGER_SET, {})
        if legacy.get("state") == "migrated":
            for keymap in data.get("keymaps", []):
                if keymap.get("id") == legacy.get("keymap_id"):
                    keymap[self._config_service.INTERNAL_KEYMAP_DIRTY] = True
            self.config_dirty = True
            self.is_dirty = True
            self._on_change()

    def set_dirty(self, value: bool, *, config_dirty: bool = True) -> None:
        self.is_dirty = bool(value)
        if value and config_dirty:
            self.config_dirty = True
        if not value:
            self.config_dirty = False
        self._on_change()

    def capture_dirty_snapshot(self) -> tuple[bool, bool]:
        """dirty 状態を記録する（OFF 操作の前後で復元するため）。"""
        return (bool(self.is_dirty), bool(self.config_dirty))

    def restore_dirty_snapshot(self, snapshot: tuple[bool, bool]) -> None:
        self.is_dirty, self.config_dirty = bool(snapshot[0]), bool(snapshot[1])
        self._on_change()

    def mark_keymap_dirty(self, target) -> None:
        if isinstance(target, dict):
            target[self._config_service.INTERNAL_KEYMAP_DIRTY] = True
        self.set_dirty(True, config_dirty=False)

    def mark_trigger_set_dirty(self, key: str | None = None) -> None:
        self._set_trigger_state(INTERNAL_TRIGGER_SET_DIRTY, True, key)
        self.set_dirty(True, config_dirty=False)

    def mark_sequence_dirty(self, target) -> None:
        if isinstance(target, dict):
            target[self._config_service.INTERNAL_SEQUENCE_DIRTY] = True
        self.set_dirty(True, config_dirty=False)

    def has_unsaved_changes(self) -> bool:
        return bool(self.config_dirty) or self.has_individual_dirty()

    def sync_dirty_state(self) -> None:
        self.is_dirty = self.has_unsaved_changes()
        self._on_change()

    def has_individual_dirty(self) -> bool:
        data = self._get_data()
        for owner, _, triggers in iter_trigger_sets(data):
            if owner.get(INTERNAL_TRIGGER_SET_DIRTY, False):
                return True
            for trigger in triggers:
                if bool(trigger.get(self._config_service.INTERNAL_SEQUENCE_DIRTY, False)):
                    return True
        for keymap in self._keymap_service.get_keymaps(data):
            if isinstance(keymap, dict) and bool(keymap.get(self._config_service.INTERNAL_KEYMAP_DIRTY, False)):
                return True
        return False

    def clear_individual_dirty_flags(
        self,
        *,
        skipped_keymap_ids: Iterable[str] | None = None,
        skipped_sequence_keys: Iterable[str] | None = None,
        skip_trigger_set: bool = False,
        skipped_trigger_set_ids: Iterable[str] | None = None,
    ) -> None:
        skipped_keymaps = _normalize_keys(skipped_keymap_ids)
        skipped_sequences = _normalize_keys(skipped_sequence_keys)
        skipped_sets = set(skipped_trigger_set_ids or ())
        data = self._get_data()
        if skip_trigger_set:
            members = trigger_set_members(data)
            if members:
                skipped_sets.add(str(members[0]["id"]))
        for owner, members, triggers in iter_trigger_sets(data):
            owner_id = str(owner["id"])
            if owner_id not in skipped_sets:
                for member in members:
                    member[INTERNAL_TRIGGER_SET_DIRTY] = False
                    member[INTERNAL_TRIGGER_SET_IMPORTED] = False
            for trigger in triggers:
                key = normalize_key_name(str(trigger.get("key") or ""))
                if compose_sequence_key(owner_id, key) not in skipped_sequences:
                    trigger[self._config_service.INTERNAL_SEQUENCE_DIRTY] = False
                    trigger[self._config_service.INTERNAL_SEQUENCE_IMPORTED] = False
        for keymap in self._keymap_service.get_keymaps(data):
            key = normalize_key_name(str(keymap.get("id") or "")) if isinstance(keymap, dict) else ""
            if isinstance(keymap, dict) and key not in skipped_keymaps:
                keymap[self._config_service.INTERNAL_KEYMAP_DIRTY] = False
                keymap[self._config_service.INTERNAL_KEYMAP_IMPORTED] = False


def _normalize_keys(values: Iterable[str] | None) -> set[str]:
    if values is None:
        return set()
    return {normalize_key_name(str(value or "")) for value in values if normalize_key_name(str(value or ""))}
