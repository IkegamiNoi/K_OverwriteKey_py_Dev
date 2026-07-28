import os
from tkinter import filedialog, messagebox

from keyseq.application.save_plan import (
    ACTION_SAVE_AS,
    ACTION_SKIP,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
)
from keyseq.domain.config import normalize_key_name
from keyseq.presentation.controllers.config_io.child_save_plan import build_save_plan
from keyseq.presentation.controllers.config_io.child_save_rows import build_row, collect_child_save_rows


DEFAULT_KEYMAP_SET_FILENAME = "keymap_set.json"


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
        self._app.data["triggers"] = []
        self._app.data = self._app.config_service.normalize_runtime_data(self._app.data)
        self._app.keymap_set_path = ""

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
            split_base_dir = self.choose_split_base_dir_for_keymap_set(save_path)
            save_plan = self._collect_child_save_plan(save_path, split_base_dir)
            if save_plan is None:
                self._app._set_flash_message("保存を中止しました。")
                return False
            skipped_dirty_children = self._skipped_dirty_children(save_plan)
            self._app.data, startup_payload = self._app.config_service.save_runtime_data(
                save_path,
                self._app.data,
                config_root=self._app.config_root,
                startup_data=self._app._startup_settings,
                keep_legacy_copy=False,
                split_base_dir=split_base_dir,
                save_plan=save_plan,
            )
            self._app.keymap_set_path = save_path
            self._app.startup_path = self._app.paths.preferred_startup_path()
            self._app._startup_settings = startup_payload
            self._clear_saved_child_dirty_flags(*skipped_dirty_children)
            self._app.dirty_tracker.set_dirty(False)
            self._app.dirty_tracker.sync_dirty_state()
            self._app._set_flash_message(flash_message)
            if show_success_dialog:
                messagebox.showinfo("保存", f"保存しました:\n{save_path}")
            return True
        except Exception as e:
            self._app._set_flash_message(f"保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def _collect_child_save_plan(self, save_path: str, split_base_dir: str) -> SavePlan | None:
        pending = SavePlan()
        show_recalculation_notice = False
        while True:
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
            )
            self._app.child_save_dialog.show_recalculation_notice = show_recalculation_notice
            choices = {} if not rows else self._app.child_save_dialog.ask_child_save_actions(rows)
            if choices is None:
                return None
            plan = build_save_plan(data=self._app.data, rows=rows, choices=choices, targets=targets)
            trigger_entry = plan.entry_for(CHILD_TRIGGER_SET)
            if trigger_entry and self._trigger_target_changed(
                trigger_entry,
                targets,
                save_path,
                split_base_dir,
            ):
                pending = SavePlan(entries=(trigger_entry,))
                show_recalculation_notice = True
                continue
            blocked = self._app.config_service.find_dependency_blocked_sequences(
                self._app.data,
                config_root=self._app.config_root,
                keymap_set_path=save_path,
                split_base_dir=split_base_dir,
                save_plan=plan,
            )
            if not blocked:
                return plan
            trigger_row = self._trigger_set_row(rows, targets, save_path)
            action = self._app.child_save_dialog.confirm_trigger_set_dependency(
                blocked_labels=self._blocked_labels(blocked),
                trigger_set_row=trigger_row,
            )
            if not action:
                pending = SavePlan()
                show_recalculation_notice = False
                continue
            confirmed = ChildSaveEntry(
                CHILD_TRIGGER_SET,
                "",
                action,
                self._app.child_save_dialog.trigger_set_save_as_path if action == ACTION_SAVE_AS else "",
            )
            if self._trigger_target_changed(confirmed, targets, save_path, split_base_dir):
                pending = SavePlan(entries=(confirmed,))
                show_recalculation_notice = True
                continue
            return self._replace_trigger_set_entry(plan, confirmed)

    def _trigger_target_changed(
        self,
        entry: ChildSaveEntry,
        targets: dict[tuple[str, str], str],
        save_path: str,
        split_base_dir: str,
    ) -> bool:
        planned_targets = self._app.config_service.resolve_child_save_targets(
            self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=save_path,
            split_base_dir=split_base_dir,
            save_plan=SavePlan(entries=(entry,)),
        )
        current_target = targets[(CHILD_TRIGGER_SET, "")]
        planned_target = planned_targets[(CHILD_TRIGGER_SET, "")]
        return os.path.normcase(os.path.abspath(planned_target)) != os.path.normcase(os.path.abspath(current_target))

    def _trigger_set_row(self, rows, targets, save_path: str):
        for row in rows:
            if row.kind == CHILD_TRIGGER_SET:
                return row
        return build_row(
            kind=CHILD_TRIGGER_SET,
            key="",
            display_name="トリガー一覧",
            target_path=targets[(CHILD_TRIGGER_SET, "")],
            current_parent=self._app.config_service.to_config_relative_or_absolute(
                save_path,
                self._app.config_root,
            ),
            config_service=self._app.config_service,
            config_root=self._app.config_root,
        )

    def _blocked_labels(self, blocked_keys: list[str]) -> list[str]:
        labels = {}
        for trigger in self._app.data.get("triggers", []):
            if isinstance(trigger, dict):
                key = normalize_key_name(str(trigger.get("key") or ""))
                labels[key] = str(trigger.get("label") or "").strip() or key
        return [labels.get(key, key) for key in blocked_keys]

    @staticmethod
    def _replace_trigger_set_entry(plan: SavePlan, entry: ChildSaveEntry) -> SavePlan:
        return SavePlan(entries=tuple(entry if item.kind == CHILD_TRIGGER_SET else item for item in plan.entries))

    def _skipped_dirty_children(self, save_plan: SavePlan) -> tuple[list[str], list[str], bool]:
        skipped_keymaps = [
            normalize_key_name(str(item.get("id") or ""))
            for item in self._app.data.get("keymaps", [])
            if isinstance(item, dict)
            and bool(item.get(self._app.config_service.INTERNAL_KEYMAP_DIRTY, False))
            and self._is_skipped(save_plan, CHILD_KEYMAP, normalize_key_name(str(item.get("id") or "")))
        ]
        skipped_sequences = [
            normalize_key_name(str(item.get("key") or ""))
            for item in self._app.data.get("triggers", [])
            if isinstance(item, dict)
            and bool(item.get(self._app.config_service.INTERNAL_SEQUENCE_DIRTY, False))
            and self._is_skipped(save_plan, CHILD_SEQUENCE, normalize_key_name(str(item.get("key") or "")))
        ]
        skip_trigger_set = bool(self._app.dirty_tracker.trigger_set_dirty) and self._is_skipped(
            save_plan,
            CHILD_TRIGGER_SET,
            "",
        )
        return skipped_keymaps, skipped_sequences, skip_trigger_set

    def _clear_saved_child_dirty_flags(
        self,
        skipped_keymaps: list[str],
        skipped_sequences: list[str],
        skip_trigger_set: bool,
    ) -> None:
        if skipped_keymaps or skipped_sequences or skip_trigger_set:
            self._app.dirty_tracker.clear_individual_dirty_flags(
                skipped_keymap_ids=skipped_keymaps,
                skipped_sequence_keys=skipped_sequences,
                skip_trigger_set=skip_trigger_set,
            )
            return
        self._app.dirty_tracker.clear_individual_dirty_flags()

    @staticmethod
    def _is_skipped(save_plan: SavePlan, kind: str, key: str) -> bool:
        entry = save_plan.entry_for(kind, key)
        return entry is not None and entry.action == ACTION_SKIP

    def load_keymap_set_from(self):
        if not self.confirm_save_if_dirty("読込"):
            return

        path = filedialog.askopenfilename(
            title="keymap_set.json を読込",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
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
            self._app.dirty_tracker.set_dirty(False)
            self._app._set_flash_message("読み込みました。")
            messagebox.showinfo("読込", f"読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

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
        if messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？"):
            self._app.data = self._app.config_service.new_default_data()
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
        self._app.startup_io.write_startup({"keymap_set_path": self._app.paths.to_config_relative_or_absolute(path)})
        self.apply_loaded_data_to_ui()
        self._app.state.reset_indices()
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
        self._app.dirty_tracker.set_dirty(False)
        self._app._set_flash_message("起動時読み込み設定を更新しました。")
        messagebox.showinfo("設定", f"次回起動時はこの keymap_set を読み込みます:\n{path}")

    def apply_loaded_data_to_ui(self):
        self._app.dirty_tracker.trigger_set_source_path = ""
        self._app.dirty_tracker.trigger_set_imported = False
        self._app.dirty_tracker.trigger_set_dirty = False
        self._app._sync_control_vars_from_data()
        self._app.dirty_tracker.clear_individual_dirty_flags()
        self._app.dirty_tracker.set_dirty(False)

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
