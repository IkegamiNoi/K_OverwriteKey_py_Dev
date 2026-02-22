import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# グローバルキーボードフック/送信
# pip install keyboard
import keyboard
# マウス操作
# pip install pyautogui pynput
import pyautogui
from pynput import mouse


DEFAULT_CONFIG = {
    "triggers": [
        {
            "key": "f1",
            "suppress": True,
            "label": "",
            "actions": [
                {"type": "hotkey", "value": "ctrl+c"},
                {"type": "hotkey", "value": "alt+tab"},
                {"type": "hotkey", "value": "ctrl+tab"},
                {"type": "hotkey", "value": "ctrl+c"},
                {"type": "hotkey", "value": "f2"},
                {"type": "text", "value": "テストネーム"},
            ],
        },
        {
            "key": "f2",
            "suppress": True,
            "label": "",
            "actions": [
                {"type": "text", "value": "F2のシーケンス 1"},
                {"type": "hotkey", "value": "ctrl+v"},
            ],
        },
    ],
    "hotkey_presets": [
        {"label": "Alt+Tab", "value": "alt+tab"},
        {"label": "Win+D", "value": "windows+d"},
        {"label": "Win+E", "value": "windows+e"},
        {"label": "Ctrl+Shift+Esc", "value": "ctrl+shift+esc"},
        {"label": "Win+R", "value": "windows+r"},
        {"label": "Win+Tab", "value": "windows+tab"},
        {"label": "Win+X", "value": "windows+x"},
        {"label": "Alt+F4", "value": "alt+f4"}
    ]
}


def normalize_key_name(s: str) -> str:
    return (s or "").strip().lower()


