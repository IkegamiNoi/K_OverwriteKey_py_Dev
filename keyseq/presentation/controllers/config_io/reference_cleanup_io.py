from tkinter import messagebox

from keyseq.application.config_service import contracts
from keyseq.presentation.dialogs import ReferenceCleanupDialog
from keyseq.presentation.reference_cleanup_text import (
    CLEANUP_EMPTY_MESSAGE,
    format_cleanup_plan,
    format_cleanup_result,
)


class ReferenceCleanupIo:
    def __init__(self, app) -> None:
        self._app = app

    def run_cleanup(self) -> None:
        if not self._app.keymap_set_path:
            if not messagebox.askyesno(
                "参照元の掃除",
                "掃除するには構成セットの保存が必要です。保存しますか？",
            ):
                return
            if not self._app.keymap_set_io.save_keymap_set(show_success_dialog=False):
                return

        inspections = self._app.config_service.inspect_parent_refs(
            self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path,
        )
        if not any(
            inspection.state in (contracts.CLEANUP_TARGET, contracts.CLEANUP_ALL_STALE)
            for inspection in inspections
        ):
            messagebox.showinfo("参照元の掃除", CLEANUP_EMPTY_MESSAGE)
            return

        dialog = ReferenceCleanupDialog(
            self._app,
            title="参照元の掃除",
            lines=format_cleanup_plan(inspections),
        )
        dialog.wait_window()
        if not dialog.result:
            return

        result = self._app.config_service.prune_parent_refs(
            inspections,
            runtime=self._app.data,
            config_root=self._app.config_root,
            keymap_set_path=self._app.keymap_set_path,
        )
        messagebox.showinfo("参照元の掃除", "\n".join(format_cleanup_result(result)))
