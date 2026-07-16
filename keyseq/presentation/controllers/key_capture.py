from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from keyseq.presentation.tk_keys import normalize_tk_keysym


class SingleKeyCaptureController:
    """「単キーを 1 つキャプチャして data に書く」処理の共通実装。

    キャプチャ中はフックを一時停止する（App.suspend_hook_for_dialog / resume_hook_after_dialog）。
    """

    def __init__(
        self,
        app,
        *,
        data_key: str,            # "hook_stop_key" / "hook_toggle_key"
        var: tk.StringVar,
        label: str,               # "停止トリガー" / "トグルキー"
        single_key_example: str,  # "f12" / "f11"
        conflict_checks,          # list[tuple[Callable[[App, str], bool], str]]
    ) -> None:
        self._app = app
        self._data_key = data_key
        self._var = var
        self._entry = None
        self._capture_btn = None
        self._clear_btn = None
        self._label = label
        self._single_key_example = single_key_example
        self._conflict_checks = conflict_checks
        self.capturing = False

    def register_widgets(self, entry, capture_btn, clear_btn) -> None:
        self._entry = entry
        self._capture_btn = capture_btn
        self._clear_btn = clear_btn

    def toggle(self) -> None:
        if self.capturing:
            self.stop(cancel=True)
        else:
            self.start()

    def start(self) -> None:
        """キャプチャ開始（キャプチャ中はフックを一時停止）"""
        self.capturing = True
        if self._capture_btn is not None:
            self._capture_btn.configure(text="取得中…（Escで停止）")
        if self._clear_btn is not None:
            self._clear_btn.configure(state="disabled")

        # キャプチャ中なのでフックを一時停止（開始中なら止まる / 終了時に元に戻る）
        self._app.hook.suspend_hook_for_dialog()

        # フォーカスは表示欄に（入力はしないが、キーを拾いやすくする）
        if self._entry is not None:
            self._entry.focus_set()

        # ルートで拾う
        self._app.bind("<KeyPress>", self.on_keypress, add="+")

    def stop(self, cancel: bool = False) -> None:
        if not self.capturing:
            return
        self.capturing = False
        try:
            self._app.unbind("<KeyPress>")
        except Exception:
            pass

        if self._capture_btn is not None:
            self._capture_btn.configure(text="キー入力で取得")
        if self._clear_btn is not None:
            self._clear_btn.configure(state="normal")

        # 一時停止していたフックを元に戻す
        self._app.hook.resume_hook_after_dialog()

        if cancel:
            return

    def clear(self) -> None:
        """未設定（空）に戻す"""
        if self.capturing:
            self.stop(cancel=True)

        old = str(self._app.data.get(self._data_key, ""))
        self._app.data[self._data_key] = ""
        self._var.set("")
        if old:
            self._app.dirty_tracker.set_dirty(True)

    def on_keypress(self, event):
        """単キーのキャプチャ確定処理"""
        if not self.capturing:
            return

        key = normalize_tk_keysym(event.keysym)

        # Esc はキャンセル
        if key == "esc":
            self.stop(cancel=True)
            return "break"

        # 修飾キー単体は無視
        if key in ("ctrl", "shift", "alt", "windows"):
            return "break"

        # 単キーのみ（ここに来る時点で "+" は入らないが保険）
        if "+" in key:
            messagebox.showerror("設定できません", f"{self._label}は単キーのみ対応です（例: {self._single_key_example}）。")
            return "break"

        # 各種重複禁止（キャプチャ確定時にチェック）
        for check_fn, other_name in self._conflict_checks:
            if check_fn(self._app, key):
                messagebox.showerror("設定できません", f"{self._label}が{other_name}と重複しています:\n{key}")
                return "break"

        # 妥当性チェック
        try:
            self._app.input_gateway.validate_key_name(key)
        except Exception as e:
            messagebox.showerror("設定できません", f"不明なキー名です:\n{key}\n\n{e}")
            return "break"

        # 重複OKならそのまま適用（保存→表示更新）
        self._app.data[self._data_key] = key
        self._var.set(key)
        self._app.dirty_tracker.set_dirty(True)

        # キャプチャ終了（この時点で resume により、元がONなら start_hook が呼ばれる）
        self.stop(cancel=False)
        return "break"
