import os
from tkinter import filedialog, messagebox


class SequenceFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def save_selected_sequence(self) -> bool:
        trigger = self._app.trigger_panel.selected_trigger()
        if not trigger:
            messagebox.showinfo("出力シーケンス", "対象のトリガーを選択してください。")
            return False
        source_path = str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        if source_path and bool(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_IMPORTED, False)) and bool(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_DIRTY, False)):
            if messagebox.askyesno("保存", "読込で持ってきた出力シーケンスです。\n別名で保存しますか？"):
                return self.save_selected_sequence_as()
        if not source_path:
            label = str(trigger.get("label") or trigger.get("key") or "sequence").strip()
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_sequences_dir(), label, "sequence")
            source_path = self._app.config_io.choose_save_path_with_collision(title="出力シーケンスを保存", suggested_path=suggested)
            if not source_path:
                return False
        return self.save_sequence_to_path(trigger, source_path)

    def save_selected_sequence_as(self) -> bool:
        trigger = self._app.trigger_panel.selected_trigger()
        if not trigger:
            messagebox.showinfo("出力シーケンス", "対象のトリガーを選択してください。")
            return False
        source_path = str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        label = str(trigger.get("label") or trigger.get("key") or "sequence").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_sequences_dir(), source_path),
            label,
            "sequence",
        )
        path = filedialog.asksaveasfilename(
            title="出力シーケンスを別名で保存",
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        try:
            if self._app.config_io.ask_link_label_to_filename(title="出力シーケンス名の連動", path=path):
                trigger["label"] = self._app.paths.filename_stem(path)
        except RuntimeError:
            return False
        return self.save_sequence_to_path(trigger, path)

    def save_sequence_to_path(self, trigger: dict, path: str) -> bool:
        try:
            sequence = self._app.config_service.save_sequence_file(path, trigger)
            trigger.update(sequence)
            self._app.dirty_tracker.mark_trigger_set_dirty()
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            self._app._set_flash_message("出力シーケンスを保存しました。")
            messagebox.showinfo("保存", f"出力シーケンスを保存しました:\n{path}")
            return True
        except Exception as e:
            self._app._set_flash_message(f"出力シーケンス保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def load_sequence_file(self) -> None:
        trigger = self._app.trigger_panel.selected_trigger()
        if not trigger:
            messagebox.showinfo("出力シーケンス", "読込先のトリガーを選択してください。")
            return
        path = filedialog.askopenfilename(
            title="出力シーケンスを読込",
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_sequences_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            sequence = self._app.config_service.load_sequence_file(path, imported=True)
            trigger.update(sequence)
            self._app.dirty_tracker.mark_trigger_set_dirty()
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            self._app._set_flash_message("出力シーケンスを読み込みました。")
            messagebox.showinfo("読込", f"出力シーケンスを読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"出力シーケンス読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))
