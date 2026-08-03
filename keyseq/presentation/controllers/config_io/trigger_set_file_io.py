import os
from tkinter import filedialog, messagebox

from keyseq.application.save_plan import (
    ACTION_SAVE_AS,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
)
from keyseq.presentation.controllers.config_io.child_save_plan import build_save_plan
from keyseq.presentation.controllers.config_io.child_save_rows import collect_child_save_rows


class TriggerSetFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def save_trigger_set_file(self) -> bool:
        path = str(self._app.dirty_tracker.trigger_set_source_path or "").strip()
        if not path:
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_trigger_sets_dir(), self._app.keymap_set_file_stem(), "trigger_set")
            path = self._app.io_dialogs.choose_save_path_with_collision(title="トリガー一覧を保存", suggested_path=suggested)
            if not path:
                return False
        return self.save_trigger_set_to_path(path)

    def save_trigger_set_file_as(self) -> bool:
        source_path = str(self._app.dirty_tracker.trigger_set_source_path or "").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_trigger_sets_dir(), source_path),
            self._app.paths.filename_stem(source_path) or self._app.keymap_set_file_stem(),
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
            previous_source_path = str(
                self._app.dirty_tracker.trigger_set_source_path or ""
            ).strip()
            triggers, _payload = self._app.config_service.save_trigger_set_file(
                path,
                self._app.data,
                config_root=self._app.config_root,
                parent_ref=self._app.keymap_set_path,
                save_plan=save_plan,
            )
            self._app.data["triggers"] = triggers
            self._app.dirty_tracker.set_trigger_set_source_path(
                (
                    self._app.config_service.to_config_relative_or_absolute(
                        path,
                        self._app.config_root,
                    )
                    if self._app.config_root
                    else path
                )
            )
            self._app.dirty_tracker.trigger_set_imported = False
            self._app.dirty_tracker.trigger_set_dirty = False
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            source_path_changed = (
                self._app.config_service.canonical_path(
                    previous_source_path,
                    self._app.config_root,
                )
                != self._app.config_service.canonical_path(path, self._app.config_root)
            )
            if source_path_changed:
                self._app.dirty_tracker.set_dirty(True)
            self._app.dirty_tracker.sync_dirty_state()
            completion_message = "トリガー一覧を保存しました。"
            info_message = f"トリガー一覧を保存しました:\n{path}"
            if source_path_changed:
                completion_message += "\n上位の索引を保存すると追随します。"
                info_message += "\n上位の索引を保存すると追随します。"
            self._app._set_flash_message(completion_message)
            messagebox.showinfo("保存", info_message)
            return True
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def _collect_sequence_save_plan(self, path: str) -> SavePlan | None:
        confirmed = SavePlan(
            entries=(
                ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SAVE_AS, path),
            )
        )
        targets = self._app.config_service.resolve_child_save_targets(
            self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path,
            save_plan=confirmed,
        )
        rows = [
            row
            for row in collect_child_save_rows(
                data=self._app.data,
                dirty_tracker=self._app.dirty_tracker,
                config_service=self._app.config_service,
                config_root=self._app.config_root,
                keymap_set_path=self._app.keymap_set_path,
                save_plan=confirmed,
            )
            if row.kind == CHILD_SEQUENCE
        ]
        choices = {} if not rows else self._app.child_save_dialog.ask_child_save_actions(rows)
        if choices is None:
            return None
        return build_save_plan(
            data=self._app.data,
            rows=rows,
            choices=choices,
            targets=targets,
            confirmed=confirmed,
        )

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
            self._app.data["triggers"] = self._app.config_service.load_trigger_set_file(
                path,
                config_root=self._app.config_root,
                imported=True,
            )
            self._app.dirty_tracker.set_trigger_set_source_path(
                (
                    self._app.config_service.to_config_relative_or_absolute(
                        path,
                        self._app.config_root,
                    )
                    if self._app.config_root
                    else path
                )
            )
            self._app.dirty_tracker.trigger_set_imported = True
            self._app.dirty_tracker.trigger_set_dirty = False
            self._app.state.reset_indices()
            self._app._selected_trigger_idx = 0
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("トリガー一覧を読み込みました。")
            messagebox.showinfo("読込", f"トリガー一覧を読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))
