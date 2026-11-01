from tkinter import messagebox
from keyseq.shared.i18n import tr

from keyseq.presentation.dialogs import QuarantineManageDialog, ReferenceCleanupDialog
from keyseq.presentation.quarantine_manage_text import (
    format_delete_plan,
    format_delete_result,
    format_restore_plan,
    format_restore_result,
    format_unit_list,
)


class QuarantineManageIo:
    def __init__(self, app) -> None:
        self._app = app

    def manage_quarantine(self) -> None:
        units = self._app.config_service.list_quarantine_units(config_root=self._app.config_root)
        if not units:
            messagebox.showinfo(tr("quarantine_manage.title"), tr("quarantine_manage.no_units"))
            return
        dialog = QuarantineManageDialog(
            self._app, lines=format_unit_list(units),
            unit_ids=tuple(unit.unit_id for unit in units),
        )
        dialog.wait_window()
        if dialog.action not in ("restore", "delete") or not dialog.selected_unit_id:
            return
        unit = next((unit for unit in units if unit.unit_id == dialog.selected_unit_id), None)
        if unit is None:
            return
        if dialog.action == "delete":
            self._confirm_and_delete(unit)
            return
        if not unit.manifest_valid:
            messagebox.showinfo(tr("quarantine_manage.title"), tr("quarantine_manage.restore_unavailable"))
            return
        self._confirm_and_restore(unit)

    def _confirm_and_restore(self, unit) -> None:
        dialog = ReferenceCleanupDialog(
            self._app, title=tr("quarantine_manage.title"), lines=format_restore_plan(unit),
            header=tr("quarantine_manage.restore_header"), run_label=tr("quarantine_manage.restore_run"),
        )
        dialog.wait_window()
        if not dialog.result:
            return
        result = self._app.config_service.restore_quarantine_unit(
            unit.unit_id, config_root=self._app.config_root,
        )
        messagebox.showinfo(tr("quarantine_manage.title"), "\n".join(format_restore_result(result)))

    def _confirm_and_delete(self, unit) -> None:
        try:
            paths = self._app.config_service.collect_unit_paths(
                unit.unit_id, config_root=self._app.config_root,
            )
        except (OSError, ValueError) as error:
            messagebox.showinfo(tr("quarantine_manage.title"), tr("quarantine_manage.list_delete_failed", error=error))
            return
        dialog = ReferenceCleanupDialog(
            self._app, title=tr("quarantine_manage.title"),
            lines=format_delete_plan(unit, paths, manifest_valid=unit.manifest_valid),
            header=tr("quarantine_manage.delete_header"), run_label=tr("quarantine_manage.delete_run"),
        )
        dialog.wait_window()
        if not dialog.result:
            return
        result = self._app.config_service.delete_quarantine_unit(
            unit.unit_id, config_root=self._app.config_root,
            allow_invalid_manifest=not unit.manifest_valid,
        )
        messagebox.showinfo(tr("quarantine_manage.title"), "\n".join(format_delete_result(result)))
