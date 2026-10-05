"""呼び出し先の描画・上下境界線・希望の高さの保存。"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import TYPE_CHECKING

from keyseq.presentation.call_view_heights import (
    CALL_VIEW_HEIGHTS_KEY, default_call_view_height,
    displayed_call_view_height, parse_call_view_heights,
)
from keyseq.presentation.controllers.action_list_rendering import build_action_rows
from keyseq.presentation.views.full_view.call_view_frame import CallViewFrame, list_minimum_height

if TYPE_CHECKING:
    from keyseq.application.call_view import CallViewSummary
    from keyseq.presentation.app import App


@dataclass
class _CallViewHost:
    key: str
    panes: tk.PanedWindow
    top_frame: tk.Widget
    listing: tk.Listbox
    frame: CallViewFrame
    column: tk.Widget
    drag_height: int | None = None
    layout_id: str | None = None

    @property
    def is_open(self) -> bool:
        return str(self.frame.body) in {str(pane) for pane in self.panes.panes()}

    def minimum_height(self) -> int:
        return self.frame.heading.winfo_reqheight() + self.frame.minimum_body_height()


class CallViewController:
    def __init__(self, app: App):
        self.app = app
        startup = getattr(app, "_startup_settings", {})
        self.desired = parse_call_view_heights(
            startup.get(CALL_VIEW_HEIGHTS_KEY) if isinstance(startup, dict) else None,
        )
        self._open_by_trigger: dict[tuple[str, str], bool] = {}
        self._manually_operated: set[tuple[str, str]] = set()
        self.hosts: dict[str, _CallViewHost] = {}

    @property
    def _identity(self) -> tuple[str, str] | None:
        key = self.app.trigger_panel.selected_trigger_key()
        if not key:
            return None
        return self.app._active_trigger_set_id(), key

    @property
    def is_open(self) -> bool:
        return self.hosts["full"].is_open

    def install(self) -> None:
        full = self.app.full_view.sequence_box
        compact = self.app.compact_view.trigger_box
        self.hosts = {
            "full": _CallViewHost(
                "full", full.action_panes, full.action_frame, full.action_list,
                full.call_view_frame, full.action_column,
            ),
            "compact": _CallViewHost(
                "compact", compact.trigger_panes, compact.trigger_frame, compact.trigger_list,
                compact.call_view_frame, compact.call_view_column,
            ),
        }
        self.on_font_changed()
        for host in self.hosts.values():
            for event, callback in (
                ("<Configure>", self._on_configure), ("<Button-1>", self._on_press),
                ("<ButtonRelease-1>", self._on_release),
            ):
                host.panes.bind(event, lambda event, h=host, cb=callback: cb(h, event), add="+")
            for event in ("<Button-2>", "<B2-Motion>", "<ButtonRelease-2>"):
                host.panes.bind(event, lambda _event: "break", add="+")

    def on_font_changed(self) -> None:
        for host in self.hosts.values():
            host.top_frame.update_idletasks()
            host.frame.heading.update_idletasks()
            # 下の枠は要求寸法に加算しない。
            pane_height = max(
                list_minimum_height(host.listing),
                host.top_frame.winfo_reqheight() - host.frame.heading.winfo_reqheight(),
            )
            host.panes.configure(width=host.top_frame.winfo_reqwidth(), height=pane_height)
            self._set_minimums(host)
            self._schedule_layout(host)

    def _set_minimums(self, host: _CallViewHost) -> None:
        host.panes.paneconfigure(host.top_frame, minsize=list_minimum_height(host.listing))
        if host.is_open:
            host.panes.paneconfigure(host.frame.body, minsize=host.minimum_height())

    def _ensure_desired(self, host: _CallViewHost) -> None:
        # 非表示側の既定は、表示されて実寸が入るまで決めない。
        total = host.panes.winfo_height()
        if total <= 1 or not host.panes.winfo_ismapped():
            return
        if not host.is_open:
            total += host.frame.heading.winfo_reqheight()
        self.desired.setdefault(host.key, default_call_view_height(total))

    def on_changed(self) -> None:
        """runner が UI スレッドから通知する。実行状態は変更しない。"""
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
        summary = self.app.sequence_runner.call_view_summary_for(identity[1]) if identity else None
        if summary is not None and identity not in self._manually_operated:
            self._open_by_trigger[identity] = True
        is_open = bool(identity and self._open_by_trigger.get(identity, False))
        for host in self.hosts.values():
            self._render_host(host, is_open, summary)

    def _render_host(
        self, host: _CallViewHost, is_open: bool, summary: CallViewSummary | None,
    ) -> None:
        frame = host.frame
        frame.set_heading(is_open, summary.path if is_open and summary is not None else ())
        if not is_open:
            if host.is_open:
                host.panes.forget(frame.body)
            frame.show_heading_below_list(host.column)
            host.drag_height = None
            return
        # 省略表示は幅変更・ヘッダの折り返しが済んだ _apply_height で既定を決める。
        if host.key == "full":
            self._ensure_desired(host)
        if not host.is_open:
            host.panes.add(
                frame.body, stretch="never", padx=0, pady=0, minsize=host.minimum_height(),
            )
            frame.show_heading_in_body()
        self._schedule_layout(host)
        if summary is None:
            frame.set_empty_state()
        else:
            self._render_rows(frame, summary)

    def _render_rows(self, frame: CallViewFrame, summary: CallViewSummary) -> None:
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

    def _on_configure(self, host: _CallViewHost, event) -> None:
        if event.height > 1:
            self._schedule_layout(host)

    def _schedule_layout(self, host: _CallViewHost) -> None:
        if host.layout_id is None and host.is_open and host.panes.winfo_ismapped():
            host.layout_id = self.app.after_idle(lambda: self._apply_height(host))

    def _apply_height(self, host: _CallViewHost) -> None:
        host.layout_id = None
        if not host.is_open or host.drag_height is not None or not host.panes.winfo_ismapped():
            return
        self._set_minimums(host)
        panes = host.panes
        panes.update_idletasks()
        self._ensure_desired(host)
        if panes.winfo_height() <= 1 or host.key not in self.desired:
            return
        height = displayed_call_view_height(
            self.desired[host.key], host.minimum_height(), panes.winfo_height(),
            list_minimum_height(host.listing), int(panes.cget("sashwidth")),
        )
        panes.sash_place(0, 0, panes.winfo_height() - height - int(panes.cget("sashwidth")))

    def _on_press(self, host: _CallViewHost, event) -> None:
        if host.is_open and host.panes.identify(event.x, event.y):
            host.drag_height = host.frame.body.winfo_height()

    def _on_release(self, host: _CallViewHost, _event) -> None:
        before = host.drag_height
        if before is None or not host.is_open:
            host.drag_height = None
            return
        host.panes.update_idletasks()
        height = host.frame.body.winfo_height()
        host.drag_height = None
        if height != before and height != self.desired.get(host.key):
            self.desired[host.key] = height
            self.app.startup_io.write_startup({CALL_VIEW_HEIGHTS_KEY: dict(self.desired)})
