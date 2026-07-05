from __future__ import annotations


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

    def set_dirty(self, value: bool, *, config_dirty: bool = True) -> None:
        self.is_dirty = bool(value)
        if value and config_dirty:
            self.config_dirty = True
        if not value:
            self.config_dirty = False
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

    def clear_individual_dirty_flags(self) -> None:
        self.trigger_set_dirty = False
        self.trigger_set_imported = False
        data = self._get_data()
        for trigger in data.get("triggers", []):
            if isinstance(trigger, dict):
                trigger[self._config_service.INTERNAL_SEQUENCE_DIRTY] = False
                trigger[self._config_service.INTERNAL_SEQUENCE_IMPORTED] = False
        for keymap in self._keymap_service.get_keymaps(data):
            if isinstance(keymap, dict):
                keymap[self._config_service.INTERNAL_KEYMAP_DIRTY] = False
                keymap[self._config_service.INTERNAL_KEYMAP_IMPORTED] = False
