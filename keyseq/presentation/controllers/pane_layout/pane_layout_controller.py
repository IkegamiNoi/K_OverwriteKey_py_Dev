from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from keyseq.presentation.pane_width_rules import (
    PANE_WIDTHS_KEY, SASH_WIDTH, LayoutPlan, MinWidths, PaneWidths, clamp,
    WINDOW_WIDTH_KEY, default_basis_main_width, default_pane_widths,
    drag_limits, parse_saved_pane_widths,
    resolve_layout, startup_window_width_to_save,
    update_desired_after_drag,
    window_min_width_after_drag,
)

from .pane_measure import measure_header_window_width, measure_min_widths, measure_window_min_height

if TYPE_CHECKING:
    from keyseq.presentation.app import App

WINDOW_WIDTH_SAVE_DELAY_MS = 500


class _Drag:
    """サッシュ上で始まったドラッグの開始時の状態。"""

    def __init__(self, sash: int, offset: int, width_before: int) -> None:
        self.sash = sash
        self.offset = offset
        self.width_before = width_before


class PaneLayoutController:
    """フル表示の幅配分・境界線ドラッグ・ウィンドウ最小幅を扱う（暫定仕様16）。"""

    def __init__(self, app: App) -> None:
        self.app = app
        self._installed = False
        self._applied = False
        self.desired: PaneWidths | None = None
        self.min_widths: MinWidths | None = None
        self.header_window_width: int = 0
        self.window_min_height: int = 1
        self._remeasure_pending = False
        self._drag: _Drag | None = None
        self._motion_id: str | None = None
        self._motion_x = 0
        self._auto_window_width: int | None = None
        self._last_window_width: int | None = None
        self._width_save_id: str | None = None

    def install(self) -> None:
        if self._installed:
            return
        panes = self.app.full_view.panes
        self.app.bind("<Configure>", self._on_window_configure, add="+")
        self.app.bind("<Destroy>", self._on_window_destroy, add="+")
        panes.bind("<Configure>", self._on_configure, add="+")
        panes.bind("<Button-1>", self._on_press, add="+")
        panes.bind("<B1-Motion>", self._on_motion, add="+")
        panes.bind("<ButtonRelease-1>", self._on_release, add="+")
        for sequence in ("<Button-2>", "<B2-Motion>", "<ButtonRelease-2>"):
            panes.bind(sequence, self._block_middle_button, add="+")
        self._installed = True

    def _is_ready(self) -> bool:
        return self.desired is not None and self.min_widths is not None

    def _on_configure(self, event: tk.Event) -> None:
        if event.width > 1 and not self._applied:
            # 測定中の update_idletasks による Configure の再入も防ぐ。
            self._applied = True
            self.apply_initial_widths()

    def measure_min_widths(self) -> MinWidths:
        return measure_min_widths(self.app)

    def _measure(self) -> None:
        """最小幅とヘッダ幅を同じ契機で測る（暫定仕様16 §3-4 / 暫定仕様17 §3-1）。"""
        self.min_widths = self.measure_min_widths()
        self.header_window_width = measure_header_window_width(self.app)

    def apply_initial_widths(self) -> None:
        view = self.app.full_view
        self._measure()
        startup = getattr(self.app, "_startup_settings", None)
        saved = parse_saved_pane_widths(startup.get(PANE_WIDTHS_KEY)) if isinstance(startup, dict) else None
        self.desired = saved if saved is not None else default_pane_widths(
            main_width=default_basis_main_width(view.panes.winfo_width(), self.app.winfo_width()),
            keymap_req=view.keymap_box.winfo_reqwidth(),
            trigger_req=view.trigger_box.winfo_reqwidth(), sash_total=2 * SASH_WIDTH,
            mins=self.min_widths,
        )
        self.apply_layout()
        self.app.update_idletasks()
        self._auto_window_width = self.app.winfo_width()
        startup = getattr(self.app, "_startup_settings", None)
        if isinstance(startup, dict):
            width = startup_window_width_to_save(startup.get(WINDOW_WIDTH_KEY), self.app.winfo_width())
            if width is not None:
                self.app.startup_io.write_startup({WINDOW_WIDTH_KEY: width})

    def apply_layout(self) -> None:
        """最終値を 1 回だけ計算して一括適用する（暫定仕様16 §3-7）。"""
        if not self._is_ready():
            return
        app, view = self.app, self.app.full_view
        panes, mins = view.panes, self.min_widths
        app.update_idletasks()
        plan = self._plan()
        geometry_changed = plan.window_width != app.winfo_width()
        app.minsize(plan.window_min_width, self.window_min_height)
        if geometry_changed:
            app.geometry(f"{plan.window_width}x{max(app.winfo_height(), self.window_min_height)}")
        app.update_idletasks()
        if geometry_changed:
            self._auto_window_width = app.winfo_width()
        panes.paneconfigure(view.keymap_box, minsize=mins.keymap, width=plan.keymap)
        panes.paneconfigure(view.trigger_box, minsize=mins.trigger)
        panes.paneconfigure(view.sequence_box, minsize=mins.sequence, width=plan.sequence)
        self.window_min_height = measure_window_min_height(app)
        if app.wm_state() == "normal" and app.winfo_height() < self.window_min_height:
            app.geometry(f"{app.winfo_width()}x{self.window_min_height}")
        app.minsize(plan.window_min_width, self.window_min_height)

    def on_font_changed(self) -> None:
        """最小幅を再計算する。省略表示中は再計算の印だけ立てる（暫定仕様16 §3-4）。"""
        if not self._is_ready():
            return
        if self.app._compact_mode:
            self._remeasure_pending = True
            return
        self._measure()
        self.apply_layout()

    def release_window_min_size(self) -> None:
        self.app.minsize(1, 1)

    def on_full_view_shown(self) -> None:
        if not self._is_ready():
            return
        if self._remeasure_pending:
            self._measure()
            self._remeasure_pending = False
        self.apply_layout()

    def _sash_at(self, x: int, y: int) -> int | None:
        # identify の戻り値は Tk により文字列 / タプルで揺れるため、ここだけで正規化する。
        panes = self.app.full_view.panes
        parts = panes.tk.splitlist(panes.identify(x, y))
        if len(parts) == 2 and str(parts[1]) == "sash":
            return int(parts[0])
        return None

    def _side_box(self, sash: int) -> tk.Widget:
        view = self.app.full_view
        return view.keymap_box if sash == 0 else view.sequence_box

    def _on_press(self, event: tk.Event) -> str | None:
        self._cancel_motion()
        self._drag = None
        if not self._is_ready():
            return None
        sash = self._sash_at(event.x, event.y)
        if sash is None:
            return None
        sash_x = self.app.full_view.panes.sash_coord(sash)[0]
        self._drag = _Drag(sash, event.x - sash_x, self._side_box(sash).winfo_width())
        return "break"

    def _on_motion(self, event: tk.Event) -> str | None:
        if self._drag is None or not self._is_ready():
            return None
        self._motion_x = event.x
        if self._motion_id is None:
            self._motion_id = self.app.after_idle(self._apply_motion)
        return "break"

    def _cancel_motion(self) -> None:
        if self._motion_id is not None:
            self.app.after_cancel(self._motion_id)
            self._motion_id = None

    def _apply_motion(self) -> None:
        self._motion_id = None
        drag = self._drag
        if drag is None or not self._is_ready():
            return
        view, mins = self.app.full_view, self.min_widths
        panes = view.panes
        sash_x = self._motion_x - drag.offset
        if drag.sash == 0:
            own, own_min, other = sash_x, mins.keymap, view.sequence_box
        else:
            own = panes.winfo_width() - (sash_x + SASH_WIDTH)
            own_min, other = mins.sequence, view.keymap_box
        low, high = drag_limits(
            total_width=panes.winfo_width(), own_min=own_min,
            other_side_width=other.winfo_width(), trigger_min=mins.trigger,
            sash_total=2 * SASH_WIDTH,
        )
        panes.paneconfigure(self._side_box(drag.sash), width=clamp(own, low, high))

    def _on_release(self, _event: tk.Event) -> str | None:
        if self._motion_id is not None:
            self._cancel_motion()
            self._apply_motion()
        drag, self._drag = self._drag, None
        if drag is None or not self._is_ready():
            return None
        box = self._side_box(drag.sash)
        box.update_idletasks()
        side = "keymap" if drag.sash == 0 else "sequence"
        new = update_desired_after_drag(self.desired, side, drag.width_before, box.winfo_width())
        if new != self.desired:
            self._on_desired_changed(new)
        return "break"

    def _on_desired_changed(self, new: PaneWidths) -> None:
        self.desired = new
        self._update_window_min_size()
        self.app.startup_io.write_startup({
            PANE_WIDTHS_KEY: {"keymap": new.keymap, "sequence": new.sequence},
        })

    def _on_window_configure(self, event: tk.Event) -> None:
        if event.widget is not self.app or event.width == self._last_window_width:
            return
        self._last_window_width = event.width
        self.cancel_window_width_save()
        self._width_save_id = self.app.after(WINDOW_WIDTH_SAVE_DELAY_MS, self._save_window_width)

    def _save_window_width(self) -> None:
        """予約実行時の状態で幅を保存する（暫定仕様16 §3-8）。"""
        self._width_save_id = None
        app = self.app
        try:
            if not self._is_ready() or app.wm_state() != "normal" or app._compact_mode:
                return
            width = app.winfo_width()
        except tk.TclError:
            return  # App 破棄後に実行された予約は何もしない。
        if width == self._auto_window_width:
            return
        self._auto_window_width = None
        if app._startup_settings.get(WINDOW_WIDTH_KEY) != width:
            app.startup_io.write_startup({WINDOW_WIDTH_KEY: width})

    def _on_window_destroy(self, event: tk.Event) -> None:
        # on_close 以外で破棄されても、破棄後に予約を実行させない。
        if event.widget is self.app:
            self.cancel_window_width_save()

    def cancel_window_width_save(self) -> None:
        if self._width_save_id is not None:
            self.app.after_cancel(self._width_save_id)
            self._width_save_id = None

    def _plan(self, widths: PaneWidths | None = None) -> LayoutPlan:
        app = self.app
        return resolve_layout(
            self.desired if widths is None else widths, self.min_widths, sash_total=2 * SASH_WIDTH,
            window_extra=app.winfo_width() - app.full_view.panes.winfo_width(),
            current_window_width=app.winfo_width(), screen_width=app.winfo_screenwidth(),
            header_window_width=self.header_window_width,
        )

    def _update_window_min_size(self) -> None:
        # ドラッグ直後に幅を動かさないよう、最小幅だけを当てる。
        view = self.app.full_view
        displayed = PaneWidths(view.keymap_box.winfo_width(), view.sequence_box.winfo_width())
        window_extra = self.app.winfo_width() - view.panes.winfo_width()
        self.app.minsize(window_min_width_after_drag(
            displayed, self.min_widths, 2 * SASH_WIDTH, window_extra, self.header_window_width,
        ), self.window_min_height)

    def _block_middle_button(self, _event: tk.Event) -> str:
        return "break"
