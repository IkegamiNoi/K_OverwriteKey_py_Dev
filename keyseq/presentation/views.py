from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import TYPE_CHECKING

from pynput import mouse

from keyseq.presentation.dialogs import PresetManagerDialog

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FullView(ttk.Frame):
    """フル画面UI"""
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        # header
        self.header_area = ttk.Frame(self, padding=0)
        self.header_area.pack(fill="x", expand=False, pady=(12, 0))

        # フックラベルフレーム
        self.hook_frame = ttk.LabelFrame(self.header_area, text="フック", padding=10)
        self.hook_frame.pack(side="left", fill="y")
        
        # フックラベルフレーム1行目
        self.full_hook_line1 = ttk.Frame(self.hook_frame)
        self.full_hook_line1.pack(side="top", fill="x")
        app.hook_toggle_btn = ttk.Button(self.full_hook_line1, text="開始（フックON）", command=app.toggle_hook)
        app.trigger_toggle_btn = ttk.Button(self.full_hook_line1, text="通常トリガー無効化", command=app.toggle_triggers_enabled, state="disabled")
        app.hook_toggle_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        app.trigger_toggle_btn.grid(row=0, column=1, padx=(8, 0), sticky="w")
        
        # フックラベルフレーム2行目
        self.full_hook_line2 = ttk.Frame(self.hook_frame)
        self.full_hook_line2.pack(side="top", fill="x")
        # フック停止トリガー（フル：取得/クリアあり）
        ttk.Label(self.full_hook_line2, text="フック停止トリガー: ").grid(row=0, column=0, sticky="w")
        app.stop_key_entry = ttk.Entry(self.full_hook_line2, textvariable=app.stop_key_var, width=8, state="readonly")
        app.stop_key_entry.grid(row=0, column=1, sticky="w", padx=(0, 0))
        app.stop_key_capture_btn = ttk.Button(self.full_hook_line2, text="キー入力で取得", command=app._toggle_stop_key_capture)
        app.stop_key_capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))
        app.stop_key_clear_btn = ttk.Button(self.full_hook_line2, text="クリア", command=app.clear_stop_key)
        app.stop_key_clear_btn.grid(row=0, column=3, sticky="w", padx=(8, 0))

        # 通常トリガー有効/無効トグルキー（フル：取得/クリアあり）
        ttk.Label(self.full_hook_line2, text="有効/無効トグルキー: ").grid(row=1, column=0, sticky="w")
        app.toggle_key_entry = ttk.Entry(self.full_hook_line2, textvariable=app.toggle_key_var, width=8, state="readonly")
        app.toggle_key_entry.grid(row=1, column=1, sticky="w", padx=(0, 0))
        app.toggle_key_capture_btn = ttk.Button(self.full_hook_line2, text="キー入力で取得", command=app._toggle_toggle_key_capture)
        app.toggle_key_capture_btn.grid(row=1, column=2, sticky="w", padx=(8, 0))
        app.toggle_key_clear_btn = ttk.Button(self.full_hook_line2, text="クリア", command=app.clear_toggle_key)
        app.toggle_key_clear_btn.grid(row=1, column=3, sticky="w", padx=(8, 0))

        ttk.Label(self.hook_frame, textvariable=app.status_var).pack(side="top")
        # 表示ラベルフレーム
        self.display_frame = ttk.LabelFrame(self.header_area, text="表示", padding=(10, 6))
        self.display_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))
        app.topmost_chk = ttk.Checkbutton(
            self.display_frame,
            text="常に手前",
            variable=app.always_on_top_var,
            command=app._apply_always_on_top,
        )
        app.topmost_chk.grid(row=0, column=0, sticky="w")
        # 省略表示へ
        app.compact_btn = ttk.Button(self.display_frame, text="省略表示", command=app.show_compact_view)
        app.compact_btn.grid(row=1, column=0, sticky="w", pady=(10, 0))

        # main
        self.main_area = ttk.Frame(self)
        self.main_area.pack(fill="both", expand=True, pady=(12, 0))

        self.trigger_box = ttk.LabelFrame(self.main_area, text="トリガー一覧（選択して編集）", padding=10)
        self.trigger_box.pack(side="left", fill="y")

        # トリガー一覧（スクロール）
        tl_frame = ttk.Frame(self.trigger_box)
        tl_frame.pack(side="top", fill="y", expand=False)
        self.trigger_list = tk.Listbox(tl_frame, height=12, width=26, exportselection=False)
        self.trigger_list.pack(side="left", fill="y", expand=False)
        sb = ttk.Scrollbar(tl_frame, orient="vertical", command=self.trigger_list.yview)
        sb.pack(side="left", fill="y")
        self.trigger_list.configure(yscrollcommand=sb.set)
        self.trigger_list.bind("<<ListboxSelect>>", lambda _e: app._set_selected_trigger_index(self._cur_sel_or(app._selected_trigger_idx)))
        self.trigger_list.bind("<Double-Button-1>", app._on_trigger_double_click)

        tbtns = ttk.Frame(self.trigger_box)
        tbtns.pack(fill="x", pady=(6, 0))
        ttk.Button(tbtns, text="追加", command=app.add_trigger).pack(fill="x", pady=(0, 3))
        ttk.Button(tbtns, text="トリガー変更", command=app.rename_trigger).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="削除", command=app.delete_trigger).pack(fill="x", pady=3)

        app.suppress_chk = ttk.Checkbutton(
            self.trigger_box,
            text="トリガーキーを抑止（suppress）",
            variable=app.suppress_var,
            command=app.update_suppress,
        )
        app.suppress_chk.pack(anchor="w", pady=(6, 0))

        self.sequence_box = ttk.LabelFrame(self.main_area, text="出力シーケンス（選択中トリガーの内容）", padding=10)
        self.sequence_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.action_list = tk.Listbox(self.sequence_box, height=18, exportselection=False)
        self.action_list.pack(side="left", fill="both", expand=True)
        self.action_list.bind("<<ListboxSelect>>", app._on_action_list_select)
        self.action_list.bind("<Double-Button-1>", app._on_action_double_click)
        asb = ttk.Scrollbar(self.sequence_box, orient="vertical", command=self.action_list.yview)
        asb.pack(side="left", fill="y")
        self.action_list.configure(yscrollcommand=asb.set)

        abtns = ttk.Frame(self.sequence_box)
        abtns.pack(side="left", fill="y", padx=(12, 0))
        ttk.Button(abtns, text="追加", width=16, command=app.add_action).pack(pady=(0, 6))
        ttk.Button(abtns, text="編集", width=16, command=app.edit_action).pack(pady=6)
        ttk.Button(abtns, text="削除", width=16, command=app.delete_action).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="上へ", width=16, command=lambda: app.move_action(-1)).pack(pady=6)
        ttk.Button(abtns, text="下へ", width=16, command=lambda: app.move_action(+1)).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        # 連続実行（run_to_end）
        app.run_to_end_chk = ttk.Checkbutton(
            abtns,
            text="連続実行",
            variable=app.run_to_end_var,
            command=app.update_run_to_end,
        )
        app.run_to_end_chk.pack(anchor="w", pady=(8, 0))

        # 連続実行 間隔（ms） ※トリガーごと / デフォルト300
        delay_line = ttk.Frame(abtns)
        delay_line.pack(fill="x", pady=(6, 0))
        ttk.Label(delay_line, text="間隔(ms)").pack(side="left")
        app.run_to_end_delay_entry = ttk.Entry(delay_line, width=8, textvariable=app.run_to_end_delay_var)
        app.run_to_end_delay_entry.pack(side="left", padx=(8, 0))
        # Enter / フォーカスアウトで保存
        app.run_to_end_delay_entry.bind("<Return>", app.update_run_to_end_delay)
        app.run_to_end_delay_entry.bind("<FocusOut>", app.update_run_to_end_delay)

        # footer
        self.footer_area = ttk.Frame(self)
        self.footer_area.pack(fill="x", pady=(12, 0))
        ttk.Button(self.footer_area, text="保存", command=app.save_config).pack(side="left")
        ttk.Button(self.footer_area, text="別名で保存…", command=app.save_as).pack(side="left", padx=(8, 0))
        ttk.Button(self.footer_area, text="読込…", command=app.load_from).pack(side="left", padx=(8, 0))
        ttk.Button(self.footer_area, text="プリセット編集…", command=app.open_preset_manager).pack(side="left", padx=(8, 0))
        ttk.Button(self.footer_area, text="起動時に読むJSONを指定…", command=app.set_startup_config).pack(side="left", padx=(8, 0))
        ttk.Button(self.footer_area, text="例を復元", command=app.restore_default).pack(side="right")

    def _cur_sel_or(self, default_idx: int) -> int:
        try:
            s = self.trigger_list.curselection()
            return int(s[0]) if s else int(default_idx)
        except Exception:
            return int(default_idx)


