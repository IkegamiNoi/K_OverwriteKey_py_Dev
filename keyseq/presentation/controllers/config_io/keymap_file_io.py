import os
from tkinter import filedialog, messagebox

from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
    SavePlanError,
)
from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import (
    INTERNAL_TRIGGER_SET_DIRTY,
    INTERNAL_TRIGGER_SET_IMPORTED,
    iter_trigger_sets,
    trigger_set_members,
)
from keyseq.presentation.controllers.config_io.child_save_plan import build_save_plan
from keyseq.presentation.controllers.config_io.child_save_rows import collect_child_save_rows


class KeymapFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def selected_keymap_for_io(self) -> "tuple[int, dict] | tuple[None, None]":
        index = self._app.keymap_panel.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo("キーマップ", "対象のキーマップを選択してください。")
            return None, None
        return index, keymaps[index]

    def save_selected_keymap(self) -> bool:
        index, keymap = self.selected_keymap_for_io()
        if keymap is None:
            return False
        source_path = str(keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        if source_path and keymap.get(self._app.config_service.INTERNAL_KEYMAP_IMPORTED) and keymap.get(
            self._app.config_service.INTERNAL_KEYMAP_DIRTY
        ):
            if messagebox.askyesno("保存", "読込で持ってきたキーマップです。\n別名で保存しますか？"):
                return self.save_selected_keymap_as()
        if not source_path:
            label = str(keymap.get("label") or keymap.get("id") or "keymap").strip()
            suggested = self._app.paths.suggest_json_path(
                self._app.paths.preferred_keymaps_dir(), label, "keymap"
            )
            source_path = self._app.io_dialogs.choose_save_path_with_collision(
                title="キーマップを保存", suggested_path=suggested
            )
            if not source_path:
                return False
        return self.save_keymap_to_path(index, keymap, source_path)

    def save_selected_keymap_as(self) -> bool:
        index, keymap = self.selected_keymap_for_io()
        if keymap is None:
            return False
        source_path = str(keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        label = str(keymap.get("label") or keymap.get("id") or "keymap").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_keymaps_dir(), source_path),
            label,
            "keymap",
        )
        path = filedialog.asksaveasfilename(
            title="キーマップを別名で保存",
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        previous_label = keymap.get("label")
        try:
            if self._app.io_dialogs.ask_link_label_to_filename(title="キーマップ名の連動", path=path):
                keymap["label"] = self._app.paths.filename_stem(path)
        except RuntimeError:
            return False
        saved = self.save_keymap_to_path(index, keymap, path)
        if not saved:
            keymap["label"] = previous_label
        return saved

    def save_keymap_to_path(self, index: int, keymap: dict, path: str) -> bool:
        try:
            return self._perform_keymap_save(index, keymap, path)
        except Exception as e:
            self._app._set_flash_message(f"キーマップ保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def _perform_keymap_save(self, index: int, keymap: dict, path: str) -> bool:
        previous_path = str(keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "")
        runtime_data = self._scope_for_keymap(keymap)
        save_plan = self._collect_keymap_save_plan(runtime_data, keymap, path)
        if save_plan is None:
            self._app._set_flash_message("キーマップの保存を中止しました。")
            return False
        saved = self._save_keymap_file(path, keymap, runtime_data, save_plan)
        self._sync_saved_keymap(keymap, saved)
        self._app.keymap_panel.refresh_keymap_list_ui(preferred_index=index)
        self._app.layout.refresh_keyboard_window()
        changed = self._path_changed(
            previous_path,
            str(keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or ""),
        )
        if changed:
            self._app.dirty_tracker.set_dirty(True)
        self._app.dirty_tracker.sync_dirty_state()
        self._show_save_success(path, changed)
        return True

    def _save_keymap_file(
        self, path: str, keymap: dict, runtime_data: dict, save_plan: SavePlan,
    ) -> dict:
        return self._app.config_service.save_keymap_file(
            path,
            keymap,
            parent_ref=self._app.keymap_set_path,
            config_root=self._app.config_root,
            runtime_data=runtime_data,
            save_plan=save_plan,
        )

    def _scope_for_keymap(self, keymap: dict) -> dict:
        key = normalize_key_name(str(keymap.get("id") or ""))
        members = trigger_set_members(self._app.data, key)
        if not any(member is keymap for member in members):
            members = [keymap]
        return {**self._app.data, "keymaps": members, "active_keymap_id": key}

    def _collect_keymap_save_plan(
        self, runtime_data: dict, keymap: dict, path: str,
    ) -> SavePlan | None:
        initial = self._initial_keymap_save_plan(runtime_data, keymap, path)
        targets = self._app.config_service.resolve_child_save_targets(
            runtime_data,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path,
            save_plan=initial,
        )
        rows = self._keymap_child_rows(runtime_data, initial)
        choices = {} if not rows else self._app.child_save_dialog.ask_child_save_actions(rows)
        if choices is None:
            return None
        plan = build_save_plan(
            data=runtime_data, rows=rows, choices=choices, targets=targets, confirmed=initial,
        )
        return self._save_required_trigger_sets(runtime_data, plan, rows)

    def _initial_keymap_save_plan(self, runtime_data: dict, keymap: dict, path: str) -> SavePlan:
        key = normalize_key_name(str(keymap.get("id") or ""))
        entries = []
        for member in runtime_data.get("keymaps", []):
            member_id = normalize_key_name(str(member.get("id") or ""))
            if member_id != key:
                entries.append(ChildSaveEntry(CHILD_KEYMAP, member_id, ACTION_SKIP))
                continue
            source = str(member.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "")
            action = ACTION_SAVE if source and not self._path_changed(source, path) else ACTION_SAVE_AS
            entries.append(ChildSaveEntry(CHILD_KEYMAP, member_id, action, path if action == ACTION_SAVE_AS else ""))
        return SavePlan(entries=tuple(entries), allow_deferred_index=True)

    def _keymap_child_rows(self, runtime_data: dict, save_plan: SavePlan) -> list:
        rows = collect_child_save_rows(
            data=runtime_data,
            dirty_tracker=self._app.dirty_tracker,
            config_service=self._app.config_service,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path,
            save_plan=save_plan,
        )
        return [row for row in rows if row.kind in {CHILD_TRIGGER_SET, CHILD_SEQUENCE}]

    def _save_required_trigger_sets(
        self, runtime_data: dict, save_plan: SavePlan, rows: list,
    ) -> SavePlan:
        blocked = self._app.config_service.find_dependency_blocked_parents(
            runtime_data,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path or "",
            save_plan=save_plan,
        )
        row_ids = {(row.kind, row.key) for row in rows}
        entries = list(save_plan.entries)
        for child_id in blocked:
            kind, key = child_id
            if kind != CHILD_TRIGGER_SET:
                continue
            current = next((entry for entry in entries if (entry.kind, entry.key) == child_id), None)
            if current is None or current.action != ACTION_SKIP:
                continue
            if child_id in row_ids:
                raise SavePlanError("sequence の保存先変更には trigger_set の保存が必要です。")
            replacement = ChildSaveEntry(CHILD_TRIGGER_SET, key, ACTION_SAVE)
            entries[entries.index(current)] = replacement
        return SavePlan(entries=tuple(entries), allow_deferred_index=True)

    def _sync_saved_keymap(self, keymap: dict, saved: dict) -> None:
        names = (
            self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH,
            self._app.config_service.INTERNAL_KEYMAP_IMPORTED,
            self._app.config_service.INTERNAL_KEYMAP_DIRTY,
            self._app.config_service.INTERNAL_KEYMAP_PARENT_REFS,
            self._app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH,
            self._app.config_service.INTERNAL_TRIGGER_SET_PARENT_REFS,
        )
        for name in names:
            if name in saved:
                keymap[name] = saved[name]
            else:
                keymap.pop(name, None)

    def _path_changed(self, previous: str, current: str) -> bool:
        return self._app.config_service.canonical_path(
            previous, self._app.config_root
        ) != self._app.config_service.canonical_path(current, self._app.config_root)

    def _show_save_success(self, path: str, source_path_changed: bool) -> None:
        completion_message = "キーマップを保存しました。"
        info_message = f"キーマップを保存しました:\n{path}"
        if source_path_changed:
            completion_message += "\n上位の索引を保存すると追随します。"
            info_message += "\n上位の索引を保存すると追随します。"
        self._app._set_flash_message(completion_message)
        messagebox.showinfo("保存", info_message)

    def load_keymap_file(self) -> None:
        path = filedialog.askopenfilename(
            title="キーマップを読込",
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_keymaps_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        if self._is_already_loaded_path(path):
            messagebox.showerror("読込できません", "このキーマップは既に読み込まれています")
            return
        try:
            keymap = self._load_keymap(path)
            joins_existing_set = self._joins_existing_trigger_set(keymap)
            if not self._app.keymap_panel.add_imported_keymap(keymap):
                return
            if joins_existing_set:
                self._app.dirty_tracker.mark_trigger_set_dirty(str(keymap.get("id") or ""))
            self._refresh_after_load(path)
        except Exception as e:
            self._app._set_flash_message(f"キーマップ読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

    def _is_already_loaded_path(self, path: str) -> bool:
        service = self._app.config_service
        identity = service.canonical_path(path, self._app.config_root)
        source_key = service.INTERNAL_KEYMAP_SOURCE_PATH
        for item in self._app.keymap_service.get_keymaps(self._app.data):
            if not isinstance(item, dict):
                continue
            source = str(item.get(source_key) or "")
            if source and service.canonical_path(source, self._app.config_root) == identity:
                return True
        return False

    def _load_keymap(self, path: str) -> dict:
        used_ids = {
            normalize_key_name(item.get("id", ""))
            for item in self._app.keymap_service.get_keymaps(self._app.data)
        }
        return self._app.config_service.load_keymap_file(
            path,
            used_keymap_ids=used_ids,
            imported=True,
            config_root=self._app.config_root,
            trigger_set_cache=self._trigger_set_cache(),
        )

    def _trigger_set_cache(self) -> dict:
        cache = {}
        for owner, _, triggers in iter_trigger_sets(self._app.data):
            source = str(owner.get(self._app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH) or "")
            if not source:
                continue
            identity = self._app.config_service.canonical_path(source, self._app.config_root)
            refs = owner.get(self._app.config_service.INTERNAL_TRIGGER_SET_PARENT_REFS)
            cache[identity] = (
                triggers,
                refs if isinstance(refs, list) else None,
                source,
                bool(owner.get(INTERNAL_TRIGGER_SET_DIRTY, False)),
                bool(owner.get(INTERNAL_TRIGGER_SET_IMPORTED, False)),
            )
        return cache

    def _joins_existing_trigger_set(self, keymap: dict) -> bool:
        source_key = self._app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH
        source_path = str(keymap.get(source_key) or "").strip()
        if not source_path:
            return False
        identity = self._app.config_service.canonical_path(source_path, self._app.config_root)
        for owner, _, _ in iter_trigger_sets(self._app.data):
            existing_source = str(owner.get(source_key) or "").strip()
            if existing_source and self._app.config_service.canonical_path(
                existing_source, self._app.config_root
            ) == identity:
                return True
        return False

    def _refresh_after_load(self, path: str) -> None:
        self._app.dirty_tracker.set_dirty(True)
        self._app._set_flash_message("キーマップを読み込みました。")
        messagebox.showinfo("読込", f"キーマップを読み込みました:\n{path}")
