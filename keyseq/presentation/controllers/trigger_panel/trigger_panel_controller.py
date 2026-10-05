from __future__ import annotations

import tkinter as tk

from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.domain.trigger_duplicates import is_effective_trigger, shadowed_duplicate_indices
from keyseq.domain.config import (
    DEFAULT_RUN_TO_END_DELAY_MS,
    coerce_nonnegative_int,
    format_trigger_list_item,
    normalize_key_name,
)
from keyseq.presentation.controllers.action_list_rendering import (
    build_action_rows,
    format_next_action_summary,
)
from keyseq.presentation.listbox_utils import (
    listbox_mouse_button_is_down,
    sync_listbox_selection_to_focus,
)
from keyseq.presentation.controllers.trigger_panel.action_edit import ActionEditFlow
from keyseq.presentation.controllers.trigger_panel.trigger_list_edit import TriggerListEditFlow
from keyseq.presentation.controllers.trigger_panel.trigger_row_edit import TriggerRowEditFlow
from keyseq.presentation.listbox_range_drag import select_range, selected_range


class TriggerPanelController:
    """トリガー/シーケンスパネルの選択・表示・編集とステータス表示。"""

    def __init__(self, app) -> None:
        self._app = app
        self._trigger_lists = []

    @property
    def _action_edit(self) -> ActionEditFlow:
        # 初回参照時に作る（__init__ を通さずに組み立てるテストでも委譲先が得られるように）
        flow = self.__dict__.get("_action_edit_flow")
        if flow is None:
            flow = ActionEditFlow(self)
            self.__dict__["_action_edit_flow"] = flow
        return flow

    def register_trigger_list(self, listbox) -> None:
        self._trigger_lists.append(listbox)

    @property
    def _trigger_edit(self) -> TriggerListEditFlow:
        flow = self.__dict__.get("_trigger_edit_flow")
        if flow is None:
            flow = TriggerListEditFlow(self)
            self.__dict__["_trigger_edit_flow"] = flow
        return flow

    @property
    def _trigger_row_edit(self) -> TriggerRowEditFlow:
        flow = self.__dict__.get("_trigger_row_edit_flow")
        if flow is None:
            flow = TriggerRowEditFlow(self)
            self.__dict__["_trigger_row_edit_flow"] = flow
        return flow

    # ---------------- 選択系 ----------------
    def sync_trigger_selection_to_views(self):
        """現在の選択idxを、Full/Compact両方のトリガーListboxへ反映"""
        idx = int(getattr(self._app, "_selected_trigger_idx", 0) or 0)
        for lb in self._trigger_lists:
            try:
                lb.selection_clear(0, tk.END)
                if lb.size() > 0:
                    idx = max(0, min(idx, lb.size() - 1))
                    lb.selection_set(idx)
                    lb.selection_anchor(idx)
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
        triggers = get_active_triggers(self._app.data)
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
        triggers = get_active_triggers(self._app.data)
        if idx < 0 or idx >= len(triggers):
            return None
        return triggers[idx]

    def selected_trigger_key(self):
        t = self.selected_trigger()
        if not t:
            return None
        return normalize_key_name(t.get("key", ""))

    def selected_trigger_is_effective(self) -> bool:
        index = self.selected_trigger_index()
        return index is not None and is_effective_trigger(
            get_active_triggers(self._app.data), index
        )

    def on_trigger_list_select(self, event=None):
        self._sync_trigger_list_selection(event, prefer_selection=True)

    def on_trigger_list_focus_index_change(self, event=None):
        self._sync_trigger_list_selection(event, prefer_selection=False)

    def on_trigger_list_mouse_release(self, listbox: tk.Listbox) -> None:
        self._sync_trigger_list_selection(listbox, prefer_selection=True)

    def _sync_trigger_list_selection(self, event, *, prefer_selection: bool) -> None:
        triggers = get_active_triggers(self._app.data)
        widget = event if isinstance(event, tk.Listbox) else getattr(event, "widget", None)
        if not isinstance(widget, tk.Listbox):
            widget = None
        if widget is None or listbox_mouse_button_is_down(widget):
            return
        full_list = self._trigger_edit.listbox
        if widget is full_list and triggers:
            idx = int(widget.index(tk.ACTIVE))
            if 0 <= idx < len(triggers):
                self._app._selected_trigger_idx = idx
                self._sync_trigger_selection_preserving_range(widget)
                self.refresh_actions()
                self.update_status()
            return
        idx = sync_listbox_selection_to_focus(
            self._app, widget, len(triggers), prefer_selection=prefer_selection
        )
        if idx is not None:
            self.set_selected_trigger_index(idx)

    def on_trigger_double_click(self, _event=None):
        """トリガー一覧をダブルクリックしたらトリガー変更（rename_trigger）を開く"""
        self.rename_trigger()

    # ---------------- 表示系 ----------------
    def _sync_trigger_selection_preserving_range(self, listbox):
        bounds = selected_range(listbox)
        active = int(listbox.index(tk.ACTIVE))
        anchor = int(listbox.index(tk.ANCHOR))
        self.sync_trigger_selection_to_views()
        if bounds is not None:
            select_range(listbox, *bounds, active=active)
            listbox.selection_anchor(anchor)

    def refresh_triggers(self, select: tuple[int, int] | None = None):
        full_list = self._trigger_edit.listbox
        active = None
        anchor = None
        if select is None and full_list is not None and not getattr(self._app, "_compact_mode", False):
            bounds = selected_range(full_list)
            if bounds and bounds[0] != bounds[1]:
                active = int(full_list.index(tk.ACTIVE))
                if active == self.selected_trigger_index():
                    select = bounds
                    anchor = int(full_list.index(tk.ANCHOR))
        # Full/Compact 両方に反映
        for trigger_list in self._trigger_lists:
            try:
                trigger_list.delete(0, tk.END)
            except Exception:
                pass
        triggers = get_active_triggers(self._app.data)
        overlap = self._app._refresh_key_overlap_report()
        duplicate_indices = shadowed_duplicate_indices(triggers)
        for i, t in enumerate(triggers):
            k = normalize_key_name(t.get("key", ""))
            conflict = overlap.trigger_conflict(k)
            s = format_trigger_list_item(i, t)
            if conflict is not None:
                s = f"{s}（{self._trigger_conflict_reason(conflict.winner)}）"
            elif i in duplicate_indices:
                s = f"{s}（上のトリガーと重複）"
            for trigger_list in self._trigger_lists:
                try:
                    trigger_list.insert(tk.END, s)
                    self._set_trigger_row_color(
                        trigger_list, i, conflict is not None or i in duplicate_indices
                    )
                except Exception:
                    pass
            if k not in self._app._indices:
                self._app._indices[k] = 0

        # 選択を維持/補正（共通idx）
        if triggers:
            if select is not None:
                self._app._selected_trigger_idx = select[1] if active is None else active
            if getattr(self._app, "_selected_trigger_idx", None) is None:
                self._app._selected_trigger_idx = 0
            self._app._selected_trigger_idx = max(0, min(int(self._app._selected_trigger_idx), len(triggers) - 1))
            self.sync_trigger_selection_to_views()
            if select is not None and full_list is not None:
                select_range(full_list, *select, active=active)
                if anchor is not None:
                    full_list.selection_anchor(max(0, min(anchor, len(triggers) - 1)))
        self.sync_suppress_checkbox()
        self.sync_run_to_end_ui()
        self._app.keymap_panel.refresh_keymap_list_ui(overlap=overlap)
        self._app.layout.refresh_keyboard_window()
        self.update_status()

    @staticmethod
    def _trigger_conflict_reason(winner: str) -> str:
        return {
            "stop": "停止キーと重複",
            "toggle": "一時停止/再開キーと重複",
            "switch": "切替キーと重複",
        }.get(winner, "上位の割り当てと重複")

    @staticmethod
    def _set_trigger_row_color(listbox, index: int, is_shadowed: bool) -> None:
        color = "#888888" if is_shadowed else listbox.cget("foreground")
        listbox.itemconfigure(index, foreground=color)

    def refresh_actions(self, select: tuple[int, int] | None = None):
        # 省略画面では右側（action_list）が無いので、フル側のみ更新
        try:
            self._app.full_view.action_list.delete(0, tk.END)
        except Exception:
            self.sync_suppress_checkbox()
            self.sync_run_to_end_ui()
            self.update_status()
            call_view = getattr(self._app, "call_view", None)
            if call_view is not None:
                call_view.on_selection_changed()
            return
        trig = self.selected_trigger()
        if not trig:
            self.sync_suppress_checkbox()
            self.sync_run_to_end_ui()
            self.update_status()
            call_view = getattr(self._app, "call_view", None)
            if call_view is not None:
                call_view.on_selection_changed()
            return
        actions = trig.get("actions", [])
        key = normalize_key_name(trig.get("key", ""))
        effective = self.selected_trigger_is_effective()
        trigger_set_id = self._app._active_trigger_set_id()
        loop_iterations = self._app.state.loop_iterations_for(trigger_set_id, key) if effective else {}
        counters = self._app.state.counters
        rows = build_action_rows(
            actions,
            loop_iterations=loop_iterations,
            counters=counters,
            resolve_call=self._resolve_call_target,
        )
        if effective and key not in self._app._indices:
            self._app._indices[key] = 0
        # index補正
        if not effective:
            next_index = None
        elif not actions:
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
        if effective:
            next_index = self._app._indices[key]
        if actions and next_index == len(actions):
            next_index = 0
        for i, (item_text, background) in enumerate(rows):
            prefix = "▶ " if i == next_index else "　 "
            self._app.full_view.action_list.insert(tk.END, prefix + item_text)
            if background is not None:
                self._app.full_view.action_list.itemconfigure(i, background=background)
        if select is None:
            self.select_next_action_row(key)
        else:
            self._action_edit.select_action_range(*select)
        self.sync_suppress_checkbox()
        self.sync_run_to_end_ui()
        self.update_status()
        call_view = getattr(self._app, "call_view", None)
        if call_view is not None:
            call_view.on_selection_changed()

    def select_next_action_row(self, key: str):
        """現在の next index（self._indices[key]）を action_list 上で選択表示する（UIスレッド専用）"""
        key = normalize_key_name(key)
        if not self.selected_trigger_is_effective() or key != self.selected_trigger_key():
            return
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
            self._app.full_view.action_list.selection_anchor(idx)
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
                sequence_box = getattr(getattr(self._app, "full_view", None), "sequence_box", None)
                run_to_end_delay_entry = getattr(sequence_box, "run_to_end_delay_entry", None)
                if run_to_end_delay_entry is not None:
                    run_to_end_delay_entry.configure(state="disabled")
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
            sequence_box = getattr(getattr(self._app, "full_view", None), "sequence_box", None)
            run_to_end_delay_entry = getattr(sequence_box, "run_to_end_delay_entry", None)
            if run_to_end_delay_entry is not None:
                run_to_end_delay_entry.configure(state="normal")
        except Exception:
            pass

    def update_status(self):
        hook_state = "ON" if self._app.hook.hook_active else "OFF"
        keymap_text = self._app.keymap_panel.get_active_keymap_text()
        sel_key = self.selected_trigger_key() or "(未選択)"
        effective = self.selected_trigger_is_effective()
        if getattr(self._app, "_compact_mode", False):
            # 省略表示：フック状態 + キーマップの動作状態 + 選択中トリガー + 次に実行（行の内容）
            line = self.get_next_action_summary(sel_key)
            suffix = f" / 次: {line}" if effective else ""
            self._app.ui_vars.status_var.set(f"フック: {hook_state} / キーマップ: {keymap_text}\n選択: {sel_key}{suffix}")
            return

        triggers = get_active_triggers(self._app.data)
        keys = [normalize_key_name(t.get("key", "")) for t in triggers if t.get("key")]
        keys_text = ", ".join(keys) if keys else "(未設定)"
        # 「次」は run_to_end の場合、終端（len）なら次回は先頭なので 1 を出す
        next_i = 0
        try:
            trig = self.selected_trigger() if effective else None
            actions = trig.get("actions", []) if trig else []
            idx = int(self._app._indices.get(sel_key, 0) or 0) if effective else 0
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
        suffix = f" / 選択中の次: {next_i}" if effective else ""
        self._app.ui_vars.status_var.set(
            f"フック: {hook_state} / キーマップ: {keymap_text} / トリガー: {keys_text} / 選択中: {sel_key}{suffix}"
        )

    def get_next_action_summary(self, trigger_key: str) -> str:
        """省略表示用：次に実行されるアクションを1行で返す"""
        key = normalize_key_name(trigger_key or "")
        if not self.selected_trigger_is_effective():
            return ""
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

        loop_iterations = self._app.state.loop_iterations_for(
            self._app._active_trigger_set_id(), key
        )
        return format_next_action_summary(
            idx,
            a,
            loop_iterations=loop_iterations,
            counters=self._app.state.counters,
            resolve_call=self._resolve_call_target,
        )

    def _resolve_call_target(self, target: str) -> tuple[str, str | None]:
        key = normalize_key_name(target)
        for trigger in get_active_triggers(self._app.data):
            if normalize_key_name(trigger.get("key", "")) == key:
                return key, (trigger.get("label") or "").strip()
        return key, None

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
        return self._trigger_row_edit.add_trigger()

    def rename_trigger(self):
        return self._trigger_row_edit.rename_trigger()

    def delete_trigger(self):
        return self._trigger_row_edit.delete_trigger()

    def copy_triggers(self, event=None):
        return self._trigger_edit.copy_triggers(event)

    def paste_triggers(self, event=None):
        return self._trigger_edit.paste_triggers(event)

    def on_trigger_list_move(self, start: int, end: int, target_start: int) -> bool:
        return self._trigger_edit.move_trigger_range(start, end, target_start)

    # ---------------- Actions CRUD (selected trigger) ----------------
    def selected_action_index(self):
        return self._action_edit.selected_action_index()

    def add_action(self):
        return self._action_edit.add_action()

    def edit_action(self):
        return self._action_edit.edit_action()

    def delete_action(self):
        return self._action_edit.delete_action()

    def duplicate_action(self):
        return self._action_edit.duplicate_action()

    def copy_actions(self, event=None):
        return self._action_edit.copy_actions(event)

    def paste_actions(self, event=None):
        return self._action_edit.paste_actions(event)

    def move_action(self, delta: int):
        return self._action_edit.move_action(delta)

    def on_action_list_move(self, start: int, end: int, target_start: int) -> bool:
        return self._action_edit.move_action_range(start, end, target_start)

    def _counter_names(self) -> list[str]:
        return self._action_edit._counter_names()

    def on_action_list_select(self, _event=None, *, prefer_selection: bool = True):
        """ユーザーが action_list の行を選んだら、その行を『次に実行』として indices に反映"""
        if self._app._programmatic_action_select:
            return
        if not self.selected_trigger_is_effective():
            return
        listbox = self._app.full_view.action_list
        if listbox_mouse_button_is_down(listbox):
            return
        if prefer_selection and len(listbox.curselection()) > 1:
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
        idx = sync_listbox_selection_to_focus(
            self._app,
            listbox,
            len(actions),
            prefer_selection=prefer_selection,
        )
        if idx is None:
            return
        if 0 <= idx < len(actions):
            if idx == self._app._indices.get(key, 0):
                self.update_status()
                return
            self._app._indices[key] = idx
            self._app.sequence_runner.reset_loop_frames(key)
            self.refresh_actions()
            self.update_status()

    def on_action_list_focus_index_change(self, _event=None):
        return self._action_edit.on_focus_index_change(_event)

    def on_action_list_mouse_release(self, listbox: tk.Listbox) -> None:
        return self._action_edit.on_selection_commit(listbox)

    def on_action_double_click(self, _event=None):
        """シーケンス一覧をダブルクリックしたら編集を開く"""
        # 選択行が無いときは何もしない
        if not self._app.full_view.action_list.curselection():
            return
        self.edit_action()
