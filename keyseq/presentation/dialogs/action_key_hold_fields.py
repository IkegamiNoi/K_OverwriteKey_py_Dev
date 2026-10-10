from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from keyseq.presentation.tk_keys import normalize_key_hold_tk_keysym


class ActionKeyHoldFields:
    """Input controls for one key_hold action."""

    def __init__(self, parent: tk.Misc, *, capture_mouse_position: Callable) -> None:
        self.parent = parent
        self.dialog = parent.winfo_toplevel()
        self.capture_mouse_position = capture_mouse_position
        self.recording = False
        self._key_press_bind_id: str | None = None

        self.frame = ttk.LabelFrame(parent, text="キーの押下 / 解放", padding=8)
        self.frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.frame, text="動作").grid(row=0, column=0, sticky="w")
        self.edge_var = tk.StringVar(value="押す")
        self.edge_combo = ttk.Combobox(
            self.frame, textvariable=self.edge_var, values=("押す", "離す"),
            state="readonly", width=10,
        )
        self.edge_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(self.frame, text="対象").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.target_var = tk.StringVar(value="キー")
        self.target_combo = ttk.Combobox(
            self.frame, textvariable=self.target_var, values=("キー", "マウスのボタン"),
            state="readonly", width=16,
        )
        self.target_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.target_combo.bind("<<ComboboxSelected>>", lambda _event: self.sync_target())

        self.key_frame = ttk.Frame(self.frame)
        self.key_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(8, 0))
        ttk.Label(self.key_frame, text="キー名").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar(value="")
        self.key_entry = ttk.Entry(self.key_frame, textvariable=self.key_var, width=24)
        self.key_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.record_button = ttk.Button(self.key_frame, text="1 キーを記録", command=self.start_recording)
        self.record_button.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.key_hint = ttk.Label(self.key_frame, text="キーを 1 つ押すと記録します")
        self.key_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(8, 0))
        ttk.Label(self.button_frame, text="ボタン").grid(row=0, column=0, sticky="w")
        self.button_var = tk.StringVar(value="左")
        self.button_combo = ttk.Combobox(
            self.button_frame, textvariable=self.button_var,
            values=("左", "右", "中"), state="readonly", width=10,
        )
        self.button_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self._button_values = {"左": "left", "右": "right", "中": "middle"}
        self._button_labels = {value: label for label, value in self._button_values.items()}

        self.coordinates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.button_frame, text="座標を指定する", variable=self.coordinates_var,
            command=self.sync_coordinates,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.coordinates_frame = ttk.Frame(self.button_frame)
        self.coordinates_frame.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6, 0))
        ttk.Label(self.coordinates_frame, text="X").grid(row=0, column=0, sticky="w")
        self.x_var = tk.StringVar(value="")
        ttk.Entry(self.coordinates_frame, textvariable=self.x_var, width=10).grid(
            row=0, column=1, sticky="w", padx=(8, 16),
        )
        ttk.Label(self.coordinates_frame, text="Y").grid(row=0, column=2, sticky="w")
        self.y_var = tk.StringVar(value="")
        ttk.Entry(self.coordinates_frame, textvariable=self.y_var, width=10).grid(
            row=0, column=3, sticky="w", padx=(8, 0),
        )
        self.capture_button = ttk.Button(
            self.coordinates_frame, text="座標を取得",
            command=lambda: self.capture_mouse_position(
                self.x_var, self.y_var, self.capture_button, self.capture_hint,
            ),
        )
        self.capture_button.grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.capture_hint = ttk.Label(
            self.coordinates_frame,
            text="※押したあと、画面上の任意の場所を1回クリックすると座標が入ります",
        )
        self.capture_hint.grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
        self.sync_target()

    def load(self, action: dict) -> None:
        edge = str(action.get("edge", "down")).strip().lower()
        self.edge_var.set({"down": "押す", "up": "離す"}.get(edge, edge))
        if isinstance(action.get("button"), str) and action["button"].strip():
            self.target_var.set("マウスのボタン")
            raw_button = action["button"].strip().lower()
            self.button_var.set(self._button_labels.get(raw_button, raw_button))
            if "x" in action or "y" in action:
                self.coordinates_var.set(True)
                self.x_var.set(str(action.get("x", "")))
                self.y_var.set(str(action.get("y", "")))
        else:
            self.target_var.set("キー")
            self.key_var.set(str(action.get("value") or ""))
        self.sync_target()

    def build_action(self, label: str) -> dict:
        edge = self.edge_var.get()
        action = {"type": "key_hold", "edge": {"押す": "down", "離す": "up"}.get(edge, edge)}
        if self.target_var.get() == "キー":
            action["value"] = self.key_var.get().strip()
        else:
            button = self.button_var.get()
            action["button"] = self._button_values.get(button, button)
            if self.coordinates_var.get():
                action["x"] = self.x_var.get().strip()
                action["y"] = self.y_var.get().strip()
        action["label"] = label
        return action

    def sync_target(self) -> None:
        self.stop_recording()
        if self.target_var.get() == "キー":
            self.key_frame.grid()
            self.button_frame.grid_remove()
        else:
            self.key_frame.grid_remove()
            self.button_frame.grid()
            self.sync_coordinates()

    def sync_coordinates(self) -> None:
        if self.coordinates_var.get():
            self.coordinates_frame.grid()
        else:
            self.coordinates_frame.grid_remove()

    def start_recording(self) -> None:
        if self.recording:
            self.stop_recording()
            return
        self.recording = True
        self.record_button.configure(text="記録中…")
        self.key_hint.configure(text="キーを 1 つ押してください（Esc で停止）")
        self.key_entry.focus_set()
        self._key_press_bind_id = self.dialog.bind("<KeyPress>", self._on_key_press, add="+")

    def stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        self.record_button.configure(text="1 キーを記録")
        self.key_hint.configure(text="キーを 1 つ押すと記録します")
        if self._key_press_bind_id:
            self.dialog.unbind("<KeyPress>", self._key_press_bind_id)
            self._key_press_bind_id = None

    def _on_key_press(self, event: tk.Event) -> str:
        if not self.recording:
            return "break"
        keysym = str(event.keysym)
        if keysym.lower() == "escape":
            self.stop_recording()
            return "break"
        self.key_var.set(normalize_key_hold_tk_keysym(keysym))
        self.stop_recording()
        return "break"
