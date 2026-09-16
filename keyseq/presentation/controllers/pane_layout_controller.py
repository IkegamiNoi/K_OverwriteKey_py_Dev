from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import TYPE_CHECKING

from keyseq.presentation.pane_width_rules import (
    MIN_LIST_CHARS, PANE_WIDTHS_KEY, SASH_WIDTH, LayoutPlan, MinWidths, PaneWidths, clamp,
    default_pane_widths, drag_limits, list_row_width, parse_saved_pane_widths,
    resolve_layout, side_by_side_min_width,
    stacked_min_width, update_desired_after_drag,
)

if TYPE_CHECKING:
    from keyseq.presentation.app import App


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
        self._remeasure_pending = False
        self._drag: _Drag | None = None

    def install(self) -> None:
        if self._installed:
            return
        panes = self.app.full_view.panes
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
        view = self.app.full_view
        view.update_idletasks()
        sequence = view.sequence_box
        buttons = sequence.run_to_end_chk.master
        chrome, title = self._frame_widths(sequence)
        gap_parts = sequence.tk.splitlist(buttons.pack_info()["padx"])
        gap = sum(sequence.winfo_pixels(str(part)) for part in gap_parts)
        if len(gap_parts) == 1:
            gap *= 2
        return MinWidths(
            keymap=self._stacked_width(view.keymap_box, view.keymap_box.keymap_listbox),
            trigger=self._stacked_width(view.trigger_box, view.trigger_box.trigger_list),
            sequence=side_by_side_min_width(
                self._list_row(sequence.action_list), buttons.winfo_reqwidth(),
                gap, chrome, title,
            ),
        )

    def _stacked_width(self, box: ttk.LabelFrame, listing: tk.Listbox) -> int:
        chrome, title = self._frame_widths(box)
        others = [
            child.winfo_reqwidth() for child in box.winfo_children()
            if child is not listing.master
        ]
        return stacked_min_width(self._list_row(listing), others, chrome, title)

    def _list_row(self, listing: tk.Listbox) -> int:
        font = tkfont.Font(root=self.app, font=listing.cget("font"))
        char_width = font.measure("0")
        chrome = listing.winfo_reqwidth() - char_width * int(listing.cget("width"))
        scrollbar = next(
            child for child in listing.master.winfo_children()
            if isinstance(child, ttk.Scrollbar)
        )
        return list_row_width(char_width, MIN_LIST_CHARS, chrome, scrollbar.winfo_reqwidth())

    def _frame_widths(self, box: ttk.LabelFrame) -> tuple[int, int]:
        # 未配置の同一テーマの枠で、native theme の枠線も含めて測る。
        probe = ttk.LabelFrame(
            self.app, padding=box.cget("padding"), style=box.cget("style"),
        )
        try:
            # 空見出しの領域が要求幅を決めないよう、中身を十分広くして枠の分を測る。
            content = ttk.Frame(probe, width=500, height=1)
            content.pack()
            probe.update_idletasks()
            chrome = probe.winfo_reqwidth() - 500
            font = tkfont.nametofont("TkDefaultFont", root=self.app)
            sample = "0" * 100  # 内側余白より見出しが必ず広い状態で測定。
            content.configure(width=1)
            probe.configure(text=sample)
            probe.update_idletasks()
            # タイトル要求幅に既に含まれる枠の分は二重加算しない。
            inset = max(0, probe.winfo_reqwidth() - font.measure(sample) - chrome)
            title = font.measure(str(box.cget("text"))) + chrome + inset
            return chrome, title
        finally:
            probe.destroy()

    def apply_initial_widths(self) -> None:
        view = self.app.full_view
        self.min_widths = self.measure_min_widths()
        startup = getattr(self.app, "_startup_settings", None)
        saved = parse_saved_pane_widths(startup.get(PANE_WIDTHS_KEY)) if isinstance(startup, dict) else None
        self.desired = saved if saved is not None else default_pane_widths(
            main_width=view.panes.winfo_width(), keymap_req=view.keymap_box.winfo_reqwidth(),
            trigger_req=view.trigger_box.winfo_reqwidth(), sash_total=2 * SASH_WIDTH,
            mins=self.min_widths,
        )
        self.apply_layout()

    def apply_layout(self) -> None:
        """最終値を 1 回だけ計算して一括適用する（暫定仕様16 §3-7）。"""
        if not self._is_ready():
            return
        app, view = self.app, self.app.full_view
        panes, mins = view.panes, self.min_widths
        app.update_idletasks()
        plan = self._plan()
        app.minsize(plan.window_min_width, 1)
        if plan.window_width != app.winfo_width():
            app.geometry(f"{plan.window_width}x{app.winfo_height()}")
        app.update_idletasks()
        panes.paneconfigure(view.keymap_box, minsize=mins.keymap, width=plan.keymap)
        panes.paneconfigure(view.trigger_box, minsize=mins.trigger)
        panes.paneconfigure(view.sequence_box, minsize=mins.sequence, width=plan.sequence)

    def on_font_changed(self) -> None:
        """最小幅を再計算する。省略表示中は再計算の印だけ立てる（暫定仕様16 §3-4）。"""
        if not self._is_ready():
            return
        if self.app._compact_mode:
            self._remeasure_pending = True
            return
        self.min_widths = self.measure_min_widths()
        self.apply_layout()

    def release_window_min_size(self) -> None:
        self.app.minsize(1, 1)

    def on_full_view_shown(self) -> None:
        if not self._is_ready():
            return
        if self._remeasure_pending:
            self.min_widths = self.measure_min_widths()
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
        drag = self._drag
        if drag is None or not self._is_ready():
            return None
        view, mins = self.app.full_view, self.min_widths
        panes = view.panes
        sash_x = event.x - drag.offset
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
        return "break"

    def _on_release(self, _event: tk.Event) -> str | None:
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

    def _plan(self, widths: PaneWidths | None = None) -> LayoutPlan:
        app = self.app
        return resolve_layout(
            self.desired if widths is None else widths, self.min_widths, sash_total=2 * SASH_WIDTH,
            window_extra=app.winfo_width() - app.full_view.panes.winfo_width(),
            current_window_width=app.winfo_width(), screen_width=app.winfo_screenwidth(),
        )

    def _update_window_min_size(self) -> None:
        # ドラッグ直後に幅を動かさないよう、最小幅だけを当てる。
        view = self.app.full_view
        displayed = PaneWidths(view.keymap_box.winfo_width(), view.sequence_box.winfo_width())
        self.app.minsize(self._plan(displayed).window_min_width, 1)

    def _block_middle_button(self, _event: tk.Event) -> str:
        return "break"
