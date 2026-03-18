from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

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
}


def normalize_key_name(value: str) -> str:
    return (value or "").strip().lower()


class KeyboardWindow(tk.Toplevel):
    def __init__(self, parent, *, layout: KeyboardLayout | None = None, on_close=None):
        super().__init__(parent)
        self.title("Keyboard UI")
        self.geometry("510x210")
        self.minsize(510, 210)
        self._on_close = on_close
        self._layout = layout or resolve_keyboard_layout()
        self._display_map: dict[str, str] = {}
        self._kind_map: dict[str, str] = {}

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        self.summary_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=self.summary_var, anchor="w").pack(fill="x", pady=(0, 8))

        self.canvas = tk.Canvas(container, background="#f5f7fb", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._update_summary()

    def update_layout(self, layout: KeyboardLayout | None) -> None:
        self._layout = layout or resolve_keyboard_layout()
        self._update_summary()
        self.redraw()

    def update_from_config(self, data: dict | None) -> None:
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

        self._display_map = trigger_map
        self._kind_map = kind_map
        self._update_summary()
        self.redraw()

    def _handle_close(self) -> None:
        callback = self._on_close
        self._on_close = None
        try:
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
        font_family = tkfont.nametofont("TkDefaultFont").actual("family")
        for spec in key_specs:
            x1 = spec.x * unit + pad
            y1 = spec.y * unit + pad
            x2 = (spec.x + spec.w) * unit - pad
            y2 = (spec.y + spec.h) * unit - pad
            lookup_key = _LOOKUP_KEY_BY_ID.get(spec.id, spec.id)
            display = self._display_map.get(lookup_key, spec.label)
            kind = self._kind_map.get(lookup_key, "normal")

            fill = "#ffffff"
            outline = "#aab4c3"
            text_fill = "#24313f"
            if kind == "trigger":
                fill = "#dcecff"
                outline = "#4c7ed9"
                text_fill = "#163a78"

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill,
                outline=outline,
                width=2,
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

    def _update_summary(self) -> None:
        layout_name = getattr(self._layout, "display_name", "") or getattr(self._layout, "layout_id", "")
        if self._display_map:
            self.summary_var.set(f"レイアウト: {layout_name} / 表示: trigger は番号、未設定キーは元キーです。")
        else:
            self.summary_var.set(f"レイアウト: {layout_name} / 表示中の trigger はありません。未設定キーは元キーです。")
