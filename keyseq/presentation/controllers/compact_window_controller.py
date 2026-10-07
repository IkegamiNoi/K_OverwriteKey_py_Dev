"""省略表示のウィンドウサイズ・最小高さ・遅延保存を受け持つ。"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from keyseq.presentation.compact_window_size import (
    COMPACT_WINDOW_SIZE_KEY, compact_geometry, parse_compact_window_size,
)
from keyseq.presentation.controllers.pane_layout.pane_layout_controller import WINDOW_SIZE_SAVE_DELAY_MS
from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class CompactWindowController:
    def __init__(self, app: App):
        self.app = app
        self.minimum_height = 1
        self._save_id: str | None = None
        self._last_size: tuple[int, int] | None = None
        self._auto_size: tuple[int, int] | None = None
        self.status_frames = []

    def install(self) -> None:
        self.app.bind("<Configure>", self._on_configure, add="+")
        self.app.bind("<Destroy>", self._on_destroy, add="+")
        # ルート直下で pack される共通ステータスの枠を測る。
        self.status_frames = [
            frame for frame in self.app.pack_slaves() if frame is not self.app.outer
        ]

    @staticmethod
    def _pack_y(widget: tk.Widget) -> int:
        raw_values = widget.pack_info().get("pady", 0)
        values = CompactWindowController._split_tk_list(widget, raw_values)
        pixels = [widget.winfo_pixels(str(value)) for value in values]
        return 2 * pixels[0] if len(pixels) == 1 else sum(pixels)

    @staticmethod
    def _split_tk_list(widget: tk.Misc, value) -> tuple:
        if isinstance(value, str):
            return widget.tk.splitlist(value)
        if isinstance(value, (tuple, list)):
            return value
        return (value,)

    def _measure(self) -> int:
        app = self.app
        app.update_idletasks()
        view = app.compact_view
        box = view.trigger_box
        outer_padding = self._split_tk_list(app, app.outer.cget("padding"))
        padding = [app.winfo_pixels(str(value)) for value in outer_padding]
        outer_y = 2 * padding[0] if len(padding) == 1 else padding[1] + padding[-1]
        # 枠の要求高さから子の要求高さを引くので、開閉・割り当て高さに依存しない。
        box_chrome = box.winfo_reqheight() - box.call_view_column.winfo_reqheight()
        return (
            outer_y + view.header_area.winfo_reqheight() + self._pack_y(view.header_area)
            + self._pack_y(view.main_area) + box_chrome
            + 2 * box.trigger_panes.winfo_pixels(str(box.trigger_panes.cget("borderwidth")))
            + list_minimum_height(box.trigger_list)
            + box.sequence_frame.heading.winfo_reqheight() + box.call_view_frame.heading.winfo_reqheight()
            + sum(frame.winfo_reqheight() + self._pack_y(frame) for frame in self.status_frames)
        )

    def apply(self) -> None:
        self.cancel_save()
        self.minimum_height = self._measure()
        app = self.app
        saved = parse_compact_window_size(app._startup_settings.get(COMPACT_WINDOW_SIZE_KEY))
        size = compact_geometry(
            *saved, app.winfo_height(), self.minimum_height,
            app.winfo_screenwidth(), app.winfo_screenheight(),
        )
        self._apply_size(size)

    def _apply_size(self, size: tuple[int, int]) -> None:
        self._auto_size = size
        self.app.geometry(f"{size[0]}x{size[1]}")
        self.app.minsize(1, self.minimum_height)
        self.app.update_idletasks()
        # WM による丸めもアプリが当てたサイズとして扱う。
        self._auto_size = self.app.winfo_width(), self.app.winfo_height()
        self._last_size = self._auto_size
        self.cancel_save()

    def on_font_changed(self) -> None:
        if not self.app._compact_mode:
            return
        self.minimum_height = self._measure()
        if self.app.winfo_height() < self.minimum_height:
            self.cancel_save()
            self._apply_size((self.app.winfo_width(), self.minimum_height))
        else:
            self.app.minsize(1, self.minimum_height)

    def _on_configure(self, event: tk.Event) -> None:
        if event.widget is not self.app or not self.app._compact_mode:
            return
        size = event.width, event.height
        if size == self._last_size:
            return
        self._last_size = size
        self.cancel_save()
        self._save_id = self.app.after(WINDOW_SIZE_SAVE_DELAY_MS, self._save_size)

    def _save_size(self) -> None:
        self._save_id = None
        app = self.app
        try:
            if not app._compact_mode or app.wm_state() != "normal":
                return
            size = app.winfo_width(), app.winfo_height()
        except tk.TclError:
            return  # 破棄後の予約は何もしない。
        if size == self._auto_size:
            return
        self._auto_size = None
        if size != parse_compact_window_size(app._startup_settings.get(COMPACT_WINDOW_SIZE_KEY)):
            app.startup_io.write_startup({COMPACT_WINDOW_SIZE_KEY: {"width": size[0], "height": size[1]}})

    def cancel_save(self) -> None:
        if self._save_id is not None:
            self.app.after_cancel(self._save_id)
            self._save_id = None

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self.app:
            self.cancel_save()
