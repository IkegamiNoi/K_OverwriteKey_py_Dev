import os
from tkinter import filedialog, messagebox

from keyseq.shared.i18n import tr


class SequenceFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def save_selected_sequence(self) -> bool:
        trigger = self._app.trigger_panel.selected_trigger()
        if not trigger:
            messagebox.showinfo(tr("child_kind.sequence"), tr("config_io.sequence.select_trigger"))
            return False
        source_path = str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        if source_path and bool(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_IMPORTED, False)) and bool(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_DIRTY, False)):
            if messagebox.askyesno(tr("common.save"), tr("config_io.sequence.imported_save_as")):
                return self.save_selected_sequence_as()
        if not source_path:
            label = str(trigger.get("label") or trigger.get("key") or "sequence").strip()
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_sequences_dir(), label, "sequence")
            source_path = self._app.io_dialogs.choose_save_path_with_collision(title=tr("config_io.sequence.save_title"), suggested_path=suggested)
            if not source_path:
                return False
        return self.save_sequence_to_path(trigger, source_path)

    def save_selected_sequence_as(self) -> bool:
        trigger = self._app.trigger_panel.selected_trigger()
        if not trigger:
            messagebox.showinfo(tr("child_kind.sequence"), tr("config_io.sequence.select_trigger"))
            return False
        source_path = str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        label = str(trigger.get("label") or trigger.get("key") or "sequence").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_sequences_dir(), source_path),
            label,
            "sequence",
        )
        path = filedialog.asksaveasfilename(
            title=tr("config_io.sequence.save_as_title"),
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        try:
            if self._app.io_dialogs.ask_link_label_to_filename(title=tr("config_io.sequence.link_name_title"), path=path):
                trigger["label"] = self._app.paths.filename_stem(path)
        except RuntimeError:
            return False
        return self.save_sequence_to_path(trigger, path)

    def save_sequence_to_path(self, trigger: dict, path: str) -> bool:
        try:
            previous_source_path = str(
                trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or ""
            ).strip()
            sequence = self._app.config_service.save_sequence_file(
                path,
                trigger,
                parent_ref=self._app.dirty_tracker.trigger_set_source_path,
                config_root=self._app.config_root,
            )
            trigger.update(sequence)
            source_path_changed = (
                self._app.config_service.canonical_path(
                    previous_source_path,
                    self._app.config_root,
                )
                != self._app.config_service.canonical_path(
                    str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or ""),
                    self._app.config_root,
                )
            )
            self._app.dirty_tracker.mark_trigger_set_dirty()
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            if source_path_changed:
                completion_message = tr("config_io.sequence.saved_flash_with_notice")
                info_message = tr("config_io.sequence.saved_info_with_notice", path=path)
            else:
                completion_message = tr("config_io.sequence.saved_flash")
                info_message = tr("config_io.sequence.saved_info", path=path)
            self._app._set_flash_message(completion_message)
            messagebox.showinfo(tr("common.save"), info_message)
            return True
        except Exception as e:
            self._app._set_flash_message(tr("config_io.sequence.save_failed_flash", error=e), auto_clear=False)
            messagebox.showerror(tr("keyboard.layout.save_failed_title"), str(e))
            return False

    def load_sequence_file(self) -> None:
        trigger = self._app.trigger_panel.selected_trigger()
        if not trigger:
            messagebox.showinfo(tr("child_kind.sequence"), tr("config_io.sequence.select_load_trigger"))
            return
        path = filedialog.askopenfilename(
            title=tr("config_io.sequence.load_title"),
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_sequences_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            sequence = self._app.config_service.load_sequence_file(
                path,
                imported=True,
                config_root=self._app.config_root,
            )
            trigger.update(sequence)
            self._app.dirty_tracker.mark_trigger_set_dirty()
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
            self._app._set_flash_message(tr("config_io.sequence.loaded_flash"))
            messagebox.showinfo(tr("keymap_set_history.load_action"), tr("config_io.sequence.loaded_info", path=path))
        except Exception as e:
            self._app._set_flash_message(tr("config_io.sequence.load_failed_flash", error=e), auto_clear=False)
            messagebox.showerror(tr("config_io.common.load_failed_title"), str(e))
