from __future__ import annotations

from copy import deepcopy
import tkinter as tk
from tkinter import messagebox
from typing import Callable

from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.domain.key_hold import MODIFIER_KEY_NAMES
from keyseq.domain.screen_grid import (
    MIN_EDIT_CELL_PX, SubLayout, TopLayout, auto_fill_sub_keys, delete_cell, delete_row,
    grid_key_name, label_position_of, move_cell_boundary, move_row_boundary, reassign_top_keys,
    set_cell_key, split_cell, split_row, sub_layout_of, sub_layout_to_json,
    top_cell_rects, top_layout_for, top_layout_to_json, validate_sub, validate_top,
)
from keyseq.presentation.modal import grab_modal
from keyseq.presentation.tk_keys import normalize_tk_key_event
from keyseq.presentation.screen_grid.grid_editor_panel import GridEditorPanel
from keyseq.presentation.screen_grid.cell_label import (
    center_font_for_rect, corner_label_font, draw_cell_label,
)


class GridEditorWindow(tk.Toplevel):
    """画面ごとの形を下書きで編集する、クリックを受ける窓。"""

    def __init__(self, parent, *, grid: dict | None, monitors: list[MonitorInfo],
                 start_monitor_id: str, reserved: set[str],
                 key_name_from_event: Callable[[object], str] | None = None) -> None:
        if not monitors:
            raise ValueError("編集できる画面がありません")
        super().__init__(parent)
        self.result = None
        self.monitors = list(monitors)
        self.reserved = set(reserved)
        self._key_name_from_event = key_name_from_event or normalize_tk_key_event
        self._grid = deepcopy(grid) if isinstance(grid, dict) else {}
        self.label_position = label_position_of(self._grid)
        records = self._grid.get("monitors")
        self._records: dict = deepcopy(records) if isinstance(records, dict) else {}
        self._layouts: dict[str, TopLayout] = {}
        self._edited: set[str] = set()
        self.selected: tuple[int, int] | None = None
        self._drag: tuple | None = None
        self.sub = sub_layout_of(self._grid)
        self.monitor = next((m for m in monitors if m.id == start_monitor_id), monitors[0])
        self.overrideredirect(True)
        self.attributes("-alpha", 0.5)
        self.attributes("-topmost", True)
        self.canvas = tk.Canvas(self, background="#202028", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        self.bind("<KeyPress>", self.on_key)
        self.panel = GridEditorPanel(self)
        self.bind("<Map>", self._on_first_map, add="+")
        self._first_map_seen = False
        self.switch_monitor(self.monitor.id)
        grab_modal(self, parent, focus=self.canvas)

    @property
    def layout(self) -> TopLayout:
        return self._layouts[self.monitor.id]

    def switch_monitor(self, monitor_id: str) -> None:
        self.monitor = next(m for m in self.monitors if m.id == monitor_id)
        if monitor_id not in self._layouts:
            self._layouts[monitor_id] = top_layout_for(self._grid, monitor_id)
        self.selected = (0, 0)
        self.panel.clear_sub_selection()
        self._drag = None
        left, top, right, bottom = self.monitor.rect
        self.geometry(f"{right - left}x{bottom - top}+{left}+{top}")
        self.panel.geometry(f"+{left + 12}+{top + 12}")
        self.panel.monitor_combo.current(self.monitors.index(self.monitor))
        self.draw()
        self._reapply_stacking()

    def _reapply_stacking(self) -> None:
        self.wm_attributes("-topmost", True)
        self.lift()
        self.panel.wm_attributes("-topmost", True)
        self.panel.lift()

    def label_position_changed(self) -> None:
        self.label_position = "top_left" if self.panel.label_position_var.get() else "center"
        self.draw()

    def _on_first_map(self, _event=None) -> None:
        if self._first_map_seen:
            return
        self._first_map_seen = True
        self.after_idle(self._reapply_initial_window_state)

    def _reapply_initial_window_state(self) -> None:
        if self.winfo_exists():
            self.attributes("-alpha", 0.5)
            self.switch_monitor(self.monitor.id)

    def cell_rects(self):
        left, top, right, bottom = self.monitor.rect
        return top_cell_rects((0, 0, right - left, bottom - top), self.layout)

    def draw(self) -> None:
        self.canvas.delete("all")
        corner_font = corner_label_font(self.canvas)
        for row_index, row in enumerate(self.cell_rects()):
            for col_index, (rect, key) in enumerate(row):
                selected = self.selected == (row_index, col_index)
                in_row = self.selected is not None and self.selected[0] == row_index
                color = "#ffcc66" if in_row else "#66d9ef"
                self.canvas.create_rectangle(*rect, outline=color, width=3 if selected else 1,
                                             fill="#484838" if selected else "")
                draw_cell_label(
                    self.canvas, rect, key, position=self.label_position, fill=color,
                    center_font=center_font_for_rect(rect),
                    corner_font=corner_font,
                )
        self.panel.update_selection(self.selected)

    def _replace(self, layout: TopLayout) -> None:
        if layout == self.layout:
            return
        self._layouts[self.monitor.id] = layout
        self._edited.add(self.monitor.id)
        self.draw()

    def on_press(self, event) -> None:
        self.panel.clear_sub_selection()
        self.canvas.focus_set()
        rows = self.cell_rects()
        self._drag = None
        for index, row in enumerate(rows[:-1]):
            if abs(event.y - row[0][0][3]) <= 4:
                self._drag = ("row", index)
                return
        for row_index, row in enumerate(rows):
            for col_index, (rect, _key) in enumerate(row):
                x1, y1, x2, y2 = rect
                if y1 <= event.y < y2:
                    if col_index < len(row) - 1 and abs(event.x - x2) <= 4:
                        self._drag = ("cell", row_index, col_index)
                        return
                    if x1 <= event.x < x2:
                        self.selected = (row_index, col_index)
        self.draw()

    def on_motion(self, event) -> None:
        rows = self.cell_rects()
        cursor = ""
        if any(abs(event.y - row[0][0][3]) <= 4 for row in rows[:-1]):
            cursor = "sb_v_double_arrow"
        else:
            for row in rows:
                if any(abs(event.x - rect[2]) <= 4 and rect[1] <= event.y < rect[3]
                       for rect, _key in row[:-1]):
                    cursor = "sb_h_double_arrow"
                    break
        self.canvas.configure(cursor=cursor)

    def on_drag(self, event) -> None:
        if self._drag is None:
            return
        left, top, right, bottom = self.monitor.rect
        if self._drag[0] == "row":
            layout = move_row_boundary(self.layout, self._drag[1],
                                       event.y / (bottom - top), MIN_EDIT_CELL_PX / (bottom - top))
        else:
            layout = move_cell_boundary(self.layout, self._drag[1], self._drag[2],
                                        event.x / (right - left), MIN_EDIT_CELL_PX / (right - left))
        self._replace(layout)

    def on_release(self, _event=None) -> None:
        self._drag = None

    def on_escape(self, _event=None):
        if self.panel.sub_selected is not None:
            self.panel.clear_sub_selection()
        elif self.selected is not None:
            self.selected = None
            self.draw()
        else:
            self.destroy()
        return "break"

    def on_key(self, event):
        key = self._key_name_from_event(event) or normalize_tk_key_event(event)
        if key == "esc":
            return self.on_escape(event)
        if key in MODIFIER_KEY_NAMES:
            return "break"
        if self.panel.sub_selected is not None:
            self.panel.set_selected_sub_key(key)
        elif self.selected is not None:
            self._replace(set_cell_key(self.layout, *self.selected, key))
        return "break"

    def add_row(self) -> None:
        if self.selected is not None:
            self._replace(split_row(self.layout, self.selected[0], self.reserved))

    def add_cell(self) -> None:
        if self.selected is not None:
            self._replace(split_cell(self.layout, *self.selected, self.reserved))

    def remove_row(self) -> None:
        if self.selected is None:
            return
        layout = delete_row(self.layout, self.selected[0])
        self.selected = (min(self.selected[0], len(layout.rows) - 1), 0)
        self._replace(layout)
        self.draw()

    def remove_cell(self) -> None:
        if self.selected is None:
            return
        row, col = self.selected
        layout = delete_cell(self.layout, row, col)
        self.selected = (row, min(col, len(layout.rows[row].cells) - 1))
        self._replace(layout)
        self.draw()

    def reassign(self) -> None:
        self._replace(reassign_top_keys(self.layout, self.reserved))

    def reset_monitor(self) -> None:
        monitor_id = self.monitor.id
        self._records.pop(monitor_id, None)
        self._edited.discard(monitor_id)
        self._layouts[monitor_id] = top_layout_for(None, monitor_id)
        self.selected = (0, 0)
        self.panel.clear_sub_selection()
        self._drag = None
        self.draw()

    def sub_counts_changed(self, *_args) -> None:
        try:
            rows, cols = int(self.panel.rows_var.get()), int(self.panel.cols_var.get())
        except ValueError:
            return
        if 1 <= rows <= 9 and 1 <= cols <= 9:
            keys = auto_fill_sub_keys(rows, cols, self.reserved)
            self.panel.rebuild_sub_key_entries(rows, cols, keys)
            self.sub = SubLayout(rows, cols, keys)

    def accept(self) -> None:
        errors = []
        for monitor_id in self._edited:
            errors.extend(f"{monitor_id}: {reason}"
                          for reason in validate_top(self._layouts[monitor_id], self.reserved))
        try:
            rows, cols = int(self.panel.rows_var.get()), int(self.panel.cols_var.get())
            entries = self.panel.sub_key_rows()
            for index, keys in enumerate(entries, start=1):
                if len(keys) != cols:
                    errors.append(f"細分化・段 {index}: キーは {cols} 個にしてください")
            if errors:
                messagebox.showerror("枠を設定できません", "\n".join(errors), parent=self.panel)
                return
            sub = SubLayout(int(self.panel.rows_var.get()), int(self.panel.cols_var.get()),
                            tuple(grid_key_name(k) for row in entries for k in row))
            errors.extend(validate_sub(sub, self.reserved))
        except (ValueError, tk.TclError):
            errors.append("細分化: 段数・列数は1〜9の整数にしてください")
        if errors:
            messagebox.showerror("枠を設定できません", "\n".join(errors), parent=self.panel)
            return
        records = deepcopy(self._records)
        for monitor_id in self._edited:
            records[monitor_id] = top_layout_to_json(self._layouts[monitor_id])
        self.result = {"monitors": records, "sub": sub_layout_to_json(sub)}
        if self.label_position == "top_left":
            self.result["label_position"] = "top_left"
        self.destroy()
