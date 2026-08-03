from __future__ import annotations

from collections.abc import Iterable

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
        self.trigger_set_source_path = ""
        self.trigger_set_imported = False
        self.trigger_set_dirty = False

    def set_trigger_set_source_path(self, path: str) -> None:
        """tracker と runtime の内部キーを同時に更新する。"""
        source_path = str(path or "").strip()
        self.trigger_set_source_path = source_path
        data = self._get_data()
        if isinstance(data, dict):
            data[self._config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH] = source_path

    def reset_trigger_set_state(self) -> None:
        """trigger_set の保存先と個別状態を新規状態へ戻す。"""
        self.set_trigger_set_source_path("")
        data = self._get_data()
        if isinstance(data, dict):
            data.pop(self._config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, None)
        self.trigger_set_dirty = False
        self.trigger_set_imported = False

    def sync_trigger_set_source_path_from_data(self) -> None:
        """runtime の trigger_set 保存先を tracker へ取り込む。"""
        data = self._get_data()
        source_path = data.get(self._config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, "") if isinstance(data, dict) else ""
        self.trigger_set_source_path = str(source_path or "").strip()

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

    def mark_trigger_set_dirty(self) -> None:
        self.trigger_set_dirty = True
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
        if bool(self.trigger_set_dirty):
            return True
        data = self._get_data()
        for trigger in data.get("triggers", []):
            if isinstance(trigger, dict) and bool(trigger.get(self._config_service.INTERNAL_SEQUENCE_DIRTY, False)):
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
    ) -> None:
        skipped_keymaps = _normalize_keys(skipped_keymap_ids)
        skipped_sequences = _normalize_keys(skipped_sequence_keys)
        if not skip_trigger_set:
            self.trigger_set_dirty = False
            self.trigger_set_imported = False
        data = self._get_data()
        for trigger in data.get("triggers", []):
            key = normalize_key_name(str(trigger.get("key") or "")) if isinstance(trigger, dict) else ""
            if isinstance(trigger, dict) and key not in skipped_sequences:
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
