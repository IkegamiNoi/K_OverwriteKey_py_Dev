import os
from tkinter import filedialog, messagebox

from keyseq.application.config_service import ConfigService
from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
    compose_sequence_key,
    split_sequence_key,
)
from keyseq.domain.keymap_triggers import get_active_triggers, set_active_triggers, iter_trigger_sets, trigger_set_members
from keyseq.domain.config import normalize_key_name
from keyseq.presentation.controllers.config_io.child_save_plan import build_save_plan
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_NEW,
    SHARE_SOLE,
    build_row,
    collect_child_save_rows,
)


DEFAULT_KEYMAP_SET_FILENAME = "keymap_set.json"
KEYMAP_SET_LOAD_OK = "ok"
KEYMAP_SET_LOAD_FAILED = "failed"


class KeymapSetIo:
    def __init__(self, app) -> None:
        self._app = app

    def confirm_save_if_dirty(self, action_name: str) -> bool:
        if not self._app.dirty_tracker.has_unsaved_changes():
            return True

        result = messagebox.askyesnocancel(
            "未保存の変更",
            f"未保存の変更があります。\n{action_name}の前に保存しますか？",
        )
        if result is None:
            return False
        if result is False:
            return True

        if self._app.keymap_set_path:
            return self.save_keymap_set(show_success_dialog=False)
        return self.save_as(show_success_dialog=False)

    def new_config(self):
        if not self.confirm_save_if_dirty("新規作成"):
            return

        self._app.data = self._app.config_service.new_default_data()
        self._app.config_service.apply_global_defaults(self._app.data, config_root=self._app.config_root)
        set_active_triggers(self._app.data, [])
        self._app.data = self._app.config_service.normalize_runtime_data(self._app.data)
        self._app.dirty_tracker.reset_trigger_set_state()
        self._app.keymap_set_path = ""

        self._app.discard_retained_hook_keys()
        self._app._sync_control_vars_from_data()

        self._app.state.reset_indices()
        self._app._selected_trigger_idx = 0
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
        self._app.dirty_tracker.set_dirty(True)
        self._app._set_flash_message("新規作成しました（未保存）。")

    def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
        if not self._app.keymap_set_path:
            return self.save_as(show_success_dialog=show_success_dialog)
        return self.save_keymap_set_to(
            self._app.keymap_set_path,
            flash_message="保存しました。",
            show_success_dialog=show_success_dialog,
        )

    def save_as(self, *, show_success_dialog: bool = True) -> bool:
        suggested_path = self._app.suggest_keymap_set_dialog_path()
        initialfile = (
            os.path.basename(suggested_path)
            if self._app.keymap_set_path
            else DEFAULT_KEYMAP_SET_FILENAME
        )
        path = filedialog.asksaveasfilename(
            title="別名で保存（keymap_set）",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            initialfile=initialfile,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return False
        return self.save_keymap_set_to(
            path,
            flash_message="別名で保存しました。",
            show_success_dialog=show_success_dialog,
        )

    def save_keymap_set_to(self, path: str, *, flash_message: str, show_success_dialog: bool) -> bool:
        try:
            save_path = self._app.paths.normalize_keymap_set_save_path(path)
            migration_source_path = self._app.keymap_set_path
            post_save_warnings: list[str] = []
            split_base_dir = self.choose_split_base_dir_for_keymap_set(save_path)
            save_plan, recalculation_notice, deferred_index = self._collect_child_save_plan(
                save_path,
                split_base_dir,
            )
            if save_plan is None:
                self._app._set_flash_message("保存を中止しました。")
                return False
            skipped_dirty_children = self._skipped_dirty_children(save_plan)
            deferred_parents = self._blocked_parents(save_path, split_base_dir, save_plan) if deferred_index else {}
            self._app.discard_retained_hook_keys()
            if save_path != self._app.keymap_set_path:
                relocated_path = self._app.config_service.relocate_individual_hotkey_presets(
                    self._app.data,
                    config_root=self._app.config_root,
                    keymap_set_path=save_path,
                )
                if relocated_path:
                    self._app.data["hotkey_presets_path"] = relocated_path
            self._app.data, startup_payload = self._app.config_service.save_runtime_data(
                save_path,
                self._app.data,
                config_root=self._app.config_root,
                startup_data=self._app._startup_settings,
                startup_entry_loaded=self._app.startup_io.entry_loaded,
                keep_legacy_copy=False,
                split_base_dir=split_base_dir,
                migration_source_keymap_set_path=migration_source_path,
                post_save_warnings=post_save_warnings,
                save_plan=save_plan,
            )
            self._app.keymap_set_path = save_path
            self._app.startup_path = self._app.paths.preferred_startup_path()
            self._app._startup_settings = startup_payload
            self._app.startup_io.entry_loaded = True
            self._app.dirty_tracker.sync_trigger_set_source_path_from_data()
            self._clear_saved_child_dirty_flags(*skipped_dirty_children)
            for kind, key in deferred_parents:
                if kind == CHILD_TRIGGER_SET:
                    self._app.dirty_tracker.mark_trigger_set_dirty(key)
                else:
                    target = next(item for item in self._app.data["keymaps"] if item["id"] == key)
                    self._app.dirty_tracker.mark_keymap_dirty(target)
            self._app.dirty_tracker.set_dirty(False)
            self._app.dirty_tracker.sync_dirty_state()
            notices = [notice for notice in (recalculation_notice,) if notice]
            notices.extend(post_save_warnings)
            if deferred_index:
                label = "トリガー一覧" if all(kind == CHILD_TRIGGER_SET for kind, _ in deferred_parents) else "参照元の子ファイル"
                notices.append(f"{label}は未保存です。次回保存で索引を更新します。")
            completion_message = "\n".join((flash_message, *notices))
            self._app._set_flash_message(completion_message)
            if show_success_dialog:
                message = f"保存しました:\n{save_path}"
                if notices:
                    message = f"{message}\n\n" + "\n".join(notices)
                messagebox.showinfo("保存", message)
            recorded, reason = self._app.keymap_set_history_io.record(self._app.keymap_set_path)
            if not recorded:
                self._app._set_flash_message(reason, auto_clear=False)
            return True
        except Exception as e:
            self._app._set_flash_message(f"保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def _collect_child_save_plan(self, save_path: str, split_base_dir: str) -> tuple[SavePlan | None, str, bool]:
        pending = SavePlan()
        while True:
            targets, rows = self._collect_rows_and_targets(save_path, split_base_dir, pending)
            choices = {} if not rows else self._app.child_save_dialog.ask_child_save_actions(rows)
            if choices is None:
                return None, "", False
            plan = self._build_plan(rows=rows, choices=choices, targets=targets, confirmed=pending)
            recalculation_notice = ""
            if any(
                entry.kind == CHILD_TRIGGER_SET
                and self._trigger_target_changed(
                    entry, targets, save_path, split_base_dir, plan
                )
                for entry in plan.entries
            ):
                recalculated = self._recalculate_for_trigger_target(
                    rows=rows,
                    choices=choices,
                    confirmed=pending,
                    save_path=save_path,
                    split_base_dir=split_base_dir,
                    plan=plan,
                )
                if recalculated is None:
                    return None, "", False
                plan, targets, choices, recalculation_notice = recalculated
            deferred = set()
            while True:
                blocked = {child: keys for child, keys in self._blocked_parents(save_path, split_base_dir, plan).items() if child not in deferred}
                if not blocked:
                    return SavePlan(entries=plan.entries, allow_deferred_index=bool(deferred)), recalculation_notice, bool(deferred)
                parent_id, keys = next(iter(blocked.items()))
                parent_row = self._dependency_parent_row(rows, targets, save_path, parent_id)
                action = ACTION_SAVE if parent_row.share_state in (SHARE_SOLE, SHARE_NEW) else self._app.child_save_dialog.confirm_trigger_set_dependency(
                    blocked_labels=self._blocked_labels(keys), trigger_set_row=parent_row,
                )
                if not action:
                    if not rows:
                        return None, "", False
                    pending = SavePlan()
                    break
                if action == ACTION_SKIP:
                    deferred.add(parent_id)
                    continue
                if action == ACTION_SAVE and parent_id[0] == CHILD_TRIGGER_SET:
                    recalculation_notice = "\n".join(filter(None, (recalculation_notice, "トリガー一覧も保存して索引を更新しました。")))
                target = self._app.child_save_dialog.trigger_set_save_as_path if action == ACTION_SAVE_AS else ""
                replacement = ChildSaveEntry(*parent_id, action, target)
                plan = SavePlan(entries=tuple(replacement if (entry.kind, entry.key) == parent_id else entry for entry in plan.entries))
                choices = {**choices, parent_id: (action, target)}
                if parent_id[0] == CHILD_TRIGGER_SET and self._trigger_target_changed(
                    replacement, targets, save_path, split_base_dir, plan
                ):
                    recalculated = self._recalculate_for_trigger_target(
                        rows=rows, choices=choices, confirmed=plan, plan=plan,
                        save_path=save_path, split_base_dir=split_base_dir,
                    )
                    if recalculated is None:
                        return None, "", False
                    plan, targets, choices, recalculation_notice = recalculated

    def _blocked_parents(self, save_path: str, split_base_dir: str, plan: SavePlan):
        return self._app.config_service.find_dependency_blocked_parents(
            self._app.data, config_root=self._app.config_root, keymap_set_path=save_path,
            split_base_dir=split_base_dir, save_plan=plan,
        )

    def _build_plan(self, *, rows, choices, targets, confirmed) -> SavePlan:
        return build_save_plan(
            data=self._app.data,
            rows=rows,
            choices=choices,
            targets=targets,
            confirmed=confirmed,
        )

    def _collect_rows_and_targets(self, save_path: str, split_base_dir: str, pending: SavePlan):
        targets = self._app.config_service.resolve_child_save_targets(
            self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=save_path,
            split_base_dir=split_base_dir,
            save_plan=pending,
        )
        rows = collect_child_save_rows(
            data=self._app.data,
            dirty_tracker=self._app.dirty_tracker,
            config_service=self._app.config_service,
            config_root=self._app.config_root,
            keymap_set_path=save_path,
            split_base_dir=split_base_dir,
            save_plan=pending,
            migration_source_path=self._app.keymap_set_path,
        )
        return targets, rows

    def _recalculate_for_trigger_target(
        self, *, rows, choices, confirmed, plan, save_path: str, split_base_dir: str
    ):
        plan, targets = self._rebuild_plan_with_targets(
            rows=rows,
            choices=choices,
            confirmed=confirmed,
            save_path=save_path,
            split_base_dir=split_base_dir,
            plan=plan,
        )
        notice = self._recalculation_notice(rows, targets)
        confirmed_plan = self._confirm_recalculated_overwrites(
            rows=rows,
            choices=choices,
            targets=targets,
            save_path=save_path,
            confirmed=confirmed,
        )
        if confirmed_plan is None:
            return None
        plan, choices = confirmed_plan
        return plan, targets, choices, notice

    def _rebuild_plan_with_targets(
        self,
        *,
        rows,
        choices,
        confirmed: SavePlan,
        save_path: str,
        split_base_dir: str,
        plan: SavePlan,
    ) -> tuple[SavePlan, dict[tuple[str, str], str]]:
        targets = self._app.config_service.resolve_child_save_targets(
            self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=save_path,
            split_base_dir=split_base_dir,
            save_plan=plan,
        )
        return (
            self._build_plan(rows=rows, choices=choices, targets=targets, confirmed=confirmed),
            targets,
        )

    def _confirm_recalculated_overwrites(
        self,
        *,
        rows,
        choices,
        targets,
        save_path: str,
        confirmed: SavePlan,
    ) -> tuple[SavePlan, dict] | None:
        recalculated_rows = self._recalculated_existing_rows(
            rows, choices, targets, save_path, confirmed
        )
        for row in self._defaulted_save_as_rows(recalculated_rows, choices, confirmed):
            target_path = self._app.child_save_dialog._ask_save_as_path(row)
            if not target_path:
                return None
            choices = {**choices, (row.kind, row.key): (ACTION_SAVE_AS, target_path)}
        overwrite_rows = self._recalculated_overwrite_rows(recalculated_rows, choices, confirmed)
        if not overwrite_rows:
            return self._build_plan(
                rows=rows, choices=choices, targets=targets, confirmed=confirmed
            ), choices
        replacements = self._app.child_save_dialog.confirm_recalculated_overwrite(overwrite_rows)
        if replacements is None:
            return None
        choices = {**choices, **replacements}
        return (
            self._build_plan(rows=rows, choices=choices, targets=targets, confirmed=confirmed),
            choices,
        )

    def _defaulted_save_as_rows(self, rows, choices, confirmed):
        return [
            row for row in rows
            if self._recalculated_choice(row, choices, confirmed)[0] == ACTION_SAVE_AS
            and not self._recalculated_choice(row, choices, confirmed)[2]
        ]

    def _recalculated_overwrite_rows(self, rows, choices, confirmed):
        return [
            row for row in rows
            if self._recalculated_choice(row, choices, confirmed)[0] == ACTION_SAVE
            and row.share_state != SHARE_SOLE
        ]

    def _recalculated_choice(self, row, choices, confirmed) -> tuple[str, str, bool]:
        selected = self._selected_recalculated_choice(row, choices, confirmed)
        if selected is not None:
            return selected[0], selected[1], True
        return row.default_action, "", False

    def _selected_recalculated_choice(self, row, choices, confirmed):
        child_id = (row.kind, row.key)
        choice = choices.get(child_id)
        if choice is not None:
            return choice
        entry = confirmed.entry_for(*child_id)
        if entry is not None:
            return entry.action, entry.target_path
        return None

    def _recalculated_existing_rows(self, rows, choices, targets, save_path: str, confirmed):
        recalculated_rows = []
        for row in rows:
            child_id = (row.kind, row.key)
            target_path = targets[child_id]
            selected = self._selected_recalculated_choice(row, choices, confirmed)
            if (selected is not None and selected[0] == ACTION_SKIP) or (
                self._app.config_service.canonical_path(row.target_path, self._app.config_root)
                == self._app.config_service.canonical_path(target_path, self._app.config_root)
            ) or not os.path.exists(target_path):
                continue
            parent_path = save_path
            if row.kind == CHILD_SEQUENCE:
                parent_path = targets[(CHILD_TRIGGER_SET, split_sequence_key(row.key)[0])]
            elif row.kind == CHILD_TRIGGER_SET:
                parent_path = targets[(CHILD_KEYMAP, row.key)]
            current_parent = self._app.config_service.to_config_relative_or_absolute(parent_path, self._app.config_root)
            recalculated_row = build_row(
                kind=row.kind,
                key=row.key,
                display_name=row.display_name,
                target_path=target_path,
                current_parent=current_parent,
                config_service=self._app.config_service,
                config_root=self._app.config_root,
                has_source_path=self._has_source_path(row.kind, row.key),
            )
            recalculated_rows.append(recalculated_row)
        return recalculated_rows

    def _recalculation_notice(self, rows, targets) -> str:
        changed_sequences = sum(
            row.kind == CHILD_SEQUENCE
            and self._app.config_service.canonical_path(row.target_path, self._app.config_root)
            != self._app.config_service.canonical_path(
                targets[(row.kind, row.key)], self._app.config_root
            )
            for row in rows
        )
        return (
            "トリガー一覧の保存先が変わったため、"
            f"出力シーケンス {changed_sequences} 件の保存先を再計算しました。"
        )

    def _trigger_target_changed(
        self,
        entry: ChildSaveEntry,
        targets: dict[tuple[str, str], str],
        save_path: str,
        split_base_dir: str,
        save_plan: SavePlan,
    ) -> bool:
        planned_targets = self._app.config_service.resolve_child_save_targets(
            self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=save_path,
            split_base_dir=split_base_dir,
            save_plan=save_plan,
        )
        current_target = targets[(CHILD_TRIGGER_SET, entry.key)]
        planned_target = planned_targets[(CHILD_TRIGGER_SET, entry.key)]
        return self._app.config_service.canonical_path(
            planned_target, self._app.config_root
        ) != self._app.config_service.canonical_path(current_target, self._app.config_root)

    def _dependency_parent_row(self, rows, targets, save_path: str, child_id):
        for row in rows:
            if (row.kind, row.key) == child_id:
                return row
        kind, key = child_id
        owner = next(item for item in self._app.data["keymaps"] if item["id"] == key)
        parent = targets[(CHILD_KEYMAP, key)] if kind == CHILD_TRIGGER_SET else save_path
        name = str(owner.get("label") or key)
        return build_row(
            kind=kind, key=key, display_name=f"{name} / トリガー一覧" if kind == CHILD_TRIGGER_SET else name,
            target_path=targets[child_id],
            current_parent=self._app.config_service.to_config_relative_or_absolute(parent, self._app.config_root),
            config_service=self._app.config_service, config_root=self._app.config_root,
            has_source_path=self._has_source_path(kind, key),
        )

    def _has_source_path(self, kind: str, key: str) -> bool:
        if kind == CHILD_TRIGGER_SET:
            members = trigger_set_members(self._app.data, key)
            return bool(members and members[0].get(self._app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH))
        if kind == CHILD_KEYMAP:
            return any(item.get("id") == key and item.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) for item in self._app.data.get("keymaps", []))
        owner_id, trigger_key = split_sequence_key(key)
        return any(
            trigger.get("key") == trigger_key and trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH)
            for owner, _, triggers in iter_trigger_sets(self._app.data) if owner["id"] == owner_id
            for trigger in triggers
        )

    def _blocked_labels(self, blocked_keys: list[str]) -> list[str]:
        labels = {}
        for owner, _, triggers in iter_trigger_sets(self._app.data):
            name = str(owner.get("label") or owner["id"])
            labels[str(owner["id"])] = f"{name} / トリガー一覧"
            for trigger in triggers:
                key = compose_sequence_key(str(owner["id"]), str(trigger["key"]))
                labels[key] = f"{name} / {trigger.get('label') or trigger['key']}"
        return [labels.get(key, key) for key in blocked_keys]

    def _skipped_dirty_children(self, save_plan: SavePlan) -> tuple[list[str], list[str], list[str]]:
        skipped_keymaps = [
            normalize_key_name(str(item.get("id") or ""))
            for item in self._app.data.get("keymaps", [])
            if isinstance(item, dict)
            and bool(item.get(self._app.config_service.INTERNAL_KEYMAP_DIRTY, False))
            and self._is_skipped(save_plan, CHILD_KEYMAP, normalize_key_name(str(item.get("id") or "")))
        ]
        skipped_sequences = [
            entry.key for entry in save_plan.entries
            if entry.kind == CHILD_SEQUENCE and entry.action == ACTION_SKIP
        ]
        skipped_sets = [
            entry.key for entry in save_plan.entries
            if entry.kind == CHILD_TRIGGER_SET and entry.action == ACTION_SKIP
        ]
        return skipped_keymaps, skipped_sequences, skipped_sets

    def _clear_saved_child_dirty_flags(self, skipped_keymaps, skipped_sequences, skipped_sets) -> None:
        if not (skipped_keymaps or skipped_sequences or skipped_sets):
            self._app.dirty_tracker.clear_individual_dirty_flags()
            return
        self._app.dirty_tracker.clear_individual_dirty_flags(
            skipped_keymap_ids=skipped_keymaps, skipped_sequence_keys=skipped_sequences,
            skipped_trigger_set_ids=skipped_sets,
        )

    @staticmethod
    def _is_skipped(save_plan: SavePlan, kind: str, key: str) -> bool:
        entry = save_plan.entry_for(kind, key)
        return entry is not None and entry.action == ACTION_SKIP

    def load_keymap_set_from(self) -> None:
        if not self.confirm_save_if_dirty("読込"):
            return

        path = filedialog.askopenfilename(
            title="keymap_set.json を読込",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        self.load_keymap_set_path(path)

    def load_keymap_set_path(self, path: str) -> str:
        """パス指定で構成セットを読み込む。未保存確認は呼び出し側の責務。"""
        try:
            self._app.data = self._app.config_service.load_runtime_data_from_keymap_set_path(
                path,
                config_root=self._app.config_root,
            )
            self._app.keymap_set_path = path
            self.apply_loaded_data_to_ui()

            self._app._indices = {}
            self._app._selected_trigger_idx = 0
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            if self._app.data.get(ConfigService.INTERNAL_LEGACY_TRIGGER_SET, {}).get("state") != "migrated":
                self._app.dirty_tracker.set_dirty(False)
            self._app.dirty_tracker.sync_dirty_state()
            self._app._set_flash_message("読み込みました。")
            messagebox.showinfo("読込", f"読み込みました:\n{path}")
            recorded, reason = self._app.keymap_set_history_io.record(path)
            if not recorded:
                self._app._set_flash_message(reason, auto_clear=False)
            self.notify_migrated_legacy_trigger_set()
            return KEYMAP_SET_LOAD_OK
        except Exception as e:
            self._app._set_flash_message(f"読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))
            return KEYMAP_SET_LOAD_FAILED

    def notify_migrated_legacy_trigger_set(self) -> None:
        legacy = self._app.data.get(ConfigService.INTERNAL_LEGACY_TRIGGER_SET, {})
        if legacy.get("state") != "migrated" or not legacy.get("auto_created"):
            return
        keymap_id = normalize_key_name(str(legacy.get("keymap_id") or ""))
        keymap = self._app.keymap_service.find_keymap(self._app.data, keymap_id)
        name = str(keymap.get("label") or "").strip() if keymap else keymap_id
        messagebox.showinfo(
            "読込",
            f"旧形式のトリガー一覧 {legacy.get('path', '')} を、キーマップ『{name}』に移しました"
            "（切替キーは未設定です）",
        )

    def import_config(self):
        if not self.confirm_save_if_dirty("Import"):
            return

        path = filedialog.askopenfilename(
            title="Import",
            initialdir=self._app.user_root if os.path.isdir(self._app.user_root) else self._app.base_dir,
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            self._app.data = self._app.config_service.load_legacy_runtime_data(path)
            self._app.config_service.clear_individual_hotkey_presets(self._app.data)
            self._app.config_service.apply_global_defaults(self._app.data, config_root=self._app.config_root)
            self._app.keymap_set_path = ""
            self.apply_loaded_data_to_ui()
            self._app.state.reset_indices()
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("Import しました。")
            messagebox.showinfo("Import", f"単一JSONを取り込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"Import 失敗: {e}", auto_clear=False)
            messagebox.showerror("Import 失敗", str(e))

    def export_config(self):
        path = filedialog.asksaveasfilename(
            title="Export",
            initialdir=self._app.user_root if os.path.isdir(self._app.user_root) else self._app.base_dir,
            initialfile="config.json",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            self._app.config_service.export_runtime_data(path, self._app.data)
            self._app._set_flash_message("Export しました。")
            messagebox.showinfo("Export", f"単一JSONを書き出しました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"Export 失敗: {e}", auto_clear=False)
            messagebox.showerror("Export 失敗", str(e))

    def restore_default(self):
        if not self.confirm_save_if_dirty("例の復元"):
            return
        if not messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？"):
            return

        self._app.data = self._app.config_service.new_default_data()
        self._app.config_service.apply_global_defaults(self._app.data, config_root=self._app.config_root)
        self._app.dirty_tracker.reset_trigger_set_state()
        self._app.keymap_set_path = ""
        for trigger in get_active_triggers(self._app.data):
            self._app.dirty_tracker.mark_sequence_dirty(trigger)
        self._app.dirty_tracker.mark_trigger_set_dirty()
        for keymap in self._app.data.get("keymaps", []):
            self._app.dirty_tracker.mark_keymap_dirty(keymap)
        self._app.discard_retained_hook_keys()
        self._app._sync_control_vars_from_data()
        self._app._indices = {}
        self._app._selected_trigger_idx = 0
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
        self._app.dirty_tracker.set_dirty(True)
        self._app._set_flash_message("例の設定に戻しました（未保存）。")

    def set_startup_keymap_set(self):
        """ユーザーが起動時に読み込む keymap_set.json を選び、起動設定へ保存する"""
        if not self.confirm_save_if_dirty("起動時に読むJSONの変更"):
            return

        path = filedialog.askopenfilename(
            title="起動時に読み込む keymap_set.json を選択",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            self._app.data = self._app.config_service.load_runtime_data_from_keymap_set_path(
                path,
                config_root=self._app.config_root,
            )
        except Exception as e:
            messagebox.showerror("設定", str(e))
            return

        self._app.keymap_set_path = path
        self._app.keymap_set_history_io.record(path)
        startup_saved = self._app.startup_io.write_startup(
            {"keymap_set_path": self._app.paths.to_config_relative_or_absolute(path)}
        )
        if startup_saved:
            self._app.startup_io.entry_loaded = True
        self.apply_loaded_data_to_ui()
        self._app.state.reset_indices()
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
        if self._app.data.get(ConfigService.INTERNAL_LEGACY_TRIGGER_SET, {}).get("state") != "migrated":
            self._app.dirty_tracker.set_dirty(False)
        self._app.dirty_tracker.sync_dirty_state()
        if not startup_saved:
            self._app._set_flash_message("起動時読み込み設定の保存に失敗しました。", auto_clear=False)
            self.notify_migrated_legacy_trigger_set()
            return
        self._app._set_flash_message("起動時読み込み設定を更新しました。")
        messagebox.showinfo("設定", f"次回起動時はこの keymap_set を読み込みます:\n{path}")
        self.notify_migrated_legacy_trigger_set()

    def apply_loaded_data_to_ui(self):
        self._app.discard_retained_hook_keys()
        self._app.dirty_tracker.sync_trigger_set_source_path_from_data()
        self._app.dirty_tracker.trigger_set_imported = False
        self._app.dirty_tracker.trigger_set_dirty = False
        self._app._sync_control_vars_from_data()
        # 重なりの表は停止 / トグルキーの trace にも依存するが、読込の契機では明示的に作り直す（暫定 25 §2-27）。
        self._app._refresh_key_overlap_report()
        self._app.dirty_tracker.clear_individual_dirty_flags()
        if self._app.data.get(ConfigService.INTERNAL_LEGACY_TRIGGER_SET, {}).get("state") != "migrated":
            self._app.dirty_tracker.set_dirty(False)
        self._app.dirty_tracker.mark_migrated_keymap_dirty()

    def choose_split_base_dir_for_keymap_set(self, save_path: str) -> str:
        if self._app.paths.is_within_config_root(save_path):
            return ""
        use_nearby = messagebox.askyesno(
            "保存先の確認",
            "構成セットがデフォルト外に保存されます。\n"
            "keymaps / trigger_sets / sequences も構成セット周辺に保存しますか？\n\n"
            "「いいえ」の場合はデフォルト保存先を使います。",
        )
        if not use_nearby:
            return ""
        return os.path.dirname(os.path.abspath(save_path))
