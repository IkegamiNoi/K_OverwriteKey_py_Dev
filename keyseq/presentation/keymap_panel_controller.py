from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from keyseq.domain.config import normalize_key_name
from keyseq.presentation.dialogs import KeymapEditDialog
from keyseq.presentation.listbox_utils import (
    focused_listbox_index,
    sync_listbox_selection_to_focus,
)


class KeymapPanelController:
    """キーマップ管理パネル（一覧表示・追加/変更/削除/選択・キーボードUI連携）。"""

    def __init__(self, app) -> None:
        self._app = app

    def format_keymap_display_name(self, keymap: dict | None) -> str:
        if not isinstance(keymap, dict):
            return ""
        keymap_id = normalize_key_name(keymap.get("id", ""))
        label = str(keymap.get("label") or "").strip()
        return label or keymap_id

    def format_keymap_list_entry(self, index: int, keymap: dict) -> str:
        keymap_id = normalize_key_name(keymap.get("id", ""))
        marker = "> " if keymap_id and keymap_id == self._app.keymap_service.get_active_keymap_id(self._app.data) else "  "
        switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id) or "-"
        display_name = self.format_keymap_display_name(keymap) or f"keymap-{index + 1}"
        return f"{marker}{index + 1:02d}. {switch_key}: {display_name}"

    def selected_keymap_list_index(self) -> int | None:
        """keymap 管理Listboxの選択行を返す。"""
        if not hasattr(self._app, "keymap_listbox"):
            return None
        return focused_listbox_index(self._app, self._app.keymap_listbox, len(self._app.keymap_service.get_keymaps(self._app.data)))

    def sync_keymap_manage_buttons(self) -> None:
        """keymap 件数に応じて管理ボタン状態を揃える。"""
        has_selection = self.selected_keymap_list_index() is not None and bool(self._app.keymap_service.get_keymaps(self._app.data))
        state = "normal" if has_selection else "disabled"
        if hasattr(self._app, "keymap_edit_btn"):
            self._app.keymap_edit_btn.configure(state=state)
        if hasattr(self._app, "keymap_delete_btn"):
            self._app.keymap_delete_btn.configure(state=state)
        if hasattr(self._app, "keymap_select_btn"):
            self._app.keymap_select_btn.configure(state=state)

    def refresh_keymap_list_ui(self, preferred_index: int | None = None) -> None:
        """keymap 管理一覧の表示内容と選択を更新する。"""
        if not hasattr(self._app, "keymap_listbox"):
            return

        listbox = self._app.keymap_listbox
        try:
            current_index = self.selected_keymap_list_index()
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
        for index, keymap in enumerate(keymaps):
            listbox.insert(tk.END, self.format_keymap_list_entry(index, keymap))

        target_index = preferred_index
        if target_index is None:
            target_index = current_index
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
        sync_listbox_selection_to_focus(self._app, self._app.keymap_listbox, len(self._app.keymap_service.get_keymaps(self._app.data)))
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
            messagebox.showerror("設定できません", f"直接切替キーがモード切替キーと重複しています:\n{key}")
            return False
        if self._app.trigger_service.key_exists(self._app.data, key):
            messagebox.showerror("設定できません", f"直接切替キーが通常トリガーと重複しています:\n{key}")
            return False
        if self._app.keymap_service.source_key_exists(self._app.data, key):
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
        """空の keymap を追加する。"""
        created = self._app.keymap_service.create_keymap(self._app.data)
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        preferred_index = max(0, len(keymaps) - 1)
        self.refresh_keymap_list_ui(preferred_index=preferred_index)
        self._app._refresh_keyboard_window()
        self._app._update_status()
        self._app._mark_keymap_dirty(created)
        self._app._set_flash_message(f"キーマップを追加しました: {normalize_key_name(created.get('id', ''))}")

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
        self._app.suspend_hook_for_dialog()
        try:
            new_label = simpledialog.askstring(
                "名前変更",
                f"keymap の表示名を入力してください。\n空欄にすると id 表示に戻ります。\n\nid: {keymap_id}",
                initialvalue=current_label,
                parent=self._app,
            )
        finally:
            self._app.resume_hook_after_dialog()
        if new_label is None:
            return

        normalized_label = str(new_label).strip()
        if normalized_label == current_label:
            self._app._set_flash_message(f"keymap 名は変更なしです: {self.format_keymap_display_name(target) or keymap_id}")
            return

        target["label"] = normalized_label
        self.refresh_keymap_list_ui(preferred_index=index)
        self._app._refresh_keyboard_window()
        self._app._update_status()
        self._app._mark_keymap_dirty(target)
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

        target = keymaps[index]
        target_name = self.format_keymap_display_name(target) or normalize_key_name(target.get("id", ""))
        if not messagebox.askyesno("確認", f"keymap を削除しますか？\n\n{target_name}"):
            return

        deleted, next_active_id = self._app.keymap_service.delete_keymap(self._app.data, target.get("id", ""))
        if not deleted:
            messagebox.showerror("削除できません", "選択した keymap を削除できませんでした。")
            return

        remaining_count = len(self._app.keymap_service.get_keymaps(self._app.data))
        preferred_index = None if remaining_count <= 0 else min(index, remaining_count - 1)
        self.refresh_keymap_list_ui(preferred_index=preferred_index)
        self._app._refresh_keyboard_window()
        self._app._update_status()
        self._app._set_dirty(True)
        if next_active_id:
            self._app._set_flash_message(f"キーマップを削除しました: {target_name} / 現在: {self.get_active_keymap_text()}")
        else:
            self._app._set_flash_message(f"キーマップを削除しました: {target_name}")

    def select_keymap(self) -> None:
        """選択中の keymap を active にする。"""
        index = self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo("選択", "アクティブにしたい keymap を選択してください。")
            return

        target = keymaps[index]
        self.activate_keymap_by_id(target.get("id", ""), preferred_index=index, mark_dirty=True, show_flash=True)

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

        self.refresh_keymap_list_ui(preferred_index=preferred_index)
        self._app._refresh_keyboard_window()
        self._app._update_status()
        self._app._mark_keymap_dirty(keymap)
        self._app._set_flash_message(f"キーマップを変更しました: {self.format_keymap_display_name(keymap) or keymap_id}")
        return True

    def activate_keymap_by_id(
        self,
        keymap_id: str,
        *,
        preferred_index: int | None = None,
        mark_dirty: bool = False,
        show_flash: bool = True,
    ) -> bool:
        target_id = normalize_key_name(keymap_id)
        if not target_id:
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
        self._app._refresh_keyboard_window()
        self._app._update_status()
        if changed and mark_dirty:
            self._app._set_dirty(True)
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
        if not (self._app.hook_active and self._app.custom_input_enabled):
            return f"{label} (待機)"
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

        try:
            self._app.input_gateway.validate_key_name(target)
        except Exception as e:
            messagebox.showerror("設定できません", f"不明なキー名です:\n{target}\n\n{e}")
            return False

        keymap_id, changed = self._app.keymap_service.set_mapping(self._app.data, source, target)
        self.refresh_keymap_list_ui()
        self._app._refresh_keyboard_window()
        self._app._update_status()
        if changed:
            self._app._mark_keymap_dirty(self._app.keymap_service.find_keymap(self._app.data, keymap_id))
            self._app._set_flash_message(f"キーマップを更新しました: {source} -> {target} ({keymap_id})")
        else:
            self._app._set_flash_message(f"キーマップは変更なしです: {source} -> {target}")
        return True

    def clear_keymap_from_keyboard_ui(self, source_key: str) -> bool:
        source = normalize_key_name(source_key)
        if not source:
            return False
        keymap_id, changed = self._app.keymap_service.clear_mapping(self._app.data, source)
        self.refresh_keymap_list_ui()
        self._app._refresh_keyboard_window()
        self._app._update_status()
        if changed:
            self._app._mark_keymap_dirty(self._app.keymap_service.find_keymap(self._app.data, keymap_id))
            self._app._set_flash_message(f"キーマップをクリアしました: {source} ({keymap_id})")
            return True

        self._app._set_flash_message(f"クリア対象のキーマップはありません: {source}")
        return False
