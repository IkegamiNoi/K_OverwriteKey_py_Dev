from __future__ import annotations

from copy import deepcopy
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Callable

from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.domain.config import normalize_key_name
from keyseq.domain.key_identifiers import is_prohibited_assign_key
from keyseq.presentation.controllers.button_width import apply_fixed_button_width
from keyseq.presentation.dialogs.escape_close import bind_escape_close
from keyseq.presentation.hook_button_texts import (
    CAPTURE_ACTIVE_TEXT,
    CAPTURE_IDLE_TEXT,
    CAPTURE_TEXTS,
    UNKNOWN_CAPTURE_KEY_HINT_TEXT,
)
from keyseq.presentation.key_capture_ime import begin_key_capture, end_key_capture
from keyseq.presentation.modal import grab_modal
from keyseq.presentation.dialogs.grid_editor_window import GridEditorWindow
from keyseq.presentation.tk_keys import (
    is_unresolved_capture_key,
    normalize_tk_key_event,
)

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class KeymapEditDialog(tk.Toplevel):
    """keymap の切替キー + ラベルを編集するダイアログ。"""
    def __init__(
        self,
        parent: App,
        title: str,
        initial_key: str = "",
        initial_label: str = "",
        validate: Callable[[dict], bool] | None = None,
        initial_grid_enabled: bool = False,
        initial_grid: dict | None = None,
        grid_editor_context: Callable[[], tuple[list[MonitorInfo], str, set[str]]] | None = None,
        key_name_from_event: Callable[[object], str] | None = None,
    ):
        super().__init__(parent)
        self.parent = parent
        self._validate = validate
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._capturing = False
        self._grid_draft = deepcopy(initial_grid) if isinstance(initial_grid, dict) else None
        self._grid_editor_context = grid_editor_context
        self._key_name_from_event = key_name_from_event

        self.parent.hook.suspend_hook_for_dialog(self)

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="切替キー").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar(value=initial_key or "")
        self.key_entry = ttk.Entry(frm, textvariable=self.key_var, width=24, state="readonly")
        self.key_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))
        self.capture_btn = ttk.Button(
            frm, text=CAPTURE_IDLE_TEXT, command=self._toggle_capture
        )
        apply_fixed_button_width(self.capture_btn, CAPTURE_TEXTS)
        self.capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.clear_btn = ttk.Button(frm, text="クリア", command=self._clear_key)
        self.clear_btn.grid(row=0, column=3, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="ラベル").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.label_var = tk.StringVar(value=initial_label or "")
        self.label_entry = ttk.Entry(frm, textvariable=self.label_var, width=42)
        self.label_entry.grid(row=1, column=1, columnspan=3, sticky="we", padx=(8, 0), pady=(10, 0))

        self.grid_enabled_var = tk.BooleanVar(value=initial_grid_enabled)
        self.grid_enabled_check = ttk.Checkbutton(frm, text="枠を使う", variable=self.grid_enabled_var)
        editor_columns = 2 if grid_editor_context is not None else 4
        self.grid_enabled_check.grid(row=2, column=0, columnspan=editor_columns, sticky="w", pady=(8, 0))
        if grid_editor_context is not None:
            self.grid_editor_btn = ttk.Button(frm, text="枠を編集…", command=self._edit_grid)
            self.grid_editor_btn.grid(row=2, column=2, columnspan=2, sticky="e", padx=(8, 0))

        self.hint = ttk.Label(frm, text="例) 切替キー: 1\nラベル: numpad")
        self.hint.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=4, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        bind_escape_close(self, is_busy=lambda: getattr(self, "_capturing", False), stop=self._stop_capture)
        grab_modal(self, parent, focus=self.label_entry)

    def _ok(self):
        result = {
            "key": normalize_key_name(self.key_var.get()),
            "label": (self.label_var.get() or "").strip(),
            "grid_enabled": bool(self.grid_enabled_var.get()),
        }
        if self._validate is not None and not self._validate(result):
            self.key_entry.focus_set()
            return
        if self._grid_draft is not None:
            result["grid"] = deepcopy(self._grid_draft)
        self.result = result
        self.destroy()

    def _edit_grid(self) -> None:
        if self._grid_editor_context is None:
            return
        monitors, start_monitor_id, reserved = self._grid_editor_context()
        if not monitors:
            messagebox.showerror("枠を編集できません", "画面（モニタ）を取得できませんでした。", parent=self)
            return
        reserved = set(reserved)
        switch_key = normalize_key_name(self.key_var.get())
        if switch_key:
            reserved.add(switch_key)
        editor = GridEditorWindow(
            self,
            grid=deepcopy(self._grid_draft),
            monitors=monitors,
            start_monitor_id=start_monitor_id,
            reserved=reserved,
            key_name_from_event=self._key_name_from_event,
        )
        editor.wait_window()
        if self.winfo_exists():
            # 編集の窓の破棄で grab は戻るが入力フォーカスは戻らず Esc が届かなくなるため、戻す（focus_set では効かない・probe で確認）。
            self.grid_editor_btn.focus_force()
        if editor.result is not None:
            self._grid_draft = deepcopy(editor.result)

    def destroy(self):
        self._stop_capture()
        super().destroy()

    def _clear_key(self):
        self.key_var.set("")
        self.key_entry.icursor(tk.END)

    def _toggle_capture(self):
        if self._capturing:
            self._stop_capture()
        else:
            self._start_capture()

    def _start_capture(self):
        begin_key_capture(self, self, self._record_key)
        self._capturing = True
        self.capture_btn.configure(text=CAPTURE_ACTIVE_TEXT)
        self.label_entry.configure(state="disabled")
        self.hint.configure(text="取得中：切替キーにしたいキーを1回押してください（Escでキャンセル）")
        self.capture_btn.focus_set()
        self.bind("<KeyPress>", self._on_capture_keypress, add="+")

    def _stop_capture(self):
        if not getattr(self, "_capturing", False):
            return
        self._capturing = False
        end_key_capture(self)
        self.capture_btn.configure(text=CAPTURE_IDLE_TEXT)
        self.label_entry.configure(state="normal")
        self.hint.configure(text="例) 切替キー: 1\nラベル: numpad")
        try:
            self.unbind("<KeyPress>")
        except Exception:
            pass

    def _on_capture_keypress(self, event):
        if not self._capturing:
            return
        key = normalize_tk_key_event(event)
        if is_unresolved_capture_key(key):
            self.hint.configure(text=UNKNOWN_CAPTURE_KEY_HINT_TEXT)
            return "break"
        return self._record_key(key)

    def _record_key(self, key: str) -> str | None:
        if not self._capturing:
            return None
        if (
            key in ("ctrl", "shift", "alt", "windows")
            or is_prohibited_assign_key(key)
        ):
            return "break"
        self.key_var.set(key)
        self.key_entry.icursor(tk.END)
        self._stop_capture()
        return "break"
