from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from pynput import mouse

from keyseq.domain.config import format_preset_list_item, safe_deepcopy, normalize_key_name

if TYPE_CHECKING:
    from keyseq.presentation.app import App

class ActionDialog(tk.Toplevel):
    def __init__(self, parent: App, title: str, initial: dict | None = None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)

        # ダイアログ中のキー操作がフックで実行されないように一時停止
        self.parent.suspend_hook_for_dialog()

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

        ttk.Label(self.mouse_frame, text="X").grid(row=0, column=0, sticky="w")
        self.mouse_x_var = tk.StringVar(value="")
        ttk.Entry(self.mouse_frame, textvariable=self.mouse_x_var, width=10).grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(self.mouse_frame, text="Y").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.mouse_y_var = tk.StringVar(value="")
        ttk.Entry(self.mouse_frame, textvariable=self.mouse_y_var, width=10).grid(row=0, column=3, sticky="w", padx=(8, 0))

        ttk.Label(self.mouse_frame, text="ボタン").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.mouse_btn_var = tk.StringVar(value="left")
        self.mouse_btn_combo = ttk.Combobox(self.mouse_frame, textvariable=self.mouse_btn_var, values=["left", "right", "middle"], state="readonly", width=10)
        self.mouse_btn_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(self.mouse_frame, text="回数").grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        self.mouse_clicks_var = tk.StringVar(value="1")
        ttk.Entry(self.mouse_frame, textvariable=self.mouse_clicks_var, width=10).grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(8, 0))

        self.mouse_capture_btn = ttk.Button(self.mouse_frame, text="クリック位置を取得", command=self._capture_mouse_position)
        self.mouse_capture_btn.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.mouse_hint = ttk.Label(self.mouse_frame, text="※押したあと、画面上の任意の場所を1回クリックすると座標が入ります")
        self.mouse_hint.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

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

        self.value_entry.focus_set()
        self.grab_set()
        self.transient(parent)
        
        self._sync_capture_ui()

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
            self.parent._dialog_result = {"type": "mouse_click", "x": x, "y": y, "button": btn, "clicks": clicks, "label": label}
        self.destroy()

    def _capture_mouse_position(self):
        """次の1クリックで画面座標を取得して X/Y に反映"""
        # 誤爆を避ける：ボタン連打防止
        self.mouse_capture_btn.configure(state="disabled")
        self.mouse_hint.configure(text="…取得中：画面上の任意の場所を1回クリックしてください（右クリックでも可）")

        def on_click(x, y, button, pressed):
            if pressed:
                # 1回目の押下で確定
                try:
                    self.after(0, lambda: self.mouse_x_var.set(str(int(x))))
                    self.after(0, lambda: self.mouse_y_var.set(str(int(y))))
                    self.after(0, lambda: self.mouse_hint.configure(text=f"取得しました: ({int(x)}, {int(y)})"))
                finally:
                    self.after(0, lambda: self.mouse_capture_btn.configure(state="normal"))
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
        if key == "esc":
            self._stop_recording()
            return "break"

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
        k = (keysym or "").lower()
        mapping = {
            "control_l": "ctrl", "control_r": "ctrl",
            "shift_l": "shift", "shift_r": "shift",
            "alt_l": "alt", "alt_r": "alt",
            "super_l": "windows", "super_r": "windows",
            "win_l": "windows", "win_r": "windows",
            "return": "enter",
            "escape": "esc",
            "space": "space",
            "prior": "page up",
            "next": "page down",
            "backspace": "backspace",
            "tab": "tab",
        }
        if k in mapping:
            return mapping[k]
        # F1 などは "f1" になる
        return k

    def destroy(self):
        # 記録中のバインドを剥がす
        self._stop_recording()
        # ダイアログ終了でフックを必要なら再開
        self.parent.resume_hook_after_dialog()
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
                # mouse_click は value を使わないので無効化（ラベルは使う）
                self.value_entry.configure(state="disabled")
            else:
                self.mouse_frame.grid_remove()  # ��\��
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
        PresetManagerDialog(self.parent, title="ホットキープリセット編集").wait_window()
        self._rebuild_preset_buttons()


