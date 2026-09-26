from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any


SYSTEM_OPERATIONS = {
    "ループ": "loop_start",
    "カウンター +1": "counter_inc",
    "カウンターを 0 に": "counter_reset",
    "待機": "wait",
    "戻す": "back",
    "先頭へ": "rewind",
}
SYSTEM_LABELS = {operation: label for label, operation in SYSTEM_OPERATIONS.items()}
ENCODINGS = {"UTF-8": "utf-8", "Shift_JIS": "shift_jis"}
OUT_OF_RANGE_VALUES = {
    "エラーで停止": "error",
    "空を送る": "empty",
    "折り返し": "wrap",
}


class ActionControlFields:
    """Build and validate controls for system and file_line actions."""

    def __init__(self, parent: tk.Misc, *, counter_names: list[str], config_root: str,
                 config_service: Any, mode: str | None) -> None:
        self.parent = parent
        self.counter_names = list(counter_names)
        self.config_root = config_root
        self.config_service = config_service
        self.mode = mode
        operation_labels = list(SYSTEM_OPERATIONS)
        if mode == "edit":
            operation_labels.remove("ループ")
        self.system_frame = ttk.LabelFrame(parent, text="system 設定", padding=8)
        self.file_frame = ttk.LabelFrame(parent, text="file_line 設定", padding=8)
        self.system_frame.grid_columnconfigure(1, weight=1)
        self.file_frame.grid_columnconfigure(1, weight=1)

        self.system_op_var = tk.StringVar(value="カウンター +1")
        self.system_op_combo = ttk.Combobox(
            self.system_frame, textvariable=self.system_op_var,
            values=operation_labels, state="readonly", width=20,
        )
        ttk.Label(self.system_frame, text="操作").grid(row=0, column=0, sticky="w")
        self.system_op_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.system_op_combo.bind("<<ComboboxSelected>>", lambda _event: self.sync_system())

        self.loop_count_var = tk.StringVar(value="1")
        self._last_valid_loop_count = 1
        self.loop_count_var.trace_add("write", self._remember_loop_count)
        self.loop_count_label = ttk.Label(self.system_frame, text="回数")
        self.loop_count_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.loop_count_entry = ttk.Entry(self.system_frame, textvariable=self.loop_count_var, width=12)
        self.loop_count_entry.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        self.loop_infinite_var = tk.BooleanVar(value=False)
        self.loop_infinite_check = ttk.Checkbutton(
            self.system_frame, text="無限", variable=self.loop_infinite_var,
            command=self.sync_system,
        )
        self.loop_infinite_check.grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(6, 0))

        self.system_counter_var = tk.StringVar(value="")
        self.system_counter_combo = ttk.Combobox(
            self.system_frame, textvariable=self.system_counter_var,
            values=self.counter_names, state="normal", width=24,
        )
        self.system_counter_label = ttk.Label(self.system_frame, text="カウンター名")
        self.system_counter_label.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.system_counter_combo.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        self.wait_ms_var = tk.StringVar(value="1")
        self.wait_label = ttk.Label(self.system_frame, text="ミリ秒")
        self.wait_label.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.wait_entry = ttk.Entry(self.system_frame, textvariable=self.wait_ms_var, width=12)
        self.wait_entry.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        self.file_path_var = tk.StringVar(value="")
        ttk.Label(self.file_frame, text="ファイル").grid(row=0, column=0, sticky="w")
        self.file_path_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=34)
        self.file_path_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))
        self.browse_button = ttk.Button(self.file_frame, text="参照…", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=(8, 0))

        self.file_counter_var = tk.StringVar(value="")
        ttk.Label(self.file_frame, text="カウンター名").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.file_counter_combo = ttk.Combobox(
            self.file_frame, textvariable=self.file_counter_var,
            values=self.counter_names, state="normal", width=24,
        )
        self.file_counter_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        self.encoding_var = tk.StringVar(value="UTF-8")
        ttk.Label(self.file_frame, text="文字コード").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.encoding_combo = ttk.Combobox(
            self.file_frame, textvariable=self.encoding_var,
            values=list(ENCODINGS), state="readonly", width=18,
        )
        self.encoding_combo.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        self.out_of_range_var = tk.StringVar(value="エラーで停止")
        ttk.Label(self.file_frame, text="範囲外").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.out_of_range_combo = ttk.Combobox(
            self.file_frame, textvariable=self.out_of_range_var,
            values=list(OUT_OF_RANGE_VALUES), state="readonly", width=18,
        )
        self.out_of_range_combo.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        self.sync_system()

    def browse_file(self) -> None:
        selected = filedialog.askopenfilename(parent=self.parent.winfo_toplevel())
        if selected:
            self.file_path_var.set(selected)

    def sync_system(self) -> None:
        op = SYSTEM_OPERATIONS.get(self.system_op_var.get(), "counter_inc")
        self._show(self.loop_count_label, op == "loop_start")
        self._show(self.loop_count_entry, op == "loop_start")
        self._show(self.loop_infinite_check, op == "loop_start")
        self.loop_count_entry.configure(
            state="disabled" if op == "loop_start" and self.loop_infinite_var.get() else "normal"
        )
        counter_op = op in ("counter_inc", "counter_reset")
        self._show(self.system_counter_label, counter_op)
        self._show(self.system_counter_combo, counter_op)
        self._show(self.wait_label, op == "wait")
        self._show(self.wait_entry, op == "wait")

    def _remember_loop_count(self, *_args) -> None:
        try:
            value = int(self.loop_count_var.get().strip())
        except (TypeError, ValueError):
            return
        if value >= 1:
            self._last_valid_loop_count = value

    @staticmethod
    def _show(widget: ttk.Widget, visible: bool) -> None:
        if visible:
            widget.grid()
        else:
            widget.grid_remove()

    def load(self, action: dict[str, Any]) -> None:
        action_type = str(action.get("type", "")).strip().lower()
        if action_type == "system":
            op = str(action.get("op", "")).strip().lower()
            self.system_op_var.set(SYSTEM_LABELS.get(op, "カウンター +1"))
            self.loop_count_var.set(str(action.get("count", 1)))
            self.loop_infinite_var.set(bool(action.get("infinite", False)))
            self.system_counter_var.set(str(action.get("counter", "")))
            self.wait_ms_var.set(str(action.get("ms", 1)))
            self.sync_system()
        elif action_type == "file_line":
            self.file_path_var.set(str(action.get("path", "")))
            self.file_counter_var.set(str(action.get("counter", "")))
            encoding = str(action.get("encoding", "utf-8")).strip().lower()
            self.encoding_var.set(next((label for label, value in ENCODINGS.items() if value == encoding), "UTF-8"))
            out_of_range = str(action.get("out_of_range", "error")).strip().lower()
            self.out_of_range_var.set(next(
                (label for label, value in OUT_OF_RANGE_VALUES.items() if value == out_of_range),
                "エラーで停止",
            ))

    def build_result(self, action_type: str, label: str) -> dict[str, Any] | None:
        if action_type == "system":
            return self._build_system_result(label)
        if action_type == "file_line":
            return self._build_file_result(label)
        return None

    def _build_system_result(self, label: str) -> dict[str, Any] | None:
        op = "loop_start" if self.mode == "edit_loop" else SYSTEM_OPERATIONS.get(self.system_op_var.get())
        if self.mode == "edit" and op == "loop_start":
            op = None
        if op is None:
            messagebox.showerror("入力エラー", "操作が不正です。")
            return None
        result: dict[str, Any] = {"type": "system", "op": op}
        if op == "loop_start":
            return self._build_loop_result(label, result)
        if op in ("counter_inc", "counter_reset"):
            counter = self.system_counter_var.get().strip()
            if not counter:
                messagebox.showerror("入力エラー", "カウンター名が空です。")
                return None
            result.update({"counter": counter, "label": label})
        elif op == "wait":
            try:
                milliseconds = int(self.wait_ms_var.get().strip())
            except (TypeError, ValueError):
                milliseconds = 0
            if milliseconds < 1:
                messagebox.showerror("入力エラー", "ミリ秒は 1 以上の整数で入力してください。")
                return None
            result.update({"ms": milliseconds, "label": label})
        else:
            result["label"] = label
        return result

    def _build_loop_result(self, label: str, result: dict[str, Any]) -> dict[str, Any] | None:
        infinite = bool(self.loop_infinite_var.get())
        try:
            count = int(self.loop_count_var.get().strip())
        except (TypeError, ValueError):
            count = 0
        if count < 1 and not infinite:
            messagebox.showerror("入力エラー", "回数は 1 以上の整数で入力してください。")
            return None
        result.update({
            "count": count if count >= 1 else self._last_valid_loop_count,
            "infinite": infinite, "label": label,
        })
        return result

    def _build_file_result(self, label: str) -> dict[str, Any] | None:
        path = self.file_path_var.get().strip()
        counter = self.file_counter_var.get().strip()
        if not path:
            messagebox.showerror("入力エラー", "ファイルが空です。")
            return None
        if not counter:
            messagebox.showerror("入力エラー", "カウンター名が空です。")
            return None
        stored_path = self.config_service.to_config_relative_or_absolute(path, self.config_root)
        return {
            "type": "file_line", "path": stored_path, "counter": counter,
            "encoding": ENCODINGS.get(self.encoding_var.get(), "utf-8"),
            "out_of_range": OUT_OF_RANGE_VALUES.get(self.out_of_range_var.get(), "error"),
            "label": label,
        }
