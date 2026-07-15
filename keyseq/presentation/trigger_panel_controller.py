from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from keyseq.domain.config import (
    DEFAULT_RUN_TO_END_DELAY_MS,
    coerce_nonnegative_int,
    format_action_list_item,
    format_trigger_list_item,
    normalize_key_name,
)
from keyseq.presentation.dialogs import ActionDialog, TriggerDialog
from keyseq.presentation.listbox_utils import (
    focused_listbox_index,
    sync_listbox_selection_to_focus,
)


class TriggerPanelController:
    """トリガー/シーケンスパネルの選択・表示・編集とステータス表示。"""

    def __init__(self, app) -> None:
        self._app = app

    # ---------------- 選択系 ----------------
    def sync_trigger_selection_to_views(self):
        """現在の選択idxを、Full/Compact両方のトリガーListboxへ反映"""
        idx = int(getattr(self._app, "_selected_trigger_idx", 0) or 0)
        # Full
        try:
            lb = self._app.full_view.trigger_list
            lb.selection_clear(0, tk.END)
            if lb.size() > 0:
                idx = max(0, min(idx, lb.size() - 1))
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)
        except Exception:
            pass
        # Compact
        try:
            lb = self._app.compact_view.trigger_list
            lb.selection_clear(0, tk.END)
            if lb.size() > 0:
                idx = max(0, min(idx, lb.size() - 1))
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)
        except Exception:
            pass

    def set_selected_trigger_index(self, idx: int):
        self._app._selected_trigger_idx = int(idx)
        self.sync_trigger_selection_to_views()
        # フル画面なら右側も追従
        if not self._app._compact_mode:
            self.refresh_actions()
        self.update_status()

    def select_trigger_by_key(self, key: str):
        """押されたトリガーキーに対応する行をトリガー一覧で選択し、右側表示も更新する（UI専用）"""
        key = normalize_key_name(key)
        triggers = self._app.data.get("triggers", [])
        target_idx = None
        for i, t in enumerate(triggers):
            if normalize_key_name(t.get("key", "")) == key:
                target_idx = i
                break

        if target_idx is None:
            self.update_status()
            return

        self._app._selected_trigger_idx = int(target_idx)
        self.sync_trigger_selection_to_views()
        self.refresh_actions()
        self.update_status()

    def selected_trigger_index(self):
        # Full/Compact どちらのListboxでも選択は共通idxとして扱う
        idx = getattr(self._app, "_selected_trigger_idx", None)
        if idx is None:
            return None
        return int(idx)

    def selected_trigger(self):
        idx = self.selected_trigger_index()
        if idx is None:
            return None
        triggers = self._app.data.get("triggers", [])
        if idx < 0 or idx >= len(triggers):
            return None
        return triggers[idx]

    def selected_trigger_key(self):
        t = self.selected_trigger()
        if not t:
            return None
        return normalize_key_name(t.get("key", ""))

    def on_trigger_list_focus_index_change(self, event=None):
        triggers = self._app.data.get("triggers", [])
        widget = getattr(event, "widget", None)
        if not isinstance(widget, tk.Listbox):
            widget = None
        if widget is None:
            return
        idx = sync_listbox_selection_to_focus(self._app, widget, len(triggers))
        if idx is not None:
            self.set_selected_trigger_index(idx)

    def on_trigger_double_click(self, _event=None):
        """トリガー一覧をダブルクリックしたらトリガー変更（rename_trigger）を開く"""
        self.rename_trigger()

    # ---------------- 表示系 ----------------
    def refresh_triggers(self):
        # Full/Compact 両方に反映
        try:
            self._app.full_view.trigger_list.delete(0, tk.END)
        except Exception:
            pass
        try:
            self._app.compact_view.trigger_list.delete(0, tk.END)
        except Exception:
            pass
        triggers = self._app.data.get("triggers", [])
        for i, t in enumerate(triggers):
            k = normalize_key_name(t.get("key", ""))
            s = format_trigger_list_item(i, t)
            try:
                self._app.full_view.trigger_list.insert(tk.END, s)
            except Exception:
                pass
            try:
                self._app.compact_view.trigger_list.insert(tk.END, s)
            except Exception:
                pass
            if k not in self._app._indices:
                self._app._indices[k] = 0

        # 選択を維持/補正（共通idx）
        if triggers:
            if getattr(self._app, "_selected_trigger_idx", None) is None:
                self._app._selected_trigger_idx = 0
            self._app._selected_trigger_idx = max(0, min(int(self._app._selected_trigger_idx), len(triggers) - 1))
            self.sync_trigger_selection_to_views()
        self.sync_suppress_checkbox()
        self.sync_run_to_end_ui()
        self._app.keymap_panel.refresh_keymap_list_ui()
        self._app.layout.refresh_keyboard_window()
        self.update_status()

    def refresh_actions(self):
        # 省略画面では右側（action_list）が無いので、フル側のみ更新
        try:
            self._app.full_view.action_list.delete(0, tk.END)
        except Exception:
            self.sync_suppress_checkbox()
            self.sync_run_to_end_ui()
            self.update_status()
            return
        trig = self.selected_trigger()
        if not trig:
            self.sync_suppress_checkbox()
            self.sync_run_to_end_ui()
            self.update_status()
            return
        actions = trig.get("actions", [])
        for i, a in enumerate(actions):
            self._app.full_view.action_list.insert(tk.END, format_action_list_item(i, a))

        key = normalize_key_name(trig.get("key", ""))
        if key not in self._app._indices:
            self._app._indices[key] = 0
        # index補正
        if not actions:
            self._app._indices[key] = 0
        else:
            if bool(trig.get("run_to_end", False)):
                # run_to_end: 0..len を許す（lenは「終端＝次回は先頭」）
                idx = int(self._app._indices.get(key, 0) or 0)
                if idx < 0:
                    idx = 0
                if idx > len(actions):
                    idx = len(actions)
                self._app._indices[key] = idx
            else:
                # 従来: 循環
                self._app._indices[key] %= len(actions)
        # 「次に実行する行」を選択状態にする
        self.select_next_action_row(key)
        self.sync_suppress_checkbox()
        self.sync_run_to_end_ui()
        self.update_status()

    def select_next_action_row(self, key: str):
        """現在の next index（self._indices[key]）を action_list 上で選択表示する（UIスレッド専用）"""
        key = normalize_key_name(key)
        actions = self._app._find_trigger_by_key(key).get("actions", []) if self._app._find_trigger_by_key(key) else []
        if not actions:
            self._app.full_view.action_list.selection_clear(0, tk.END)
            return
        trig = self._app._find_trigger_by_key(key)
        idx_raw = int(self._app._indices.get(key, 0) or 0)
        # run_to_end で終端（len）なら次回は先頭なので、先頭をハイライト
        if trig and bool(trig.get("run_to_end", False)) and idx_raw >= len(actions):
            idx = 0
        else:
            idx = idx_raw
            if idx < 0:
                idx = 0
            if idx >= len(actions):
                idx = len(actions) - 1
                self._app._indices[key] = idx
        self._app._programmatic_action_select = True
        try:
            self._app.full_view.action_list.selection_clear(0, tk.END)
            self._app.full_view.action_list.selection_set(idx)
            self._app.full_view.action_list.activate(idx)
            self._app.full_view.action_list.see(idx)
        finally:
            self._app._programmatic_action_select = False

    def sync_suppress_checkbox(self):
        t = self.selected_trigger()
        if not t:
            self._app.ui_vars.suppress_var.set(True)
            return
        self._app.ui_vars.suppress_var.set(bool(t.get("suppress", True)))

    def sync_run_to_end_ui(self):
        """選択中トリガーの run_to_end / delay を UI へ反映"""
        t = self.selected_trigger()
        if not t:
            self._app.ui_vars.run_to_end_var.set(False)
            self._app.ui_vars.run_to_end_delay_var.set(str(DEFAULT_RUN_TO_END_DELAY_MS))
            try:
                if hasattr(self._app, "run_to_end_delay_entry"):
                    self._app.run_to_end_delay_entry.configure(state="disabled")
            except Exception:
                pass
            return

        self._app.ui_vars.run_to_end_var.set(bool(t.get("run_to_end", False)))
        d = coerce_nonnegative_int(
            t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        )
        self._app.ui_vars.run_to_end_delay_var.set(str(d))
        try:
            if hasattr(self._app, "run_to_end_delay_entry"):
                self._app.run_to_end_delay_entry.configure(state=("normal" if self._app.ui_vars.run_to_end_var.get() else "disabled"))
        except Exception:
            pass

    def update_status(self):
        hook_state = "ON" if self._app.hook.hook_active else "OFF"
        trigger_state = "ON" if self._app.hook.custom_input_enabled else "OFF"
        keymap_text = self._app.keymap_panel.get_active_keymap_text()
        sel_key = self.selected_trigger_key() or "(未選択)"
        if getattr(self._app, "_compact_mode", False):
            # 省略表示：ON/OFF + 通常トリガー有効状態 + 選択中トリガー + 次に実行（行の内容）
            line = self.get_next_action_summary(sel_key)
            self._app.ui_vars.status_var.set(f"フック: {hook_state} / 通常トリガー: {trigger_state} / キーマップ: {keymap_text}\n選択: {sel_key} / 次: {line}")
            return

        triggers = self._app.data.get("triggers", [])
        keys = [normalize_key_name(t.get("key", "")) for t in triggers if t.get("key")]
        keys_text = ", ".join(keys) if keys else "(未設定)"
        # 「次」は run_to_end の場合、終端（len）なら次回は先頭なので 1 を出す
        next_i = 0
        try:
            trig = self._app._find_trigger_by_key(sel_key) if sel_key and sel_key != "(未選択)" else None
            actions = trig.get("actions", []) if trig else []
            idx = int(self._app._indices.get(sel_key, 0) or 0) if sel_key in self._app._indices else 0
            if actions:
                if bool(trig.get("run_to_end", False)) and idx >= len(actions):
                    next_i = 1
                else:
                    # 通常は idx+1（=次に実行される行番号）
                    next_i = min(idx, len(actions)-1) + 1
            else:
                next_i = 0
        except Exception:
            next_i = 0
        self._app.ui_vars.status_var.set(
            f"フック: {hook_state} / 通常トリガー: {trigger_state} / キーマップ: {keymap_text} / トリガー: {keys_text} / 選択中: {sel_key} / 選択中の次: {next_i}"
        )

    def get_next_action_summary(self, trigger_key: str) -> str:
        """省略表示用：次に実行されるアクションを1行で返す"""
        key = normalize_key_name(trigger_key or "")
        trig = self._app._find_trigger_by_key(key) if key and key != "(未選択)" else None
        if not trig:
            return "(なし)"
        actions = trig.get("actions", [])
        if not actions:
            return "(なし)"
        idx_raw = int(self._app._indices.get(key, 0) or 0)
        # run_to_end で終端にいる（len）なら、次回は先頭から
        if bool(trig.get("run_to_end", False)) and idx_raw >= len(actions):
            idx = 0
        else:
            idx = idx_raw % len(actions)
        a = actions[idx] if 0 <= idx < len(actions) else None
        if not isinstance(a, dict):
            return "(なし)"

        t = (a.get("type") or "").strip().lower()
        if t == "mouse_click":
            x = a.get("x", "")
            y = a.get("y", "")
            btn = a.get("button", "left")
            clicks = a.get("clicks", 1)
            return f"{idx+1:02d}. [mouse_click] ({x}, {y}) {btn} x{clicks}"
        else:
            v = a.get("value", "")
            return f"{idx+1:02d}. [{t}] {v}"

    # ---------------- run_to_end / suppress ----------------
    def update_run_to_end_delay(self, _event=None):
        """間隔(ms) を選択中トリガーへ保存（トリガーごと）"""
        t = self.selected_trigger()
        if not t:
            return
        s = (self._app.ui_vars.run_to_end_delay_var.get() or "").strip()
        v = coerce_nonnegative_int(s, DEFAULT_RUN_TO_END_DELAY_MS)
        old_v = int(
            t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS)
            or DEFAULT_RUN_TO_END_DELAY_MS
        )
        t["run_to_end_delay_ms"] = v
        # 表示を正規化（"00300" 等を "300" に）
        self._app.ui_vars.run_to_end_delay_var.set(str(v))
        if old_v != v:
            self._app.mark_sequence_dirty(t)

    def update_suppress(self):
        t = self.selected_trigger()
        if not t:
            return
        new_v = bool(self._app.ui_vars.suppress_var.get())
        old_v = bool(t.get("suppress", True))
        t["suppress"] = new_v
        if old_v != new_v:
            self._app.dirty_tracker.mark_trigger_set_dirty()
        # フックON中なら再登録が必要（設定反映）
        if self._app.hook.hook_active:
            self._app.hook.start_hook()

    def update_run_to_end(self):
        """連続実行（run_to_end）を現在のトリガーへ反映"""
        t = self.selected_trigger()
        if not t:
            return
        new_v = bool(self._app.ui_vars.run_to_end_var.get())
        old_v = bool(t.get("run_to_end", False))
        t["run_to_end"] = new_v
        if old_v != new_v:
            self._app.mark_sequence_dirty(t)
        self.sync_run_to_end_ui()
        # UI表示（次の行ハイライト/ステータス）を即反映
        if not getattr(self._app, "_compact_mode", False):
            self.refresh_actions()
        self.update_status()

    # ---------------- Trigger CRUD ----------------
    def add_trigger(self):
        dlg = TriggerDialog(self._app, title="トリガー追加")
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        key = normalize_key_name(res.get("key", ""))
        label = (res.get("label") or "").strip()
        if not key:
            return
        triggers = self._app.data.setdefault("triggers", [])
        # 重複チェック
        if self._app.trigger_service.key_exists(self._app.data, key):
            messagebox.showerror("追加できません", f"すでに存在します: {key}")
            return
        # フック停止トリガーとの重複チェック
        if self._app.trigger_service.is_stop_key_conflict(self._app.data, key):
            messagebox.showerror("追加できません", f"このキーはフック停止トリガーに設定されています:\n{key}")
            return
        if self._app.trigger_service.is_toggle_key_conflict(self._app.data, key):
            messagebox.showerror("追加できません", f"このキーは有効/無効トグルキーに設定されています:\n{key}")
            return
        if self._app.keymap_service.get_keymap_by_switch_key(self._app.data, key):
            messagebox.showerror("追加できません", f"このキーはキーマップ直接切替キーに設定されています:\n{key}")
            return
        triggers.append({"key": key, "label": label, "suppress": True, "run_to_end": False, "actions": []})
        new_index = len(triggers) - 1
        self._app._indices.setdefault(key, 0)
        self.refresh_triggers()
        self._app.dirty_tracker.mark_trigger_set_dirty()
        self._app.mark_sequence_dirty(triggers[-1])
        self.set_selected_trigger_index(new_index)
        if self._app.hook.hook_active:
            self._app.hook.start_hook()

    def rename_trigger(self):
        t = self.selected_trigger()
        if not t:
            messagebox.showinfo("変更", "変更したいトリガーを選択してください。")
            return
        old = normalize_key_name(t.get("key", ""))
        cur_label = (t.get("label") or "").strip()
        dlg = TriggerDialog(self._app, title="トリガー変更", initial_key=old, initial_label=cur_label)
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        new = normalize_key_name(res.get("key", ""))
        new_label = (res.get("label") or "").strip()
        if not new:
            return
        if self._app.trigger_service.key_exists(self._app.data, new, exclude_trigger=t):
            messagebox.showerror("変更できません", f"すでに存在します: {new}")
            return
        if self._app.trigger_service.is_stop_key_conflict(self._app.data, new):
            messagebox.showerror("変更できません", f"このキーはフック停止トリガーに設定されています:\n{new}")
            return
        if self._app.trigger_service.is_toggle_key_conflict(self._app.data, new):
            messagebox.showerror("変更できません", f"このキーは有効/無効トグルキーに設定されています:\n{new}")
            return
        if self._app.keymap_service.get_keymap_by_switch_key(self._app.data, new):
            messagebox.showerror("変更できません", f"このキーはキーマップ直接切替キーに設定されています:\n{new}")
            return
        # indices の移し替え
        self._app._indices.setdefault(old, 0)
        self._app._indices.setdefault(new, self._app._indices.get(old, 0))
        if old in self._app._indices:
            del self._app._indices[old]
        t["key"] = new
        t["label"] = new_label
        self.refresh_triggers()
        if old != new:
            self._app.dirty_tracker.mark_trigger_set_dirty()
        if cur_label != new_label:
            self._app.mark_sequence_dirty(t)
        if self._app.hook.hook_active:
            self._app.hook.start_hook()

    def delete_trigger(self):
        idx = self.selected_trigger_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したいトリガーを選択してください。")
            return
        triggers = self._app.data.get("triggers", [])
        if idx < 0 or idx >= len(triggers):
            return
        key = normalize_key_name(triggers[idx].get("key", ""))
        if messagebox.askyesno("確認", f"トリガー {key} を削除しますか？"):
            del triggers[idx]
            self._app._indices.pop(key, None)
            self.refresh_triggers()
            self.refresh_actions()
            self._app.dirty_tracker.mark_trigger_set_dirty()
            if self._app.hook.hook_active:
                self._app.hook.start_hook()

    # ---------------- Actions CRUD (selected trigger) ----------------
    def selected_action_index(self):
        trig = self.selected_trigger()
        if not trig:
            return None
        actions = trig.get("actions", [])
        if not isinstance(actions, list):
            return None
        return focused_listbox_index(self._app, self._app.full_view.action_list, len(actions))

    def add_action(self):
        trig = self.selected_trigger()
        if not trig:
            messagebox.showinfo("追加", "まずトリガーを選択してください。")
            return
        ActionDialog(self._app, title="追加").wait_window()
        if getattr(self._app, "_dialog_result", None):
            trig.setdefault("actions", []).append(self._app._dialog_result)
            self.refresh_actions()
            self._app.mark_sequence_dirty(trig)
            self._app._dialog_result = None

    def edit_action(self):
        trig = self.selected_trigger()
        if not trig:
            messagebox.showinfo("編集", "まずトリガーを選択してください。")
            return
        idx = self.selected_action_index()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        current = trig.get("actions", [])[idx]
        ActionDialog(self._app, title="編集", initial=current).wait_window()
        if getattr(self._app, "_dialog_result", None):
            trig["actions"][idx] = self._app._dialog_result
            self.refresh_actions()
            self._app.mark_sequence_dirty(trig)
            # action_list は FullView 側にある（選択表示を復帰）
            try:
                self._app.full_view.action_list.selection_clear(0, tk.END)
                self._app.full_view.action_list.selection_set(idx)
                self._app.full_view.action_list.activate(idx)
                self._app.full_view.action_list.see(idx)
            except Exception:
                pass
            self._app._dialog_result = None

    def delete_action(self):
        trig = self.selected_trigger()
        if not trig:
            messagebox.showinfo("削除", "まずトリガーを選択してください。")
            return
        idx = self.selected_action_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        if messagebox.askyesno("確認", "選択した行を削除しますか？"):
            del trig["actions"][idx]
            self.refresh_actions()
            self._app.mark_sequence_dirty(trig)

    def move_action(self, delta: int):
        trig = self.selected_trigger()
        if not trig:
            messagebox.showinfo("移動", "まずトリガーを選択してください。")
            return
        idx = self.selected_action_index()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        j = idx + delta
        if j < 0 or j >= len(actions):
            return
        actions[idx], actions[j] = actions[j], actions[idx]
        key = self.selected_trigger_key()
        if key:
            self._app._indices[key] = j
        self.refresh_actions()
        self._app.mark_sequence_dirty(trig)

    def on_action_list_select(self, _event=None):
        """ユーザーが action_list の行を選んだら、その行を『次に実行』として indices に反映"""
        if self._app._programmatic_action_select:
            return
        key = self.selected_trigger_key()
        if not key:
            return
        trig = self._app._find_trigger_by_key(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return
        idx = sync_listbox_selection_to_focus(self._app, self._app.full_view.action_list, len(actions))
        if idx is None:
            return
        if 0 <= idx < len(actions):
            self._app._indices[key] = idx
            self.update_status()

    def on_action_list_focus_index_change(self, _event=None):
        self.on_action_list_select()

    def on_action_double_click(self, _event=None):
        """シーケンス一覧をダブルクリックしたら編集を開く"""
        # 選択行が無いときは何もしない
        if not self._app.full_view.action_list.curselection():
            return
        self.edit_action()
