from tkinter import messagebox

from keyseq.application.config_service.orphan_scan import ORPHAN_CANDIDATE
from keyseq.presentation.dialogs import OrphanSweepDialog, ReferenceCleanupDialog
from keyseq.presentation.orphan_sweep_text import (
    format_orphan_notice,
    format_orphan_plan,
    format_quarantine_result,
)


SCAN_DIRS_KEY = "orphan_sweep_scan_dirs"


class OrphanSweepIo:
    def __init__(self, app) -> None:
        self._app = app

    def run_sweep(self) -> None:
        if not self._save_before_sweep():
            return
        scan_dirs = self._app.config_service.normalize_scan_dirs(
            self._app._startup_settings.get(SCAN_DIRS_KEY), config_root=self._app.config_root,
        )
        dialog = OrphanSweepDialog(
            self._app, scan_dirs=scan_dirs, initial_dir=self._app.config_root,
        )
        dialog.wait_window()
        normalized = self._app.config_service.normalize_scan_dirs(
            dialog.scan_dirs, config_root=self._app.config_root,
        )
        if normalized != scan_dirs:
            self._app.startup_io.write_startup({SCAN_DIRS_KEY: list(normalized)})
        if not dialog.result:
            return
        arguments = self._scan_arguments(normalized)
        result = self._app.config_service.scan_orphans(**arguments)
        presented_paths = [
            entry.stored_path for entry in result.entries if entry.state == ORPHAN_CANDIDATE
        ]
        if not presented_paths:
            messagebox.showinfo("孤児ファイルの棚卸し", "\n".join(format_orphan_notice(result)))
            return
        self._confirm_and_quarantine(result, presented_paths, arguments)

    def _scan_arguments(self, scan_dirs) -> dict:
        """走査と隔離の再判定へ同じ値を渡すため、引数を 1 箇所で組み立てる。"""
        return {
            "config_root": self._app.config_root,
            "scan_dirs": list(scan_dirs),
            "startup_keymap_set_path": str(
                self._app._startup_settings.get("keymap_set_path") or ""
            ).strip(),
            "current_keymap_set_path": self._app.keymap_set_path,
            "protected_paths": self._app.config_service.collect_protected_paths(
                self._app.data, keymap_set_path=self._app.keymap_set_path,
            ),
        }

    def _confirm_and_quarantine(self, result, presented_paths: list[str], arguments: dict) -> None:
        dialog = ReferenceCleanupDialog(
            self._app,
            title="孤児ファイルの棚卸し",
            lines=format_orphan_plan(result),
            header="隔離する孤児候補を確認してください。",
            run_label="隔離する",
        )
        dialog.wait_window()
        if not dialog.result:
            return
        quarantined = self._app.config_service.quarantine_orphans(presented_paths, **arguments)
        messagebox.showinfo(
            "孤児ファイルの棚卸し", "\n".join(format_quarantine_result(quarantined)),
        )

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
