from __future__ import annotations

import os
import tkinter as tk
from typing import Callable, Sequence
from tkinter import filedialog, font, messagebox, ttk

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP
from keyseq.presentation.controllers.config_io.child_save_rows import ChildSaveRow


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
            dialog.transient(self._app)
            dialog.grab_set()
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.wait_window()
        finally:
            self._app.hook.resume_hook_after_dialog()
        return result["choices"]

    def _create_action_dialog(self, rows, result):
        dialog = tk.Toplevel(self._app)
        dialog.title("子ファイルの保存")
        dialog.geometry("960x480")
        dialog.resizable(True, True)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(side="bottom", anchor="e", pady=(12, 0))
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas)
        content_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        window_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"),
        )
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._add_headers(content_frame, 0)
        choices, text_cells = self._add_rows(content_frame, rows, 1)
        self._configure_columns(content_frame)
        self._bind_content_width(canvas, content_frame, window_id, text_cells)
        ttk.Button(buttons, text="キャンセル", command=dialog.destroy).pack(side="right")
        ttk.Button(
            buttons,
            text="OK",
            command=lambda: self._confirm_actions(dialog, rows, choices, result),
        ).pack(side="right", padx=(0, 8))
        self._set_minimum_size(dialog, frame, list_frame, content_frame, scrollbar, len(rows))
        return dialog, choices

    @staticmethod
    def _add_headers(frame, row: int) -> None:
        for column, text in enumerate(("種別", "対象名", "保存先パス", "共有状況", "操作")):
            is_flexible = column in (1, 2)
            label_options = {"width": 1, "anchor": "w"} if is_flexible else {}
            ttk.Label(frame, text=text, **label_options).grid(
                row=row,
                column=column,
                sticky="ew" if is_flexible else "w",
                padx=(0, 8),
            )

    def _add_rows(
        self, frame, rows, start_row: int
    ) -> tuple[dict[tuple[str, str], tk.StringVar], list[dict[str, object]]]:
        choices: dict[tuple[str, str], tk.StringVar] = {}
        text_cells = []
        for index, child_row in enumerate(rows, start=start_row):
            child_id = (child_row.kind, child_row.key)
            choice = tk.StringVar(value=child_row.default_action)
            choices[child_id] = choice
            ttk.Label(frame, text=_kind_label(child_row.kind)).grid(row=index, column=0, sticky="w", padx=(0, 8))
            name_cell = self._add_text_cell(frame, index, 1, child_row.display_name, _ellipsize)
            path_cell = self._add_text_cell(frame, index, 2, child_row.target_path, _ellipsize_path)
            text_cells.extend((name_cell, path_cell))
            ttk.Label(frame, text=child_row.share_text).grid(row=index, column=3, sticky="w", padx=(0, 8))
            actions = ttk.Frame(frame)
            actions.grid(row=index, column=4, sticky="w")
            for action, label in ((ACTION_SAVE, "保存"), (ACTION_SAVE_AS, "別名保存"), (ACTION_SKIP, "保存しない")):
                ttk.Radiobutton(actions, text=label, variable=choice, value=action).pack(side="left")
        return choices, text_cells

    def _add_text_cell(self, frame, row: int, column: int, text: str, ellipsize):
        cell = {"text": text, "display": "", "ellipsize": ellipsize}
        label = ttk.Label(frame, text="", width=1, anchor="w")
        label.grid(row=row, column=column, sticky="ew", padx=(0, 8))
        cell["label"] = label
        self._bind_tooltip(label, text, lambda: cell["display"] != cell["text"])
        return cell

    @staticmethod
    def _configure_columns(frame) -> None:
        for column in (0, 3, 4):
            frame.columnconfigure(column, weight=0)
        for column, weight in ((1, 1), (2, 2)):
            frame.columnconfigure(column, weight=weight, minsize=1)

    @staticmethod
    def _bind_content_width(canvas, content_frame, window_id, text_cells) -> None:
        measure = font.nametofont("TkDefaultFont").measure
        last_width = None

        def resize_content(event) -> None:
            nonlocal last_width
            if event.width == last_width:
                return
            last_width = event.width
            canvas.itemconfigure(window_id, width=event.width)
            content_frame.update_idletasks()
            for cell in text_cells:
                display = _fit_text(
                    cell["text"], measure, cell["label"].winfo_width(), cell["ellipsize"]
                )
                if display != cell["display"]:
                    cell["label"].configure(text=display)
                    cell["display"] = display

        canvas.bind("<Configure>", resize_content)

    @staticmethod
    def _set_minimum_size(dialog, frame, list_frame, content_frame, scrollbar, row_count: int) -> None:
        dialog.update_idletasks()
        visible_rows = min(1, row_count)
        content_width, content_height = content_frame.grid_bbox(0, 0, 4, visible_rows)[2:]
        frame_overhead_width = max(0, frame.winfo_reqwidth() - list_frame.winfo_reqwidth())
        frame_overhead_height = max(0, frame.winfo_reqheight() - list_frame.winfo_reqheight())
        required_width = content_width + scrollbar.winfo_reqwidth() + frame_overhead_width
        required_height = content_height + frame_overhead_height
        dialog.minsize(max(720, required_width), max(320, required_height))

    @staticmethod
    def _bind_tooltip(widget, text: str, should_show: Callable[[], bool]) -> None:
        tooltip = None

        def hide_tooltip(_event=None) -> None:
            nonlocal tooltip
            if tooltip is None:
                return
            try:
                tooltip.destroy()
            except Exception:
                pass
            tooltip = None

        def show_tooltip(event) -> None:
            nonlocal tooltip
            hide_tooltip()
            if not should_show():
                return
            try:
                tooltip = tk.Toplevel(widget)
                tooltip.overrideredirect(True)
                tooltip.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
                ttk.Label(tooltip, text=text, padding=4).pack()
            except Exception:
                if tooltip is not None:
                    try:
                        tooltip.destroy()
                    except Exception:
                        pass
                tooltip = None

        try:
            widget.bind("<Enter>", show_tooltip)
            widget.bind("<Leave>", hide_tooltip)
            widget.bind("<Button>", hide_tooltip)
        except Exception:
            pass

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
            target_path = self._ask_save_as_path(row) if action == ACTION_SAVE_AS else ""
            if action == ACTION_SAVE_AS and not target_path:
                return None
            choices[(row.kind, row.key)] = (action, target_path)
        return choices

    def confirm_trigger_set_dependency(
        self, *, blocked_labels: Sequence[str], trigger_set_row: ChildSaveRow
    ) -> str:
        self.trigger_set_save_as_path = ""
        message = (
            "次の出力シーケンスの保存先が変わります:\n"
            f"{', '.join(blocked_labels)}\n\n"
            f"トリガー一覧の保存先: {trigger_set_row.target_path}\n"
            f"共有状況: {trigger_set_row.share_text}\n\n"
            "保存 = このままトリガー一覧を保存して索引を更新します。\n"
            "別名保存 = 別の保存先へトリガー一覧を保存して索引を更新します。\n"
            "保存しない = この保存では索引を更新しない（次回保存で反映）。\n"
            "キャンセル = 一覧から選び直します。"
        )
        result = {"action": ""}
        self._app.hook.suspend_hook_for_dialog()
        try:
            dialog = self._create_dependency_dialog(
                message,
                trigger_set_row,
                result,
            )
            dialog.transient(self._app)
            dialog.grab_set()
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.bind("<Escape>", lambda _event: dialog.destroy())
            dialog.wait_window()
            return result["action"]
        finally:
            self._app.hook.resume_hook_after_dialog()

    def _create_dependency_dialog(self, message, trigger_set_row, result):
        dialog = tk.Toplevel(self._app)
        dialog.title("トリガー一覧の保存が必要です")
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

        ttk.Button(buttons, text="キャンセル", command=dialog.destroy).pack(side="right")
        ttk.Button(buttons, text="保存しない", command=lambda: choose(ACTION_SKIP)).pack(
            side="right", padx=(0, 8)
        )
        save_as_button = ttk.Button(
            buttons,
            text="別名保存",
            command=lambda: choose(ACTION_SAVE_AS),
        )
        save_as_button.pack(side="right", padx=(0, 8))
        ttk.Button(buttons, text="保存", command=lambda: choose(ACTION_SAVE)).pack(
            side="right", padx=(0, 8)
        )
        save_as_button.focus_set()
        return dialog

    def confirm_recalculated_overwrite(
        self, rows: Sequence[ChildSaveRow]
    ) -> dict[tuple[str, str], tuple[str, str]] | None:
        if not rows:
            return {}
        message = "再計算後の保存先に既存ファイルがあります:\n\n" + "\n\n".join(
            (
                f"種別: {_kind_label(row.kind)}\n"
                f"対象名: {row.display_name}\n"
                f"保存先: {row.target_path}\n"
                f"共有状況: {row.share_text}"
            )
            for row in rows
        ) + "\n\n「はい」= このまま上書き / 「いいえ」= 別名で保存 / 「キャンセル」= 保存を中止"
        self._app.hook.suspend_hook_for_dialog()
        try:
            result = messagebox.askyesnocancel(
                "再計算後の保存先を確認",
                message,
                default=messagebox.NO,
            )
            if result is True:
                return {}
            if result is None:
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
        return filedialog.asksaveasfilename(
            title=f"{_kind_label(row.kind)}を別名で保存",
            initialdir=os.path.dirname(os.path.abspath(row.target_path)),
            initialfile=os.path.basename(row.target_path),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        ) or ""


def _kind_label(kind: str) -> str:
    return {
        "keymap": "キーマップ",
        "trigger_set": "トリガー一覧",
        "sequence": "出力シーケンス",
    }.get(kind, kind)


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
