from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from keyseq.domain.screen_grid import GRID_OPS, OP_LABELS


_KEY_BUTTON_BG = "#e0e0e0"
_KEY_BUTTON_ACTIVE_BG = "#d0d0d0"
_KEY_BUTTON_SELECTED_BG = "#ffcc66"


class GridEditorPanel(tk.Toplevel):
    """編集窓に付属する操作と細分化のキー選択。"""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self.editor = editor
        self.sub_selected = None
        self.op_selected: str | None = None
        self.op_key_buttons: dict[str, tk.Button] = {}
        self._max_height: int | None = None
        self._measure_pending = False
        self._measuring_scroll_area = False
        # 窓が未表示のとき winfo_ismapped は 0 になるので、スクロールバーの表示は自前の印で持つ。
        self._scrollbar_shown = False
        self.title("枠を編集")
        self.transient(editor)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", editor.destroy)
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)
        self.scroll_frame = ttk.Frame(frame)
        self.scroll_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.scroll_frame, width=1, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_frame.grid_rowconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.scrollbar.grid_remove()
        content = ttk.Frame(self.canvas)
        self._scroll_content = content
        self._content_window = self.canvas.create_window((0, 0), window=content, anchor="nw")
        self.canvas.bind("<Configure>", self._on_scroll_canvas_configure)
        self.bind("<<ThemeChanged>>", lambda _event: self._schedule_scroll_measurement())

        labels = [f"{index + 1}: {monitor.id}" for index, monitor in enumerate(editor.monitors)]
        self.monitor_combo = ttk.Combobox(content, values=labels, state="readonly", width=38)
        self.monitor_combo.current(editor.monitors.index(editor.monitor))
        self.monitor_combo.pack(fill="x")
        self.monitor_combo.bind("<<ComboboxSelected>>", lambda _e: self._then_focus_editor(
            editor, lambda: editor.switch_monitor(editor.monitors[self.monitor_combo.current()].id)))
        self.hint = ttk.Label(content, text="枠をクリックして選ぶ → キーを押すとその枠のキー")
        self.hint.pack(anchor="w", pady=(4, 2))
        self.buttons = {}
        button_frame = ttk.Frame(content)
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure(0, weight=1, uniform="actions")
        button_frame.grid_columnconfigure(1, weight=1, uniform="actions")
        for index, (text, command) in enumerate((
            ("段の追加", editor.add_row), ("段の削除", editor.remove_row),
            ("列の追加", editor.add_cell), ("列の削除", editor.remove_cell),
            ("キーを振り直す", editor.reassign), ("この画面を既定に戻す", editor.reset_monitor),
        )):
            # 押した後もキーで枠のキーを変えられるよう、フォーカスを編集の窓へ戻す。
            button = ttk.Button(
                button_frame, text=text, command=lambda c=command: self._then_focus_editor(editor, c)
            )
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=1, pady=2)
            self.buttons[text] = button
        self.label_position_var = tk.BooleanVar(value=editor.label_position == "top_left")
        self.label_position_check = ttk.Checkbutton(
            content, text="キーを枠の左上に表示", variable=self.label_position_var,
            command=editor.label_position_changed,
        )
        self.label_position_check.pack(anchor="w")
        self.ops_frame = ttk.LabelFrame(content, text="操作キー（Esc = 戻る・テンキーのEnter = クリックは固定）")
        self.ops_frame.pack(fill="x", pady=(4, 2))
        for column in (1, 3):
            self.ops_frame.grid_columnconfigure(column, weight=1)
        for index, operation in enumerate(GRID_OPS):
            grid_row, group = divmod(index, 2)
            label_column = group * 2
            ttk.Label(self.ops_frame, text=OP_LABELS[operation]).grid(
                row=grid_row, column=label_column, sticky="w", padx=3, pady=1
            )
            button = tk.Button(
                self.ops_frame, text=editor.ops[operation], relief=tk.RAISED,
                background=_KEY_BUTTON_BG, activebackground=_KEY_BUTTON_ACTIVE_BG,
                command=lambda name=operation: self.select_op_key(name),
            )
            button.grid(row=grid_row, column=label_column + 1, padx=2, pady=1, sticky="ew")
            self.op_key_buttons[operation] = button
        self.update_op_buttons()
        reset_ops = ttk.Button(
            self.ops_frame, text="操作キーを既定に戻す",
            command=lambda: self._then_focus_editor(editor, editor.reset_ops),
        )
        reset_ops.grid(row=4, column=0, columnspan=4, sticky="ew", padx=3, pady=(3, 2))
        ttk.Label(content, text="細分化（段数・列数 / 枠をクリックしてキーを押す）").pack(anchor="w")
        counts = ttk.Frame(content)
        counts.pack(fill="x")
        self.rows_var = tk.StringVar(value=str(editor.sub.rows))
        self.cols_var = tk.StringVar(value=str(editor.sub.cols))
        self.count_spinboxes = []
        for label, variable in (("段", self.rows_var), ("列", self.cols_var)):
            ttk.Label(counts, text=label).pack(side="left")
            spinbox = ttk.Spinbox(counts, from_=1, to=9, width=4, textvariable=variable)
            spinbox.pack(side="left")
            self.count_spinboxes.append(spinbox)
        self.sub_keys_frame = ttk.Frame(content)
        self.sub_keys_frame.pack(fill="x", pady=4)
        self.sub_keys: list[str] = []
        self.sub_rows = 0
        self.sub_cols = 0
        self.rebuild_sub_key_entries(editor.sub.rows, editor.sub.cols, editor.sub.keys)
        self.rows_var.trace_add("write", editor.sub_counts_changed)
        self.cols_var.trace_add("write", editor.sub_counts_changed)
        self.actions = ttk.Frame(frame)
        self.actions.pack(anchor="e")
        for text, command in (("OK", editor.accept), ("キャンセル", editor.destroy)):
            ttk.Button(self.actions, text=text, command=command).pack(side="left", padx=3)
        self.bind("<Escape>", editor.on_escape)
        self._bind_mousewheel_tree(content, bind_configure=True)
        self._schedule_scroll_measurement()

    def _bind_mousewheel_tree(self, widget, *, bind_configure: bool = False) -> None:
        widget.bind("<MouseWheel>", self._on_mousewheel)
        if bind_configure:
            widget.bind("<Configure>", self._on_scroll_content_configure, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_tree(child)

    def _on_mousewheel(self, event):
        if self._scrollbar_shown:
            units = int(-event.delta / 120) or (-1 if event.delta > 0 else 1)
            self.canvas.yview_scroll(units, "units")
        return "break"

    def _on_scroll_content_configure(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if not self._measuring_scroll_area:
            self._schedule_scroll_measurement()

    def _on_scroll_canvas_configure(self, event) -> None:
        item_width = self.canvas.itemcget(self._content_window, "width")
        if not item_width or int(float(item_width)) != event.width:
            self.canvas.itemconfigure(self._content_window, width=event.width)

    def _schedule_scroll_measurement(self) -> None:
        if self._measure_pending or self._measuring_scroll_area:
            return
        self._measure_pending = True
        self.after_idle(self._measure_scroll_area)

    def _measure_scroll_area(self) -> None:
        self._measure_pending = False
        if self._measuring_scroll_area:
            return
        # 窓を閉じた後に after_idle の予約が残っていても何もしない。
        if not self.winfo_exists():
            return
        self._measuring_scroll_area = True
        try:
            # 作り直したボタン等の要求サイズを反映してから測る（after_idle は配置の計算より先に走ることがある）。
            self._scroll_content.update_idletasks()
            content_height = self._scroll_content.winfo_reqheight()
            if self._max_height is None:
                available_height = content_height
            else:
                available_height = max(1, self._max_height - self.actions.winfo_reqheight() - 20)
            canvas_height = min(content_height, available_height)
            if int(self.canvas.cget("height")) != canvas_height:
                self.canvas.configure(height=canvas_height)
            if int(self.scroll_frame.cget("height")) != canvas_height:
                self.scroll_frame.configure(height=canvas_height)

            show_scrollbar = content_height > available_height
            if self._scrollbar_shown != show_scrollbar:
                self._scrollbar_shown = show_scrollbar
                if show_scrollbar:
                    self.scrollbar.grid()
                else:
                    self.scrollbar.grid_remove()

            content_width = max(
                self._scroll_content.winfo_reqwidth(), self.monitor_combo.winfo_reqwidth()
            )
            if int(self.canvas.cget("width")) != content_width:
                self.canvas.configure(width=content_width)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        finally:
            self._measuring_scroll_area = False

    def set_max_height(self, height: int) -> None:
        self._max_height = max(1, height)
        self._measure_scroll_area()

    @staticmethod
    def _then_focus_editor(editor, command) -> None:
        command()
        if editor.winfo_exists():
            editor.canvas.focus_set()

    def select_op_key(self, name: str) -> None:
        self.editor.selected = None
        self.editor._drag = None
        self.clear_sub_selection()
        changed = self.op_selected != name
        self.op_selected = name
        if changed:
            self.editor._capture_target_changed()
        self.update_op_buttons()
        self.editor.draw()
        self.editor.canvas.focus_set()

    def clear_op_selection(self) -> None:
        changed = self.op_selected is not None
        self.op_selected = None
        if changed:
            self.editor._capture_target_changed()
        self.update_op_buttons()

    def clear_key_button_selections(self) -> None:
        self.clear_sub_selection()
        self.clear_op_selection()

    def update_op_buttons(self) -> None:
        for operation, button in self.op_key_buttons.items():
            selected = operation == self.op_selected
            button.configure(
                text=self.editor.ops[operation],
                relief=tk.SUNKEN if selected else tk.RAISED,
                background=_KEY_BUTTON_SELECTED_BG if selected else _KEY_BUTTON_BG,
            )
        self._schedule_scroll_measurement()

    def update_selection(self, selected) -> None:
        state = "normal" if selected is not None else "disabled"
        for text in ("段の追加", "段の削除", "列の追加", "列の削除"):
            self.buttons[text].configure(state=state)

    def rebuild_sub_key_entries(self, rows: int, cols: int, keys) -> None:
        self.clear_op_selection()
        for child in self.sub_keys_frame.winfo_children():
            child.destroy()
        self.sub_rows = rows
        self.sub_cols = cols
        self.sub_keys = list(keys)
        changed = self.sub_selected is not None
        self.sub_selected = None
        if changed:
            self.editor._capture_target_changed()
        self.sub_key_buttons = []
        for row_index in range(rows):
            for col_index in range(cols):
                index = row_index * cols + col_index
                button = tk.Button(
                    self.sub_keys_frame, text=self.sub_keys[index], width=6,
                    relief=tk.RAISED, background=_KEY_BUTTON_BG, activebackground=_KEY_BUTTON_ACTIVE_BG,
                    command=lambda i=index: self.select_sub_key(i),
                )
                button.grid(row=row_index, column=col_index, padx=1, pady=1)
                self.sub_key_buttons.append(button)
                self._bind_mousewheel_tree(button)
        self._schedule_scroll_measurement()

    def select_sub_key(self, index: int) -> None:
        self.clear_op_selection()
        self.editor.selected = None
        self.editor._drag = None
        changed = self.sub_selected != index
        self.sub_selected = index
        if changed:
            self.editor._capture_target_changed()
        self.update_sub_selection()
        self.editor.draw()
        self.editor.canvas.focus_set()

    def update_sub_selection(self) -> None:
        for index, button in enumerate(self.sub_key_buttons):
            selected = index == self.sub_selected
            button.configure(
                relief=tk.SUNKEN if selected else tk.RAISED,
                background=_KEY_BUTTON_SELECTED_BG if selected else _KEY_BUTTON_BG,
            )

    def clear_sub_selection(self) -> None:
        changed = self.sub_selected is not None
        self.sub_selected = None
        if changed:
            self.editor._capture_target_changed()
        self.update_sub_selection()

    def sub_key_rows(self) -> list[list[str]]:
        return [self.sub_keys[row * self.sub_cols:(row + 1) * self.sub_cols]
                for row in range(self.sub_rows)]

    def set_selected_sub_key(self, key: str) -> None:
        if self.sub_selected is None:
            return
        self.sub_keys[self.sub_selected] = key
        self.sub_key_buttons[self.sub_selected].configure(text=key)
        self._schedule_scroll_measurement()
