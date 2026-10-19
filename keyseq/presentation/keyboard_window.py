from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Callable

from keyseq.application.keymap_service import KeymapService
from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.domain.config import normalize_key_name
from keyseq.domain.key_identifiers import is_prohibited_assign_key
from keyseq.domain.make_only_keys import is_make_only_scan_code
from keyseq.domain.numpad_keys import is_numpad_key_name
from keyseq.infrastructure import win32_window
from keyseq.presentation.keyboard_layouts import (
    KeyboardLayout,
    resolve_layout_key_id_from_scan_code,
    resolve_keyboard_layout,
)
from keyseq.presentation.keyboard_window_size import (
    KEYBOARD_WINDOW_MIN_WIDTH,
    KEYBOARD_WINDOW_PADDING,
    RESIZE_SETTLE_MS,
    corrected_size,
    layout_aspect,
    minimum_size,
    size_from_width,
)
from keyseq.presentation.key_capture_ime import begin_key_capture, end_key_capture
from keyseq.presentation.tk_keys import (
    TK_KEYSYM_TO_KEYBOARD_NAME,
    is_unresolved_capture_key,
    numpad_name_from_tk_event,
)

_LOOKUP_KEY_BY_ID = {
    "shift_l": "shift",
    "shift_r": "right shift",
    "ctrl_l": "ctrl",
    "ctrl_r": "right ctrl",
    "alt_l": "alt",
    "alt_r": "right alt",
    "alt_gr": "alt gr",
    "windows_l": "left windows",
    "windows_r": "right windows",
    "grave": "`",
    "caps_lock": "caps lock",
    "page_up": "page up",
    "page_down": "page down",
    "print_screen": "print screen",
    "scroll_lock": "scroll lock",
    "left_bracket": "[",
    "right_bracket": "]",
    "backslash": "\\",
    "semicolon": ";",
    "quote": "'",
}


def keyboard_window_title(layout_name: str, editing_key: str | None) -> str:
    if editing_key:
        return f"Keyboard UI — 編集中: {editing_key}（Escでキャンセル）"
    if layout_name:
        return f"Keyboard UI — {layout_name}"
    return "Keyboard UI"


