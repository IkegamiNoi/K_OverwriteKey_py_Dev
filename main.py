import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# グローバルキーボードフック/送信
# pip install keyboard
import keyboard


DEFAULT_CONFIG = {
    "trigger_key": "f1",
    "actions": [
        {"type": "hotkey", "value": "ctrl+c"},
        {"type": "hotkey", "value": "alt+tab"},
        {"type": "hotkey", "value": "ctrl+tab"},
        {"type": "hotkey", "value": "ctrl+c"},
        {"type": "hotkey", "value": "f2"},
        {"type": "text", "value": "テストネーム"},
    ],
}


def normalize_key_name(s: str) -> str:
    return (s or "").strip().lower()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Key Replacer Sequencer")
        self.geometry("820x520")

        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.data = json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))

        self.hook_active = False
        self._hook_handle = None
        self._lock = threading.Lock()
        self._index = 0
        self._reentry_guard = False

        self._build_ui()
        self._load_if_exists()
        self._refresh_list()
        self._update_status()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- UI ----------------
    def _build_ui(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        # 上段：設定
        top = ttk.LabelFrame(outer, text="設定", padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="トリガーキー（例: f1, f2, caps lock など）").grid(row=0, column=0, sticky="w")
        self.trigger_var = tk.StringVar(value="f1")
        self.trigger_entry = ttk.Entry(top, textvariable=self.trigger_var, width=18)
        self.trigger_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.start_btn = ttk.Button(top, text="開始（フックON）", command=self.start_hook)
        self.stop_btn = ttk.Button(top, text="停止（フックOFF）", command=self.stop_hook, state="disabled")
        self.start_btn.grid(row=0, column=2, padx=12)
        self.stop_btn.grid(row=0, column=3)

        self.status_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.status_var).grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))

        for i in range(4):
            top.grid_columnconfigure(i, weight=0)
        top.grid_columnconfigure(0, weight=1)

        # 中段：アクション一覧
        mid = ttk.LabelFrame(outer, text="出力シーケンス（トリガー押下ごとに順番に実行）", padding=10)
        mid.pack(fill="both", expand=True, pady=(12, 0))

        self.listbox = tk.Listbox(mid, height=14)
        self.listbox.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(mid, orient="vertical", command=self.listbox.yview)
        sb.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=sb.set)

        btns = ttk.Frame(mid)
        btns.pack(side="left", fill="y", padx=(12, 0))

        ttk.Button(btns, text="追加", width=16, command=self.add_action).pack(pady=(0, 6))
        ttk.Button(btns, text="編集", width=16, command=self.edit_action).pack(pady=6)
        ttk.Button(btns, text="削除", width=16, command=self.delete_action).pack(pady=6)
        ttk.Separator(btns).pack(fill="x", pady=10)
        ttk.Button(btns, text="上へ", width=16, command=lambda: self.move_action(-1)).pack(pady=6)
        ttk.Button(btns, text="下へ", width=16, command=lambda: self.move_action(+1)).pack(pady=6)

        # 下段：保存/読込
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom, text="保存（config.json）", command=self.save_config).pack(side="left")
        ttk.Button(bottom, text="別名で保存…", command=self.save_as).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="読込…", command=self.load_from).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="例を復元", command=self.restore_default).pack(side="right")

    def _update_status(self):
        trig = normalize_key_name(self.trigger_var.get())
        n = len(self.data.get("actions", []))
        state = "ON" if self.hook_active else "OFF"
        self.status_var.set(f"フック: {state} / トリガー: {trig or '(未設定)'} / 登録数: {n} / 次に実行する番号: {self._index + 1 if n else 0}")

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        actions = self.data.get("actions", [])
        for i, a in enumerate(actions):
            t = a.get("type", "")
            v = a.get("value", "")
            label = f"{i+1:02d}. [{t}] {v}"
            self.listbox.insert(tk.END, label)
        # indexが範囲外なら戻す
        if actions:
            self._index %= len(actions)
        else:
            self._index = 0
        self._update_status()

    # ---------------- Config IO ----------------
    def _load_if_exists(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.trigger_var.set(self.data.get("trigger_key", "f1"))
            except Exception as e:
                messagebox.showwarning("読込失敗", f"config.json の読込に失敗しました。\n{e}\n\n例の設定で起動します。")
                self.data = json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))
                self.trigger_var.set(self.data.get("trigger_key", "f1"))
        else:
            self.trigger_var.set(self.data.get("trigger_key", "f1"))

    def save_config(self):
        self.data["trigger_key"] = normalize_key_name(self.trigger_var.get())
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存", f"保存しました:\n{self.config_path}")
        except Exception as e:
            messagebox.showerror("保存失敗", str(e))

    def save_as(self):
        self.data["trigger_key"] = normalize_key_name(self.trigger_var.get())
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
            self.trigger_var.set(self.data.get("trigger_key", "f1"))
            self._index = 0
            self._refresh_list()
            messagebox.showinfo("読込", f"読み込みました:\n{path}")
        except Exception as e:
            messagebox.showerror("読込失敗", str(e))

    def restore_default(self):
        if messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？"):
            self.data = json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))
            self.trigger_var.set(self.data.get("trigger_key", "f1"))
            self._index = 0
            self._refresh_list()

    # ---------------- Actions edit ----------------
    def _selected_index(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return int(sel[0])

    def add_action(self):
        ActionDialog(self, title="追加").wait_window()
        if getattr(self, "_dialog_result", None):
            self.data.setdefault("actions", []).append(self._dialog_result)
            self._refresh_list()
            self._dialog_result = None

    def edit_action(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        current = self.data.get("actions", [])[idx]
        ActionDialog(self, title="編集", initial=current).wait_window()
        if getattr(self, "_dialog_result", None):
            self.data["actions"][idx] = self._dialog_result
            self._refresh_list()
            self.listbox.selection_set(idx)
            self._dialog_result = None

    def delete_action(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        if messagebox.askyesno("確認", "選択した行を削除しますか？"):
            del self.data["actions"][idx]
            self._refresh_list()

    def move_action(self, delta: int):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        actions = self.data.get("actions", [])
        j = idx + delta
        if j < 0 or j >= len(actions):
            return
        actions[idx], actions[j] = actions[j], actions[idx]
        self._refresh_list()
        self.listbox.selection_set(j)

    # ---------------- Hook logic ----------------
    def start_hook(self):
        trig = normalize_key_name(self.trigger_var.get())
        if not trig:
            messagebox.showerror("開始できません", "トリガーキーが未設定です。")
            return
        if not self.data.get("actions"):
            messagebox.showerror("開始できません", "出力が1件も登録されていません。")
            return

        self.data["trigger_key"] = trig
        self._index = 0

        try:
            # 既存フックがあれば外す
            self.stop_hook()
            self.hook_active = True
            # suppress=True でトリガーキー自体の入力をアプリ側で止める
            self._hook_handle = keyboard.on_press_key(trig, self._on_trigger, suppress=True)
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self._update_status()
        except Exception as e:
            self.hook_active = False
            self._hook_handle = None
            messagebox.showerror("開始失敗", f"フックの開始に失敗しました。\n{e}")
            self._update_status()

    def stop_hook(self):
        if self._hook_handle is not None:
            try:
                keyboard.unhook(self._hook_handle)
            except Exception:
                pass
        self._hook_handle = None
        self.hook_active = False
        if hasattr(self, "start_btn"):
            self.start_btn.configure(state="normal")
        if hasattr(self, "stop_btn"):
            self.stop_btn.configure(state="disabled")
        self._update_status()

    def _on_trigger(self, _event):
        # フックは別スレッドで来る可能性があるのでロック + 再入防止
        with self._lock:
            if self._reentry_guard:
                return
            self._reentry_guard = True

        try:
            actions = self.data.get("actions", [])
            if not actions:
                return
            i = self._index % len(actions)
            action = actions[i]

            self._perform_action(action)

            with self._lock:
                self._index = (self._index + 1) % len(actions)
        finally:
            with self._lock:
                self._reentry_guard = False
            # UI更新はメインスレッドに投げる
            self.after(0, self._update_status)

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
