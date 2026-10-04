"""呼び出し先の描画・上下境界線・希望の高さの保存。"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from keyseq.application.call_view import CallViewSummary
from keyseq.presentation.call_view_heights import (
    CALL_VIEW_HEIGHTS_KEY, default_call_view_height,
    displayed_call_view_height, parse_call_view_heights,
)
from keyseq.presentation.controllers.action_list_rendering import build_action_rows
from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class CallViewController:
    def __init__(self, app: App):
        self.app = app
        startup = getattr(app, "_startup_settings", {})
        self.desired = parse_call_view_heights(
            startup.get(CALL_VIEW_HEIGHTS_KEY) if isinstance(startup, dict) else None,
        )
        self.last_summary: CallViewSummary | None = None
        self._drag_height: int | None = None
        self._layout_id: str | None = None

    @property
    def box(self):
        return self.app.full_view.sequence_box

    @property
    def is_open(self) -> bool:
        # panes() は Tcl_Obj を返すことがあるため文字列に揃えて比べる
        return str(self.box.call_view_frame) in {str(pane) for pane in self.box.action_panes.panes()}

    def install(self) -> None:
        self.on_font_changed()
        panes = self.box.action_panes
        panes.bind("<Configure>", self._on_configure, add="+")
        panes.bind("<Button-1>", self._on_press, add="+")
        panes.bind("<ButtonRelease-1>", self._on_release, add="+")
        for event in ("<Button-2>", "<B2-Motion>", "<ButtonRelease-2>"):
            panes.bind(event, lambda _event: "break", add="+")

    def on_font_changed(self) -> None:
        # 要求寸法は従来の 9 行の一覧だけで固定し、下の枠は加算しない。
        self.box.action_frame.update_idletasks()
        self.box.action_panes.configure(
            width=self.box.action_frame.winfo_reqwidth(),
            height=self.box.action_frame.winfo_reqheight(),
        )
        self._set_minimums()
        self._schedule_layout()

    def _set_minimums(self) -> None:
        panes = self.box.action_panes
        panes.paneconfigure(self.box.action_frame, minsize=list_minimum_height(self.box.action_list))
        if self.is_open:
            panes.paneconfigure(self.box.call_view_frame, minsize=self.box.call_view_frame.minimum_height())

    def _ensure_desired(self) -> None:
        self.desired.setdefault("full", default_call_view_height(self.box.action_panes.winfo_height()))
        compact = self.app.compact_view.trigger_box.trigger_list
        self.desired.setdefault("compact", default_call_view_height(compact.winfo_reqheight()))

    def on_summary(self, summary: CallViewSummary | None) -> None:
        """runner が UI スレッドから通知する。実行状態は変更しない。"""
        self.last_summary = summary
        if summary is None:
            if self.is_open:
                self.box.action_panes.forget(self.box.call_view_frame)
            self._drag_height = None
            return
        self._ensure_desired()
        if not self.is_open:
            self.box.action_panes.add(
                self.box.call_view_frame, stretch="never", padx=0, pady=0,
                minsize=self.box.call_view_frame.minimum_height(),
            )
            self._schedule_layout()
        frame = self.box.call_view_frame
        frame.heading.configure(text=" › ".join(summary.path))
        rows = build_action_rows(
            summary.actions,
            loop_iterations={loop.start: loop.iteration for loop in summary.loop_frames},
            counters=summary.counters,
            resolve_call=self.app.trigger_panel._resolve_call_target,
        )
        frame.action_list.delete(0, tk.END)
        for index, (text, background) in enumerate(rows):
            prefix = "▶ " if index == summary.position else "　 "
            frame.action_list.insert(tk.END, prefix + text)
            if background is not None:
                frame.action_list.itemconfigure(index, background=background)
        if 0 <= summary.position < len(rows):
            frame.action_list.see(summary.position)

    def _on_configure(self, event) -> None:
        if event.height > 1:
            self._ensure_desired()
            self._schedule_layout()

    def _schedule_layout(self) -> None:
        if self._layout_id is None and self.is_open:
            self._layout_id = self.app.after_idle(self._apply_height)

    def _apply_height(self) -> None:
        self._layout_id = None
        if not self.is_open or self._drag_height is not None:
            return
        self._set_minimums()
        panes = self.box.action_panes
        # paneconfigure の再配置を先に済ませる（後から走ると sash_place の位置を要求の高さへ戻す）
        panes.update_idletasks()
        height = displayed_call_view_height(
            self.desired["full"], self.box.call_view_frame.minimum_height(),
            panes.winfo_height(), list_minimum_height(self.box.action_list),
            int(panes.cget("sashwidth")),
        )
        panes.sash_place(0, 0, panes.winfo_height() - height - int(panes.cget("sashwidth")))

    def _on_press(self, event) -> None:
        if self.is_open and self.box.action_panes.identify(event.x, event.y):
            self._drag_height = self.box.call_view_frame.winfo_height()

    def _on_release(self, _event) -> None:
        before = self._drag_height
        if before is None or not self.is_open:
            self._drag_height = None
            return
        self.box.action_panes.update_idletasks()
        height = self.box.call_view_frame.winfo_height()
        self._drag_height = None
        if height != before and height != self.desired["full"]:
            self.desired["full"] = height
            self.app.startup_io.write_startup({CALL_VIEW_HEIGHTS_KEY: dict(self.desired)})
