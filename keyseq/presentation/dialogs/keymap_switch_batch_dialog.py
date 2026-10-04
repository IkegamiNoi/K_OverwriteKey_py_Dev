from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Callable

from keyseq.domain.config import normalize_key_name
from keyseq.presentation.controllers.button_width import apply_fixed_button_width
from keyseq.presentation.hook_button_texts import (
    CAPTURE_ACTIVE_TEXT,
    CAPTURE_IDLE_TEXT,
    CAPTURE_TEXTS,
)
from keyseq.presentation.modal import grab_modal
from keyseq.presentation.tk_keys import normalize_tk_keysym

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class KeymapSwitchBatchDialog(tk.Toplevel):
    """複数キーマップのラベルと切替キーをまとめて設定する。"""

    _SCROLL_THRESHOLD = 5
    _SCROLL_HEIGHT = 320

    def __init__(
        self,
        parent: App,
        title: str,
        rows: list[tuple[str, str, str, str]],
        validate: Callable[[list[dict]], tuple[int, str] | None],
    ):
        super().__init__(parent)
        self.parent = parent
        self._validate = validate
        self.title(title)
        self.resizable(False, False)
        self.result: list[dict] | None = None
        self._capturing = False
        self._capture_index: int | None = None
        self._escape_held = False
        self.key_vars: list[tk.StringVar] = []
        self.label_vars: list[tk.StringVar] = []
        self.key_entries: list[ttk.Entry] = []
        self.capture_buttons: list[ttk.Button] = []
        self.label_entries: list[ttk.Entry] = []
        self._row_frames: list[ttk.Frame] = []
        self._rows_frame: ttk.Frame | None = None

        self.parent.hook.suspend_hook_for_dialog(self)

        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)
        single_row = len(rows) == 1
        rows_frame = self._build_rows_area(outer, rows)
        self.hint = ttk.Label(outer, text="例) 切替キー: 1\nラベル: numpad")
        self._build_rows(rows_frame, rows, single_row)
        self.hint.pack(anchor="w", pady=(0, 0))
        self._build_buttons(outer)
        self._bind_dialog_events()
        grab_modal(self, parent, focus=self.label_entries[0] if self.label_entries else None)

    def _build_rows_area(
        self, outer: ttk.Frame, rows: list[tuple[str, str, str, str]]
    ) -> ttk.Frame:
        if len(rows) > self._SCROLL_THRESHOLD:
            body = ttk.Frame(outer)
            body.pack(fill="both", expand=True)
            canvas = tk.Canvas(body, height=self._SCROLL_HEIGHT, highlightthickness=0)
            scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            rows_frame = ttk.Frame(canvas)
            self._rows_frame = rows_frame
            canvas_window = canvas.create_window((0, 0), window=rows_frame, anchor="nw")
            rows_frame.bind(
                "<Configure>",
                lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
                add="+",
            )
            canvas.bind(
                "<Configure>",
                lambda event: canvas.itemconfigure(canvas_window, width=event.width),
                add="+",
            )
            self._canvas = canvas
        else:
            rows_frame = ttk.Frame(outer)
            self._rows_frame = rows_frame
            rows_frame.pack(fill="both", expand=True)
            self._canvas = None
        return rows_frame

    def _build_rows(
        self,
        rows_frame: ttk.Frame,
        rows: list[tuple[str, str, str, str]],
        single_row: bool,
    ) -> None:
        for index, (kind, name, initial_label, initial_key) in enumerate(rows):
            row = ttk.Frame(rows_frame, padding=(0, 0, 0, 10))
            row.pack(fill="x", expand=True)
            self._row_frames.append(row)
            row.grid_columnconfigure(1, weight=1)
            line = 0
            if not single_row:
                ttk.Label(row, text=f"{kind}　{name}").grid(
                    row=line, column=0, columnspan=3, sticky="w", pady=(0, 4)
                )
                line += 1

            ttk.Label(row, text="切替キー").grid(row=line, column=0, sticky="w")
            key_var = tk.StringVar(value=initial_key or "")
            key_entry = ttk.Entry(row, textvariable=key_var, width=24, state="readonly")
            key_entry.grid(row=line, column=1, sticky="we", padx=(8, 0))
            capture_btn = ttk.Button(
                row,
                text=CAPTURE_IDLE_TEXT,
                command=lambda i=index: self._toggle_capture(i),
            )
            apply_fixed_button_width(capture_btn, CAPTURE_TEXTS)
            capture_btn.grid(row=line, column=2, sticky="w", padx=(8, 0))

            line += 1
            ttk.Label(row, text="ラベル").grid(row=line, column=0, sticky="w", pady=(8, 0))
            label_var = tk.StringVar(value=initial_label or "")
            label_entry = ttk.Entry(row, textvariable=label_var, width=42)
            label_entry.grid(
                row=line, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=(8, 0)
            )
            self.key_vars.append(key_var)
            self.label_vars.append(label_var)
            self.key_entries.append(key_entry)
            self.capture_buttons.append(capture_btn)
            self.label_entries.append(label_entry)

    def _build_buttons(self, outer: ttk.Frame) -> None:
        btns = ttk.Frame(outer)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="キャンセル", command=self._cancel).pack(side="right")

    def _bind_dialog_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.bind("<KeyRelease-Escape>", self._on_escape_release)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _ok(self) -> None:
        values = [
            {"key": normalize_key_name(key.get()), "label": (label.get() or "").strip()}
            for key, label in zip(self.key_vars, self.label_vars)
        ]
        error = self._validate(values)
        if error is not None:
            row_index, reason = error
            messagebox.showerror("設定できません", reason, parent=self)
            if 0 <= row_index < len(self.key_entries):
                self._focus_key(row_index)
            return
        self.result = values
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()

    def _on_escape(self, _event=None):
        if self._capturing:
            self._stop_capture()
            self._escape_held = True
            return "break"
        if self._escape_held:
            return "break"
        self._cancel()
        return "break"

    def _on_escape_release(self, _event=None):
        self._escape_held = False

    def _focus_key(self, index: int) -> None:
        if self._canvas is not None:
            row = self._row_frames[index]
            height = max(1, self._rows_frame.winfo_height())
            self._canvas.yview_moveto(max(0, row.winfo_y() / height))
        self.key_entries[index].focus_set()

    def destroy(self) -> None:
        self._stop_capture()
        super().destroy()

    def _toggle_capture(self, index: int) -> None:
        if self._capturing:
            self._stop_capture()
        else:
            self._start_capture(index)

    def _start_capture(self, index: int) -> None:
        self._capturing = True
        self._capture_index = index
        self.capture_buttons[index].configure(text=CAPTURE_ACTIVE_TEXT)
        for label_entry in self.label_entries:
            label_entry.configure(state="disabled")
        self.hint.configure(text="取得中：切替キーにしたいキーを1回押してください（Escでキャンセル）")
        self.capture_buttons[index].focus_set()
        self.bind("<KeyPress>", self._on_capture_keypress, add="+")

    def _stop_capture(self) -> None:
        if not self._capturing:
            return
        self._capturing = False
        index = self._capture_index
        self._capture_index = None
        if index is not None:
            self.capture_buttons[index].configure(text=CAPTURE_IDLE_TEXT)
        for label_entry in self.label_entries:
            label_entry.configure(state="normal")
        self.hint.configure(text="例) 切替キー: 1\nラベル: numpad")
        try:
            self.unbind("<KeyPress>")
        except tk.TclError:
            pass

    def _on_capture_keypress(self, event):
        if not self._capturing or self._capture_index is None:
            return
        if event.keysym == "Escape":
            self._on_escape(event)
            return "break"
        key = normalize_tk_keysym(event.keysym)
        if key in ("ctrl", "shift", "alt", "windows"):
            return "break"
        self.key_vars[self._capture_index].set(key)
        self._stop_capture()
        return "break"
