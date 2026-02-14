import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# グローバルキーボードフック/送信
# pip install keyboard
import keyboard


DEFAULT_CONFIG = {
    "triggers": [
        {
            "key": "f1",
            "suppress": True,
            "actions": [
                {"type": "hotkey", "value": "ctrlc"},
                {"type": "hotkey", "value": "alttab"},
                {"type": "hotkey", "value": "ctrltab"},
                {"type": "hotkey", "value": "ctrlc"},
                {"type": "hotkey", "value": "f2"},
                {"type": "text", "value": "テストネーム"},
            ],
        },
        {
            "key": "f2",
            "suppress": True,
            "actions": [
                {"type": "text", "value": "F2のシーケンス 1"},
                {"type": "hotkey", "value": "ctrlv"},
            ],
        },
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

        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.data = safe_deepcopy(DEFAULT_CONFIG)

        self.hook_active = False
        self._hook_handles = {}     # key -> hook_handle
        self._lock = threading.Lock()
        self._indices = {}          # key -> next index
        self._reentry_guard = set() # keys currently sending (prevent recursion)

        self._build_ui()
        self._load_if_exists()
        self._refresh_triggers()
        self._refresh_actions()
        self._update_status()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

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

        self.trigger_list = tk.Listbox(left, height=12, width=22)
        self.trigger_list.pack(side="top", fill="y", expand=False)
        self.trigger_list.bind("<<ListboxSelect>>", lambda _e: self._refresh_actions())

        tbtns = ttk.Frame(left)
        tbtns.pack(fill="x", pady=(10, 0))
        ttk.Button(tbtns, text="追加", command=self.add_trigger).pack(fill="x", pady=(0, 6))
        ttk.Button(tbtns, text="名前変更", command=self.rename_trigger).pack(fill="x", pady=6)
        ttk.Button(tbtns, text="削除", command=self.delete_trigger).pack(fill="x", pady=6)

        self.suppress_var = tk.BooleanVar(value=True)
        self.suppress_chk = ttk.Checkbutton(left, text="トリガーキーを抑止（suppress）", variable=self.suppress_var, command=self.update_suppress)
        self.suppress_chk.pack(anchor="w", pady=(10, 0))

        right = ttk.LabelFrame(mid, text="出力シーケンス（選択中トリガーの内容）", padding=10)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.action_list = tk.Listbox(right, height=18)
        self.action_list.pack(side="left", fill="both", expand=True)

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
        ttk.Button(abtns, text="下へ", width=16, command=lambda: self.move_action(1)).pack(pady=6)

        # 下段：保存/読込
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="保存（config.json）", command=self.save_config).pack(side="left")
        ttk.Button(bottom, text="別名で保存…", command=self.save_as).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="読込…", command=self.load_from).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="例を復元", command=self.restore_default).pack(side="right")

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
            v = a.get("value", "")
            self.action_list.insert(tk.END, f"{i+1:02d}. [{t}] {v}")

        key = normalize_key_name(trig.get("key", ""))
        if key not in self._indices:
            self._indices[key] = 0
        # index補正
        if actions:
            self._indices[key] %= len(actions)
        else:
            self._indices[key] = 0
        self._sync_suppress_checkbox()
        self._update_status()

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
            self.data = {"triggers": [{"key": old_key, "suppress": True, "actions": old_actions}]}

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
        key = simpledialog.askstring("追加", "トリガーキーを入力（例: f1, f2, caps lock）", parent=self)
        if not key:
            return
        key = normalize_key_name(key)
        if not key:
            return
        triggers = self.data.setdefault("triggers", [])
        # 重複チェック
        if any(normalize_key_name(t.get("key", "")) == key for t in triggers):
            messagebox.showerror("追加できません", f"すでに存在します: {key}")
            return
        triggers.append({"key": key, "suppress": True, "actions": []})
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
        new = simpledialog.askstring("名前変更", f"新しいトリガーキー（現在: {old}）", initialvalue=old, parent=self)
        if not new:
            return
        new = normalize_key_name(new)
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
        self._refresh_actions()
        self.action_list.selection_set(j)

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
        # フックは別スレッドで来る可能性があるのでロック  再入防止（key単位）
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
            self.after(0, self._update_status)

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
            # keyboard は "ctrl+c" のような表記でOK
            keyboard.send(v)
        elif t == "text":
            keyboard.write(v)
        else:
            # 不明タイプはテキスト扱い
            keyboard.write(str(v))

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

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="種類").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value="hotkey")
        self.type_combo = ttk.Combobox(frm, textvariable=self.type_var, values=["hotkey", "text"], state="readonly", width=12)
        self.type_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="値（hotkey例: ctrl+c / text例: テスト）").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.value_var = tk.StringVar(value="")
        self.value_entry = ttk.Entry(frm, textvariable=self.value_var, width=42)
        self.value_entry.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(10, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="OK", command=self.on_ok).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="キャンセル", command=self.destroy).pack(side="left")

        if initial:
            self.type_var.set((initial.get("type") or "hotkey").strip().lower())
            self.value_var.set(initial.get("value") or "")

        self.value_entry.focus_set()
        self.grab_set()
        self.transient(parent)

    def on_ok(self):
        t = (self.type_var.get() or "").strip().lower()
        v = self.value_var.get()
        if not v:
            messagebox.showerror("入力エラー", "値が空です。")
            return
        if t not in ("hotkey", "text"):
            messagebox.showerror("入力エラー", "種類が不正です。")
            return
        self.parent._dialog_result = {"type": t, "value": v}
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
