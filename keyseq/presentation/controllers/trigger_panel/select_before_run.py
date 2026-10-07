"""トリガーごとの「選んでから実行」の UI 同期と書き戻し。"""
from __future__ import annotations


def sync_select_before_run(app, trigger: dict | None) -> None:
    app.ui_vars.sequence_select_before_run_var.set(bool(trigger and trigger.get("select_before_run") is True))


def update_select_before_run(controller) -> None:
    trigger = controller.selected_trigger()
    if not trigger:
        return
    app = controller._app
    value = bool(app.ui_vars.sequence_select_before_run_var.get())
    previous = trigger.get("select_before_run") is True
    trigger["select_before_run"] = value
    if previous != value:
        app.mark_sequence_dirty(trigger)