def safe_deepcopy(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Key Replacer Sequencer (Multi Trigger)")
        self.geometry("980x560")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, r"settings\config.json")  # 実際に読込/保存する本体JSON（既定）
        self.startup_path = os.path.join(self.base_dir, r"settings\startup.json")  # 起動時に参照する“外部指定”ファイル
        self.data = safe_deepcopy(DEFAULT_CONFIG)

        self.hook_active = False
        self._hook_handles = {}     # key -> hook_handle
        # ダイアログのネストに対応するためカウンタ方式にする
        self._hook_suspend_count = 0
        self._hook_was_active_before_dialog = False
        self._lock = threading.Lock()
        self._indices = {}          # key -> next index
        self._reentry_guard = set() # keys currently sending (prevent recursion)
        self._programmatic_action_select = False  # action_list選択をコード側で変更中か
        self._error_dialog_open = False           # エラーダイアログ多重表示防止
 
        self._build_ui()
        #self._load_if_exists()
        self._load_startup_and_config()
        self._refresh_triggers()
        self._refresh_actions()
        self._update_status()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- Hook suspend/resume for modal dialogs ----------------
    def suspend_hook_for_dialog(self):
        """編集系ダイアログ表示中の誤爆を防ぐため、フックを一時停止（ネスト対応）"""
        self._hook_suspend_count += 1
        if self._hook_suspend_count == 1:
            self._hook_was_active_before_dialog = bool(self.hook_active)
            if self._hook_was_active_before_dialog:
                self.stop_hook()

    def resume_hook_after_dialog(self):
        """一時停止したフックを元に戻す（ネスト対応。最後のダイアログが閉じた時だけ復帰）"""
        if self._hook_suspend_count <= 0:
            self._hook_suspend_count = 0
            return
        self._hook_suspend_count -= 1
        if self._hook_suspend_count == 0:
            was_on = self._hook_was_active_before_dialog
            self._hook_was_active_before_dialog = False
            if was_on:
                self.start_hook()

    # ---------------- UI ----------------
    def _build_ui(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        # 上段：フック操作
        top = ttk.LabelFrame(outer, text="フック", padding=10)
        top.pack(fill="x")

        self.start_btn = ttk.Button(top, text="開始（フックON）", command=self.start_hook)
        self.stop_btn = ttk.Button(top, text="停止（フックOFF）", command=self.stop_hook, state="disabled")
        self.start_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.stop_btn.grid(row=0, column=1, sticky="w")

        self.status_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.status_var).grid(row=1, column=0, columnspan=6, sticky="w", pady=(8, 0))

        # 中段：左=トリガー一覧 / 右=アクション
        mid = ttk.Frame(outer)
        mid.pack(fill="both", expand=True, pady=(12, 0))

        left = ttk.LabelFrame(mid, text="トリガー一覧（選択して編集）", padding=10)
        left.pack(side="left", fill="y")

        self.trigger_list = tk.Listbox(left, height=12, width=22, exportselection=False)
        self.trigger_list.pack(side="top", fill="y", expand=False)
        self.trigger_list.bind("<<ListboxSelect>>", lambda _e: self._refresh_actions())
        # ダブルクリックで「トリガー変更」（= rename_trigger）を開く
        self.trigger_list.bind("<Double-Button-1>", self._on_trigger_double_click)

        tbtns = ttk.Frame(left)
        tbtns.pack(fill="x", pady=(10, 0))
        ttk.Button(tbtns, text="追加", command=self.add_trigger).pack(fill="x", pady=(0, 6))
        ttk.Button(tbtns, text="トリガー変更", command=self.rename_trigger).pack(fill="x", pady=6)
        ttk.Button(tbtns, text="削除", command=self.delete_trigger).pack(fill="x", pady=6)

        self.suppress_var = tk.BooleanVar(value=True)
        self.suppress_chk = ttk.Checkbutton(left, text="トリガーキーを抑止（suppress）", variable=self.suppress_var, command=self.update_suppress)
        self.suppress_chk.pack(anchor="w", pady=(10, 0))

        right = ttk.LabelFrame(mid, text="出力シーケンス（選択中トリガーの内容）", padding=10)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.action_list = tk.Listbox(right, height=18, exportselection=False)
        self.action_list.pack(side="left", fill="both", expand=True)
        # ユーザーがシーケンス一覧の選択を変えたら「次に実行」をその位置に変更
        self.action_list.bind("<<ListboxSelect>>", self._on_action_list_select)
        # ダブルクリックで編集
        self.action_list.bind("<Double-Button-1>", self._on_action_double_click)

        sb = ttk.Scrollbar(right, orient="vertical", command=self.action_list.yview)
        sb.pack(side="left", fill="y")
        self.action_list.configure(yscrollcommand=sb.set)

        abtns = ttk.Frame(right)
        abtns.pack(side="left", fill="y", padx=(12, 0))
        ttk.Button(abtns, text="追加", width=16, command=self.add_action).pack(pady=(0, 6))
        ttk.Button(abtns, text="編集", width=16, command=self.edit_action).pack(pady=6)
        ttk.Button(abtns, text="削除", width=16, command=self.delete_action).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="上へ", width=16, command=lambda: self.move_action(-1)).pack(pady=6)
        ttk.Button(abtns, text="下へ", width=16, command=lambda: self.move_action(+1)).pack(pady=6)

        # 下段：保存/読込
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="保存（config.json）", command=self.save_config).pack(side="left")
        ttk.Button(bottom, text="別名で保存…", command=self.save_as).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="読込…", command=self.load_from).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="プリセット編集…", command=self.open_preset_manager).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="起動時に読むJSONを指定…", command=self.set_startup_config).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="例を復元", command=self.restore_default).pack(side="right")

    # ---------------- Startup config ----------------
    def _load_startup_and_config(self):
        """
        startup.json があればそれを読み、そこに書かれた config_path を起動時に読み込む。
        無い場合は従来通り self.config_path（= ./config.json）を読み込む。
        """
        # まず既定パス（./config.json）をセットした状態で、startup.json を見に行く
        startup = None
        if os.path.exists(self.startup_path):
            try:
                with open(self.startup_path, "r", encoding="utf-8") as f:
                    startup = json.load(f)
            except Exception as e:
                messagebox.showwarning("startup.json 読込失敗", f"startup.json の読込に失敗しました。\n{e}\n\n既定の config.json を読み込みます。")

        if isinstance(startup, dict):
            cfg = startup.get("config_path")
            prompt_if_missing = bool(startup.get("prompt_if_missing", True))
            if cfg:
                # 相対パスはアプリフォルダ基準にする
                cfg_path = cfg
                if not os.path.isabs(cfg_path):
                    cfg_path = os.path.join(self.base_dir, cfg_path)
                if os.path.exists(cfg_path):
                    self.config_path = cfg_path
                else:
                    # 指定先が無い
                    if prompt_if_missing:
                        picked = filedialog.askopenfilename(
                            title="起動時に読み込むJSONが見つかりません。別のJSONを選択してください。",
                            filetypes=[("JSON", "*.json"), ("All", "*.*")]
                        )
                        if picked:
                            self.config_path = picked
                            # startup.json を更新して次回も同じに
                            self._write_startup({"config_path": self._to_rel_if_possible(picked), "prompt_if_missing": True})
                    # promptしない場合は既定の config.json にフォールバック

        # 最終的に決まった self.config_path を読み込む（従来のロジックへ）
        self._load_if_exists()

    def _write_startup(self, data: dict):
        try:
            with open(self.startup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("startup.json 保存失敗", str(e))

    def _to_rel_if_possible(self, path: str) -> str:
        """base_dir 配下なら相対パスで保存（持ち運びしやすくする）"""
        try:
            rel = os.path.relpath(path, self.base_dir)
            # ".." を含むなら無理に相対化しない
            if rel.startswith(".."):
                return path
            return rel
        except Exception:
            return path

    def set_startup_config(self):
        """ユーザーが起動時に読み込む本体JSON（出力シーケンス）を選び、startup.json に保存する"""
        path = filedialog.askopenfilename(
            title="起動時に読み込むJSONを選択",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        self.config_path = path
        self._write_startup({"config_path": self._to_rel_if_possible(path), "prompt_if_missing": True})
        # その場で読み込みも反映
        self._load_if_exists()
        self._indices = {}
        self._refresh_triggers()
        self._refresh_actions()
        messagebox.showinfo("設定", f"次回起動時はこのJSONを読み込みます:\n{path}")

    def _update_status(self):
        state = "ON" if self.hook_active else "OFF"
        triggers = self.data.get("triggers", [])
        keys = [normalize_key_name(t.get("key", "")) for t in triggers if t.get("key")]
        keys_text = ", ".join(keys) if keys else "(未設定)"
        sel_key = self._selected_trigger_key() or "(未選択)"
        next_i = self._indices.get(sel_key, 0) + 1 if sel_key in self._indices else 0
        self.status_var.set(f"フック: {state} / トリガー: {keys_text} / 選択中: {sel_key} / 選択中の次: {next_i}")

    def _refresh_triggers(self):
        self.trigger_list.delete(0, tk.END)
        triggers = self.data.get("triggers", [])
        for i, t in enumerate(triggers):
            k = normalize_key_name(t.get("key", ""))
            label = (t.get("label") or "").strip()
            if label:
                self.trigger_list.insert(tk.END, f"{i+1:02d}. {k}: {label}")
            else:
                self.trigger_list.insert(tk.END, f"{i+1:02d}. {k}")
            if k not in self._indices:
                self._indices[k] = 0

        # 選択を維持/補正
        if triggers:
            if not self.trigger_list.curselection():
                self.trigger_list.selection_set(0)
        self._sync_suppress_checkbox()
        self._update_status()

    def _refresh_actions(self):
        self.action_list.delete(0, tk.END)
        trig = self._selected_trigger()
        if not trig:
            self._sync_suppress_checkbox()
            self._update_status()
            return
        actions = trig.get("actions", [])
        for i, a in enumerate(actions):
            t = a.get("type", "")
            # 表示用 value（mouse_click は value ではなく x,y を表示）
            if (a.get("type") or "").strip().lower() == "mouse_click":
                x = a.get("x", "")
                y = a.get("y", "")
                btn = a.get("button", "left")
                clicks = a.get("clicks", 1)
                v_disp = f"({x}, {y}) {btn} x{clicks}"
            else:
                v_disp = a.get("value", "")

            label = (a.get("label") or "").strip()
            if label:
                self.action_list.insert(tk.END, f"{i+1:02d}. [{t}] {v_disp}: {label}")
            else:
                self.action_list.insert(tk.END, f"{i+1:02d}. [{t}] {v_disp}")

        key = normalize_key_name(trig.get("key", ""))
        if key not in self._indices:
            self._indices[key] = 0
        # index補正
        if actions:
            self._indices[key] %= len(actions)
        else:
            self._indices[key] = 0
        # 「次に実行する行」を選択状態にする
        self._select_next_action_row(key)
        self._sync_suppress_checkbox()
        self._update_status()

    def _select_next_action_row(self, key: str):
        """現在の next index（self._indices[key]）を action_list 上で選択表示する（UIスレッド専用）"""
        key = normalize_key_name(key)
        actions = self._find_trigger_by_key(key).get("actions", []) if self._find_trigger_by_key(key) else []
        if not actions:
            self.action_list.selection_clear(0, tk.END)
            return
        idx = self._indices.get(key, 0)
        if idx < 0:
            idx = 0
        if idx >= len(actions):
            idx = len(actions) - 1
            self._indices[key] = idx
        self._programmatic_action_select = True
        try:
            self.action_list.selection_clear(0, tk.END)
            self.action_list.selection_set(idx)
            self.action_list.activate(idx)
            self.action_list.see(idx)
        finally:
            self._programmatic_action_select = False

    def _on_action_list_select(self, _event=None):
        """ユーザーが action_list の行を選んだら、その行を『次に実行』として indices に反映"""
        if self._programmatic_action_select:
            return
        key = self._selected_trigger_key()
        if not key:
            return
        sel = self.action_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        trig = self._find_trigger_by_key(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return
        if 0 <= idx < len(actions):
            self._indices[key] = idx
            self._update_status()

    def _on_trigger_double_click(self, _event=None):
        """トリガー一覧をダブルクリックしたらトリガー変更（rename_trigger）を開く"""
        if not self.trigger_list.curselection():
            return
        self.rename_trigger()

    def _on_action_double_click(self, _event=None):
        """シーケンス一覧をダブルクリックしたら編集を開く"""
        # 選択行が無いときは何もしない
        if not self.action_list.curselection():
            return
        self.edit_action()

    # ---------------- Config IO ----------------
    def _load_if_exists(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                messagebox.showwarning("読込失敗", f"config.json の読込に失敗しました。\n{e}\n\n例の設定で起動します。")
                self.data = safe_deepcopy(DEFAULT_CONFIG)
        # 旧フォーマット互換（trigger_key/actions）→ triggers に変換
        if "triggers" not in self.data and "trigger_key" in self.data:
            old_key = normalize_key_name(self.data.get("trigger_key", "f1"))
            old_actions = self.data.get("actions", [])
            self.data = {"triggers": [{"key": old_key, "label": "", "suppress": True, "actions": old_actions}]}
            
        # プリセットが無ければデフォルトを補う（既存ユーザー互換）
        if "hotkey_presets" not in self.data or not isinstance(self.data.get("hotkey_presets"), list):
            self.data["hotkey_presets"] = safe_deepcopy(DEFAULT_CONFIG.get("hotkey_presets", []))

        # trigger の label 欠落を補う（既存データ互換）
        for t in self.data.get("triggers", []) if isinstance(self.data.get("triggers"), list) else []:
            if "label" not in t:
                t["label"] = ""
            # action の label 欠落を補う（既存データ互換）
            actions = t.get("actions", [])
            if isinstance(actions, list):
                for a in actions:
                    if isinstance(a, dict) and "label" not in a:
                        a["label"] = ""

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存", f"保存しました:\n{self.config_path}")
        except Exception as e:
            messagebox.showerror("保存失敗", str(e))

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="別名で保存",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存", f"保存しました:\n{path}")
        except Exception as e:
            messagebox.showerror("保存失敗", str(e))

    def load_from(self):
        path = filedialog.askopenfilename(
            title="読込",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            # 旧フォーマット互換
            if "triggers" not in self.data and "trigger_key" in self.data:
                old_key = normalize_key_name(self.data.get("trigger_key", "f1"))
                old_actions = self.data.get("actions", [])
                self.data = {"triggers": [{"key": old_key, "suppress": True, "actions": old_actions}]}
            self._indices = {}
            self._refresh_triggers()
            self._refresh_actions()
            messagebox.showinfo("読込", f"読み込みました:\n{path}")
        except Exception as e:
            messagebox.showerror("読込失敗", str(e))

    def open_preset_manager(self):
        PresetManagerDialog(self, title="ホットキープリセット編集").wait_window()

    def restore_default(self):
        if messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？"):
            self.data = safe_deepcopy(DEFAULT_CONFIG)
            self._indices = {}
            self._refresh_triggers()
            self._refresh_actions()

    # ---------------- Trigger selection/helpers ----------------
    def _selected_trigger_index(self):
        sel = self.trigger_list.curselection()
        if not sel:
            return None
        return int(sel[0])

    def _selected_trigger(self):
        idx = self._selected_trigger_index()
        if idx is None:
            return None
        triggers = self.data.get("triggers", [])
        if idx < 0 or idx >= len(triggers):
            return None
        return triggers[idx]

    def _selected_trigger_key(self):
        t = self._selected_trigger()
        if not t:
            return None
        return normalize_key_name(t.get("key", ""))

    def _sync_suppress_checkbox(self):
        t = self._selected_trigger()
        if not t:
            self.suppress_var.set(True)
            return
        self.suppress_var.set(bool(t.get("suppress", True)))

    def update_suppress(self):
        t = self._selected_trigger()
        if not t:
            return
        t["suppress"] = bool(self.suppress_var.get())
        # フックON中なら再登録が必要（設定反映）
        if self.hook_active:
            self.start_hook()

    # ---------------- Trigger CRUD ----------------
    def add_trigger(self):
        dlg = TriggerDialog(self, title="トリガー追加")
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        key = normalize_key_name(res.get("key", ""))
        label = (res.get("label") or "").strip()
        if not key:
            return
        triggers = self.data.setdefault("triggers", [])
        # 重複チェック
        if any(normalize_key_name(t.get("key", "")) == key for t in triggers):
            messagebox.showerror("追加できません", f"すでに存在します: {key}")
            return
        triggers.append({"key": key, "label": label, "suppress": True, "actions": []})
        self._indices.setdefault(key, 0)
        self._refresh_triggers()
        # 末尾を選択
        self.trigger_list.selection_clear(0, tk.END)
        self.trigger_list.selection_set(len(triggers) - 1)
        self._refresh_actions()
        if self.hook_active:
            self.start_hook()

    def rename_trigger(self):
        t = self._selected_trigger()
        if not t:
            messagebox.showinfo("変更", "変更したいトリガーを選択してください。")
            return
        old = normalize_key_name(t.get("key", ""))
        cur_label = (t.get("label") or "").strip()
        dlg = TriggerDialog(self, title="トリガー変更", initial_key=old, initial_label=cur_label)
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        new = normalize_key_name(res.get("key", ""))
        new_label = (res.get("label") or "").strip()
        if not new:
            return
        triggers = self.data.get("triggers", [])
        if any(normalize_key_name(x.get("key", "")) == new for x in triggers if x is not t):
            messagebox.showerror("変更できません", f"すでに存在します: {new}")
            return
        # indices の移し替え
        self._indices.setdefault(old, 0)
        self._indices.setdefault(new, self._indices.get(old, 0))
        if old in self._indices:
            del self._indices[old]
        t["key"] = new
        t["label"] = new_label
        self._refresh_triggers()
        if self.hook_active:
            self.start_hook()

    def delete_trigger(self):
        idx = self._selected_trigger_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したいトリガーを選択してください。")
            return
        triggers = self.data.get("triggers", [])
        if idx < 0 or idx >= len(triggers):
            return
        key = normalize_key_name(triggers[idx].get("key", ""))
        if messagebox.askyesno("確認", f"トリガー {key} を削除しますか？"):
            del triggers[idx]
            self._indices.pop(key, None)
            self._refresh_triggers()
            self._refresh_actions()
            if self.hook_active:
                self.start_hook()

    # ---------------- Actions CRUD (selected trigger) ----------------
    def _selected_action_index(self):
        sel = self.action_list.curselection()
        if not sel:
            return None
        return int(sel[0])

    def add_action(self):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("追加", "まずトリガーを選択してください。")
            return
        ActionDialog(self, title="追加").wait_window()
        if getattr(self, "_dialog_result", None):
            trig.setdefault("actions", []).append(self._dialog_result)
            self._refresh_actions()
            self._dialog_result = None

    def edit_action(self):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("編集", "まずトリガーを選択してください。")
            return
        idx = self._selected_action_index()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        current = trig.get("actions", [])[idx]
        ActionDialog(self, title="編集", initial=current).wait_window()
        if getattr(self, "_dialog_result", None):
            trig["actions"][idx] = self._dialog_result
            self._refresh_actions()
            self.action_list.selection_set(idx)
            self._dialog_result = None

    def delete_action(self):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("削除", "まずトリガーを選択してください。")
            return
        idx = self._selected_action_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        if messagebox.askyesno("確認", "選択した行を削除しますか？"):
            del trig["actions"][idx]
            self._refresh_actions()

    def move_action(self, delta: int):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("移動", "まずトリガーを選択してください。")
            return
        idx = self._selected_action_index()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        j = idx + delta
        if j < 0 or j >= len(actions):
            return
        actions[idx], actions[j] = actions[j], actions[idx]
        key = self._selected_trigger_key()
        if key:
            self._indices[key] = j
        self._refresh_actions()

    # ---------------- Hook logic ----------------
    def start_hook(self):
        triggers = self.data.get("triggers", [])
        if not triggers:
            messagebox.showerror("開始できません", "トリガーが1件も登録されていません。")
            return
        # 有効トリガー（キーがあり、アクションがあるもの）だけフック
        usable = []
        for t in triggers:
            k = normalize_key_name(t.get("key", ""))
            acts = t.get("actions", [])
            if k and acts:
                usable.append((k, bool(t.get("suppress", True))))
        if not usable:
            messagebox.showerror("開始できません", "アクションが入っているトリガーがありません。")
            return

        try:
            # 既存フック解除 → 全再登録（設定変更を確実に反映）
            self.stop_hook()
            self.hook_active = True
            self._hook_handles = {}
            for k, sup in usable:
                self._indices.setdefault(k, 0)
                # keyごとにコールバックを束縛
                handle = keyboard.on_press_key(k, lambda e, kk=k: self._on_trigger_key(kk), suppress=sup)
                self._hook_handles[k] = handle
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self._update_status()
        except Exception as e:
            self.hook_active = False
            self._hook_handles = {}
            messagebox.showerror("開始失敗", f"フックの開始に失敗しました。\n{e}")
            self._update_status()

    def stop_hook(self):
        for _k, h in list(self._hook_handles.items()):
            try:
                keyboard.unhook(h)
            except Exception:
                pass
        self._hook_handles = {}
        self.hook_active = False
        if hasattr(self, "start_btn"):
            self.start_btn.configure(state="normal")
        if hasattr(self, "stop_btn"):
            self.stop_btn.configure(state="disabled")
        self._update_status()

    def _on_trigger_key(self, key: str):
        # フックは別スレッドで来る可能性があるのでロック + 再入防止（key単位）
        key = normalize_key_name(key)
        with self._lock:
            if key in self._reentry_guard:
                return
            self._reentry_guard.add(key)

        try:
            trig = self._find_trigger_by_key(key)
            if not trig:
                return
            actions = trig.get("actions", [])
            if not actions:
                return
            i = self._indices.get(key, 0) % len(actions)
            action = actions[i]

            self._perform_action(action)

            with self._lock:
                self._indices[key] = (i + 1) % len(actions)
        finally:
            with self._lock:
                self._reentry_guard.discard(key)
            # UI更新はメインスレッドで：押されたトリガーを左で選択 + 次の行を右で選択
            self.after(0, lambda k=key: self._select_trigger_by_key(k))

    def _select_trigger_by_key(self, key: str):
        """押されたトリガーキーに対応する行をトリガー一覧で選択し、右側表示も更新する（UIスレッド専用）"""
        key = normalize_key_name(key)
        triggers = self.data.get("triggers", [])
        target_idx = None
        for i, t in enumerate(triggers):
            if normalize_key_name(t.get("key", "")) == key:
                target_idx = i
                break
        if target_idx is None:
            self._update_status()
            return

        # すでに同じ行が選択されていればそのままでもOKだが、見た目を確実に更新するため明示的にセット
        self.trigger_list.selection_clear(0, tk.END)
        self.trigger_list.selection_set(target_idx)
        self.trigger_list.activate(target_idx)
        self.trigger_list.see(target_idx)
        self._refresh_actions()
        self._update_status()

    def _find_trigger_by_key(self, key: str):
        key = normalize_key_name(key)
        for t in self.data.get("triggers", []):
            if normalize_key_name(t.get("key", "")) == key:
                return t
        return None

    def _perform_action(self, action: dict):
        t = (action.get("type") or "").strip().lower()
        v = action.get("value") or ""

        # 送信中にトリガーが混ざっても暴走しないように、短時間だけ抑制したい場合はここで工夫可能。
        # まずはシンプルに送信。
        if t == "hotkey":
            err_msg, normalized = self.validate_hotkey(v)
            if err_msg:
                # アプリを止めない。UIスレッドで原因を表示
                self.after(0, lambda kk=t, aa=action, ee=err_msg: self._show_action_error(kk, aa, ee))
                return
            # keyboard は "ctrl+c" のような表記でOK（打ち間違いだと例外が出ることがある）
            keyboard.send(normalized)
        elif t == "text":
            keyboard.write(v)
        elif t == "mouse_click":
            # 例: {"type":"mouse_click","x":100,"y":200,"button":"left","clicks":1}
            try:
                x = int(action.get("x"))
                y = int(action.get("y"))
            except Exception:
                self.after(0, lambda: messagebox.showerror("送信エラー", "mouse_click の x/y が不正です（整数で指定してください）。"))
                return
            button = (action.get("button") or "left").strip().lower()
            clicks = action.get("clicks", 1)
            try:
                clicks = int(clicks)
            except Exception:
                clicks = 1
            if clicks < 1:
                clicks = 1
            if button not in ("left", "right", "middle"):
                button = "left"
            # 実行
            try:
                pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("送信エラー", f"mouse_click の実行に失敗しました。\n{type(e).__name__}: {e}"))
        else:
            # 不明タイプはテキスト扱い
            keyboard.write(str(v))
            
    def validate_hotkey(self, hotkey: str) -> tuple[str, str]:
        """
        hotkey を検証し、(エラーメッセージ, 正規化したhotkey) を返す。
        エラーなしならエラーメッセージは ""。
        """
        s = (hotkey or "").strip()
        if not s:
            return "hotkey が空です。", ""

        # split結果を保持して空要素を検出する（ctrl++c / +ctrl+c / ctrl+c+ を弾く）
        raw = s.split("+")
        parts = [p.strip().lower() for p in raw]

        if any(p == "" for p in parts):
            return "hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。", ""

        # ここで正規化（余分な空白・大文字を吸収）
        normalized = "+".join(parts)

        # 同一キーの重複を弾く（例: ctrl+ctrl+c）
        if len(set(parts)) != len(parts):
            return "hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", ""

        # キー名の妥当性チェック（各キー単体が解決できるか）
        try:
            for p in parts:
                keyboard.key_to_scan_codes(p)
        except Exception as e:
            return f"不明なキー名があります: '{p}'（詳細: {e}）", ""

        return "", normalized

    def _show_action_error(self, trigger_key: str, action: dict, err: Exception):
        """送信エラーをUIスレッドで表示（多重表示は抑止）"""
        if self._error_dialog_open:
            return
        self._error_dialog_open = True
        try:
            t = (action.get("type") or "").strip().lower()
            v = action.get("value") or ""
            msg = (
                "キー送信中にエラーが発生しました。\n"
                f"送信キーに間違いがあります。修正してください。\n\n"
                #f"トリガー: {normalize_key_name(trigger_key)}\n"
                f"種別: {t}\n"
                f"値: {v}\n\n"
                f"エラー: {err}"
            )
            messagebox.showerror("送信エラー", msg)
        finally:
            self._error_dialog_open = False

    # ---------------- Close ----------------
    def on_close(self):
        try:
            self.stop_hook()
        finally:
            self.destroy()


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
        self.listbox.grid(row=1, column=0, rowspan=6, sticky="nsew", padx=(0, 10))
        # ダブルクリックで編集
        self.listbox.bind("<Double-Button-1>", self._on_double_click)

        btns = ttk.Frame(frm)
        btns.grid(row=1, column=1, sticky="n")
        ttk.Button(btns, text="追加", width=14, command=self.add).pack(pady=(0, 6))
        ttk.Button(btns, text="編集", width=14, command=self.edit).pack(pady=6)
        ttk.Button(btns, text="削除", width=14, command=self.delete).pack(pady=6)
        ttk.Separator(btns).pack(fill="x", pady=10)
        ttk.Button(btns, text="上へ", width=14, command=lambda: self.move(-1)).pack(pady=6)
        ttk.Button(btns, text="下へ", width=14, command=lambda: self.move(+1)).pack(pady=6)

        bottom = ttk.Frame(frm)
        bottom.grid(row=7, column=0, columnspan=2, sticky="e", pady=(12, 0))
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
            label = (str(p.get("label", "")) or "").strip()
            value = (str(p.get("value", "")) or "").strip()
            if label:
                self.listbox.insert(tk.END, f"{i+1:02d}. {value}: {label}")
            else:
                self.listbox.insert(tk.END, f"{i+1:02d}. {value}")

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
        self.hint.configure(text="例）トリガー: f1 / ラベル: コピー→ウィンドウ切替→貼り付け")
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

if __name__ == "__main__":
    app = App()
    app.mainloop()
