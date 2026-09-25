import os
from dataclasses import replace
from tkinter import filedialog, messagebox

from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SKIP,
    ACTION_SAVE_AS,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
    split_sequence_key,
)
from keyseq.domain.keymap_triggers import (
    INTERNAL_TRIGGER_SET_DIRTY,
    INTERNAL_TRIGGER_SET_IMPORTED,
    ensure_active_triggers,
    get_active_triggers, iter_trigger_sets, set_active_triggers, trigger_set_owner,
    trigger_set_members,
)
from keyseq.domain.config import normalize_key_name
from keyseq.presentation.controllers.config_io.child_save_rows import collect_child_save_rows


class TriggerSetFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def save_trigger_set_file(self) -> bool:
        path = str(self._app.dirty_tracker.trigger_set_source_path or "").strip()
        if not path:
            suggested = self._app.paths.suggest_json_path(
                self._app.paths.preferred_trigger_sets_dir(),
                self._default_trigger_set_stem(),
                "trigger_set",
            )
            path = self._app.io_dialogs.choose_save_path_with_collision(title="トリガー一覧を保存", suggested_path=suggested)
            if not path:
                return False
        return self.save_trigger_set_to_path(path)

    def save_trigger_set_file_as(self) -> bool:
        source_path = str(self._app.dirty_tracker.trigger_set_source_path or "").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_trigger_sets_dir(), source_path),
            self._app.paths.filename_stem(source_path) or self._default_trigger_set_stem(),
            "trigger_set",
        )
        path = filedialog.asksaveasfilename(
            title="トリガー一覧を別名で保存",
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        return self.save_trigger_set_to_path(path)

    def save_trigger_set_to_path(self, path: str) -> bool:
        try:
            save_plan = self._collect_sequence_save_plan(path)
            if save_plan is None:
                self._app._set_flash_message("トリガー一覧の保存を中止しました。")
                return False
            source_path_changed = self._save_trigger_set(path, save_plan)
            self._show_save_success(path, source_path_changed)
            return True
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def _save_trigger_set(self, path: str, save_plan: SavePlan) -> bool:
        previous_path = str(self._app.dirty_tracker.trigger_set_source_path or "").strip()
        parent_refs = self._shared_keymap_source_paths()
        parent_path = parent_refs[0] if parent_refs else ""
        triggers, _payload = self._app.config_service.save_trigger_set_file(
            path, self._app.data, config_root=self._app.config_root,
            parent_ref=parent_path, parent_refs=parent_refs, save_plan=save_plan,
        )
        self._apply_saved_trigger_set(triggers, path)
        source_path_changed = self._path_changed(previous_path, path)
        if source_path_changed:
            for member in trigger_set_members(self._app.data):
                self._app.dirty_tracker.mark_keymap_dirty(member)
            self._app.dirty_tracker.set_dirty(True)
        self._app.dirty_tracker.sync_dirty_state()
        return source_path_changed

    def _shared_keymap_source_paths(self) -> list[str]:
        service = self._app.config_service
        paths = []
        for member in trigger_set_members(self._app.data):
            source_path = str(member.get(service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
            if not source_path:
                continue
            resolved_path = service.resolve_config_path(source_path, self._app.config_root)
            if os.path.exists(resolved_path):
                paths.append(source_path)
        return paths

    def _apply_saved_trigger_set(self, triggers: list[dict], path: str) -> None:
        if len(trigger_set_members(self._app.data)) > 1:
            get_active_triggers(self._app.data)[:] = triggers
        else:
            set_active_triggers(self._app.data, triggers)
        self._app.dirty_tracker.set_trigger_set_source_path(self._stored_path(path))
        self._app.dirty_tracker.trigger_set_imported = False
        self._app.dirty_tracker.trigger_set_dirty = False
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()

    def _show_save_success(self, path: str, source_path_changed: bool) -> None:
        completion = "トリガー一覧を保存しました。"
        info = f"トリガー一覧を保存しました:\n{path}"
        if source_path_changed:
            completion += "\n上位の索引を保存すると追随します。"
            info += "\n上位の索引を保存すると追随します。"
        self._app._set_flash_message(completion)
        messagebox.showinfo("保存", info)

    def _path_changed(self, previous: str, current: str) -> bool:
        return self._app.config_service.canonical_path(
            previous, self._app.config_root
        ) != self._app.config_service.canonical_path(current, self._app.config_root)

    def _collect_sequence_save_plan(self, path: str) -> SavePlan | None:
        owner = trigger_set_owner(self._app.data)
        owner_id = normalize_key_name(str(owner.get("id") or ""))
        if not owner_id:
            return SavePlan()
        scoped_data = {**self._app.data, "keymaps": [owner], "active_keymap_id": owner_id}
        confirmed = SavePlan(
            entries=(
                ChildSaveEntry(CHILD_TRIGGER_SET, owner_id, ACTION_SAVE_AS, path),
            )
        )
        targets = self._app.config_service.resolve_child_save_targets(
            scoped_data,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path,
            save_plan=confirmed,
        )
        rows = [
            replace(row, key=split_sequence_key(row.key)[1])
            for row in collect_child_save_rows(
                data=scoped_data,
                dirty_tracker=self._app.dirty_tracker,
                config_service=self._app.config_service,
                config_root=self._app.config_root,
                keymap_set_path=self._app.keymap_set_path,
                save_plan=confirmed,
            )
            if row.kind == CHILD_SEQUENCE and split_sequence_key(row.key)[0] == owner_id
        ]
        choices = {} if not rows else self._app.child_save_dialog.ask_child_save_actions(rows)
        if choices is None:
            return None
        entries = []
        for (kind, key), target in targets.items():
            if kind != CHILD_SEQUENCE or split_sequence_key(key)[0] != owner_id:
                continue
            trigger_key = split_sequence_key(key)[1]
            action, destination = choices.get(
                (kind, trigger_key), (ACTION_SKIP if os.path.exists(target) else ACTION_SAVE, ""),
            )
            entries.append(ChildSaveEntry(kind, trigger_key, action, destination))
        return SavePlan(entries=tuple(entries))

    def _default_trigger_set_stem(self) -> str:
        owner = trigger_set_owner(self._app.data)
        parent_path = owner.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH)
        return self._app.paths.filename_stem(str(parent_path or "")) or "trigger_set"

    def load_trigger_set_file(self) -> None:
        if not self._app.keymap_set_io.confirm_save_if_dirty("トリガー一覧読込"):
            return
        path = filedialog.askopenfilename(
            title="トリガー一覧を読込",
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_trigger_sets_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            self._apply_loaded_trigger_set(path)
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

    def _apply_loaded_trigger_set(self, path: str) -> None:
        existing = self._existing_trigger_set(path)
        triggers = self._load_or_reuse_trigger_set(path, existing)
        ensure_active_triggers(self._app.data)
        active_id = str(self._app.data.get("active_keymap_id") or "")
        active = self._app.keymap_service.find_keymap(self._app.data, active_id)
        if active is None:
            raise ValueError("読込先のキーマップがありません。")
        previous_path = str(active.get(self._app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH) or "")
        set_active_triggers(self._app.data, triggers)
        stored_path = self._stored_path(path)
        self._app.dirty_tracker.set_trigger_set_source_path(stored_path, key=active_id)
        refs = existing[1].get(self._app.config_service.INTERNAL_TRIGGER_SET_PARENT_REFS) if existing else (
            self._app.config_service.read_parent_refs(path)
        )
        self._apply_loaded_trigger_refs(active_id, refs)
        self._sync_loaded_trigger_set_state(active_id, existing=existing[1] if existing else None)
        if self._path_changed(previous_path, stored_path):
            self._app.dirty_tracker.mark_keymap_dirty(active)
        self._refresh_after_load(path)

    def _existing_trigger_set(self, path: str) -> tuple[list[dict], dict] | None:
        target = self._app.config_service.canonical_path(path, self._app.config_root)
        for owner, _, triggers in iter_trigger_sets(self._app.data):
            source = owner.get(self._app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH)
            if source and self._app.config_service.canonical_path(
                source, self._app.config_root
            ) == target:
                return triggers, owner
        return None

    def _load_or_reuse_trigger_set(
        self, path: str, existing: tuple[list[dict], dict] | None,
    ) -> list[dict]:
        if existing is not None:
            return existing[0]
        return self._app.config_service.load_trigger_set_file(
            path, config_root=self._app.config_root, imported=True,
        )

    def _stored_path(self, path: str) -> str:
        if not self._app.config_root:
            return path
        return self._app.config_service.to_config_relative_or_absolute(
            path, self._app.config_root
        )

    def _apply_loaded_trigger_refs(self, key: str, refs: list[str] | None) -> None:
        refs_key = self._app.config_service.INTERNAL_TRIGGER_SET_PARENT_REFS
        for member in trigger_set_members(self._app.data, key):
            if refs is None:
                member.pop(refs_key, None)
            else:
                member[refs_key] = refs

    def _sync_loaded_trigger_set_state(self, key: str, *, existing: dict | None) -> None:
        if existing is None:
            self._app.dirty_tracker.trigger_set_imported = True
            self._app.dirty_tracker.trigger_set_dirty = False
            return
        for member in trigger_set_members(self._app.data, key):
            member[INTERNAL_TRIGGER_SET_DIRTY] = bool(existing.get(INTERNAL_TRIGGER_SET_DIRTY, False))
            member[INTERNAL_TRIGGER_SET_IMPORTED] = bool(existing.get(INTERNAL_TRIGGER_SET_IMPORTED, False))

    def _refresh_after_load(self, path: str) -> None:
        self._app.state.reset_indices()
        self._app._selected_trigger_idx = 0
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
        self._app.dirty_tracker.set_dirty(True)
        self._app._set_flash_message("トリガー一覧を読み込みました。")
        messagebox.showinfo("読込", f"トリガー一覧を読み込みました:\n{path}")
