from tkinter import messagebox

from keyseq.application.config_service.orphan_scan import ORPHAN_CANDIDATE
from keyseq.presentation.orphan_sweep_text import format_orphan_notice, format_orphan_plan


class OrphanSweepIo:
    def __init__(self, app) -> None:
        self._app = app

    def run_sweep(self) -> None:
        if not self._save_before_sweep():
            return
        protected_paths = self._app.config_service.collect_protected_paths(
            self._app.data, keymap_set_path=self._app.keymap_set_path,
        )
        result = self._app.config_service.scan_orphans(
            config_root=self._app.config_root,
            scan_dirs=[],
            startup_keymap_set_path=str(
                self._app._startup_settings.get("keymap_set_path") or ""
            ).strip(),
            current_keymap_set_path=self._app.keymap_set_path,
            protected_paths=protected_paths,
        )
        if not any(entry.state == ORPHAN_CANDIDATE for entry in result.entries):
            messagebox.showinfo("孤児ファイルの棚卸し", "\n".join(format_orphan_notice(result)))
            return
        messagebox.showinfo("孤児ファイルの棚卸し", "\n".join(format_orphan_plan(result)))

    def _save_before_sweep(self) -> bool:
        if not self._app.dirty_tracker.has_unsaved_changes():
            return True
        if not messagebox.askyesno(
            "孤児ファイルの棚卸し", "棚卸しの前に保存が必要です。保存しますか？",
        ):
            return False
        if self._app.keymap_set_path:
            return self._app.keymap_set_io.save_keymap_set(show_success_dialog=False)
        return self._app.keymap_set_io.save_as(show_success_dialog=False)