class PresetManagerDialog(tk.Toplevel):
    """App.data['hotkey_presets'] を編集する"""
    def __init__(self, parent: App, title: str = "プリセット編集"):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)
        
        # 編集中の誤爆防止
        self.parent.suspend_hook_for_dialog()

        self._temp = safe_deepcopy(parent.data.get("hotkey_presets", []))
        if not isinstance(self._temp, list):
            self._temp = []

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="プリセット一覧").grid(row=0, column=0, sticky="w")
        self.listbox = tk.Listbox(frm, height=12, width=56, exportselection=False)
        self.listbox.grid(row=1, column=0, rowspan=6, sticky="nsew", padx=(0, 0))

        # スクロールバー（プリセット一覧）
        presets_sb = ttk.Scrollbar(frm, orient="vertical", command=self.listbox.yview)
        presets_sb.grid(row=1, column=1, rowspan=6, sticky="ns", padx=(6, 10))
        self.listbox.configure(yscrollcommand=presets_sb.set)
        # ダブルクリックで編集
        self.listbox.bind("<Double-Button-1>", self._on_double_click)

        btns = ttk.Frame(frm)
        btns.grid(row=1, column=2, sticky="n")
        ttk.Button(btns, text="追加", width=14, command=self.add).pack(pady=(0, 6))
        ttk.Button(btns, text="編集", width=14, command=self.edit).pack(pady=6)
        ttk.Button(btns, text="削除", width=14, command=self.delete).pack(pady=6)
        ttk.Separator(btns).pack(fill="x", pady=10)
        ttk.Button(btns, text="上へ", width=14, command=lambda: self.move(-1)).pack(pady=6)
        ttk.Button(btns, text="下へ", width=14, command=lambda: self.move(+1)).pack(pady=6)

        bottom = ttk.Frame(frm)
        bottom.grid(row=7, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(bottom, text="OK", command=self.on_ok).pack(side="left", padx=(0, 8))
        ttk.Button(bottom, text="キャンセル", command=self.destroy).pack(side="left")

        frm.grid_columnconfigure(0, weight=1)
        frm.grid_rowconfigure(1, weight=1)

        self._refresh()
        self.grab_set()
        self.transient(parent)

    def _on_double_click(self, _event=None):
        """プリセット一覧をダブルクリックしたら編集を開く"""
        if not self.listbox.curselection():
            return
        self.edit()

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for i, p in enumerate(self._temp):
            self.listbox.insert(tk.END, format_preset_list_item(i, p))

    def _sel(self):
        s = self.listbox.curselection()
        return int(s[0]) if s else None
    
    def _norm_label(self, s: str) -> str:
        return (s or "").strip().lower()

    def _label_exists(self, label: str, exclude_index: int | None = None) -> bool:
        target = self._norm_label(label)
        if not target:
            return False
        for i, p in enumerate(self._temp):
            if exclude_index is not None and i == exclude_index:
                continue
            if self._norm_label(str(p.get("label", ""))) == target:
                return True
        return False

    def add(self):
        dlg = PresetDialog(self, title="プリセット追加")
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return

        value = (res.get("value") or "").strip()
        label = (res.get("label") or "").strip()

        # label 重複チェック（同名プリセット禁止）
        if self._label_exists(label):
            messagebox.showerror("追加できません", f"同名のプリセットが既に存在します。\n\nlabel: {label}")
            return

        # hotkey を検証して不正なら弾く（即時UIエラー）
        err_msg, normalized = self.parent.validate_hotkey(value)
        if err_msg:
            messagebox.showerror("不正なhotkey", f"プリセットの hotkey 値が不正です。\n\n入力: {value}\n理由: {err_msg}")
            return

        self._temp.append({"label": label, "value": normalized})
        self._refresh()
        self.listbox.selection_set(len(self._temp) - 1)

    def edit(self):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        cur = self._temp[idx]
        dlg = PresetDialog(
            self,
            title="プリセット編集",
            initial_value=str(cur.get("value", "")),
            initial_label=str(cur.get("label", "")),
        )
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return

        value = (res.get("value") or "").strip()
        label = (res.get("label") or "").strip()

        # label 重複チェック（自分以外）
        if self._label_exists(label, exclude_index=idx):
            messagebox.showerror("変更できません", f"同名のプリセットが既に存在します。\n\nlabel: {label}")
            return

        # hotkey を検証して不正なら弾く（即時UIエラー）
        err_msg, normalized = self.parent.validate_hotkey(value)
        if err_msg:
            messagebox.showerror("不正なhotkey", f"プリセットの hotkey 値が不正です。\n\n入力: {value}\n理由: {err_msg}")
            return

        self._temp[idx] = {"label": label, "value": normalized}
        self._refresh()
        self.listbox.selection_set(idx)

    def delete(self):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        if messagebox.askyesno("確認", "選択したプリセットを削除しますか？"):
            del self._temp[idx]
            self._refresh()

    def move(self, delta: int):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        j = idx + delta
        if j < 0 or j >= len(self._temp):
            return
        self._temp[idx], self._temp[j] = self._temp[j], self._temp[idx]
        self._refresh()
        self.listbox.selection_set(j)

    def on_ok(self):
        # 保存して閉じる（※保存自体は親の保存ボタンで行う運用）
        self.parent.data["hotkey_presets"] = self._temp
        self.destroy()

    def destroy(self):
        # ダイアログ終了でフックを必要なら再開
        self.parent.resume_hook_after_dialog()
        super().destroy()

class PresetDialog(tk.Toplevel):
    """プリセット（value=hotkey内容, label=表示名）を入力するダイアログ（追加/編集で共通）"""
    def __init__(self, parent, title: str, initial_value: str = "", initial_label: str = ""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="内容（hotkey）").grid(row=0, column=0, sticky="w")
        self.value_var = tk.StringVar(value=initial_value or "")
        self.value_entry = ttk.Entry(frm, textvariable=self.value_var, width=34)
        self.value_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))

        ttk.Label(frm, text="ラベル").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.label_var = tk.StringVar(value=initial_label or "")
        self.label_entry = ttk.Entry(frm, textvariable=self.label_var, width=34)
        self.label_entry.grid(row=1, column=1, sticky="we", padx=(8, 0), pady=(10, 0))

        hint = ttk.Label(frm, text="例）内容: windows+d / ラベル: Win+D（ラベルは重複禁止）")
        hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        self.value_entry.focus_set()
        self.grab_set()
        self.transient(parent)

    def _ok(self):
        value = (self.value_var.get() or "").strip()
        label = (self.label_var.get() or "").strip()
        if not value:
            messagebox.showerror("入力エラー", "内容（hotkey）が空です。")
            return
        if not label:
            messagebox.showerror("入力エラー", "ラベルが空です。")
            return
        self.result = {"value": value, "label": label}
        self.destroy()

