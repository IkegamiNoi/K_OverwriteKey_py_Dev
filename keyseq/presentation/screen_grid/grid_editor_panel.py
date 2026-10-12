from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class GridEditorPanel(tk.Toplevel):
    """編集窓に付属する操作と細分化の入力欄。"""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self.title("枠を編集")
        self.transient(editor)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", editor.destroy)
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)
        labels = [f"{index + 1}: {monitor.id}" for index, monitor in enumerate(editor.monitors)]
        self.monitor_combo = ttk.Combobox(frame, values=labels, state="readonly", width=38)
        self.monitor_combo.current(editor.monitors.index(editor.monitor))
        self.monitor_combo.pack(fill="x")
        self.monitor_combo.bind("<<ComboboxSelected>>", lambda _e: self._then_focus_editor(
            editor, lambda: editor.switch_monitor(editor.monitors[self.monitor_combo.current()].id)))
        self.hint = ttk.Label(frame, text="枠をクリックして選ぶ → キーを押すとその枠のキー")
        self.hint.pack(anchor="w", pady=(4, 2))
        self.buttons = {}
        for text, command in (
            ("行の追加", editor.add_row), ("行の削除", editor.remove_row),
            ("列の追加", editor.add_cell), ("列の削除", editor.remove_cell),
            ("振り直し", editor.reassign), ("この画面を既定に戻す", editor.reset_monitor),
        ):
            # 押した後もキーで枠のキーを変えられるよう、フォーカスを編集の窓へ戻す。
            button = ttk.Button(
                frame, text=text, command=lambda c=command: self._then_focus_editor(editor, c)
            )
            button.pack(fill="x", pady=2)
            self.buttons[text] = button
        ttk.Label(frame, text="細分化（行数・列数 / 行ごとの読む順のキー）").pack(anchor="w")
        counts = ttk.Frame(frame)
        counts.pack(fill="x")
        self.rows_var = tk.StringVar(value=str(editor.sub.rows))
        self.cols_var = tk.StringVar(value=str(editor.sub.cols))
        for label, variable in (("行", self.rows_var), ("列", self.cols_var)):
            ttk.Label(counts, text=label).pack(side="left")
            ttk.Spinbox(counts, from_=1, to=9, width=4, textvariable=variable).pack(side="left")
        self.sub_keys_frame = ttk.Frame(frame)
        self.sub_keys_frame.pack(fill="x", pady=4)
        self.sub_key_vars = []
        self.sub_key_entries = []
        self.rebuild_sub_key_entries(editor.sub.rows, editor.sub.cols, editor.sub.keys)
        self.rows_var.trace_add("write", editor.sub_counts_changed)
        self.cols_var.trace_add("write", editor.sub_counts_changed)
        actions = ttk.Frame(frame)
        actions.pack(anchor="e")
        for text, command in (("OK", editor.accept), ("キャンセル", editor.destroy)):
            ttk.Button(actions, text=text, command=command).pack(side="left", padx=3)
        self.bind("<Escape>", editor.on_escape)

    @staticmethod
    def _then_focus_editor(editor, command) -> None:
        command()
        if editor.winfo_exists():
            editor.canvas.focus_set()

    def update_selection(self, selected) -> None:
        state = "normal" if selected is not None else "disabled"
        for text in ("行の追加", "行の削除", "列の追加", "列の削除"):
            self.buttons[text].configure(state=state)

    def rebuild_sub_key_entries(self, rows: int, cols: int, keys) -> None:
        for child in self.sub_keys_frame.winfo_children():
            child.destroy()
        self.sub_key_vars = []
        self.sub_key_entries = []
        for row_index in range(rows):
            ttk.Label(self.sub_keys_frame, text=f"行 {row_index + 1}").pack(anchor="w")
            variable = tk.StringVar(value=" ".join(keys[row_index * cols:(row_index + 1) * cols]))
            entry = ttk.Entry(self.sub_keys_frame, textvariable=variable, width=42)
            entry.pack(fill="x", pady=(0, 3))
            self.sub_key_vars.append(variable)
            self.sub_key_entries.append(entry)
