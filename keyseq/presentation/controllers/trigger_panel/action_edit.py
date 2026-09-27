from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.domain.sequence_control import (
    ACTION_TYPE_SYSTEM,
    MAX_LOOP_DEPTH,
    OP_LOOP_END,
    OP_LOOP_START,
    action_type,
    system_op,
)
from keyseq.domain.sequence_editing import (
    adjust_position_after_insert,
    can_insert_loop,
    can_move,
    delete_indices,
    insert_actions,
    loop_pair_items,
    pair_index,
    standalone_violation,
)
from keyseq.presentation.dialogs import ActionDialog
from keyseq.presentation.listbox_utils import focused_listbox_index


class ActionEditFlow:
    """トリガーの出力シーケンス編集フロー。"""

    def __init__(self, trigger_panel) -> None:
        self._trigger_panel = trigger_panel
        self._app = trigger_panel._app

    def selected_action_index(self):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            return None
        actions = trig.get("actions", [])
        if not isinstance(actions, list):
            return None
        return focused_listbox_index(self._app, self._app.full_view.action_list, len(actions))

    def add_action(self):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("追加", "まずトリガーを選択してください。")
            return
        actions = trig.setdefault("actions", [])
        selected_index = self._trigger_panel.selected_action_index()
        key = normalize_key_name(trig.get("key", ""))
        dialog = ActionDialog(
            self._app,
            title="追加",
            mode="add",
            counter_names=self._trigger_panel._counter_names(),
            config_root=getattr(self._app, "config_root", ""),
        )
        dialog.wait_window()
        position = int(self._app._indices.get(key, 0) or 0)
        result = getattr(self._app, "_dialog_result", None)
        if not result:
            return
        if standalone_violation(actions, result):
            messagebox.showinfo(
                "追加",
                "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。",
            )
            self._app._dialog_result = None
            return
        append_to_end = bool(getattr(dialog, "append_to_end", True))
        after_index = None if append_to_end or selected_index is None else selected_index
        is_loop = (
            action_type(result) == ACTION_TYPE_SYSTEM
            and system_op(result) == OP_LOOP_START
        )
        if is_loop and not can_insert_loop(actions, after_index):
            messagebox.showinfo(
                "追加",
                f"ループの入れ子が {MAX_LOOP_DEPTH} 段を超えるため追加できません。",
            )
            self._app._dialog_result = None
            return
        items = loop_pair_items(result) if is_loop else [result]
        insert_at = insert_actions(actions, items, after_index=after_index)
        self._app._indices[key] = adjust_position_after_insert(
            position, insert_at, len(items)
        )
        self._app.sequence_runner.reset_loop_frames(key)
        self._trigger_panel.refresh_actions()
        self._app.mark_sequence_dirty(trig)
        self._app._dialog_result = None

    def edit_action(self):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("編集", "まずトリガーを選択してください。")
            return
        idx = self._trigger_panel.selected_action_index()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        current = actions[idx]
        is_loop_row = (
            action_type(current) == ACTION_TYPE_SYSTEM
            and system_op(current) in (OP_LOOP_START, OP_LOOP_END)
        )
        target_idx = idx
        mode = "edit"
        if is_loop_row:
            paired_idx = pair_index(actions, idx)
            if paired_idx is None:
                messagebox.showinfo(
                    "編集",
                    "ループの対応が崩れているため編集できません。削除して追加し直してください",
                )
                return
            target_idx = paired_idx if system_op(current) == OP_LOOP_END else idx
            mode = "edit_loop"
        initial = actions[target_idx]
        ActionDialog(
            self._app,
            title="編集",
            initial=initial,
            mode=mode,
            counter_names=self._trigger_panel._counter_names(),
            config_root=getattr(self._app, "config_root", ""),
        ).wait_window()
        result = getattr(self._app, "_dialog_result", None)
        if result:
            if standalone_violation(actions, result, replace_index=target_idx):
                messagebox.showinfo(
                    "編集",
                    "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。",
                )
                self._app._dialog_result = None
                return
            actions[target_idx] = result
            self._app.sequence_runner.reset_loop_frames(normalize_key_name(trig.get("key", "")))
            self._trigger_panel.refresh_actions()
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
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("削除", "まずトリガーを選択してください。")
            return
        idx = self._trigger_panel.selected_action_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        indices = delete_indices(actions, idx)
        paired_loop = len(indices) > 1
        prompt = (
            "ループの始まりと終わりを削除します（中の行は残ります）。よろしいですか？"
            if paired_loop else "選択した行を削除しますか？"
        )
        if messagebox.askyesno("確認", prompt):
            for action_index in sorted(indices, reverse=True):
                del actions[action_index]
            self._app.sequence_runner.reset_loop_frames(normalize_key_name(trig.get("key", "")))
            self._trigger_panel.refresh_actions()
            self._app.mark_sequence_dirty(trig)

    def move_action(self, delta: int):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("移動", "まずトリガーを選択してください。")
            return
        idx = self._trigger_panel.selected_action_index()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        j = idx + delta
        if j < 0 or j >= len(actions):
            return
        if not can_move(actions, idx, delta):
            return
        actions[idx], actions[j] = actions[j], actions[idx]
        key = self._trigger_panel.selected_trigger_key()
        if key:
            self._app._indices[key] = j
            self._app.sequence_runner.reset_loop_frames(key)
        self._trigger_panel.refresh_actions()
        self._app.mark_sequence_dirty(trig)

    def _counter_names(self) -> list[str]:
        names = set()
        counters = getattr(getattr(self._app, "state", None), "counters", {})
        if isinstance(counters, dict):
            names.update(name for name in counters if isinstance(name, str) and name)
        for trigger in get_active_triggers(self._app.data):
            actions = trigger.get("actions", [])
            if not isinstance(actions, list):
                continue
            for action in actions:
                if not isinstance(action, dict):
                    continue
                name = action.get("counter")
                if isinstance(name, str) and name:
                    names.add(name)
        return sorted(names)
