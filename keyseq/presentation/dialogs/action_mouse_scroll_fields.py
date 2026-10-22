from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from keyseq.domain.mouse_scroll import (
    ACTION_TYPE_MOUSE_SCROLL,
    DEFAULT_NOTCHES,
    DIRECTIONS,
    UNIT_DELTA,
    UNIT_NOTCH,
    WHEEL_DELTA,
    parse_mouse_scroll,
)


class ActionMouseScrollFields:
    """mouse_scroll 1 行分の入力欄。"""

    _DIRECTION_VALUES = dict(zip(("上", "下", "左", "右"), DIRECTIONS))
    _DIRECTION_LABELS = {value: label for label, value in _DIRECTION_VALUES.items()}

    def __init__(self, parent: tk.Misc, *, capture_mouse_position: Callable) -> None:
        self.capture_mouse_position = capture_mouse_position
        self._capture_state = "normal"
        self.frame = ttk.LabelFrame(parent, text="マウススクロール", padding=8)
        self.frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.frame, text="向き").grid(row=0, column=0, sticky="w")
        self.direction_var = tk.StringVar(value="下")
        self.direction_combo = ttk.Combobox(
            self.frame, textvariable=self.direction_var,
            values=("上", "下", "左", "右"), state="readonly", width=8,
        )
        self.direction_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.unit_var = tk.StringVar(value=UNIT_NOTCH)
        self.notch_radio = ttk.Radiobutton(
            self.frame, text="ノッチ数", variable=self.unit_var, value=UNIT_NOTCH,
            command=self.sync_amount,
        )
        self.notch_radio.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.amount_notch_var = tk.StringVar(value=str(DEFAULT_NOTCHES))
        self.amount_notch_entry = ttk.Entry(self.frame, textvariable=self.amount_notch_var, width=12)
        self.amount_notch_entry.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.delta_radio = ttk.Radiobutton(
            self.frame, text=f"生の値（{WHEEL_DELTA} = 1ノッチ）",
            variable=self.unit_var, value=UNIT_DELTA,
            command=self.sync_amount,
        )
        self.delta_radio.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.amount_delta_var = tk.StringVar(value=str(WHEEL_DELTA))
        self.amount_delta_entry = ttk.Entry(self.frame, textvariable=self.amount_delta_var, width=12)
        self.amount_delta_entry.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        self.coordinates_var = tk.BooleanVar(value=False)
        self.coordinates_check = ttk.Checkbutton(
            self.frame, text="座標を指定する", variable=self.coordinates_var,
            command=self.sync_coordinates,
        )
        self.coordinates_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.x_var = tk.StringVar(value="")
        self.y_var = tk.StringVar(value="")
        ttk.Label(self.frame, text="X").grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.x_entry = ttk.Entry(self.frame, textvariable=self.x_var, width=10)
        self.x_entry.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        ttk.Label(self.frame, text="Y").grid(row=4, column=2, sticky="w", padx=(16, 0), pady=(6, 0))
        self.y_entry = ttk.Entry(self.frame, textvariable=self.y_var, width=10)
        self.y_entry.grid(row=4, column=3, sticky="w", padx=(8, 0), pady=(6, 0))
        self.capture_button = ttk.Button(
            self.frame, text="座標を取得",
            command=lambda: self.capture_mouse_position(
                self.x_var, self.y_var, self.capture_button, self.capture_hint,
            ),
        )
        self.capture_button.grid(row=5, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.capture_hint = ttk.Label(
            self.frame, text="※押したあと、画面上の任意の場所を1回クリックすると座標が入ります",
        )
        self.capture_hint.grid(row=6, column=0, columnspan=4, sticky="w", pady=(4, 0))
        self.sync_amount()
        self.sync_coordinates()

    def load(self, action: dict) -> None:
        raw_unit = action.get("unit", UNIT_NOTCH)
        if not isinstance(raw_unit, str):
            unit = ""
        else:
            normalized_unit = raw_unit.strip().lower()
            unit = UNIT_NOTCH if not normalized_unit or normalized_unit == UNIT_NOTCH else (
                UNIT_DELTA if normalized_unit == UNIT_DELTA else ""
            )
        self.unit_var.set(unit)

        raw_direction = action.get("direction")
        direction = raw_direction.strip().lower() if isinstance(raw_direction, str) else ""
        self.direction_var.set(self._DIRECTION_LABELS.get(direction, "下"))

        amount_text = self._parsed_amount(action, unit)
        if "amount" not in action:
            if unit == UNIT_NOTCH:
                self.amount_notch_var.set("")
            elif unit == UNIT_DELTA:
                self.amount_delta_var.set("")
            else:
                self.amount_notch_var.set("")
                self.amount_delta_var.set("")
        else:
            if unit == UNIT_NOTCH:
                self.amount_notch_var.set(amount_text)
            elif unit == UNIT_DELTA:
                self.amount_delta_var.set(amount_text)
            else:
                self.amount_notch_var.set(amount_text)
                self.amount_delta_var.set(amount_text)

        if "x" in action or "y" in action:
            self.coordinates_var.set(True)
            self.x_var.set(self._coordinate_text(action, "x"))
            self.y_var.set(self._coordinate_text(action, "y"))
        else:
            self.coordinates_var.set(False)
            self.x_var.set("")
            self.y_var.set("")
        self.sync_amount()
        self.sync_coordinates()

    def build_action(self, label: str) -> dict:
        unit = self.unit_var.get()
        action = {
            "type": ACTION_TYPE_MOUSE_SCROLL,
            "direction": self._DIRECTION_VALUES.get(self.direction_var.get(), self.direction_var.get()),
            "unit": unit,
            "amount": (self.amount_notch_var if unit == UNIT_NOTCH else self.amount_delta_var).get().strip(),
            "label": label,
        }
        if self.coordinates_var.get():
            action["x"] = self.x_var.get().strip()
            action["y"] = self.y_var.get().strip()
        return action

    def sync_amount(self) -> None:
        unit = self.unit_var.get()
        self.amount_notch_entry.configure(state="disabled" if unit == UNIT_DELTA else "normal")
        self.amount_delta_entry.configure(state="disabled" if unit == UNIT_NOTCH else "normal")

    def sync_coordinates(self, capture_state: str | None = None) -> None:
        if capture_state is not None:
            self._capture_state = capture_state
        enabled = self.coordinates_var.get()
        state = "normal" if enabled else "disabled"
        self.x_entry.configure(state=state)
        self.y_entry.configure(state=state)
        self.capture_button.configure(
            state=self._capture_state if enabled else "disabled",
        )

    @staticmethod
    def _parsed_amount(action: dict, unit: str) -> str:
        candidates = (unit,) if unit else (UNIT_NOTCH, UNIT_DELTA)
        for candidate in candidates:
            parsed = parse_mouse_scroll({
                "type": ACTION_TYPE_MOUSE_SCROLL, "direction": DIRECTIONS[1], "unit": candidate,
                "amount": action.get("amount"),
            })
            if not isinstance(parsed, str):
                return str(parsed.amount)
        return str(action.get("amount"))

    @staticmethod
    def _coordinate_text(action: dict, key: str) -> str:
        if key not in action:
            return ""
        value = action[key]
        try:
            return str(int(value))
        except (TypeError, ValueError, OverflowError):
            return str(value)
