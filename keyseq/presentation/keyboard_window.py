from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from keyseq.application.keymap_service import KeymapService
from keyseq.presentation.keyboard_layouts import KeyboardLayout, resolve_keyboard_layout

_LOOKUP_KEY_BY_ID = {
    "shift_l": "shift",
    "shift_r": "shift",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "alt_l": "alt",
    "alt_r": "alt",
    "windows_l": "windows",
    "windows_r": "windows",
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


def normalize_key_name(value: str) -> str:
    return (value or "").strip().lower()


class KeyboardWindow(tk.Toplevel):
    def __init__(
        self,
        parent,
        *,
        layout: KeyboardLayout | None = None,
        on_close=None,
        on_assign_keymap=None,
        on_clear_keymap=None,
    ):
        super().__init__(parent)
        self.title("Keyboard UI")
        self.geometry("510x210")
        self.minsize(510, 210)
        self._on_close = on_close
        self._on_assign_keymap = on_assign_keymap
        self._on_clear_keymap = on_clear_keymap
        self._layout = layout or resolve_keyboard_layout()
        self._display_map: dict[str, str] = {}
        self._kind_map: dict[str, str] = {}
        self._key_bounds: list[tuple[str, float, float, float, float]] = []
        self._editing_source_key: str | None = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        self.summary_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=self.summary_var, anchor="w").pack(fill="x", pady=(0, 8))

        self.canvas = tk.Canvas(container, background="#f5f7fb", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.bind("<KeyPress>", self._on_key_press, add="+")
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._update_summary()

    def update_layout(self, layout: KeyboardLayout | None) -> None:
        self._layout = layout or resolve_keyboard_layout()
        self._update_summary()
        self.redraw()

    def update_from_config(self, data: dict | None, *, custom_enabled: bool = True) -> None:
        trigger_map: dict[str, str] = {}
        kind_map: dict[str, str] = {}

        triggers = []
        if isinstance(data, dict):
            raw_triggers = data.get("triggers", [])
            if isinstance(raw_triggers, list):
                triggers = raw_triggers

        for index, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                continue
            key = normalize_key_name(trigger.get("key", ""))
            if not key:
                continue
            trigger_map[key] = str(index + 1)
            kind_map[key] = "trigger"

        if custom_enabled and isinstance(data, dict):
            active_keymap = KeymapService.get_active_keymap(data)
            if isinstance(active_keymap, dict):
                mappings = active_keymap.get("mappings", {})
                if isinstance(mappings, dict):
                    for raw_source, raw_target in mappings.items():
                        source = normalize_key_name(str(raw_source or ""))
                        target = normalize_key_name(str(raw_target or ""))
                        if not source or not target or source in trigger_map:
                            continue
                        trigger_map[source] = target
                        kind_map[source] = "keymap"

        self._display_map = trigger_map
        self._kind_map = kind_map
        self._update_summary()
        self.redraw()

    def _handle_close(self) -> None:
        callback = self._on_close
        self._on_close = None
        try:
            self._cancel_edit(resume_hook=True)
            self.destroy()
        finally:
            if callable(callback):
                callback()

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
            kind = self._kind_map.get(lookup_key, "normal")
            self._key_bounds.append((lookup_key, x1, y1, x2, y2))

            fill = "#ffffff"
            outline = "#aab4c3"
            text_fill = "#24313f"
            width = 2
            if kind == "trigger":
                fill = "#dcecff"
                outline = "#4c7ed9"
                text_fill = "#163a78"
            elif kind == "keymap":
                fill = "#e8f6df"
                outline = "#5c9c3b"
                text_fill = "#214d18"
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
            font_size = max(6, int(unit * (0.22 if len(display) > 4 else 0.28)))
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=display,
                fill=text_fill,
                font=(font_family, font_size, "bold"),
                width=max(10, (x2 - x1) - 8),
                justify="center",
            )

    def _find_key_at_point(self, x: float, y: float) -> str:
        for key, x1, y1, x2, y2 in self._key_bounds:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return key
        return ""

    def _on_canvas_left_click(self, event) -> str | None:
        key = self._find_key_at_point(event.x, event.y)
        if not key:
            return None
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
        if not self._editing_source_key and hasattr(self.master, "suspend_hook_for_dialog"):
            self.master.suspend_hook_for_dialog()
        self._editing_source_key = normalize_key_name(source_key)
        self.focus_force()
        self.canvas.focus_set()
        self._update_summary()
        self.redraw()

    def _cancel_edit(self, *, resume_hook: bool) -> None:
        if not self._editing_source_key:
            return
        self._editing_source_key = None
        if resume_hook and hasattr(self.master, "resume_hook_after_dialog"):
            self.master.resume_hook_after_dialog()
        self._update_summary()
        self.redraw()

    def _on_key_press(self, event) -> str | None:
        if not self._editing_source_key:
            return None

        key = self._normalize_tk_key(event.keysym)
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

    def _normalize_tk_key(self, keysym: str) -> str:
        k = (keysym or "").lower()
        mapping = {
            "control_l": "ctrl",
            "control_r": "ctrl",
            "shift_l": "shift",
            "shift_r": "shift",
            "alt_l": "alt",
            "alt_r": "alt",
            "super_l": "windows",
            "super_r": "windows",
            "win_l": "windows",
            "win_r": "windows",
            "return": "enter",
            "escape": "esc",
            "space": "space",
            "tab": "tab",
            "backspace": "backspace",
            "prior": "page up",
            "next": "page down",
        }
        return mapping.get(k, k)

    def _update_summary(self) -> None:
        layout_name = getattr(self._layout, "display_name", "") or getattr(self._layout, "layout_id", "")
        if self._editing_source_key:
            self.summary_var.set(
                f"レイアウト: {layout_name} / 編集中: {self._editing_source_key} / 置換先キーを押してください（Escでキャンセル、右クリックでクリア）"
            )
            return
        if not self._kind_map:
            self.summary_var.set(
                f"レイアウト: {layout_name} / 表示中の trigger・keymap はありません。左クリックで編集、右クリックでクリアできます。"
            )
            return

        has_trigger = any(kind == "trigger" for kind in self._kind_map.values())
        has_keymap = any(kind == "keymap" for kind in self._kind_map.values())
        if has_trigger and has_keymap:
            self.summary_var.set(
                f"レイアウト: {layout_name} / trigger は番号、keymap は出力キー、未設定キーは元キーです。左クリックで編集、右クリックでクリアできます。"
            )
            return
        if has_trigger:
            self.summary_var.set(
                f"レイアウト: {layout_name} / trigger は番号、未設定キーは元キーです。左クリックで編集、右クリックでクリアできます。"
            )
            return
        self.summary_var.set(
            f"レイアウト: {layout_name} / keymap は出力キー、未設定キーは元キーです。左クリックで編集、右クリックでクリアできます。"
        )
