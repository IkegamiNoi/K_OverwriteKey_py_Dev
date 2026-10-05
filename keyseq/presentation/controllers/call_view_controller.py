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
        self._open_by_trigger: dict[tuple[str, str], bool] = {}
        self._manually_operated: set[tuple[str, str]] = set()
        self._drag_height: int | None = None
        self._layout_id: str | None = None

    @property
    def box(self):
        return self.app.full_view.sequence_box

    @property
    def _identity(self) -> tuple[str, str] | None:
        key = self.app.trigger_panel.selected_trigger_key()
        if not key:
            return None
        return self.app._active_trigger_set_id(), key

    @property
    def is_open(self) -> bool:
        body = self.box.call_view_frame.body
        return str(body) in {str(pane) for pane in self.box.action_panes.panes()}

    def install(self) -> None:
        self.on_font_changed()
        panes = self.box.action_panes
        panes.bind("<Configure>", self._on_configure, add="+")
        panes.bind("<Button-1>", self._on_press, add="+")
        panes.bind("<ButtonRelease-1>", self._on_release, add="+")
        for event in ("<Button-2>", "<B2-Motion>", "<ButtonRelease-2>"):
            panes.bind(event, lambda _event: "break", add="+")

    def on_font_changed(self) -> None:
        self.box.action_frame.update_idletasks()
        self.box.call_view_frame.heading.update_idletasks()
        # 下の枠は要求寸法に加算しない。
        pane_height = max(
            list_minimum_height(self.box.action_list),
            self.box.action_frame.winfo_reqheight()
            - self.box.call_view_frame.heading.winfo_reqheight(),
        )
        self.box.action_panes.configure(
            width=self.box.action_frame.winfo_reqwidth(),
            height=pane_height,
        )
        self._set_minimums()
        self._schedule_layout()

    def _set_minimums(self) -> None:
        panes = self.box.action_panes
        panes.paneconfigure(self.box.action_frame, minsize=list_minimum_height(self.box.action_list))
        if self.is_open:
            panes.paneconfigure(
                self.box.call_view_frame.body,
                minsize=(
                    self.box.call_view_frame.heading.winfo_reqheight()
                    + self.box.call_view_frame.minimum_body_height()
                ),
            )

    def _ensure_desired(self) -> None:
        # 既定は開いたときの一覧と枠の合計から決める（閉じている間は見出しが PanedWindow の外）
        total = self.box.action_panes.winfo_height()
        if not self.is_open:
            total += self.box.call_view_frame.heading.winfo_reqheight()
        self.desired.setdefault("full", default_call_view_height(total))
        compact = self.app.compact_view.trigger_box.trigger_list
        self.desired.setdefault("compact", default_call_view_height(compact.winfo_reqheight()))

    def on_summary(self, summary: CallViewSummary | None) -> None:
        """runner が UI スレッドから通知する。実行状態は変更しない。"""
        self.last_summary = summary
        identity = self._identity
        if (
            summary is not None and identity is not None
            and summary.path and summary.path[0] == identity[1]
            and identity not in self._manually_operated
        ):
            self._open_by_trigger[identity] = True
        self._render()

    def on_selection_changed(self) -> None:
        """選択中トリガーに対応する開閉状態と表示内容へ切り替える。"""
        self._render()

    def on_heading_click(self) -> None:
        identity = self._identity
        if identity is None:
            return
        self._manually_operated.add(identity)
        self._open_by_trigger[identity] = not self._open_by_trigger.get(identity, False)
        self._render()

    def _render(self) -> None:
        identity = self._identity
        is_open = bool(identity and self._open_by_trigger.get(identity, False))
        frame = self.box.call_view_frame
        summary = self.last_summary
        visible_summary = (
            summary if is_open and identity is not None and identity[1] in summary.path else None
        ) if summary is not None else None
        frame.set_heading(is_open, visible_summary.path if visible_summary is not None else ())
        if not is_open:
            if self.is_open:
                self.box.action_panes.forget(frame.body)
            frame.show_heading_below_list(self.box.action_column)
            self._drag_height = None
            return

        self._ensure_desired()
        panes = self.box.action_panes
        if not self.is_open:
            panes.add(
                frame.body, stretch="never", padx=0, pady=0,
                minsize=(
                    frame.heading.winfo_reqheight() + frame.minimum_body_height()
                ),
            )
            frame.show_heading_in_body()
            self._schedule_layout()
        if visible_summary is None:
            frame.set_empty_state()
            return
        rows = build_action_rows(
            visible_summary.actions,
            loop_iterations={loop.start: loop.iteration for loop in visible_summary.loop_frames},
            counters=visible_summary.counters,
            resolve_call=self.app.trigger_panel._resolve_call_target,
        )
        frame.action_list.delete(0, tk.END)
        for index, (text, background) in enumerate(rows):
            prefix = "▶ " if index == visible_summary.position else "　 "
            frame.action_list.insert(tk.END, prefix + text)
            if background is not None:
                frame.action_list.itemconfigure(index, background=background)
        if 0 <= visible_summary.position < len(rows):
            frame.action_list.see(visible_summary.position)

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
        panes.update_idletasks()
        height = displayed_call_view_height(
            self.desired["full"],
            self.box.call_view_frame.heading.winfo_reqheight()
            + self.box.call_view_frame.minimum_body_height(),
            panes.winfo_height(), list_minimum_height(self.box.action_list),
            int(panes.cget("sashwidth")),
        )
        panes.sash_place(0, 0, panes.winfo_height() - height - int(panes.cget("sashwidth")))

    def _on_press(self, event) -> None:
        if self.is_open and self.box.action_panes.identify(event.x, event.y):
            self._drag_height = self.box.call_view_frame.body.winfo_height()

    def _on_release(self, _event) -> None:
        before = self._drag_height
        if before is None or not self.is_open:
            self._drag_height = None
            return
        self.box.action_panes.update_idletasks()
        height = self.box.call_view_frame.body.winfo_height()
        self._drag_height = None
        if height != before and height != self.desired["full"]:
            self.desired["full"] = height
            self.app.startup_io.write_startup({CALL_VIEW_HEIGHTS_KEY: dict(self.desired)})
