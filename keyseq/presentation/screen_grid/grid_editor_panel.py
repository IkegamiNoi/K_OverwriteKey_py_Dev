from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class GridEditorPanel(tk.Toplevel):
    """編集窓に付属する操作と細分化のキー選択。"""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self.editor = editor
        self.sub_selected = None
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
            ("段の追加", editor.add_row), ("段の削除", editor.remove_row),
            ("列の追加", editor.add_cell), ("列の削除", editor.remove_cell),
            ("振り直し", editor.reassign), ("この画面を既定に戻す", editor.reset_monitor),
        ):
            # 押した後もキーで枠のキーを変えられるよう、フォーカスを編集の窓へ戻す。
            button = ttk.Button(
                frame, text=text, command=lambda c=command: self._then_focus_editor(editor, c)
            )
            button.pack(fill="x", pady=2)
            self.buttons[text] = button
        self.label_position_var = tk.BooleanVar(value=editor.label_position == "top_left")
        self.label_position_check = ttk.Checkbutton(
            frame, text="キーを枠の左上に表示", variable=self.label_position_var,
            command=editor.label_position_changed,
        )
        self.label_position_check.pack(anchor="w")
        ttk.Label(frame, text="細分化（段数・列数 / 枠をクリックしてキーを押す）").pack(anchor="w")
        counts = ttk.Frame(frame)
        counts.pack(fill="x")
        self.rows_var = tk.StringVar(value=str(editor.sub.rows))
        self.cols_var = tk.StringVar(value=str(editor.sub.cols))
        self.count_spinboxes = []
        for label, variable in (("段", self.rows_var), ("列", self.cols_var)):
            ttk.Label(counts, text=label).pack(side="left")
            spinbox = ttk.Spinbox(counts, from_=1, to=9, width=4, textvariable=variable)
            spinbox.pack(side="left")
            self.count_spinboxes.append(spinbox)
        self.sub_keys_frame = ttk.Frame(frame)
        self.sub_keys_frame.pack(fill="x", pady=4)
        self.sub_keys: list[str] = []
        self.sub_rows = 0
        self.sub_cols = 0
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
        for text in ("段の追加", "段の削除", "列の追加", "列の削除"):
            self.buttons[text].configure(state=state)

    def rebuild_sub_key_entries(self, rows: int, cols: int, keys) -> None:
        for child in self.sub_keys_frame.winfo_children():
            child.destroy()
        self.sub_rows = rows
        self.sub_cols = cols
        self.sub_keys = list(keys)
        self.sub_selected = None
        self.sub_key_buttons = []
        for row_index in range(rows):
            for col_index in range(cols):
                index = row_index * cols + col_index
                button = tk.Button(
                    self.sub_keys_frame, text=self.sub_keys[index], width=6,
                    relief=tk.RAISED, background="#e0e0e0", activebackground="#d0d0d0",
                    command=lambda i=index: self.select_sub_key(i),
                )
                button.grid(row=row_index, column=col_index, padx=1, pady=1)
                self.sub_key_buttons.append(button)

    def select_sub_key(self, index: int) -> None:
        self.editor.selected = None
        self.editor._drag = None
        self.sub_selected = index
        self.update_sub_selection()
        self.editor.draw()
        self.editor.canvas.focus_set()

    def update_sub_selection(self) -> None:
        for index, button in enumerate(self.sub_key_buttons):
            selected = index == self.sub_selected
            button.configure(
                relief=tk.SUNKEN if selected else tk.RAISED,
                background="#ffcc66" if selected else "#e0e0e0",
            )

    def clear_sub_selection(self) -> None:
        self.sub_selected = None
        self.update_sub_selection()

    def sub_key_rows(self) -> list[list[str]]:
        return [self.sub_keys[row * self.sub_cols:(row + 1) * self.sub_cols]
                for row in range(self.sub_rows)]

    def set_selected_sub_key(self, key: str) -> None:
        if self.sub_selected is None:
            return
        self.sub_keys[self.sub_selected] = key
        self.sub_key_buttons[self.sub_selected].configure(text=key)
