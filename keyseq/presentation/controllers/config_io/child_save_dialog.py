from __future__ import annotations

import os
import tkinter as tk
from typing import Sequence
from tkinter import filedialog, messagebox, ttk

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_OTHER_PARENT,
    SHARE_UNKNOWN,
    ChildSaveRow,
)


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
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        self._add_headers(frame, 0)
        choices = self._add_rows(frame, rows, 1)
        buttons = ttk.Frame(frame)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=5, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="キャンセル", command=dialog.destroy).pack(side="right")
        ttk.Button(
            buttons,
            text="OK",
            command=lambda: self._confirm_actions(dialog, rows, choices, result),
        ).pack(side="right", padx=(0, 8))
        return dialog, choices

    @staticmethod
    def _add_headers(frame, row: int) -> None:
        for column, text in enumerate(("種別", "対象名", "保存先パス", "共有状況", "操作")):
            ttk.Label(frame, text=text).grid(row=row, column=column, sticky="w", padx=(0, 8))

    def _add_rows(self, frame, rows, start_row: int) -> dict[tuple[str, str], tk.StringVar]:
        choices: dict[tuple[str, str], tk.StringVar] = {}
        for index, child_row in enumerate(rows, start=start_row):
            child_id = (child_row.kind, child_row.key)
            choice = tk.StringVar(value=child_row.default_action)
            choices[child_id] = choice
            ttk.Label(frame, text=_kind_label(child_row.kind)).grid(row=index, column=0, sticky="w", padx=(0, 8))
            ttk.Label(frame, text=child_row.display_name).grid(row=index, column=1, sticky="w", padx=(0, 8))
            ttk.Label(frame, text=child_row.target_path).grid(row=index, column=2, sticky="w", padx=(0, 8))
            ttk.Label(frame, text=child_row.share_text).grid(row=index, column=3, sticky="w", padx=(0, 8))
            actions = ttk.Frame(frame)
            actions.grid(row=index, column=4, sticky="w")
            for action, label in ((ACTION_SAVE, "保存"), (ACTION_SAVE_AS, "別名保存"), (ACTION_SKIP, "保存しない")):
                ttk.Radiobutton(actions, text=label, variable=choice, value=action).pack(side="left")
        return choices

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
        recommendation = "\n\n所有元の安全確認のため、別名保存を推奨します。" if trigger_set_row.share_state in (
            SHARE_UNKNOWN,
            SHARE_OTHER_PARENT,
        ) else ""
        message = (
            "次の出力シーケンスの保存先が変わります:\n"
            f"{', '.join(blocked_labels)}\n\n"
            f"トリガー一覧の保存先: {trigger_set_row.target_path}\n"
            f"共有状況: {trigger_set_row.share_text}\n\n"
            "「はい」= このまま保存 / 「いいえ」= 別名で保存 / 「キャンセル」= 選び直す"
            f"{recommendation}"
        )
        default = messagebox.NO if trigger_set_row.share_state in (SHARE_UNKNOWN, SHARE_OTHER_PARENT) else messagebox.YES
        self._app.hook.suspend_hook_for_dialog()
        try:
            result = messagebox.askyesnocancel("トリガー一覧の保存が必要です", message, default=default)
            if result is True:
                return ACTION_SAVE
            if result is False:
                self.trigger_set_save_as_path = self._ask_save_as_path(trigger_set_row)
                return ACTION_SAVE_AS if self.trigger_set_save_as_path else ""
            return ""
        finally:
            self._app.hook.resume_hook_after_dialog()

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
