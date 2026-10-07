"""省略表示のシーケンス描画と次に実行の操作。"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from keyseq.presentation.compact_pane_heights import (
    COMPACT_SEQUENCE_VIEW_KEY, parse_compact_sequence_view,
)

if TYPE_CHECKING:
    from keyseq.presentation.app import App
    from keyseq.presentation.views.compact_view.sequence_frame import CompactSequenceFrame


class CompactSequenceController:
    def __init__(self, app: App):
        self.app = app
        self.frame: CompactSequenceFrame | None = None
        self.is_open, self.desired_height = parse_compact_sequence_view(
            app._startup_settings.get(COMPACT_SEQUENCE_VIEW_KEY),
        )
        self._rendering = False
        self._generation = 0
        self._next_index: int | None = None
        self._pressed: tuple[int, str, str | None, int] | None = None

    def register_frame(self, frame: CompactSequenceFrame) -> None:
        self.frame = frame
        frame.set_heading(self.is_open)
        if self.is_open:
            frame.body.master.add(frame.body, stretch="never", padx=0, pady=0)
            frame.show_heading_in_body()

    def render(self, rows: list[tuple[str, str | None]], next_index: int | None) -> None:
        self._generation += 1
        self._next_index = (
            next_index if next_index is not None and 0 <= next_index < len(rows) else None
        )
        if self.frame is None:
            return
        listing = self.frame.action_list
        self._rendering = True
        try:
            listing.delete(0, tk.END)
            for index, (text, background) in enumerate(rows):
                listing.insert(tk.END, ("▶ " if index == self._next_index else "　 ") + text)
                if background is not None:
                    listing.itemconfigure(index, background=background)
            if self._next_index is not None:
                listing.selection_set(self._next_index)
                listing.selection_anchor(self._next_index)
                listing.activate(self._next_index)
                listing.see(self._next_index)
        finally:
            self._rendering = False

    def on_heading_click(self) -> None:
        frame = self.frame
        if frame is None:
            return
        box = self.app.compact_view.trigger_box
        self.is_open = not self.is_open
        frame.set_heading(self.is_open)
        if self.is_open:
            call_body = box.call_view_frame.body
            options = (
                {"before": call_body}
                if str(call_body) in map(str, box.trigger_panes.panes()) else {}
            )
            box.trigger_panes.add(
                frame.body, stretch="never", padx=0, pady=0,
                **options,
            )
            frame.show_heading_in_body()
            self.app.trigger_panel.refresh_actions()
        else:
            self._pressed = None
            box.trigger_panes.forget(frame.body)
            frame.show_heading_at(box.trigger_frame)
        self.app.compact_pane_layout.schedule_layout()
        self.app.compact_pane_layout.save_sequence()

    def _row_at(self, event) -> int | None:
        listing = self.frame.action_list
        if (
            not 0 <= event.x < listing.winfo_width()
            or not 0 <= event.y < listing.winfo_height()
            or not listing.size()
        ):
            return None
        row = int(listing.nearest(event.y))
        bounds = listing.bbox(row)
        if bounds is None:
            return None
        _x, top, _width, height = bounds
        return row if top <= event.y < top + height else None

    def _identity(self) -> tuple[str, str | None, int]:
        return (
            self.app._active_trigger_set_id(),
            self.app.trigger_panel.selected_trigger_key(), self._generation,
        )

    def on_press(self, event):
        self._pressed = None
        if self.is_open and not self._rendering:
            self.frame.action_list.focus_set()
            row = self._row_at(event)
            if row is not None:
                self._pressed = (row, *self._identity())
        return "break"

    def on_release(self, event):
        pressed, self._pressed = self._pressed, None
        if pressed is not None and self.is_open and not self._rendering:
            row = self._row_at(event)
            if (row, *self._identity()) == pressed:
                self.app.trigger_panel.set_next_action_index(row, refuse_running_callee=True)
        return "break"

    def _visible_rows(self) -> int:
        listing = self.frame.action_list
        first, last = listing.yview()
        return max(1, int(round((last - first) * listing.size())))

    def on_key(self, event):
        if not self.is_open or self._rendering or event.state & 0x0001 or self._next_index is None:
            return "break"
        size = self.frame.action_list.size()
        current = self._next_index
        destinations = {
            "Up": current - 1, "Down": current + 1,
            "Prior": current - self._visible_rows(), "Next": current + self._visible_rows(),
            "Home": 0, "End": size - 1,
        }
        if event.keysym in destinations:
            row = max(0, min(size - 1, destinations[event.keysym]))
            self.app.trigger_panel.set_next_action_index(row, refuse_running_callee=True)
        return "break"

    @staticmethod
    def ignore(_event):
        return "break"
