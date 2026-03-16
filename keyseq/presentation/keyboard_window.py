from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk


@dataclass(frozen=True)
class KeySpec:
    id: str
    label: str
    x: float
    y: float
    w: float = 1.0
    h: float = 1.0


KEY_SPECS: tuple[KeySpec, ...] = (
    KeySpec("esc", "Esc", 0.0, 0.0),
    KeySpec("f1", "F1", 2.0, 0.0),
    KeySpec("f2", "F2", 3.0, 0.0),
    KeySpec("f3", "F3", 4.0, 0.0),
    KeySpec("f4", "F4", 5.0, 0.0),
    KeySpec("f5", "F5", 6.5, 0.0),
    KeySpec("f6", "F6", 7.5, 0.0),
    KeySpec("f7", "F7", 8.5, 0.0),
    KeySpec("f8", "F8", 9.5, 0.0),
    KeySpec("f9", "F9", 11.0, 0.0),
    KeySpec("f10", "F10", 12.0, 0.0),
    KeySpec("f11", "F11", 13.0, 0.0),
    KeySpec("f12", "F12", 14.0, 0.0),
    KeySpec("print screen", "PrtSc", 15.25, 0.0),
    KeySpec("scroll lock", "Scroll", 16.25, 0.0),
    KeySpec("pause", "Pause", 17.25, 0.0),
    KeySpec("`", "`", 0.0, 1.2),
    KeySpec("1", "1", 1.0, 1.2),
    KeySpec("2", "2", 2.0, 1.2),
    KeySpec("3", "3", 3.0, 1.2),
    KeySpec("4", "4", 4.0, 1.2),
    KeySpec("5", "5", 5.0, 1.2),
    KeySpec("6", "6", 6.0, 1.2),
    KeySpec("7", "7", 7.0, 1.2),
    KeySpec("8", "8", 8.0, 1.2),
    KeySpec("9", "9", 9.0, 1.2),
    KeySpec("0", "0", 10.0, 1.2),
    KeySpec("-", "-", 11.0, 1.2),
    KeySpec("=", "=", 12.0, 1.2),
    KeySpec("backspace", "Backspace", 13.0, 1.2, 2.0),
    KeySpec("insert", "Ins", 15.25, 1.2),
    KeySpec("home", "Home", 16.25, 1.2),
    KeySpec("page up", "PgUp", 17.25, 1.2),
    KeySpec("tab", "Tab", 0.0, 2.2, 1.5),
    KeySpec("q", "Q", 1.5, 2.2),
    KeySpec("w", "W", 2.5, 2.2),
    KeySpec("e", "E", 3.5, 2.2),
    KeySpec("r", "R", 4.5, 2.2),
    KeySpec("t", "T", 5.5, 2.2),
    KeySpec("y", "Y", 6.5, 2.2),
    KeySpec("u", "U", 7.5, 2.2),
    KeySpec("i", "I", 8.5, 2.2),
    KeySpec("o", "O", 9.5, 2.2),
    KeySpec("p", "P", 10.5, 2.2),
    KeySpec("[", "[", 11.5, 2.2),
    KeySpec("]", "]", 12.5, 2.2),
    KeySpec("\\", "\\", 13.5, 2.2, 1.5),
    KeySpec("delete", "Del", 15.25, 2.2),
    KeySpec("end", "End", 16.25, 2.2),
    KeySpec("page down", "PgDn", 17.25, 2.2),
    KeySpec("caps lock", "Caps", 0.0, 3.2, 1.75),
    KeySpec("a", "A", 1.75, 3.2),
    KeySpec("s", "S", 2.75, 3.2),
    KeySpec("d", "D", 3.75, 3.2),
    KeySpec("f", "F", 4.75, 3.2),
    KeySpec("g", "G", 5.75, 3.2),
    KeySpec("h", "H", 6.75, 3.2),
    KeySpec("j", "J", 7.75, 3.2),
    KeySpec("k", "K", 8.75, 3.2),
    KeySpec("l", "L", 9.75, 3.2),
    KeySpec(";", ";", 10.75, 3.2),
    KeySpec("'", "'", 11.75, 3.2),
    KeySpec("enter", "Enter", 12.75, 3.2, 2.25),
    KeySpec("shift_l", "Shift", 0.0, 4.2, 2.25),
    KeySpec("z", "Z", 2.25, 4.2),
    KeySpec("x", "X", 3.25, 4.2),
    KeySpec("c", "C", 4.25, 4.2),
    KeySpec("v", "V", 5.25, 4.2),
    KeySpec("b", "B", 6.25, 4.2),
    KeySpec("n", "N", 7.25, 4.2),
    KeySpec("m", "M", 8.25, 4.2),
    KeySpec(",", ",", 9.25, 4.2),
    KeySpec(".", ".", 10.25, 4.2),
    KeySpec("/", "/", 11.25, 4.2),
    KeySpec("shift_r", "Shift", 12.25, 4.2, 2.75),
    KeySpec("up", "Up", 16.25, 4.2),
    KeySpec("ctrl_l", "Ctrl", 0.0, 5.2, 1.5),
    KeySpec("windows_l", "Win", 1.5, 5.2, 1.5),
    KeySpec("alt_l", "Alt", 3.0, 5.2, 1.5),
    KeySpec("space", "Space", 4.5, 5.2, 4.5),
    KeySpec("alt_r", "Alt", 9.0, 5.2, 1.5),
    KeySpec("windows_r", "Win", 10.5, 5.2, 1.5),
    KeySpec("menu", "Menu", 12.0, 5.2, 1.5),
    KeySpec("ctrl_r", "Ctrl", 13.5, 5.2, 1.5),
    KeySpec("left", "Left", 15.25, 5.2),
    KeySpec("down", "Down", 16.25, 5.2),
    KeySpec("right", "Right", 17.25, 5.2),
)

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
    def __init__(self, parent, *, on_close=None):
        super().__init__(parent)
        self.title("Keyboard UI")
        self.geometry("510x210")
        self.minsize(510, 210)
        self._on_close = on_close
        self._display_map: dict[str, str] = {}
        self._kind_map: dict[str, str] = {}

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        self.summary_var = tk.StringVar(
            value="表示: trigger は番号、未設定キーは元キーを表示します。"
        )
        ttk.Label(container, textvariable=self.summary_var, anchor="w").pack(fill="x", pady=(0, 8))

        self.canvas = tk.Canvas(container, background="#f5f7fb", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.protocol("WM_DELETE_WINDOW", self._handle_close)

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

        if trigger_map:
            self.summary_var.set(
                "表示: trigger は番号、未設定キーは元キーを表示します。"
            )
        else:
            self.summary_var.set(
                "表示中の trigger はありません。未設定キーは元キーを表示します。"
            )
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

        width = max(int(canvas.winfo_width()), 1)
        height = max(int(canvas.winfo_height()), 1)
        if width <= 1 or height <= 1:
            return

        max_x = max(spec.x + spec.w for spec in KEY_SPECS)
        max_y = max(spec.y + spec.h for spec in KEY_SPECS)
        unit = min(width / max_x, height / max_y)
        pad = max(2, int(unit * 0.08))

        canvas.delete("all")
        font_family = tkfont.nametofont("TkDefaultFont").actual("family")
        for spec in KEY_SPECS:
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
