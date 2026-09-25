from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from keyseq.application.key_overlap import KeyOverlapAnalysis
from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import INTERNAL_TRIGGER_SET_DIRTY, iter_trigger_sets, trigger_set_members
from keyseq.presentation.dialogs import KeymapEditDialog
from keyseq.presentation.listbox_utils import (
    focused_listbox_index,
    sync_listbox_selection_to_focus,
)


class KeymapPanelController:
    """キーマップ管理パネル（一覧表示・追加/変更/削除・キーボードUI連携）。"""

    SWITCH_BLOCKED_MESSAGE = "連続実行中のためキーマップを切り替えられません"

    def __init__(self, app) -> None:
        self._app = app

    def format_keymap_display_name(self, keymap: dict | None) -> str:
        if not isinstance(keymap, dict):
            return ""
        keymap_id = normalize_key_name(keymap.get("id", ""))
        label = str(keymap.get("label") or "").strip()
        return label or keymap_id

    def format_keymap_list_entry(
        self, index: int, keymap: dict, overlap: KeyOverlapAnalysis | None = None
    ) -> str:
        keymap_id = normalize_key_name(keymap.get("id", ""))
        marker = "> " if keymap_id and keymap_id == self._app.keymap_service.get_active_keymap_id(self._app.data) else "  "
        switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id) or "-"
        display_name = self.format_keymap_display_name(keymap) or f"keymap-{index + 1}"
        entry = f"{marker}{index + 1:02d}. {switch_key}: {display_name}"
        if overlap is None:
            overlap = self._app._key_overlap_report()
        conflict = overlap.keymap_switch_conflict(keymap_id, switch_key)
        if conflict is not None:
            entry += f"（{self._switch_conflict_reason(conflict.winner)}）"
        return entry

    @staticmethod
    def _switch_conflict_reason(winner: str) -> str:
        return "停止キーと重複" if winner == "stop" else "一時停止/再開キーと重複"

    @staticmethod
    def _set_keymap_row_color(listbox, index: int, is_shadowed: bool) -> None:
        color = "#888888" if is_shadowed else listbox.cget("foreground")
        listbox.itemconfigure(index, foreground=color)

    def selected_keymap_list_index(self) -> int | None:
        """keymap 管理Listboxの選択行を返す。"""
        keymap_box = getattr(getattr(self._app, "full_view", None), "keymap_box", None)
        listbox = getattr(keymap_box, "keymap_listbox", None)
        if listbox is None:
            return None
        return focused_listbox_index(self._app, listbox, len(self._app.keymap_service.get_keymaps(self._app.data)))

    def sync_keymap_manage_buttons(self) -> None:
        """keymap 件数に応じて管理ボタン状態を揃える。"""
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        has_selection = self.selected_keymap_list_index() is not None and bool(keymaps)
        edit_state = "normal" if has_selection else "disabled"
        delete_state = "normal" if has_selection and len(keymaps) > 1 else "disabled"
        keymap_box = getattr(getattr(self._app, "full_view", None), "keymap_box", None)
        if keymap_box is not None:
            keymap_box.keymap_edit_btn.configure(state=edit_state)
            keymap_box.keymap_delete_btn.configure(state=delete_state)

    def refresh_keymap_list_ui(self, preferred_index: int | None = None) -> None:
        """keymap 管理一覧の表示内容と選択を更新する。"""
        keymap_box = getattr(getattr(self._app, "full_view", None), "keymap_box", None)
        listbox = getattr(keymap_box, "keymap_listbox", None)
        if listbox is None:
            return

        try:
            listbox.delete(0, tk.END)
        except Exception:
            self.sync_keymap_manage_buttons()
            return

        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if not keymaps:
            listbox.insert(tk.END, "キーマップは未登録です")
            listbox.selection_clear(0, tk.END)
            self.sync_keymap_manage_buttons()
            return

        active_id = self._app.keymap_service.get_active_keymap_id(self._app.data)
        overlap = self._app._key_overlap_report()
        for index, keymap in enumerate(keymaps):
            listbox.insert(tk.END, self.format_keymap_list_entry(index, keymap, overlap))
            keymap_id = normalize_key_name(keymap.get("id", ""))
            switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id)
            conflict = overlap.keymap_switch_conflict(keymap_id, switch_key)
            self._set_keymap_row_color(listbox, index, conflict is not None)

        target_index = preferred_index
        if target_index is None:
            active_index = next(
                (
                    index
                    for index, keymap in enumerate(keymaps)
                    if normalize_key_name(keymap.get("id", "")) == active_id
                ),
                0,
            )
            target_index = active_index

        target_index = max(0, min(int(target_index), len(keymaps) - 1))
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(target_index)
        listbox.activate(target_index)
        listbox.see(target_index)
        self.sync_keymap_manage_buttons()

    def on_keymap_list_select(self, _event=None) -> None:
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        listbox = self._app.full_view.keymap_box.keymap_listbox
        index = sync_listbox_selection_to_focus(self._app, listbox, len(keymaps))
        if index is not None:
            keymap_id = normalize_key_name(keymaps[index].get("id", ""))
            if keymap_id != self._app.keymap_service.get_active_keymap_id(self._app.data):
                self.activate_keymap_by_id(keymap_id, preferred_index=index, show_flash=False)
        self.sync_keymap_manage_buttons()

    def on_keymap_list_focus_index_change(self, _event=None) -> None:
        self.on_keymap_list_select()

    def on_keymap_list_double_click(self, _event=None) -> None:
        """一覧ダブルクリックで選択中 keymap の編集導線を開く。"""
        self.edit_selected_keymap()

    def validate_keymap_switch_assignment(self, key: str, *, target_id: str, exclude_switch_key: str = "") -> bool:
        if self._app.trigger_service.is_stop_key_conflict(self._app.data, key):
            messagebox.showerror("設定できません", f"直接切替キーが停止キーと重複しています:\n{key}")
            return False
        if self._app.trigger_service.is_toggle_key_conflict(self._app.data, key):
            messagebox.showerror("設定できません", f"直接切替キーが一時停止/再開キーと重複しています:\n{key}")
            return False
        if normalize_key_name(key) in self._app._key_overlap_report().all_trigger_keys:
            messagebox.showerror("設定できません", f"直接切替キーが通常トリガーと重複しています:\n{key}")
            return False
        if normalize_key_name(key) in self._app._key_overlap_report().all_source_keys:
            messagebox.showerror("設定できません", f"直接切替キーがキーマップ元キーと重複しています:\n{key}")
            return False

        existing_target_id = self._app.keymap_service.get_keymap_by_switch_key(self._app.data, key)
        normalized_target_id = normalize_key_name(target_id)
        excluded_key = normalize_key_name(exclude_switch_key)
        if existing_target_id and key != excluded_key:
            existing_name = self.format_keymap_display_name(self._app.keymap_service.find_keymap(self._app.data, existing_target_id)) or existing_target_id
            messagebox.showerror("設定できません", f"この切替キーは既に使用されています:\n{key} -> {existing_name}")
            return False

        existing_switch_key = self._app.keymap_service.find_switch_key_for_keymap(
            self._app.data,
            normalized_target_id,
            exclude_key=excluded_key,
        )
        if existing_switch_key and existing_switch_key != key:
            target_name = self.format_keymap_display_name(self._app.keymap_service.find_keymap(self._app.data, normalized_target_id)) or normalized_target_id
            messagebox.showerror("設定できません", f"この keymap には既に直接切替キーがあります:\n{existing_switch_key} -> {target_name}")
            return False

        try:
            self._app.input_gateway.validate_key_name(key)
        except Exception as e:
            messagebox.showerror("設定できません", f"不明なキー名です:\n{key}\n\n{e}")
            return False

        return True

    def add_keymap(self) -> None:
        """必要な切替キーを確認してから、新しいキーマップを追加する。"""
        if not self._app.keymap_service.get_keymaps(self._app.data):
            created = self._app.keymap_service.create_keymap(self._app.data)
            self._app.mark_keymap_dirty(created)
            self._refresh_after_keymap_change()
            self._app._set_flash_message(f"キーマップを追加しました: {normalize_key_name(created.get('id', ''))}")
            return

        original_active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        pending = self._collect_missing_switch_edits(original_active)
        if pending is None:
            self._restore_active_keymap(original_active)
            return
        candidate_id = self._app.keymap_service.next_keymap_id(self._app.data)
        result = self._prompt_keymap_edit("キーマップ追加", "")
        if not result or not self._validate_addition_key(result.get("key", ""), candidate_id, pending):
            self._restore_active_keymap(original_active)
            return
        if not self._apply_pending_switch_edits(pending):
            self._restore_active_keymap(original_active)
            return

        created = self._app.keymap_service.create_keymap(self._app.data)
        created["label"] = str(result.get("label", "") or "").strip()
        self._app.keymap_service.set_keymap_switch_key(self._app.data, result["key"], candidate_id)
        self._app.mark_keymap_dirty(created)
        self._restore_active_keymap(original_active)
        self._refresh_after_keymap_change()
        self._app._set_flash_message(f"キーマップを追加しました: {normalize_key_name(created.get('id', ''))}")

    def add_imported_keymap(self, keymap: dict) -> bool:
        """個別読込を追加フローとして実行し、取消時は runtime を変えない。"""
        original_active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if not keymaps:
            self._append_keymap(keymap)
            self._refresh_after_keymap_change()
            return True

        pending = self._collect_missing_switch_edits(original_active)
        if pending is None:
            self._restore_active_keymap(original_active)
            return False
        result = self._prompt_keymap_edit("読込キーマップの追加", str(keymap.get("label") or ""))
        keymap_id = normalize_key_name(keymap.get("id", ""))
        if not result or not self._validate_addition_key(result.get("key", ""), keymap_id, pending):
            self._restore_active_keymap(original_active)
            return False
        if not self._apply_pending_switch_edits(pending):
            self._restore_active_keymap(original_active)
            return False

        keymap["label"] = str(result.get("label", "") or "").strip()
        self._append_keymap(keymap)
        self._app.keymap_service.set_keymap_switch_key(self._app.data, result["key"], keymap_id)
        self._app.mark_keymap_dirty(keymap)
        self._restore_active_keymap(original_active)
        self._refresh_after_keymap_change()
        return True

    def _collect_missing_switch_edits(self, original_active: str) -> list[tuple[dict, dict, int]] | None:
        pending = []
        for index, keymap in enumerate(self._app.keymap_service.get_keymaps(self._app.data)):
            keymap_id = normalize_key_name(keymap.get("id", ""))
            if self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id):
                continue
            if keymap_id != self._app.keymap_service.get_active_keymap_id(self._app.data):
                if not self.activate_keymap_by_id(keymap_id, preferred_index=index, show_flash=False):
                    return None
            name = self.format_keymap_display_name(keymap) or keymap_id
            messagebox.showerror("切替キーが必要です", f"{name} に切替キーを設定してください")
            result = self._prompt_keymap_edit("キーマップ変更", keymap)
            if not result or not normalize_key_name(result.get("key", "")):
                if result is not None:
                    messagebox.showerror("設定できません", "切替キーは必須です。")
                return None
            switch_key = normalize_key_name(result["key"])
            if not self._validate_addition_key(switch_key, keymap_id, pending):
                return None
            pending.append((keymap, result, index))
        self._restore_active_keymap(original_active)
        return pending

    def _prompt_keymap_edit(self, title: str, keymap_or_label) -> dict | None:
        keymap = keymap_or_label if isinstance(keymap_or_label, dict) else None
        label = str(keymap.get("label") or "") if keymap else str(keymap_or_label or "")
        dlg = KeymapEditDialog(
            self._app,
            title=title,
            initial_key="" if title != "キーマップ変更" else self._app.keymap_service.find_switch_key_for_keymap(
                self._app.data, keymap.get("id", "")
            ),
            initial_label=label,
        )
        dlg.wait_window()
        result = getattr(dlg, "result", None)
        return result if isinstance(result, dict) else None

    def _validate_addition_key(self, key: str, target_id: str, pending: list[tuple[dict, dict, int]]) -> bool:
        normalized = normalize_key_name(key)
        if not normalized:
            messagebox.showerror("設定できません", "切替キーは必須です。")
            return False
        if any(normalize_key_name(item[1].get("key", "")) == normalized for item in pending):
            messagebox.showerror("設定できません", f"直接切替キーは既に使用されています:\n{normalized}")
            return False
        return self.validate_keymap_switch_assignment(normalized, target_id=target_id)

    def _apply_pending_switch_edits(self, pending: list[tuple[dict, dict, int]]) -> bool:
        original_active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        for keymap, result, index in pending:
            keymap_id = normalize_key_name(keymap.get("id", ""))
            if keymap_id != self._app.keymap_service.get_active_keymap_id(self._app.data):
                if not self.activate_keymap_by_id(keymap_id, preferred_index=index, show_flash=False):
                    return False
            if not self.apply_keymap_edit(
                keymap, new_label=result.get("label", ""), new_key=result.get("key", ""),
                preferred_index=index,
            ):
                return False
        self._restore_active_keymap(original_active)
        return True

    def _append_keymap(self, keymap: dict) -> None:
        keymaps = self._app.data.get("keymaps")
        if not isinstance(keymaps, list):
            keymaps = []
            self._app.data["keymaps"] = keymaps
        if not self._app.data.get("active_keymap_id"):
            self._app.data["active_keymap_id"] = normalize_key_name(keymap.get("id", ""))
        keymaps.append(keymap)

    def _restore_active_keymap(self, keymap_id: str) -> None:
        if keymap_id and self._app.keymap_service.get_active_keymap_id(self._app.data) != keymap_id:
            self.activate_keymap_by_id(keymap_id, show_flash=False)

    def _refresh_after_keymap_change(self) -> None:
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()

    def rename_keymap_label(self) -> None:
        """選択中 keymap の表示ラベルだけを更新する。"""
        index = self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo("名前変更", "名前変更したい keymap を選択してください。")
            return

        target = keymaps[index]
        keymap_id = normalize_key_name(target.get("id", ""))
        current_label = str(target.get("label") or "").strip()
        self._app.hook.suspend_hook_for_dialog()
        try:
            new_label = simpledialog.askstring(
                "名前変更",
                f"keymap の表示名を入力してください。\n空欄にすると id 表示に戻ります。\n\nid: {keymap_id}",
                initialvalue=current_label,
                parent=self._app,
            )
        finally:
            self._app.hook.resume_hook_after_dialog()
        if new_label is None:
            return

        normalized_label = str(new_label).strip()
        if normalized_label == current_label:
            self._app._set_flash_message(f"keymap 名は変更なしです: {self.format_keymap_display_name(target) or keymap_id}")
            return

        target["label"] = normalized_label
        self.refresh_keymap_list_ui(preferred_index=index)
        self._app.layout.refresh_keyboard_window()
        self._app.trigger_panel.update_status()
        self._app.mark_keymap_dirty(target)
        if normalized_label:
            self._app._set_flash_message(f"keymap 名を変更しました: {normalized_label}")
        else:
            self._app._set_flash_message(f"keymap 名をクリアしました: {keymap_id}")

    def delete_keymap(self) -> None:
        """選択中の keymap を削除する。"""
        index = self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo("削除", "削除したい keymap を選択してください。")
            return
        if len(keymaps) == 1:
            messagebox.showerror("削除できません", "キーマップが1つだけのため削除できません。")
            return

        target = keymaps[index]
        target_id = normalize_key_name(target.get("id", ""))
        trigger_set_id = self._app.keymap_service.get_trigger_set_id(self._app.data, target_id)
        drops_trigger_set = len(trigger_set_members(self._app.data, target_id)) <= 1
        if target_id == self._app.keymap_service.get_active_keymap_id(self._app.data):
            if not self._app.state.can_switch_keymap(
                target_id, self._app.keymap_service.get_active_keymap_id(self._app.data), changes_active=True
            ):
                self.show_keymap_switch_blocked()
                self.refresh_keymap_list_ui()
                return
        target_name = self.format_keymap_display_name(target) or normalize_key_name(target.get("id", ""))
        prompt = f"keymap を削除しますか？\n\n{target_name}"
        if self._has_unsaved_children(target):
            prompt += "\n\n未保存のトリガー一覧・シーケンスも破棄されます。"
        if not messagebox.askyesno("確認", prompt):
            return

        deleted, next_active_id = self._app.keymap_service.delete_keymap(self._app.data, target.get("id", ""))
        if not deleted:
            messagebox.showerror("削除できません", "選択した keymap を削除できませんでした。")
            return
        if drops_trigger_set:
            self._app.state.forget_trigger_set(trigger_set_id)

        self._refresh_after_keymap_change()
        self._app.dirty_tracker.set_dirty(True)
        if next_active_id:
            self._app._set_flash_message(f"キーマップを削除しました: {target_name} / 現在: {self.get_active_keymap_text()}")
        else:
            self._app._set_flash_message(f"キーマップを削除しました: {target_name}")

    def _has_unsaved_children(self, keymap: dict) -> bool:
        keymap_id = normalize_key_name(keymap.get("id", ""))
        members = trigger_set_members(self._app.data, keymap_id)
        if len(members) > 1:
            return False
        if any(bool(member.get(INTERNAL_TRIGGER_SET_DIRTY, False)) for member in members):
            return True
        sequence_dirty_key = self._app.config_service.INTERNAL_SEQUENCE_DIRTY
        trigger_list = next(
            (items for _, group, items in iter_trigger_sets(self._app.data) if any(member is keymap for member in group)),
            [],
        )
        return any(
            bool(trigger.get(sequence_dirty_key, False))
            for trigger in trigger_list
            if isinstance(trigger, dict)
        )

    def show_keymap_switch_blocked(self) -> None:
        self._app.ui_vars.status_var.set(self.SWITCH_BLOCKED_MESSAGE)

    def edit_selected_keymap(self) -> None:
        """選択中の keymap をダイアログで編集する。"""
        index = self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo("変更", "編集したい keymap を選択してください。")
            return

        target = keymaps[index]
        target_id = normalize_key_name(target.get("id", ""))
        if not target_id:
            messagebox.showerror("変更できません", "選択した keymap を特定できませんでした。")
            return

        current_switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, target_id)
        dlg = KeymapEditDialog(
            self._app,
            title="キーマップ変更",
            initial_key=current_switch_key,
            initial_label=str(target.get("label") or "").strip(),
        )
        dlg.wait_window()
        result = getattr(dlg, "result", None)
        if not result:
            return

        self.apply_keymap_edit(
            target,
            new_label=result.get("label", ""),
            new_key=result.get("key", ""),
            preferred_index=index,
        )

    def apply_keymap_edit(self, keymap: dict, *, new_label: str, new_key: str, preferred_index: int | None = None) -> bool:
        keymap_id = normalize_key_name(keymap.get("id", ""))
        if not keymap_id:
            return False

        normalized_label = str(new_label or "").strip()
        normalized_key = normalize_key_name(new_key)
        current_label = str(keymap.get("label") or "").strip()
        current_switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id)

        if not normalized_key and len(self._app.keymap_service.get_keymaps(self._app.data)) > 1:
            messagebox.showerror("設定できません", "キーマップが2つ以上ある場合、切替キーは空にできません。")
            return False

        if normalized_key and not self.validate_keymap_switch_assignment(
            normalized_key,
            target_id=keymap_id,
            exclude_switch_key=current_switch_key,
        ):
            return False

        changed = False
        if normalized_label != current_label:
            keymap["label"] = normalized_label
            changed = True

        if current_switch_key and current_switch_key != normalized_key:
            changed = self._app.keymap_service.remove_keymap_switch_key(self._app.data, current_switch_key) or changed

        if normalized_key and normalized_key != current_switch_key:
            changed = self._app.keymap_service.set_keymap_switch_key(self._app.data, normalized_key, keymap_id) or changed

        if not changed:
            self._app._set_flash_message(f"キーマップは変更なしです: {self.format_keymap_display_name(keymap) or keymap_id}")
            return False

        self.refresh_keymap_list_ui()
        self._app.trigger_panel.refresh_triggers()
        self._app.mark_keymap_dirty(keymap)
        self._app._set_flash_message(f"キーマップを変更しました: {self.format_keymap_display_name(keymap) or keymap_id}")
        return True

    def activate_keymap_by_id(
        self,
        keymap_id: str,
        *,
        preferred_index: int | None = None,
        show_flash: bool = True,
    ) -> bool:
        target_id = normalize_key_name(keymap_id)
        if not target_id:
            return False

        active_before = self._app.keymap_service.get_active_keymap_id(self._app.data)
        if not self._app.state.can_switch_keymap(target_id, active_before):
            self.show_keymap_switch_blocked()
            self.refresh_keymap_list_ui()
            return False

        changed = self._app.keymap_service.set_active_keymap_id(self._app.data, target_id)
        active_id = self._app.keymap_service.get_active_keymap_id(self._app.data)
        if active_id != target_id:
            return False

        if preferred_index is None:
            keymaps = self._app.keymap_service.get_keymaps(self._app.data)
            preferred_index = next(
                (index for index, keymap in enumerate(keymaps) if normalize_key_name(keymap.get("id", "")) == target_id),
                None,
            )

        self.refresh_keymap_list_ui(preferred_index=preferred_index)
        if changed:
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
        else:
            self._app.layout.refresh_keyboard_window()
            self._app.trigger_panel.update_status()
        if show_flash:
            if changed:
                self._app._set_flash_message(f"アクティブなキーマップを切り替えました: {self.get_active_keymap_text()}")
            else:
                self._app._set_flash_message(f"アクティブなキーマップは変更なしです: {self.get_active_keymap_text()}")
        return True

    def get_active_keymap_text(self) -> str:
        label = self._app.keymap_service.get_active_keymap_label(self._app.data)
        if not label:
            return "(なし)"
        if not self._app.hook.hook_active:
            return f"{label}（フック停止中）"
        if not self._app.hook.custom_input_enabled:
            return f"{label}（一時停止）"
        return label

    def assign_keymap_from_keyboard_ui(self, source_key: str, target_key: str) -> bool:
        source = normalize_key_name(source_key)
        target = normalize_key_name(target_key)
        if not source or not target:
            return False
        if "+" in target:
            messagebox.showerror("設定できません", "キーマップは単キーのみ対応です。")
            return False
        if source in {
            normalize_key_name(self._app.data.get("hook_stop_key", "")),
            normalize_key_name(self._app.data.get("hook_toggle_key", "")),
        }:
            messagebox.showerror("設定できません", f"このキーは予約キーのため、キーマップ元キーにできません:\n{source}")
            return False
        if self._app.keymap_service.get_keymap_by_switch_key(self._app.data, source):
            messagebox.showerror("設定できません", f"このキーはキーマップ直接切替キーに設定されています:\n{source}")
            return False
        if source in self._app._key_overlap_report().active_trigger_keys:
            messagebox.showerror("設定できません", f"このキーはアクティブキーマップのトリガーキーに設定されています:\n{source}")
            return False

        try:
            self._app.input_gateway.validate_key_name(target)
        except Exception as e:
            messagebox.showerror("設定できません", f"不明なキー名です:\n{target}\n\n{e}")
            return False

        keymap_id, changed = self._app.keymap_service.set_mapping(self._app.data, source, target)
        self._app.trigger_panel.refresh_triggers()
        if changed:
            self._app.mark_keymap_dirty(self._app.keymap_service.find_keymap(self._app.data, keymap_id))
            self._app._set_flash_message(f"キーマップを更新しました: {source} -> {target} ({keymap_id})")
        else:
            self._app._set_flash_message(f"キーマップは変更なしです: {source} -> {target}")
        return True

    def clear_keymap_from_keyboard_ui(self, source_key: str) -> bool:
        source = normalize_key_name(source_key)
        if not source:
            return False
        keymap_id, changed = self._app.keymap_service.clear_mapping(self._app.data, source)
        self._app.trigger_panel.refresh_triggers()
        if changed:
            self._app.mark_keymap_dirty(self._app.keymap_service.find_keymap(self._app.data, keymap_id))
            self._app._set_flash_message(f"キーマップをクリアしました: {source} ({keymap_id})")
            return True

        self._app._set_flash_message(f"クリア対象のキーマップはありません: {source}")
        return False
