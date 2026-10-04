from __future__ import annotations

from tkinter import messagebox

from keyseq.domain.call_graph import rename_call_targets
from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import ensure_active_triggers, get_active_triggers
from keyseq.domain.trigger_duplicates import is_effective_trigger
from keyseq.presentation.dialogs import TriggerDialog
from keyseq.presentation.controllers.trigger_panel.effective_row_transition import (
    apply_effective_row_transition,
)


class TriggerRowEditFlow:
    """トリガー行の追加・改名・削除。"""

    def __init__(self, trigger_panel) -> None:
        self._panel = trigger_panel

    def add_trigger(self):
        dlg = TriggerDialog(self._panel._app, title="トリガー追加")
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        key = normalize_key_name(res.get("key", ""))
        label = (res.get("label") or "").strip()
        if not key:
            return
        triggers = ensure_active_triggers(self._panel._app.data)
        # 重複チェック
        if self._panel._app.trigger_service.key_exists(self._panel._app.data, key):
            messagebox.showerror("追加できません", f"すでに存在します: {key}")
            return
        # フック停止トリガーとの重複チェック
        if self._panel._app.trigger_service.is_stop_key_conflict(self._panel._app.data, key):
            messagebox.showerror("追加できません", f"このキーはフック停止トリガーに設定されています:\n{key}")
            return
        if self._panel._app.trigger_service.is_toggle_key_conflict(self._panel._app.data, key):
            messagebox.showerror("追加できません", f"このキーは一時停止/再開キーに設定されています:\n{key}")
            return
        if self._panel._app.keymap_service.get_keymap_by_switch_key(self._panel._app.data, key):
            messagebox.showerror("追加できません", f"このキーはキーマップ直接切替キーに設定されています:\n{key}")
            return
        if key in self._panel._app._key_overlap_report().active_source_keys:
            messagebox.showerror("追加できません", f"このキーはアクティブキーマップの置換元キーに設定されています:\n{key}")
            return
        triggers.append({"key": key, "label": label, "suppress": True, "run_to_end": False, "actions": []})
        new_index = len(triggers) - 1
        self._panel._app._indices.setdefault(key, 0)
        self._panel.refresh_triggers()
        self._panel._app.dirty_tracker.mark_trigger_set_dirty()
        self._panel._app.mark_sequence_dirty(triggers[-1])
        self._panel.set_selected_trigger_index(new_index)
        if self._panel._app.hook.hook_active:
            self._panel._app.hook.start_hook()

    def rename_trigger(self):
        t = self._panel.selected_trigger()
        if not t:
            messagebox.showinfo("変更", "変更したいトリガーを選択してください。")
            return
        old = normalize_key_name(t.get("key", ""))
        triggers = get_active_triggers(self._panel._app.data)
        trigger_index = next(
            (index for index, trigger in enumerate(triggers) if trigger is t), None
        )
        was_effective = (
            trigger_index is not None and is_effective_trigger(triggers, trigger_index)
        )
        cur_label = (t.get("label") or "").strip()
        dlg = TriggerDialog(self._panel._app, title="トリガー変更", initial_key=old, initial_label=cur_label)
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        new = normalize_key_name(res.get("key", ""))
        new_label = (res.get("label") or "").strip()
        if not new:
            return
        if old != new:
            if self._panel._app.trigger_service.key_exists(
                self._panel._app.data, new, exclude_trigger=t
            ):
                messagebox.showerror("変更できません", f"すでに存在します: {new}")
                return
            if self._panel._app.trigger_service.is_stop_key_conflict(self._panel._app.data, new):
                messagebox.showerror("変更できません", f"このキーはフック停止トリガーに設定されています:\n{new}")
                return
            if self._panel._app.trigger_service.is_toggle_key_conflict(self._panel._app.data, new):
                messagebox.showerror("変更できません", f"このキーは一時停止/再開キーに設定されています:\n{new}")
                return
            if self._panel._app.keymap_service.get_keymap_by_switch_key(self._panel._app.data, new):
                messagebox.showerror("変更できません", f"このキーはキーマップ直接切替キーに設定されています:\n{new}")
                return
            if new in self._panel._app._key_overlap_report().active_source_keys:
                messagebox.showerror("変更できません", f"このキーはアクティブキーマップの置換元キーに設定されています:\n{new}")
                return
        after = list(triggers)
        if old != new and trigger_index is not None:
            after[trigger_index] = dict(t, key=new)
        if not apply_effective_row_transition(
            self._panel._app, triggers, after,
            lambda: self._apply_trigger_rename(t, old, new, new_label, was_effective),
        ):
            return
        self._panel.refresh_triggers()
        self._panel.refresh_actions()
        if old != new:
            self._panel._app.dirty_tracker.mark_trigger_set_dirty()
        if cur_label != new_label:
            self._panel._app.mark_sequence_dirty(t)
        if self._panel._app.hook.hook_active:
            self._panel._app.hook.start_hook()

    def _apply_trigger_rename(self, t, old, new, new_label, was_effective):
        if old != new and was_effective:
            self._panel._app.sequence_runner.cancel_pending_wait(old)
        if old != new and was_effective:
            # Transfer key-scoped runtime state only with its effective row.
            self._panel._app._indices.setdefault(old, 0)
            self._panel._app._indices.setdefault(new, self._panel._app._indices.get(old, 0))
            if old in self._panel._app._indices:
                del self._panel._app._indices[old]
            frames = self._panel._app.state.loop_frames_for(self._panel._app._active_trigger_set_id())
            if old in frames:
                frames.setdefault(new, frames[old])
                del frames[old]
            self._panel._app.state.rekey_trigger(self._panel._app._active_trigger_set_id(), old, new)
        elif old != new:
            self._panel._app._indices.setdefault(new, 0)
        t["key"] = new
        t["label"] = new_label
        if old != new and was_effective:
            for trigger in get_active_triggers(self._panel._app.data):
                actions = trigger.get("actions", [])
                if not isinstance(actions, list):
                    continue
                renamed_actions = rename_call_targets(actions, old, new)
                if renamed_actions is not None:
                    trigger["actions"] = renamed_actions
                    self._panel._app.mark_sequence_dirty(trigger)

    def delete_trigger(self):
        bounds = self._panel._trigger_edit.selection_bounds()
        if bounds is not None and bounds[0] != bounds[1]:
            return self._panel._trigger_edit.delete_trigger_range()
        idx = self._panel.selected_trigger_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したいトリガーを選択してください。")
            return
        triggers = get_active_triggers(self._panel._app.data)
        if idx < 0 or idx >= len(triggers):
            return
        key = normalize_key_name(triggers[idx].get("key", ""))
        if messagebox.askyesno("確認", f"トリガー {key} を削除しますか？"):
            after = triggers[:idx] + triggers[idx + 1:]
            if not apply_effective_row_transition(
                self._panel._app, triggers, after, lambda: triggers.__delitem__(idx),
            ):
                return
            self._panel.refresh_triggers()
            self._panel.refresh_actions()
            self._panel._app.dirty_tracker.mark_trigger_set_dirty()
            if self._panel._app.hook.hook_active:
                self._panel._app.hook.start_hook()