class KeyboardWindow(tk.Toplevel):
    def __init__(
        self,
        parent,
        *,
        layout: KeyboardLayout | None = None,
        on_close=None,
        on_assign_keymap=None,
        on_clear_keymap=None,
        is_mouse_button_down: Callable[[], bool] | None = None,
    ):
        super().__init__(parent)
        self.title("Keyboard UI")
        self._on_close = on_close
        self._on_assign_keymap = on_assign_keymap
        self._on_clear_keymap = on_clear_keymap
        self._is_mouse_button_down = is_mouse_button_down
        self._layout = layout or resolve_keyboard_layout()
        self._ratio = layout_aspect(self._layout.keys)
        initial_size = (
            minimum_size(self._ratio)
            if self._ratio is not None
            else (KEYBOARD_WINDOW_MIN_WIDTH, 210)
        )
        self._size_base = initial_size
        self._resize_job = None
        self._applied_size: tuple[int, int] | None = None
        self._suspended = False
        self._ratio_pending = False
        try:
            self.geometry(f"{initial_size[0]}x{initial_size[1]}")
        except tk.TclError:
            pass
        try:
            self.minsize(*initial_size)
        except tk.TclError:
            pass
        self._display_map: dict[str, str] = {}
        self._kind_map: dict[str, str] = {}
        self._key_bounds: list[tuple[str, float, float, float, float]] = []
        self._editing_source_key: str | None = None
        self._show_physical_key_labels = False

        container = ttk.Frame(self, padding=KEYBOARD_WINDOW_PADDING)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, background="#f5f7fb", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.bind("<KeyPress>", self._on_key_press, add="+")
        self.bind("<Configure>", self._on_window_configure, add="+")
        self.bind("<Map>", self._on_window_map, add="+")
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._update_title()

    def update_layout(self, layout: KeyboardLayout | None) -> None:
        self._layout = layout or resolve_keyboard_layout()
        ratio = layout_aspect(self._layout.keys)
        if ratio != self._ratio:
            self._ratio = ratio
            try:
                suspended = self.state() in ("zoomed", "iconic")
            except tk.TclError:
                suspended = True
            if suspended:
                self._suspended = True
                self._ratio_pending = True
            elif ratio is not None:
                self._apply_ratio_to_base()
        self._update_title()
        self.redraw()

    def update_from_config(
        self,
        data: dict | None,
        *,
        custom_enabled: bool = True,
        show_physical_key_labels: bool = False,
    ) -> None:
        self._show_physical_key_labels = bool(show_physical_key_labels)
        display_map: dict[str, str] = {}
        kind_map: dict[str, str] = {}

        triggers = []
        if isinstance(data, dict):
            raw_triggers = get_active_triggers(data)
            if isinstance(raw_triggers, list):
                triggers = raw_triggers

        for index, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                continue
            key = normalize_key_name(trigger.get("key", ""))
            if not key or key in display_map:
                continue
            display_map[key] = str(index + 1)
            kind_map[key] = "trigger"

        if custom_enabled and isinstance(data, dict):
            active_keymap = KeymapService.get_active_keymap(data)
            if isinstance(active_keymap, dict):
                mappings = active_keymap.get("mappings", {})
                if isinstance(mappings, dict):
                    for raw_source, raw_target in mappings.items():
                        source = normalize_key_name(str(raw_source or ""))
                        target = normalize_key_name(str(raw_target or ""))
                        if not source or not target or source in display_map:
                            continue
                        display_map[source] = target
                        kind_map[source] = "keymap"

        # 予約キーは最後に上書きして優先順位を守る。
        if isinstance(data, dict):
            switch_items = sorted(KeymapService.get_keymap_switch_keys(data).items(), key=lambda item: normalize_key_name(item[0]))
            for index, (raw_switch_key, raw_keymap_id) in enumerate(switch_items, start=1):
                switch_key = normalize_key_name(str(raw_switch_key or ""))
                keymap_id = normalize_key_name(str(raw_keymap_id or ""))
                if not switch_key or not keymap_id or not KeymapService.find_keymap(data, keymap_id):
                    continue
                display_map[switch_key] = f"KM{index}"
                kind_map[switch_key] = "keymap_switch"

            mode_toggle_key = normalize_key_name(data.get("hook_toggle_key", ""))
            if mode_toggle_key:
                display_map[mode_toggle_key] = "MODE"
                kind_map[mode_toggle_key] = "mode_toggle"

            stop_key = normalize_key_name(data.get("hook_stop_key", ""))
            if stop_key:
                display_map[stop_key] = "STOP"
                kind_map[stop_key] = "stop"

        self._display_map = display_map
        self._kind_map = kind_map
        self._update_title()
        self.redraw()

    def _handle_close(self) -> None:
        self._cancel_resize_job()
        callback = self._on_close
        self._on_close = None
        try:
            self._cancel_edit(resume_hook=True)
            self.destroy()
        finally:
            if callable(callback):
                callback()

    def _cancel_resize_job(self) -> None:
        job = self._resize_job
        self._resize_job = None
        if job is None:
            return
        try:
            self.after_cancel(job)
        except tk.TclError:
            pass

    def _on_window_configure(self, event) -> None:
        if event.widget is not self:
            return
        try:
            state = self.state()
        except tk.TclError:
            return
        if state in ("zoomed", "iconic"):
            self._cancel_resize_job()
            self._suspended = True
            return
        current = (event.width, event.height)
        if self._suspended:
            self._suspended = False
            self._size_base = current
            if self._ratio_pending:
                self._schedule_pending_ratio()
            return
        if self._applied_size is not None:
            self._size_base = current
            self._applied_size = None
            return
        if current == self._size_base:
            return
        self._cancel_resize_job()
        try:
            self._resize_job = self.after(RESIZE_SETTLE_MS, self._settle_size)
        except tk.TclError:
            self._resize_job = None

    def _on_window_map(self, event) -> None:
        if event.widget is not self or not self._ratio_pending:
            return
        try:
            if self.state() != "normal":
                return
            self._suspended = False
            self._size_base = (self.winfo_width(), self.winfo_height())
        except tk.TclError:
            return
        self._schedule_pending_ratio()

    def _schedule_pending_ratio(self) -> None:
        self._cancel_resize_job()
        try:
            self._resize_job = self.after(
                RESIZE_SETTLE_MS, self._apply_pending_ratio
            )
        except tk.TclError:
            self._resize_job = None

    def _apply_pending_ratio(self) -> None:
        self._resize_job = None
        is_mouse_button_down = self._is_mouse_button_down
        if callable(is_mouse_button_down):
            try:
                if is_mouse_button_down():
                    self._schedule_pending_ratio()
                    return
            except Exception:
                pass
        try:
            if self.state() in ("zoomed", "iconic"):
                return
        except tk.TclError:
            return
        self._ratio_pending = False
        self._apply_ratio_to_base()

    def _settle_size(self) -> None:
        self._resize_job = None
        is_mouse_button_down = self._is_mouse_button_down
        if callable(is_mouse_button_down):
            try:
                if is_mouse_button_down():
                    try:
                        self._resize_job = self.after(
                            RESIZE_SETTLE_MS, self._settle_size
                        )
                    except tk.TclError:
                        self._resize_job = None
                    return
            except Exception:
                pass
        try:
            if self.state() in ("zoomed", "iconic"):
                return
            current = (self.winfo_width(), self.winfo_height())
        except tk.TclError:
            return
        if self._ratio_pending and self._ratio is not None:
            self._ratio_pending = False
            try:
                self.minsize(*minimum_size(self._ratio))
            except tk.TclError:
                pass
        if self._ratio is None:
            self._size_base = current
            return
        target = corrected_size(self._size_base, current, self._ratio)
        if target is None or target == current:
            self._size_base = current
            return
        try:
            self.geometry(f"{target[0]}x{target[1]}")
        except tk.TclError:
            return
        self._applied_size = target
        self._size_base = target

    def _apply_ratio_to_base(self) -> None:
        self._cancel_resize_job()
        ratio = self._ratio
        if ratio is None:
            return
        target = size_from_width(self._size_base[0], ratio)
        try:
            current = (self.winfo_width(), self.winfo_height())
            self.minsize(*minimum_size(ratio))
            if current != target:
                self.geometry(f"{target[0]}x{target[1]}")
                self._applied_size = target
        except tk.TclError:
            return
        self._size_base = target

    def _on_canvas_configure(self, _event=None) -> None:
        self.redraw()

    def redraw(self) -> None:
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        key_specs = tuple(getattr(self._layout, "keys", ()) or ())
        if not key_specs:
            return

        width = max(int(canvas.winfo_width()), 1)
        height = max(int(canvas.winfo_height()), 1)
        if width <= 1 or height <= 1:
            return

        max_x = max(spec.x + spec.w for spec in key_specs)
        max_y = max(spec.y + spec.h for spec in key_specs)
        unit = min(width / max_x, height / max_y)
        pad = max(2, int(unit * 0.08))

        canvas.delete("all")
        self._key_bounds = []
        font_family = tkfont.nametofont("TkDefaultFont").actual("family")
        for spec in key_specs:
            x1 = spec.x * unit + pad
            y1 = spec.y * unit + pad
            x2 = (spec.x + spec.w) * unit - pad
            y2 = (spec.y + spec.h) * unit - pad
            lookup_key = _LOOKUP_KEY_BY_ID.get(spec.id, spec.id)
            display = self._display_map.get(lookup_key, spec.label)
            sub_display = spec.label if self._show_physical_key_labels else ""
            kind = self._kind_map.get(lookup_key, "normal")
            if kind in ("normal", "keymap") and is_prohibited_assign_key(lookup_key):
                kind = "prohibited"
            if kind == "keymap" and (
                is_make_only_scan_code(spec.scan_code)
                or any(is_make_only_scan_code(code) for code in spec.extra_scan_codes)
            ):
                kind = "keymap_make_only"
            self._key_bounds.append((lookup_key, x1, y1, x2, y2))

            fill, outline, text_fill = self.set_key_color(kind)
            width = 2
            if lookup_key == self._editing_source_key:
                outline = "#d97706"
                width = 3

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill,
                outline=outline,
                width=width,
            )
            show_sub = bool(sub_display)
            font_size = max(6, int(unit * (0.20 if show_sub else (0.22 if len(display) > 4 else 0.28))))
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2 - (unit * 0.12 if show_sub else 0),
                text=display,
                fill=text_fill,
                font=(font_family, font_size, "bold"),
                width=max(10, (x2 - x1) - 8),
                justify="center",
            )
            if show_sub:
                sub_font_size = max(5, int(unit * 0.14))
                canvas.create_text(
                    (x1 + x2) / 2,
                    y2 - max(8, unit * 0.18),
                    text=sub_display,
                    fill="#4f5d73",
                    font=(font_family, sub_font_size),
                    width=max(10, (x2 - x1) - 8),
                    justify="center",
                )

    def set_key_color(self, kind: str) -> tuple[str, str, str]:
        if kind == "stop":
            return "#fde2e2", "#c62828", "#7f1d1d"
        if kind == "mode_toggle":
            return "#ffe8cc", "#ef6c00", "#8a3c00"
        if kind == "keymap_switch":
            return "#ede9fe", "#6d28d9", "#4c1d95"
        if kind == "trigger":
            return "#dcecff", "#4c7ed9", "#163a78"
        if kind == "keymap":
            return "#e8f6df", "#5c9c3b", "#214d18"
        if kind == "keymap_make_only":
            return "#e4ebe1", "#7f9a74", "#2f4429"
        if kind == "prohibited":
            return "#e5e7eb", "#9ca3af", "#6b7280"
        return "#ffffff", "#aab4c3", "#24313f"

    def _find_key_at_point(self, x: float, y: float) -> str:
        for key, x1, y1, x2, y2 in self._key_bounds:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return key
        return ""

    def _on_canvas_left_click(self, event) -> str | None:
        key = self._find_key_at_point(event.x, event.y)
        if not key:
            return None
        if is_prohibited_assign_key(key):
            return "break"
        self._begin_edit(key)
        return "break"

    def _on_canvas_right_click(self, event) -> str | None:
        key = self._find_key_at_point(event.x, event.y)
        if not key:
            return None
        self._cancel_edit(resume_hook=True)
        callback = self._on_clear_keymap
        if callable(callback):
            callback(key)
        self.focus_force()
        self.canvas.focus_set()
        return "break"

    def _begin_edit(self, source_key: str) -> None:
        if not self._editing_source_key:
            begin_key_capture(self, self)
            if hasattr(self.master, "hook"):
                self.master.hook.suspend_hook_for_dialog()
        self._editing_source_key = normalize_key_name(source_key)
        self.focus_force()
        self.canvas.focus_set()
        self._update_title()
        self.redraw()

    def _cancel_edit(self, *, resume_hook: bool) -> None:
        if not self._editing_source_key:
            return
        self._editing_source_key = None
        end_key_capture(self)
        if resume_hook and hasattr(self.master, "hook"):
            self.master.hook.resume_hook_after_dialog()
        self._update_title()
        self.redraw()

    def _on_key_press(self, event) -> str | None:
        if not self._editing_source_key:
            return None

        key = self._normalize_tk_key(event)
        if is_unresolved_capture_key(key):
            return "break"
        if key == "esc":
            self._cancel_edit(resume_hook=True)
            return "break"
        if key in ("ctrl", "shift", "alt", "windows"):
            return "break"
        if not key:
            return "break"

        callback = self._on_assign_keymap
        if callable(callback):
            changed = callback(self._editing_source_key, key)
            if changed:
                self._cancel_edit(resume_hook=True)
            return "break"

        self._cancel_edit(resume_hook=True)
        return "break"

    def _normalize_tk_key(self, event: object) -> str:
        numpad_name = numpad_name_from_tk_event(
            getattr(event, "keycode", None), getattr(event, "state", 0)
        )
        if numpad_name:
            return numpad_name
        keysym = str(getattr(event, "keysym", "") or "")
        k = keysym.lower()
        if k in TK_KEYSYM_TO_KEYBOARD_NAME:
            return TK_KEYSYM_TO_KEYBOARD_NAME[k]

        keycode = getattr(event, "keycode", None)
        try:
            vk = int(keycode)
        except (TypeError, ValueError, OverflowError):
            vk = None
        scan_code = win32_window.vk_to_scan_code(vk) if vk is not None else None
        resolved = (
            resolve_layout_key_id_from_scan_code(self._layout, scan_code)
            if scan_code is not None
            else ""
        )
        normalized = normalize_key_name(resolved)
        if normalized and not is_numpad_key_name(normalized):
            return normalized

        return k

    def _update_title(self) -> None:
        layout_name = getattr(self._layout, "display_name", "") or getattr(self._layout, "layout_id", "")
        self.title(keyboard_window_title(layout_name, self._editing_source_key))
