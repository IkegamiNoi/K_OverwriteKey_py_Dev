from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from keyseq.domain.key_hold import wants_repeat
from keyseq.presentation.hook_button_texts import UNKNOWN_CAPTURE_KEY_HINT_TEXT
from keyseq.presentation.key_capture_ime import begin_key_capture, end_key_capture
from keyseq.presentation.tk_keys import (
    is_unresolved_capture_key,
    normalize_key_hold_tk_key_event,
)
from keyseq.shared.i18n import tr


class ActionKeyHoldFields:
    """key_hold 1 行分の入力欄。"""

    @staticmethod
    def _target_labels() -> dict[str, str]:
        return {
            "key": tr("action_dialog.key_hold.target.key"),
            "mouse_button": tr("action_dialog.key_hold.target.mouse_button"),
        }

    @staticmethod
    def _edge_labels() -> dict[str, str]:
        return {
            "down": tr("action_dialog.key_hold.edge.down"),
            "up": tr("action_dialog.key_hold.edge.up"),
        }

    @staticmethod
    def _button_labels() -> dict[str, str]:
        return {
            "left": tr("action_dialog.key_hold.button.left"),
            "right": tr("action_dialog.key_hold.button.right"),
            "middle": tr("action_dialog.key_hold.button.middle"),
        }

    def __init__(self, parent: tk.Misc, *, capture_mouse_position: Callable) -> None:
        self.parent = parent
        self.dialog = parent.winfo_toplevel()
        self.capture_mouse_position = capture_mouse_position
        self.recording = False
        self._key_press_bind_id: str | None = None
        self._target_labels_by_code = self._target_labels()
        self._edge_labels_by_code = self._edge_labels()
        self._button_labels_by_code = self._button_labels()
        self._target_codes_by_label = {v: k for k, v in self._target_labels_by_code.items()}
        self._edge_codes_by_label = {v: k for k, v in self._edge_labels_by_code.items()}
        self._button_codes_by_label = {v: k for k, v in self._button_labels_by_code.items()}

        self.frame = ttk.LabelFrame(parent, text=tr("action_dialog.key_hold.title"), padding=8)
        self.frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.frame, text=tr("action_dialog.key_hold.edge.label")).grid(
            row=0, column=0, sticky="w",
        )
        self.edge_var = tk.StringVar(value=self._edge_labels_by_code["down"])
        self.edge_combo = ttk.Combobox(
            self.frame, textvariable=self.edge_var, values=tuple(self._edge_labels_by_code.values()),
            state="readonly", width=10,
        )
        self.edge_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.edge_combo.bind("<<ComboboxSelected>>", lambda _event: self.sync_repeat_visibility())

        ttk.Label(self.frame, text=tr("action_dialog.key_hold.target.label")).grid(
            row=1, column=0, sticky="w", pady=(8, 0),
        )
        self.target_var = tk.StringVar(value=self._target_labels_by_code["key"])
        self.target_combo = ttk.Combobox(
            self.frame, textvariable=self.target_var, values=tuple(self._target_labels_by_code.values()),
            state="readonly", width=16,
        )
        self.target_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.target_combo.bind("<<ComboboxSelected>>", lambda _event: self.sync_target())

        self.key_frame = ttk.Frame(self.frame)
        self.key_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(8, 0))
        ttk.Label(self.key_frame, text=tr("action_dialog.key_hold.key_name")).grid(
            row=0, column=0, sticky="w",
        )
        self.key_var = tk.StringVar(value="")
        self.key_entry = ttk.Entry(self.key_frame, textvariable=self.key_var, width=24)
        self.key_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.record_button = ttk.Button(
            self.key_frame, text=tr("action_dialog.key_hold.record"), command=self.start_recording,
        )
        self.record_button.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.key_hint = ttk.Label(self.key_frame, text=tr("action_dialog.key_hold.record_hint"))
        self.key_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(8, 0))
        ttk.Label(self.button_frame, text=tr("action_dialog.button")).grid(row=0, column=0, sticky="w")
        self.button_var = tk.StringVar(value=self._button_labels_by_code["left"])
        self.button_combo = ttk.Combobox(
            self.button_frame, textvariable=self.button_var,
            values=tuple(self._button_labels_by_code.values()), state="readonly", width=10,
        )
        self.button_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.coordinates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.button_frame, text=tr("action_dialog.coordinates.toggle"), variable=self.coordinates_var,
            command=self.sync_coordinates,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.coordinates_frame = ttk.Frame(self.button_frame)
        self.coordinates_frame.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6, 0))
        ttk.Label(self.coordinates_frame, text=tr("action_dialog.mouse.axis_x")).grid(
            row=0, column=0, sticky="w",
        )
        self.x_var = tk.StringVar(value="")
        ttk.Entry(self.coordinates_frame, textvariable=self.x_var, width=10).grid(
            row=0, column=1, sticky="w", padx=(8, 16),
        )
        ttk.Label(self.coordinates_frame, text=tr("action_dialog.mouse.axis_y")).grid(
            row=0, column=2, sticky="w",
        )
        self.y_var = tk.StringVar(value="")
        ttk.Entry(self.coordinates_frame, textvariable=self.y_var, width=10).grid(
            row=0, column=3, sticky="w", padx=(8, 0),
        )
        self.capture_button = ttk.Button(
            self.coordinates_frame, text=tr("action_dialog.coordinates.capture"),
            command=lambda: self.capture_mouse_position(
                self.x_var, self.y_var, self.capture_button, self.capture_hint,
            ),
        )
        self.capture_button.grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.capture_hint = ttk.Label(
            self.coordinates_frame,
            text=tr("action_dialog.coordinates.capture_hint"),
        )
        self.capture_hint.grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
        self.repeat_var = tk.BooleanVar(value=True)
        self.repeat_frame = ttk.Frame(self.frame)
        self.repeat_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.repeat_check = ttk.Checkbutton(
            self.repeat_frame, text=tr("action_dialog.key_hold.repeat"), variable=self.repeat_var,
        )
        self.repeat_check.pack(side="left")
        ttk.Label(self.repeat_frame, text=tr("action_dialog.key_hold.repeat_hint")).pack(side="left", padx=(4, 0))
        self.sync_target()

    def load(self, action: dict) -> None:
        edge = str(action.get("edge", "down")).strip().lower()
        self.edge_var.set(self._edge_labels_by_code.get(edge, edge))
        if isinstance(action.get("button"), str) and action["button"].strip():
            self.target_var.set(self._target_labels_by_code["mouse_button"])
            raw_button = action["button"].strip().lower()
            self.button_var.set(self._button_labels_by_code.get(raw_button, raw_button))
            if "x" in action or "y" in action:
                self.coordinates_var.set(True)
                self.x_var.set(str(action.get("x", "")))
                self.y_var.set(str(action.get("y", "")))
        else:
            self.target_var.set(self._target_labels_by_code["key"])
            self.key_var.set(str(action.get("value") or ""))
        if self.edge_code() == "down" and self.target_kind() == "key":
            self.repeat_var.set(wants_repeat(action))
        else:
            self.repeat_var.set(True)
        self.sync_target()

    def build_action(self, label: str) -> dict:
        action = {"type": "key_hold", "edge": self.edge_code()}
        if self.target_kind() == "key":
            action["value"] = self.key_var.get().strip()
        else:
            button = self.button_var.get()
            action["button"] = self._button_codes_by_label.get(button, button)
            if self.coordinates_var.get():
                action["x"] = self.x_var.get().strip()
                action["y"] = self.y_var.get().strip()
        action["label"] = label
        return action

    def sync_target(self) -> None:
        self.stop_recording()
        if self.target_kind() == "key":
            self.key_frame.grid()
            self.button_frame.grid_remove()
        else:
            self.key_frame.grid_remove()
            self.button_frame.grid()
            self.sync_coordinates()
        self.sync_repeat_visibility()

    def sync_repeat_visibility(self) -> None:
        """押すキー行のときだけリピート欄を表示する。"""
        if self.edge_code() == "down" and self.target_kind() == "key":
            self.repeat_frame.grid()
        else:
            self.repeat_frame.grid_remove()

    def target_kind(self) -> str:
        return self._target_codes_by_label.get(self.target_var.get(), self.target_var.get())

    def edge_code(self) -> str:
        return self._edge_codes_by_label.get(self.edge_var.get(), self.edge_var.get())

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
        begin_key_capture(self, self.dialog, self._record_key)
        self.record_button.configure(text=tr("action_dialog.key_hold.recording"))
        self.key_hint.configure(text=tr("action_dialog.key_hold.recording_hint"))
        self.key_entry.focus_set()
        self._key_press_bind_id = self.dialog.bind("<KeyPress>", self._on_key_press, add="+")

    def stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        end_key_capture(self)
        self.record_button.configure(text=tr("action_dialog.key_hold.record"))
        self.key_hint.configure(text=tr("action_dialog.key_hold.record_hint"))
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
        key = normalize_key_hold_tk_key_event(event)
        if is_unresolved_capture_key(key):
            self.key_hint.configure(text=UNKNOWN_CAPTURE_KEY_HINT_TEXT)
            return "break"
        self._record_key(key)
        return "break"

    def _record_key(self, key: str) -> None:
        if not self.recording:
            return
        self.key_var.set(key)
        self.stop_recording()
