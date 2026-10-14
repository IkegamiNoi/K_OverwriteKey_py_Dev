from __future__ import annotations

import tkinter as tk

from keyseq.application.screen_grid_session import GridView
from keyseq.infrastructure import win32_window
from keyseq.presentation.screen_grid.cell_label import (
    center_font_for_rect, corner_label_font, draw_cell_label,
)
from keyseq.presentation.screen_grid.crosshair import draw_crosshair


_TRANSPARENT = "#ff00fe"
_LINE = "#66d9ef"
_SELECTED = "#ffcc66"
_SHADE = "#202028"


class GridOverlayWindow:
    """今のモニタに一枚だけ表示する、遅延生成の透過窓。"""

    def __init__(self, root: tk.Misc) -> None:
        self._root = root
        self._window: tk.Toplevel | None = None
        self._canvas: tk.Canvas | None = None
        self._shown = False

    def _create(self) -> None:
        window = tk.Toplevel(self._root)
        window.withdraw()
        try:
            window.overrideredirect(True)
            window.attributes("-topmost", True)
            window.configure(background=_TRANSPARENT)
            canvas = tk.Canvas(
                window, background=_TRANSPARENT, highlightthickness=0, borderwidth=0,
            )
            canvas.pack(fill="both", expand=True)
            window.attributes("-transparentcolor", _TRANSPARENT)
            window.update_idletasks()
            if not win32_window.make_click_through_overlay(window.winfo_id()):
                raise RuntimeError("枠の窓のクリック透過設定に失敗しました")
        except Exception:
            window.destroy()
            raise
        self._window = window
        self._canvas = canvas

    def show(self, view: GridView) -> None:
        if not view.visible or view.monitor is None:
            self.hide()
            return
        if self._window is None:
            self._create()
        left, top, right, bottom = view.monitor.rect
        self._window.geometry(f"{right - left}x{bottom - top}+{left}+{top}")
        self._draw(view)
        if not self._shown:
            self._window.deiconify()
            self._shown = True

    def _draw(self, view: GridView) -> None:
        canvas = self._canvas
        canvas.delete("all")
        left, top, right, bottom = view.monitor.rect
        if view.level >= 1 and view.region is not None:
            self._shade_outside(view, right - left, bottom - top)
        corner_font = corner_label_font(canvas)
        for index, (rect, key) in enumerate(view.cells):
            x1, y1, x2, y2 = rect
            x1, x2 = x1 - left, x2 - left
            y1, y2 = y1 - top, y2 - top
            selected = index == view.selected
            color = _SELECTED if selected else _LINE
            canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3 if selected else 1)
            crosshair_on = selected and view.click_point is not None
            if crosshair_on:
                px, py = view.click_point
                draw_crosshair(
                    canvas, (x1, y1, x2, y2), (px - left, py - top), fill=_SELECTED,
                )
            if not (crosshair_on and view.label_position == "center"):
                draw_cell_label(
                    canvas, (x1, y1, x2, y2), key, position=view.label_position, fill=color,
                    center_font=center_font_for_rect((x1, y1, x2, y2)),
                    corner_font=corner_font,
                )

    def _shade_outside(self, view: GridView, width: int, height: int) -> None:
        left, top, _right, _bottom = view.monitor.rect
        x1, y1, x2, y2 = view.region
        x1, x2 = x1 - left, x2 - left
        y1, y2 = y1 - top, y2 - top
        for rect in ((0, 0, width, y1), (0, y2, width, height),
                     (0, y1, x1, y2), (x2, y1, width, y2)):
            if rect[2] > rect[0] and rect[3] > rect[1]:
                self._canvas.create_rectangle(
                    *rect, fill=_SHADE, outline="", stipple="gray50",
                )

    def hide(self) -> None:
        if self._window is not None:
            self._window.withdraw()
        self._shown = False

    def destroy(self) -> None:
        if self._window is not None:
            self._window.destroy()
        self._window = None
        self._canvas = None
        self._shown = False
