from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from keyseq.domain.config import normalize_key_name, safe_deepcopy
from keyseq.domain.call_graph import edit_call_violation
from keyseq.domain.control_target import edit_control_target_violation
from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.domain.trigger_duplicates import is_effective_trigger, shadowed_duplicate_indices
from keyseq.domain.list_editing import index_after_reorder, move_block, shift_block
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
    can_move_block,
    closed_loop_range,
    delete_indices,
    insert_actions,
    loop_pair_items,
    PASTE_STANDALONE,
    PASTE_TOO_DEEP,
    PASTE_UNBALANCED_LOOP,
    paste_violation,
    pair_index,
    standalone_violation,
)
from keyseq.presentation.dialogs import ActionDialog
from keyseq.presentation.listbox_utils import focused_listbox_index
from keyseq.presentation.listbox_range_drag import select_range, selected_range
from keyseq.presentation.list_clipboard import CLIP_ACTIONS


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

    def _is_effective_row(self, trigger: dict) -> bool:
        rows = get_active_triggers(self._app.data)
        index = next((i for i, row in enumerate(rows) if row is trigger), None)
        return index is not None and is_effective_trigger(rows, index)

    def add_action(self):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("追加", "まずトリガーを選択してください。")
            return
        effective = self._is_effective_row(trig)
        actions = trig.setdefault("actions", [])
        selected_index = self._trigger_panel.selected_action_index()
        key = normalize_key_name(trig.get("key", ""))
        call_candidates, call_check, control_target_check = self._call_dialog_options(key)
        dialog = ActionDialog(
            self._app,
            title="追加",
            mode="add",
            counter_names=self._trigger_panel._counter_names(),
            config_root=getattr(self._app, "config_root", ""),
            call_candidates=call_candidates,
            call_check=call_check,
            control_target_check=control_target_check,
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
        if effective:
            self._app._indices[key] = adjust_position_after_insert(
                position, insert_at, len(items)
            )
            self._app.sequence_runner.reset_loop_frames(key)
        self._trigger_panel.refresh_actions()
        self._app.mark_sequence_dirty(trig)
        self._app._dialog_result = None

    def duplicate_action(self) -> None:
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            return
        actions = trig.get("actions", [])
        bounds = self._copy_range(actions)
        if bounds is None:
            return
        start, end = bounds
        self._append_actions(trig, safe_deepcopy(closed_loop_range(actions, start, end)), "複製")

    def copy_actions(self, _event=None) -> str:
        trig = self._trigger_panel.selected_trigger()
        if trig:
            actions = trig.get("actions", [])
            bounds = self._copy_range(actions)
            if bounds is not None:
                start, end = bounds
                self._app.list_clipboard.copy(
                    CLIP_ACTIONS, closed_loop_range(actions, start, end)
                )
        return "break"

    def paste_actions(self, _event=None) -> str:
        trig = self._trigger_panel.selected_trigger()
        items = self._app.list_clipboard.paste(CLIP_ACTIONS)
        if trig and items:
            self._append_actions(trig, items, "貼り付け")
        return "break"

    def _copy_range(self, actions: list) -> tuple[int, int] | None:
        if not isinstance(actions, list) or not actions:
            return None
        listbox = getattr(getattr(self._app, "full_view", None), "action_list", None)
        bounds = selected_range(listbox) if listbox is not None else None
        if bounds is not None:
            return bounds
        index = self._trigger_panel.selected_action_index()
        return (index, index) if index is not None and 0 <= index < len(actions) else None

    def _append_actions(self, trig: dict, items: list[dict], title: str) -> None:
        actions = trig.get("actions", [])
        reason = paste_violation(actions, items)
        if reason:
            self._show_append_violation(title, reason)
            return
        effective = self._is_effective_row(trig)
        key = normalize_key_name(trig.get("key", ""))
        old_length = len(actions)
        position = int(self._app._indices.get(key, 0) or 0)
        actions.extend(items)
        if effective:
            if bool(trig.get("run_to_end", False)) and position == old_length:
                self._app._indices[key] = len(actions)
            self._app.sequence_runner.reset_loop_frames(key)
        self._trigger_panel.refresh_actions(select=(old_length, len(actions) - 1))
        self._app.mark_sequence_dirty(trig)

    @staticmethod
    def _show_append_violation(title: str, reason: str) -> None:
        messages = {
            PASTE_UNBALANCED_LOOP: "対になっていないループの始まり / 終わりは複製 / 貼り付けできません。",
            PASTE_TOO_DEEP: f"ループの入れ子が {MAX_LOOP_DEPTH} 段を超えるため複製 / 貼り付けできません。",
            PASTE_STANDALONE: "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。",
        }
        messagebox.showinfo(title, messages[reason])

    def edit_action(self):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("編集", "まずトリガーを選択してください。")
            return
        effective = self._is_effective_row(trig)
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
        key = normalize_key_name(trig.get("key", ""))
        call_candidates, call_check, control_target_check = self._call_dialog_options(key)
        ActionDialog(
            self._app,
            title="編集",
            initial=initial,
            mode=mode,
            counter_names=self._trigger_panel._counter_names(),
            config_root=getattr(self._app, "config_root", ""),
            call_candidates=call_candidates,
            call_check=call_check,
            control_target_check=control_target_check,
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
            if effective:
                self._app.sequence_runner.reset_loop_frames(
                    normalize_key_name(trig.get("key", ""))
                )
            self._trigger_panel.refresh_actions(select=(idx, idx))
            self._app.mark_sequence_dirty(trig)
            self._app._dialog_result = None

    def delete_action(self):
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            messagebox.showinfo("削除", "まずトリガーを選択してください。")
            return
        effective = self._is_effective_row(trig)
        idx = self._trigger_panel.selected_action_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        start, end = self._selection_bounds(idx)
        selected = set(range(start, end + 1))
        indices = {i for row in selected for i in delete_indices(actions, row)}
        prompt = self._delete_prompt(actions, selected, indices)
        if messagebox.askyesno("確認", prompt):
            before = list(actions)
            key = normalize_key_name(trig.get("key", ""))
            position = int(self._app._indices.get(key, 0) or 0)
            for action_index in sorted(indices, reverse=True):
                del actions[action_index]
            if effective:
                if position not in indices:
                    self._app._indices[key] = index_after_reorder(before, actions, position)
                self._app.sequence_runner.reset_loop_frames(key)
            self._trigger_panel.refresh_actions(select=(start, start))
            self._app.mark_sequence_dirty(trig)

    def _delete_prompt(self, actions: list, selected: set[int], indices: set[int]) -> str:
        if len(indices) == 1:
            return "選択した行を削除しますか？"
        first = min(indices)
        if len(indices) == 2 and set(delete_indices(actions, first)) == indices:
            return "ループの始まりと終わりを削除します（中の行は残ります）。よろしいですか？"
        prompt = f"選択した {len(indices)} 行を削除しますか？"
        if indices - selected:
            prompt += "\nループの始まりと終わりは対で削除します（中の行は残ります）。"
        return prompt

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
        start, end = self._selection_bounds(idx)
        target = shift_block(len(actions), start, end, delta)
        if target is None:
            return
        self.move_action_range(start, end, target)

    def move_action_range(self, start: int, end: int, target_start: int) -> bool:
        trig = self._trigger_panel.selected_trigger()
        if not trig:
            return False
        effective = self._is_effective_row(trig)
        actions = trig.get("actions", [])
        if not can_move_block(actions, start, end, target_start):
            self._app._set_flash_message("ループの始まりと終わりの組が変わるため移動できません")
            return False
        after = move_block(actions, start, end, target_start)
        if all(old is new for old, new in zip(actions, after)):
            return True
        key = normalize_key_name(trig.get("key", ""))
        position = int(self._app._indices.get(key, 0) or 0)
        if effective:
            self._app._indices[key] = index_after_reorder(actions, after, position)
        actions[:] = after
        if effective:
            self._app.sequence_runner.reset_loop_frames(key)
        target = max(0, min(target_start, len(actions) - (end - start + 1)))
        self._trigger_panel.refresh_actions(select=(target, target + end - start))
        self._app.mark_sequence_dirty(trig)
        return True

    def _selection_bounds(self, fallback: int) -> tuple[int, int]:
        listbox = getattr(getattr(self._app, "full_view", None), "action_list", None)
        bounds = selected_range(listbox) if listbox is not None else None
        return bounds if bounds and bounds[0] != bounds[1] else (fallback, fallback)

    def select_action_range(self, start: int, end: int) -> None:
        self._app._programmatic_action_select = True
        try:
            select_range(self._app.full_view.action_list, start, end)
        finally:
            self._app._programmatic_action_select = False

    def on_selection_commit(self, listbox: tk.Listbox) -> None:
        sequence_box = self._app.full_view.sequence_box
        if not sequence_box.action_range_drag.last_commit_extended:
            self._trigger_panel.on_action_list_select(prefer_selection=True)

    def on_focus_index_change(self, event) -> None:
        if event is None or event.state & 0x0001:
            return
        if event.keysym in ("Up", "Down", "Prior", "Next", "Home", "End"):
            self._trigger_panel.on_action_list_select(prefer_selection=False)

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

    def _call_dialog_options(
        self, owner_key: str,
    ) -> tuple[list[tuple[str, str]], Callable[[str], str | None], Callable[[str], str | None]]:
        triggers = get_active_triggers(self._app.data)
        shadowed = shadowed_duplicate_indices(triggers)
        candidates = []
        for index, trigger in enumerate(triggers):
            if not isinstance(trigger, dict) or index in shadowed:
                continue
            key = normalize_key_name(trigger.get("key", ""))
            if not key or key == owner_key:
                continue
            label = trigger.get("label", "")
            candidates.append((key, label if isinstance(label, str) else ""))

        def find_trigger(target: str) -> dict | None:
            normalized = normalize_key_name(target)
            return next(
                (trigger for trigger in triggers
                 if normalize_key_name(trigger.get("key", "")) == normalized),
                None,
            )

        return (
            candidates,
            lambda target: edit_call_violation(owner_key, target, find_trigger),
            lambda target: edit_control_target_violation(owner_key, target, find_trigger),
        )
