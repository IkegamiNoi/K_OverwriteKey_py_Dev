from __future__ import annotations

import os
import tkinter as tk
from typing import Callable, Sequence
from tkinter import filedialog, font, ttk

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP
from keyseq.presentation.controllers.config_io import choice_dialog
from keyseq.presentation.controllers.config_io.child_save_rows import ChildSaveRow
from keyseq.presentation.controllers.config_io.child_save_columns import CELL_GAP, HEADING_KEYS, size_action_dialog
from keyseq.presentation.child_kind_labels import kind_label as _kind_label
from keyseq.presentation.hover_tooltip import bind_hover_tooltip
from keyseq.presentation.modal import grab_modal
from keyseq.presentation.help.help_button import add_help_button
from keyseq.presentation.help.help_targets import KEYMAP_SET
from keyseq.shared.i18n import tr


class ChildSaveDialog:
    def __init__(self, app) -> None:
        self._app = app
        self.trigger_set_save_as_path = ""

    def ask_child_save_actions(
        self, rows: Sequence[ChildSaveRow]
    ) -> dict[tuple[str, str], tuple[str, str]] | None:
        result: dict[str, dict[tuple[str, str], tuple[str, str]] | None] = {"choices": None}
        self._app.hook.suspend_hook_for_dialog()
        try:
            dialog, choices = self._create_action_dialog(rows, result)
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.bind("<Escape>", lambda _event: dialog.destroy())
            grab_modal(dialog, self._app)
            dialog.wait_window()
        finally:
            self._app.hook.resume_hook_after_dialog()
        return result["choices"]

    def _create_action_dialog(self, rows, result):
        dialog = tk.Toplevel(self._app)
        dialog.title(tr("config_io.child_save.title"))
        dialog.resizable(True, True)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(side="bottom", fill="x", pady=(12, 0))
        add_help_button(buttons, dialog, KEYMAP_SET)
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        header_frame = ttk.Frame(list_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas)
        content_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        window_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        dialog.bind(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"),
        )
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        headers = self._add_headers(header_frame, 0)
        choices, text_cells = self._add_rows(content_frame, rows, 0)
        self._bind_content_width(canvas, content_frame, window_id, text_cells)
        ttk.Button(buttons, text=tr("common.cancel"), command=dialog.destroy).pack(side="right")
        ttk.Button(
            buttons,
            text="OK",
            command=lambda: self._confirm_actions(dialog, rows, choices, result),
        ).pack(side="right", padx=(0, CELL_GAP))
        size_action_dialog(dialog, frame, list_frame, header_frame, content_frame,
                           scrollbar, headers, text_cells, len(rows))
        return dialog, choices

    @staticmethod
    def _add_headers(frame, row: int) -> list:
        headers = []
        for column, key in enumerate(HEADING_KEYS):
            text = tr(key)
            is_flexible = column < 4
            label_options = {"width": 1, "anchor": "w"} if is_flexible else {}
            label = ttk.Label(frame, text=text, **label_options)
            label.grid(
                row=row,
                column=column,
                sticky="ew" if is_flexible else "w",
                padx=(0, CELL_GAP),
            )
            headers.append(label)
        return headers

    def _add_rows(
        self, frame, rows, start_row: int
    ) -> tuple[dict[tuple[str, str], tk.StringVar], list[dict[str, object]]]:
        choices: dict[tuple[str, str], tk.StringVar] = {}
        text_cells = []
        for index, child_row in enumerate(rows, start=start_row):
            child_id = (child_row.kind, child_row.key)
            choice = tk.StringVar(value=child_row.default_action)
            choices[child_id] = choice
            kind_cell = self._add_text_cell(frame, index, 0, _kind_label(child_row.kind), _ellipsize)
            name_cell = self._add_text_cell(frame, index, 1, child_row.display_name, _ellipsize)
            path_cell = self._add_text_cell(frame, index, 2, child_row.target_path, _ellipsize_path)
            share_cell = self._add_text_cell(frame, index, 3, child_row.share_text, _ellipsize)
            text_cells.extend((kind_cell, name_cell, path_cell, share_cell))
            actions = ttk.Frame(frame)
            actions.grid(row=index, column=4, sticky="w")
            for action, label_key in (
                (ACTION_SAVE, "common.save"),
                (ACTION_SAVE_AS, "config_io.child_save.action.save_as"),
                (ACTION_SKIP, "config_io.child_save.action.skip"),
            ):
                label = tr(label_key)
                state = "disabled" if action == ACTION_SKIP and not child_row.allow_skip else "normal"
                ttk.Radiobutton(actions, text=label, variable=choice, value=action, state=state).pack(side="left")
        return choices, text_cells

    def _add_text_cell(self, frame, row: int, column: int, text: str, ellipsize):
        cell = {"text": text, "display": "", "column": column, "ellipsize": ellipsize, "last_fit_width": None}
        label = ttk.Label(frame, text="", width=1, anchor="w")
        label.grid(row=row, column=column, sticky="ew", padx=(0, CELL_GAP))
        cell["label"] = label
        bind_hover_tooltip(
            label,
            lambda: text,
            lambda: cell["display"] != cell["text"],
        )
        return cell

    @staticmethod
    def _bind_content_width(canvas, content_frame, window_id, text_cells) -> None:
        measure = font.nametofont("TkDefaultFont").measure
        last_width = None

        def fit_text_cell(cell, width: int) -> None:
            if width <= 1 or width == cell["last_fit_width"]:
                return
            cell["last_fit_width"] = width
            display = _fit_text(cell["text"], measure, width, cell["ellipsize"])
            if display != cell["display"]:
                cell["label"].configure(text=display)
                cell["display"] = display

        def resize_text_cell(cell, event) -> None:
            fit_text_cell(cell, event.width)

        def resize_content(event) -> None:
            nonlocal last_width
            if event.width == last_width:
                return
            last_width = event.width
            canvas.itemconfigure(window_id, width=event.width)
            content_frame.update_idletasks()

        canvas.bind("<Configure>", resize_content)
        for cell in text_cells:
            cell["label"].bind(
                "<Configure>",
                lambda event, cell=cell: resize_text_cell(cell, event),
            )

    def _confirm_actions(self, dialog, rows, choice_vars, result) -> None:
        choices = self._resolve_action_targets(rows, choice_vars)
        if choices is None:
            return
        result["choices"] = choices
        dialog.destroy()

    def _resolve_action_targets(self, rows, choice_vars):
        choices: dict[tuple[str, str], tuple[str, str]] = {}
        for row in rows:
            action = choice_vars[(row.kind, row.key)].get()
            if action == ACTION_SKIP and not row.allow_skip:
                raise ValueError(tr("config_io.child_save.skip_migrated_error"))
            target_path = self._ask_save_as_path(row) if action == ACTION_SAVE_AS else ""
            if action == ACTION_SAVE_AS and not target_path:
                return None
            choices[(row.kind, row.key)] = (action, target_path)
        return choices

    def confirm_trigger_set_dependency(
        self, *, blocked_labels: Sequence[str], trigger_set_row: ChildSaveRow
    ) -> str:
        self.trigger_set_save_as_path = ""
        parent_name = _kind_label(trigger_set_row.kind)
        blocked_text = ", ".join(blocked_labels)
        message = tr(
            "config_io.child_save.dependency.message",
            blocked_labels=blocked_text,
            parent=parent_name,
            target_path=trigger_set_row.target_path,
            share_status=trigger_set_row.share_text,
        )
        result = {"action": ""}
        self._app.hook.suspend_hook_for_dialog()
        try:
            dialog, focus_widget = self._create_dependency_dialog(
                message,
                trigger_set_row,
                result,
            )
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.bind("<Escape>", lambda _event: dialog.destroy())
            grab_modal(dialog, self._app, focus=focus_widget)
            dialog.wait_window()
            return result["action"]
        finally:
            self._app.hook.resume_hook_after_dialog()

    def _create_dependency_dialog(self, message, trigger_set_row, result):
        dialog = tk.Toplevel(self._app)
        kind_name = _kind_label(trigger_set_row.kind)
        dialog.title(
            tr(
                "config_io.child_save.dependency.title",
                kind=kind_name,
            )
        )
        dialog.geometry("640x300")
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=message, justify="left", wraplength=600).pack(
            fill="both", expand=True
        )
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="e", pady=(12, 0))

        def choose(action: str) -> None:
            if action == ACTION_SAVE_AS:
                self.trigger_set_save_as_path = self._ask_save_as_path(trigger_set_row)
                if not self.trigger_set_save_as_path:
                    dialog.destroy()
                    return
            result["action"] = action
            dialog.destroy()

        ttk.Button(buttons, text=tr("common.cancel"), command=dialog.destroy).pack(side="right")
        ttk.Button(buttons, text=tr("config_io.child_save.action.skip"), command=lambda: choose(ACTION_SKIP)).pack(
            side="right", padx=(0, 8)
        )
        save_as_button = ttk.Button(
            buttons,
            text=tr("common.save_as"),
            command=lambda: choose(ACTION_SAVE_AS),
        )
        save_as_button.pack(side="right", padx=(0, 8))
        ttk.Button(buttons, text=tr("common.save"), command=lambda: choose(ACTION_SAVE)).pack(
            side="right", padx=(0, 8)
        )
        return dialog, save_as_button

    def confirm_recalculated_overwrite(
        self, rows: Sequence[ChildSaveRow]
    ) -> dict[tuple[str, str], tuple[str, str]] | None:
        if not rows:
            return {}
        rows_text = "\n\n".join(
            tr(
                "config_io.child_save.overwrite.row",
                kind=kind_name,
                name=row.display_name,
                target_path=row.target_path,
                share_status=row.share_text,
            )
            for row, kind_name in (
                (row, _kind_label(row.kind)) for row in rows
            )
        )
        message = tr(
            "config_io.child_save.overwrite.message",
            rows=rows_text,
        )
        self._app.hook.suspend_hook_for_dialog()
        try:
            choice = choice_dialog.ask_choice(
                self._app,
                title=tr("config_io.child_save.overwrite.title"),
                message=message,
                choices=[
                    ("overwrite", tr("config_io.io_dialogs.collision.overwrite")),
                    ("save_as", tr("common.save_as")),
                    ("abort", tr("config_io.child_save.overwrite.action.abort")),
                ],
                default="save_as",
                cancel="abort",
            )
            if choice == "overwrite":
                return {}
            if choice == "abort":
                return None
            choices: dict[tuple[str, str], tuple[str, str]] = {}
            for row in rows:
                target_path = self._ask_save_as_path(row)
                if not target_path:
                    return None
                choices[(row.kind, row.key)] = (ACTION_SAVE_AS, target_path)
            return choices
        finally:
            self._app.hook.resume_hook_after_dialog()

    @staticmethod
    def _ask_save_as_path(row: ChildSaveRow) -> str:
        kind_name = _kind_label(row.kind)
        return filedialog.asksaveasfilename(
            title=tr(
                "config_io.child_save.save_as.title",
                kind=kind_name,
            ),
            initialdir=os.path.dirname(os.path.abspath(row.target_path)),
            initialfile=os.path.basename(row.target_path),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        ) or ""


def _ellipsize(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _ellipsize_path(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    prefix_length = limit // 3
    suffix_length = limit - prefix_length - 1
    return text[:prefix_length] + "…" + text[-suffix_length:]


def _fit_text(text: str, measure: Callable[[str], int], max_px: int, ellipsize: Callable[[str, int], str]) -> str:
    if measure(text) <= max_px:
        return text
    first_candidate = ellipsize(text, 1)
    fitted = first_candidate if measure(first_candidate) <= max_px else ""
    low, high = 2, len(text)
    while low <= high:
        limit = (low + high) // 2
        candidate = ellipsize(text, limit)
        if measure(candidate) <= max_px:
            fitted = candidate
            low = limit + 1
        else:
            high = limit - 1
    return fitted or "…"
