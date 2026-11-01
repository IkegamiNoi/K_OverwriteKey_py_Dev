from tkinter import messagebox
from keyseq.shared.i18n import tr

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
                tr("reference_cleanup.title"),
                tr("reference_cleanup.save_required"),
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
            messagebox.showinfo(tr("reference_cleanup.title"), tr(CLEANUP_EMPTY_MESSAGE))
            return

        dialog = ReferenceCleanupDialog(
            self._app,
            title=tr("reference_cleanup.title"),
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
        messagebox.showinfo(tr("reference_cleanup.title"), "\n".join(format_cleanup_result(result)))
