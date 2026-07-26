import os
from tkinter import filedialog, messagebox


class TriggerSetFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def save_trigger_set_file(self) -> bool:
        path = str(getattr(self._app, "_trigger_set_source_path", "") or "").strip()
        if path and self._app.dirty_tracker.trigger_set_imported and self._app.dirty_tracker.trigger_set_dirty:
            if messagebox.askyesno("保存", "読込で持ってきたトリガー一覧です。\n別名で保存しますか？"):
                return self.save_trigger_set_file_as()
        if not path:
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_trigger_sets_dir(), self._app.keymap_set_file_stem(), "trigger_set")
            path = self._app.io_dialogs.choose_save_path_with_collision(title="トリガー一覧を保存", suggested_path=suggested)
            if not path:
                return False
        return self.save_trigger_set_to_path(path)

    def save_trigger_set_file_as(self) -> bool:
        source_path = str(getattr(self._app, "_trigger_set_source_path", "") or "").strip()
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
            triggers, _payload = self._app.config_service.save_trigger_set_file(path, self._app.data, config_root=self._app.config_root)
            self._app.data["triggers"] = triggers
            self._app.dirty_tracker.trigger_set_source_path = path
            self._app.dirty_tracker.trigger_set_imported = False
            self._app.dirty_tracker.trigger_set_dirty = False
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            self._app.dirty_tracker.sync_dirty_state()
            self._app._set_flash_message("トリガー一覧を保存しました。")
            messagebox.showinfo("保存", f"トリガー一覧を保存しました:\n{path}")
            return True
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

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
            self._app.dirty_tracker.trigger_set_source_path = path
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
