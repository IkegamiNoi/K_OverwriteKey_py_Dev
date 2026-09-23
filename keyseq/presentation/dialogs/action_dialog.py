from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from pynput import mouse

from keyseq.domain.config import DEFAULT_DRAG_SPEED_PX_PER_SEC
from keyseq.presentation.dialogs.escape_close import bind_escape_close
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog
from keyseq.presentation.modal import grab_modal
from keyseq.presentation.tk_keys import normalize_tk_keysym

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class ActionDialog(tk.Toplevel):
    def __init__(self, parent: App, title: str, initial: dict | None = None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)

        # ダイアログ中のキー操作がフックで実行されないように一時停止
        self.parent.hook.suspend_hook_for_dialog(self)

        # hotkey 記録用
        self._recording = False
        self._mods_down = set()   # {"ctrl","shift","alt","windows"}
        self._last_nonmod = None  # 直近の非修飾キー

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        # 4列に拡張（値＋ラベルを同じ行に置くため）
        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(3, weight=1)

        ttk.Label(frm, text="種類").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value="hotkey")
        self.type_combo = ttk.Combobox(frm, textvariable=self.type_var, values=["hotkey", "text", "mouse_click"], state="readonly", width=12)
        self.type_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.type_combo.bind("<<ComboboxSelected>>", lambda _e: self._sync_capture_ui())

        ttk.Label(frm, text="値").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.value_var = tk.StringVar(value="")
        self.value_entry = ttk.Entry(frm, textvariable=self.value_var, width=42)
        self.value_entry.grid(row=1, column=1, columnspan=3, sticky="we", padx=(8, 0), pady=(10, 0))

        # hotkey のときだけ「記録」UIを出す
        self.capture_btn = ttk.Button(frm, text="キー入力で記録", command=self._toggle_recording)
        self.capture_btn.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        # ヒントはボタンの右側に置く（行を空けてラベル欄を下へ移すため）
        self.capture_hint = ttk.Label(frm, text="※記録中は、押したキーが hotkey として反映されます（Escで停止）")
        self.capture_hint.grid(row=2, column=2, columnspan=2, sticky="w", padx=(12, 0), pady=(8, 0))

        # シーケンス用ラベル（任意）：キー入力で記録ボタンの1行下へ移動
        ttk.Label(frm, text="ラベル").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.action_label_var = tk.StringVar(value="")
        self.action_label_entry = ttk.Entry(frm, textvariable=self.action_label_var, width=42)
        self.action_label_entry.grid(row=3, column=1, columnspan=3, sticky="we", padx=(8, 0), pady=(6, 0))
        
        # OSショートカット用プリセット（JSONから生成 / hotkeyのときのみ有効）
        self.presets_frame = ttk.LabelFrame(frm, text="OSショートカット（プリセット）", padding=8)
        self.presets_frame.grid(row=4, column=0, columnspan=4, sticky="we", pady=(10, 0))
        self.presets_frame.grid_columnconfigure(0, weight=1)
        self.presets_frame.grid_columnconfigure(1, weight=1)
        self.presets_frame.grid_columnconfigure(2, weight=1)
        self.presets_frame.grid_columnconfigure(3, weight=1)

        self.preset_buttons = []
        self._rebuild_preset_buttons()

        self.preset_edit_btn = ttk.Button(frm, text="プリセット編集…", command=self._open_preset_manager)
        self.preset_edit_btn.grid(row=6, column=0, sticky="w", padx=(8, 0), pady=(14, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=2, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self.on_ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left", padx=(0, 8))

        # mouse_click 用UI（座標/ボタン/回数）
        self.mouse_frame = ttk.LabelFrame(frm, text="マウスクリック設定", padding=8)
        self.mouse_frame.grid(row=5, column=0, columnspan=4, sticky="we", pady=(10, 0))
        self.mouse_frame.grid_columnconfigure(1, weight=1)

        self.mouse_x_label = ttk.Label(self.mouse_frame, text="X")
        self.mouse_x_label.grid(row=0, column=0, sticky="w")
        self.mouse_x_var = tk.StringVar(value="")
        ttk.Entry(self.mouse_frame, textvariable=self.mouse_x_var, width=10).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.mouse_y_label = ttk.Label(self.mouse_frame, text="Y")
        self.mouse_y_label.grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.mouse_y_var = tk.StringVar(value="")
        ttk.Entry(self.mouse_frame, textvariable=self.mouse_y_var, width=10).grid(row=0, column=3, sticky="w", padx=(8, 0))

        ttk.Label(self.mouse_frame, text="ボタン").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.mouse_btn_var = tk.StringVar(value="left")
        self.mouse_btn_combo = ttk.Combobox(self.mouse_frame, textvariable=self.mouse_btn_var, values=["left", "right", "middle"], state="readonly", width=10)
        self.mouse_btn_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(self.mouse_frame, text="回数").grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        self.mouse_clicks_var = tk.StringVar(value="1")
        self.mouse_clicks_entry = ttk.Entry(self.mouse_frame, textvariable=self.mouse_clicks_var, width=10)
        self.mouse_clicks_entry.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(8, 0))

        self.mouse_capture_btn = ttk.Button(self.mouse_frame, text="クリック位置を取得", command=lambda: self._capture_mouse_position(self.mouse_x_var, self.mouse_y_var, self.mouse_capture_btn, self.mouse_hint))
        self.mouse_capture_btn.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.mouse_hint = ttk.Label(self.mouse_frame, text="※押したあと、画面上の任意の場所を1回クリックすると座標が入ります")
        self.mouse_hint.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self._build_drag_ui()

        if initial:
            self.type_var.set((initial.get("type") or "hotkey").strip().lower())
            self.value_var.set(initial.get("value") or "")
            self.action_label_var.set(initial.get("label") or "")
            # mouse_click の初期値
            if (initial.get("type") or "").strip().lower() == "mouse_click":
                if "x" in initial: self.mouse_x_var.set(str(initial.get("x")))
                if "y" in initial: self.mouse_y_var.set(str(initial.get("y")))
                if "button" in initial: self.mouse_btn_var.set(str(initial.get("button")))
                if "clicks" in initial: self.mouse_clicks_var.set(str(initial.get("clicks")))
                if bool(initial.get("drag")):
                    self.mouse_drag_var.set(True)
                    self.mouse_to_x_var.set(str(initial.get("to_x", "")))
                    self.mouse_to_y_var.set(str(initial.get("to_y", "")))
                    self.mouse_drag_speed_var.set(str(initial.get("drag_speed", DEFAULT_DRAG_SPEED_PX_PER_SEC)))

        self._sync_capture_ui()
        bind_escape_close(self, is_busy=lambda: getattr(self, "_recording", False), stop=self._stop_recording)
        grab_modal(self, parent, focus=self.value_entry)

    def on_ok(self):
        t = (self.type_var.get() or "").strip().lower()
        v = self.value_var.get()
        label = (self.action_label_var.get() or "").strip()
        if t not in ("hotkey", "text", "mouse_click"):
            messagebox.showerror("入力エラー", "種類が不正です。")
            return
        if t in ("hotkey", "text"):
            if not v:
                messagebox.showerror("入力エラー", "値が空です。")
                return
            self.parent._dialog_result = {"type": t, "value": v, "label": label}
        else:
            # mouse_click
            sx = self.mouse_x_var.get().strip()
            sy = self.mouse_y_var.get().strip()
            if not sx or not sy:
                messagebox.showerror("入力エラー", "mouse_click の X/Y が空です。")
                return
            try:
                x = int(sx); y = int(sy)
            except Exception:
                messagebox.showerror("入力エラー", "mouse_click の X/Y は整数で入力してください。")
                return
            btn = (self.mouse_btn_var.get() or "left").strip().lower()
            clicks_s = (self.mouse_clicks_var.get() or "1").strip()
            try:
                clicks = int(clicks_s)
            except Exception:
                clicks = 1
            if clicks < 1:
                clicks = 1
            if btn not in ("left", "right", "middle"):
                btn = "left"
            action = {"type": "mouse_click", "x": x, "y": y, "button": btn, "clicks": clicks, "label": label}
            if self.mouse_drag_var.get():
                drag_fields = self._get_drag_fields()
                if drag_fields is None:
                    return
                action.update(drag_fields)
            self.parent._dialog_result = action
        self.destroy()

    def _build_drag_ui(self) -> None:
        self.mouse_drag_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.mouse_frame, text="ドラッグ（範囲選択・ドラッグ&ドロップ）", variable=self.mouse_drag_var, command=self._sync_drag_ui).grid(row=4, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.mouse_to_x_var = tk.StringVar(value="")
        self.mouse_to_y_var = tk.StringVar(value="")
        self.mouse_drag_speed_var = tk.StringVar(value=str(DEFAULT_DRAG_SPEED_PX_PER_SEC))
        self._drag_widgets: list[ttk.Widget] = []
        for text, variable, row, column in (
            ("離す位置 X", self.mouse_to_x_var, 5, 0),
            ("離す位置 Y", self.mouse_to_y_var, 5, 2),
            ("速度（px/秒）", self.mouse_drag_speed_var, 8, 0),
        ):
            label = ttk.Label(self.mouse_frame, text=text)
            label.grid(row=row, column=column, sticky="w", pady=(8, 0))
            entry = ttk.Entry(self.mouse_frame, textvariable=variable, width=10)
            entry.grid(row=row, column=column + 1, sticky="w", padx=(8, 0), pady=(8, 0))
            self._drag_widgets.extend((label, entry))
        self.mouse_to_capture_btn = ttk.Button(self.mouse_frame, text="離す位置を取得", command=lambda: self._capture_mouse_position(self.mouse_to_x_var, self.mouse_to_y_var, self.mouse_to_capture_btn, self.mouse_to_hint))
        self.mouse_to_capture_btn.grid(row=6, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.mouse_to_hint = ttk.Label(self.mouse_frame, text="※押したあと、画面上の任意の場所を1回クリックすると座標が入ります")
        self.mouse_to_hint.grid(row=7, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self._drag_widgets.extend((self.mouse_to_capture_btn, self.mouse_to_hint))
        self._sync_drag_ui()

    def _sync_drag_ui(self) -> None:
        dragging = self.mouse_drag_var.get()
        for widget in self._drag_widgets:
            if dragging:
                widget.grid()
            else:
                widget.grid_remove()
        self.mouse_x_label.configure(text="掴む位置 X" if dragging else "X")
        self.mouse_y_label.configure(text="掴む位置 Y" if dragging else "Y")
        self.mouse_clicks_entry.configure(state="disabled" if dragging else "normal")

    def _get_drag_fields(self) -> dict[str, int | bool] | None:
        sx = self.mouse_to_x_var.get().strip()
        sy = self.mouse_to_y_var.get().strip()
        if not sx or not sy:
            messagebox.showerror("入力エラー", "mouse_click の離す位置 X/Y が空です。")
            return None
        try:
            to_x, to_y = int(sx), int(sy)
        except ValueError:
            messagebox.showerror("入力エラー", "mouse_click の離す位置 X/Y は整数で入力してください。")
            return None
        try:
            speed = int(self.mouse_drag_speed_var.get().strip())
        except ValueError:
            speed = DEFAULT_DRAG_SPEED_PX_PER_SEC
        if speed <= 0:
            speed = DEFAULT_DRAG_SPEED_PX_PER_SEC
        return {"drag": True, "to_x": to_x, "to_y": to_y, "drag_speed": speed, "clicks": 1}

    def _set_mouse_capture_state(self, state: str) -> None:
        self.mouse_capture_btn.configure(state=state)
        self.mouse_to_capture_btn.configure(state=state)

    def _capture_mouse_position(self, x_var: tk.StringVar, y_var: tk.StringVar,
                                button_widget: ttk.Button, hint_widget: ttk.Label) -> None:
        """次の1クリックで画面座標を取得して X/Y に反映"""
        # 誤爆を避ける：ボタン連打防止
        if button_widget.instate(["disabled"]):
            return
        self._set_mouse_capture_state("disabled")
        hint_widget.configure(text="…取得中：画面上の任意の場所を1回クリックしてください（右クリックでも可）")

        def on_click(x: float, y: float, button: mouse.Button, pressed: bool) -> bool:
            if pressed:
                # 1回目の押下で確定
                try:
                    self.after(0, lambda: x_var.set(str(int(x))))
                    self.after(0, lambda: y_var.set(str(int(y))))
                    self.after(0, lambda: hint_widget.configure(text=f"取得しました: ({int(x)}, {int(y)})"))
                finally:
                    self.after(0, lambda: self._set_mouse_capture_state("normal"))
                return False  # stop listener
            return True

        # listener は別スレッドで動く
        listener = mouse.Listener(on_click=on_click)
        listener.daemon = True
        listener.start()

    def _toggle_recording(self):
        t = (self.type_var.get() or "").strip().lower()
        if t != "hotkey":
            return
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._recording = True
        self._mods_down.clear()
        self._last_nonmod = None
        self.capture_btn.configure(text="記録停止")
        # 記録モード中は Entry にフォーカスしておく（表示を分かりやすく）
        self.value_entry.focus_set()
        # キーイベントは dialog 全体で拾う（Entry 以外をクリックしても記録できる）
        self.bind("<KeyPress>", self._on_key_press, add="+")
        self.bind("<KeyRelease>", self._on_key_release, add="+")

    def _stop_recording(self):
        if not getattr(self, "_recording", False):
            return
        self._recording = False
        self.capture_btn.configure(text="キー入力で記録")
        try:
            self.unbind("<KeyPress>")
            self.unbind("<KeyRelease>")
        except Exception:
            pass

    def _on_key_press(self, event):
        if not self._recording:
            return
        key = self._normalize_tk_key(event.keysym)
        if key in ("ctrl", "shift", "alt", "windows"):
            self._mods_down.add(key)
            # 修飾キーだけでは確定しない
            self._update_hotkey_preview()
            return "break"

        # 非修飾キー：ここで確定（ctrl+tab など）
        self._last_nonmod = key
        self._update_hotkey_preview(finalize=True)
        # 1回の組み合わせを取ったら自動で記録を止める（好みで外せる）
        self._stop_recording()
        return "break"

    def _on_key_release(self, event):
        if not self._recording:
            return
        key = self._normalize_tk_key(event.keysym)
        if key in self._mods_down:
            self._mods_down.discard(key)
            self._update_hotkey_preview()
            return "break"

    def _update_hotkey_preview(self, finalize: bool = False):
        # 表示順を固定（keyboard の表記に寄せる）
        order = ["ctrl", "alt", "shift", "windows"]
        mods = [m for m in order if m in self._mods_down]
        parts = mods[:]
        if self._last_nonmod:
            parts.append(self._last_nonmod)
        if not parts:
            return
        self.value_var.set("+".join(parts))
        if finalize:
            self.value_entry.icursor(tk.END)

    def _normalize_tk_key(self, keysym: str) -> str:
        # Tk の keysym を keyboard ライブラリで使う表記に寄せる
        return normalize_tk_keysym(keysym)

    def destroy(self):
        # 記録中のバインドを剥がす
        self._stop_recording()
        super().destroy()

    def _sync_capture_ui(self):
        t = (self.type_var.get() or "").strip().lower()
        is_hotkey = (t == "hotkey")
        if not is_hotkey:
            # text のときは記録UIを無効化し、記録も止める
            self._stop_recording()
            self.capture_btn.configure(state="disabled", text="キー入力で記録")
            self.capture_hint.configure(text="※text は通常の文字入力です（記録は hotkey のみ）")
            # プリセットも無効化
            for b in getattr(self, "preset_buttons", []):
                b.configure(state="disabled")
            if hasattr(self, "preset_edit_btn"):
                self.preset_edit_btn.configure(state="disabled")
        else:
            self.capture_btn.configure(state="normal")
            self.capture_hint.configure(text="※記録中は、押したキーが hotkey として反映されます（Escで停止）")
            for b in getattr(self, "preset_buttons", []):
                b.configure(state="normal")
            if hasattr(self, "preset_edit_btn"):
                self.preset_edit_btn.configure(state="normal")
                
        # mouse_click UI の表示制御
        if hasattr(self, "mouse_frame"):
            if t == "mouse_click":
                self.mouse_frame.grid()  # 表示
                self._sync_drag_ui()
                # mouse_click は value を使わないので無効化（ラベルは使う）
                self.value_entry.configure(state="disabled")
            else:
                self.mouse_frame.grid_remove()  # 非表示
                self.value_entry.configure(state="normal")

    def _apply_preset(self, hotkey: str):
        """プリセットボタンで hotkey を値欄にセット"""
        self.value_var.set(hotkey)
        self.value_entry.focus_set()
        self.value_entry.icursor(tk.END)

    def _rebuild_preset_buttons(self):
        """親の data['hotkey_presets'] からプリセットボタンを作り直す"""
        # 既存を破棄
        for b in getattr(self, "preset_buttons", []):
            try:
                b.destroy()
            except Exception:
                pass
        self.preset_buttons = []

        presets = self.parent.data.get("hotkey_presets", [])
        if not isinstance(presets, list):
            presets = []

        # 4列で並べる
        cols = 4
        r = 0
        c = 0
        for p in presets:
            label = str(p.get("label", "")).strip()
            value = str(p.get("value", "")).strip()
            if not label or not value:
                continue
            b = ttk.Button(self.presets_frame, text=label, command=lambda hk=value: self._apply_preset(hk))
            b.grid(row=r, column=c, padx=4, pady=4, sticky="we")
            self.preset_buttons.append(b)
            c += 1
            if c >= cols:
                c = 0
                r += 1

        # 現在のタイプに応じて enable/disable
        self._sync_capture_ui()

    def _open_preset_manager(self):
        """プリセット編集ダイアログを開き、戻ったらボタンを再生成"""
        PresetManagerDialog(self.parent, title="ホットキープリセット編集", transient_parent=self).wait_window()
        self._rebuild_preset_buttons()