class TriggerDialog(tk.Toplevel):
    """トリガーキー + ラベル を入力するダイアログ（追加/変更で共通）"""
    def __init__(self, parent: App, title: str, initial_key: str = "", initial_label: str = ""):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._capturing = False
        
        # 編集中の誤爆防止
        self.parent.suspend_hook_for_dialog()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="トリガー").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar(value=initial_key or "")
        self.key_entry = ttk.Entry(frm, textvariable=self.key_var, width=28)
        self.key_entry.grid(row=0, column=1, sticky="we", padx=(8, 0))
        self.capture_btn = ttk.Button(frm, text="キー入力で取得", command=self._toggle_capture)
        self.capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="ラベル").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.label_var = tk.StringVar(value=initial_label or "")
        self.label_entry = ttk.Entry(frm, textvariable=self.label_var, width=42)
        self.label_entry.grid(row=1, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=(10, 0))

        self.hint = ttk.Label(frm, text="例）トリガー: f1 \n   ラベル: コピー→ウィンドウ切替→貼り付け")
        self.hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=3, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        self.key_entry.focus_set()
        self.grab_set()
        self.transient(parent)

    def _ok(self):
        key = normalize_key_name(self.key_var.get())
        label = (self.label_var.get() or "").strip()
        if not key:
            messagebox.showerror("入力エラー", "トリガーが空です。")
            return
        self.result = {"key": key, "label": label}
        self.destroy()
        
    def destroy(self):
        self._stop_capture()
        # ダイアログ終了でフックを必要なら再開
        self.parent.resume_hook_after_dialog()
        super().destroy()

    def _toggle_capture(self):
        if self._capturing:
            self._stop_capture()
        else:
            self._start_capture()

    def _start_capture(self):
        # 単キーの取得（F1等）を想定。Escでキャンセル。
        self._capturing = True
        self.capture_btn.configure(text="取得中…（Escで停止）")
        self.hint.configure(text="取得中：トリガーにしたいキーを1回押してください（Escでキャンセル）")
        self.key_entry.focus_set()
        # ダイアログ全体で拾う（Entryにフォーカスが無くてもOK）
        self.bind("<KeyPress>", self._on_capture_keypress, add="+")

    def _stop_capture(self):
        if not getattr(self, "_capturing", False):
            return
        self._capturing = False
        self.capture_btn.configure(text="キー入力で取得")
        self.hint.configure(text="例）トリガー: f1 / ラベル: コピー→ウィンドウ切替→貼り")
        try:
            self.unbind("<KeyPress>")
        except Exception:
            pass

    def _on_capture_keypress(self, event):
        if not self._capturing:
            return
        k = self._normalize_tk_key(event.keysym)
        # Escはキャンセル
        if k == "esc":
            self._stop_capture()
            return "break"
        # 修飾キー単体は無視（ctrl/shift/alt/windows）
        if k in ("ctrl", "shift", "alt", "windows"):
            return "break"
        # 取得して終了
        self.key_var.set(k)
        self.key_entry.icursor(tk.END)
        self._stop_capture()
        return "break"

    def _normalize_tk_key(self, keysym: str) -> str:
        # Tkのkeysymを keyboard ライブラリの表記に寄せる（トリガー用）
        k = (keysym or "").lower()
        mapping = {
            "control_l": "ctrl", "control_r": "ctrl",
            "shift_l": "shift", "shift_r": "shift",
            "alt_l": "alt", "alt_r": "alt",
            "super_l": "windows", "super_r": "windows",
            "win_l": "windows", "win_r": "windows",
            "return": "enter",
            "escape": "esc",
            "space": "space",
            "tab": "tab",
            "backspace": "backspace",
            "prior": "page up",
            "next": "page down",
        }
        return mapping.get(k, k)