class CompactView(ttk.Frame):
    """省略画面UI（開始/停止、通常トリガーON/OFF、制御キー表示、ステータス、常に手前、フル復帰、トリガー一覧）"""
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        # 縦並びで “トリガー一覧程度の幅” を想定（geometryはApp側で調整）
        self.header_area = ttk.Frame(self, padding=0)
        self.header_area.pack(fill="x", expand=False, pady=(12, 0))

        # フックラベルフレーム
        self.hook_frame = ttk.LabelFrame(self.header_area, text="フック", padding=10)
        self.hook_frame.pack(side="top", fill="x", expand=False)

        # フックラベルフレーム1行目
        self.compact_hook_line1 = ttk.Frame(self.hook_frame)
        self.compact_hook_line1.pack(side="top", fill="x")
        # 開始/停止（Appの同名メソッドを呼ぶ。ウィジェットは別物でOK）
        self.hook_toggle_btn = ttk.Button(self.compact_hook_line1, text="開始（フックON）", command=app.toggle_hook)
        self.trigger_toggle_btn = ttk.Button(self.compact_hook_line1, text="通常トリガー無効化", command=app.toggle_triggers_enabled, state="disabled")
        self.hook_toggle_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.trigger_toggle_btn.grid(row=0, column=1, padx=(8, 0), sticky="w")
        # App側でも参照できるように保持（フック開始/停止時のstate同期用）
        app.compact_hook_toggle_btn = self.hook_toggle_btn
        app.compact_trigger_toggle_btn = self.trigger_toggle_btn
        
        # フックラベルフレーム2行目
        self.compact_hook_line2 = ttk.Frame(self.hook_frame)
        self.compact_hook_line2.pack(side="top", fill="x")
        # 停止トリガー表示のみ（Entryだけ）
        ttk.Label(self.compact_hook_line2, text="フック停止トリガー: ").grid(row=0, column=0, sticky="w")
        self.stop_key_entry = ttk.Entry(self.compact_hook_line2, textvariable=app.stop_key_var, width=8, state="readonly")
        self.stop_key_entry.grid(row=0, column=1, sticky="w")

        # トグルキー表示のみ（Entryだけ）
        ttk.Label(self.compact_hook_line2, text="有効/無効トグルキー: ").grid(row=1, column=0, sticky="w")
        self.toggle_key_entry = ttk.Entry(self.compact_hook_line2, textvariable=app.toggle_key_var, width=8, state="readonly")
        self.toggle_key_entry.grid(row=1, column=1, sticky="w")

        ttk.Label(self.hook_frame, textvariable=app.status_var).pack(side="top", fill="x")

        self.display_frame = ttk.LabelFrame(self.header_area, text="表示", padding=(10, 6))
        self.display_frame.pack(side="top", fill="x", expand=False, pady=(8, 0))
        app.topmost_chk = ttk.Checkbutton(
            self.display_frame,
            text="常に手前",
            variable=app.always_on_top_var,
            command=app._apply_always_on_top,
        )
        app.topmost_chk.grid(row=0, column=0, sticky="w")
        self.full_btn = ttk.Button(self.display_frame, text="フルに戻す", command=app.show_full_view)
        self.full_btn.grid(row=1, column=0, sticky="w", pady=(10, 0))

        # トリガー一覧のみ
        self.main_area = ttk.Frame(self)
        self.main_area.pack(fill="both", expand=True, pady=(12, 0))
        self.trigger_box = ttk.LabelFrame(self.main_area, text="トリガー一覧", padding=10)
        self.trigger_box.pack(side="top", fill="both", expand=True)

        tl_frame = ttk.Frame(self.trigger_box)
        tl_frame.pack(side="top", fill="both", expand=True)
        self.trigger_list = tk.Listbox(tl_frame, height=16, width=26, exportselection=False)
        self.trigger_list.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tl_frame, orient="vertical", command=self.trigger_list.yview)
        sb.pack(side="left", fill="y")
        self.trigger_list.configure(yscrollcommand=sb.set)
        self.trigger_list.bind("<<ListboxSelect>>", lambda _e: app._set_selected_trigger_index(self._cur_sel_or(app._selected_trigger_idx)))
        self.trigger_list.bind("<Double-Button-1>", app._on_trigger_double_click)

    def _cur_sel_or(self, default_idx: int) -> int:
        try:
            s = self.trigger_list.curselection()
            return int(s[0]) if s else int(default_idx)
        except Exception:
            return int(default_idx)

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

        self.preset_edit_btn = ttk.Button(frm, text="プリセット編集…c", command=self._open_preset_manager)
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
            # mouse_click �̏����l
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
        PresetManagerDialog(self.parent, title="ホットキープリセット編集").wait_window()
        self._rebuild_preset_buttons()
