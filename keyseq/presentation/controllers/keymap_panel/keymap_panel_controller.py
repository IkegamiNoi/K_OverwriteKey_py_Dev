from __future__ import annotations

import tkinter as tk
from copy import deepcopy
from tkinter import messagebox, simpledialog

from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.application.key_overlap import KeyOverlapAnalysis
from keyseq.domain.config import normalize_identifier, normalize_key_name
from keyseq.domain.key_identifiers import is_prohibited_assign_key
from keyseq.domain.keymap_triggers import INTERNAL_TRIGGER_SET_DIRTY, iter_trigger_sets, trigger_set_members
from keyseq.domain.screen_grid import new_enabled_grid
from keyseq.infrastructure import win32_window
from keyseq.presentation.dialogs import KeymapEditDialog
from keyseq.presentation.listbox_range_drag import select_range
from keyseq.presentation.tk_keys import numpad_name_from_tk_event, normalize_tk_key_event
from .keymap_add_flow import KeymapAddFlow
from .keymap_list_edit import KeymapListEditFlow
from keyseq.shared.i18n import tr


class KeymapPanelController:
    """キーマップ管理パネル（一覧表示・追加/変更/削除・キーボードUI連携）。"""

    SWITCH_BLOCKED_MESSAGE = "keymap_panel.switch_blocked"

    def __init__(self, app) -> None:
        self._app = app
        self._keymap_add_flow = KeymapAddFlow(self)
        self._keymap_list_edit = KeymapListEditFlow(self)

    def format_keymap_display_name(self, keymap: dict | None) -> str:
        if not isinstance(keymap, dict):
            return ""
        keymap_id = normalize_identifier(keymap.get("id", ""))
        label = str(keymap.get("label") or "").strip()
        return label or keymap_id

    def format_keymap_list_entry(
        self, index: int, keymap: dict, overlap: KeyOverlapAnalysis | None = None
    ) -> str:
        keymap_id = normalize_identifier(keymap.get("id", ""))
        marker = "> " if keymap_id and keymap_id == self._app.keymap_service.get_active_keymap_id(self._app.data) else "  "
        switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id) or "-"
        display_name = self.format_keymap_display_name(keymap)
        if not display_name:
            row_index = index + 1
            display_name = tr("keymap_panel.default_name", index=row_index)
        row_number = f"{index + 1:02d}"
        entry = tr("keymap_panel.entry", marker=marker, index=row_number,
                   switch_key=switch_key, name=display_name)
        if overlap is None:
            overlap = self._app._key_overlap_report()
        conflict = overlap.keymap_switch_conflict(keymap_id, switch_key)
        if conflict is not None:
            entry = tr("keymap_panel.entry.conflict", entry=entry,
                       reason=self._switch_conflict_reason(conflict.winner))
        return entry

    @staticmethod
    def _switch_conflict_reason(winner: str) -> str:
        return tr("trigger_panel.conflict.stop") if winner == "stop" else tr("trigger_panel.conflict.toggle")

    @staticmethod
    def _set_keymap_row_color(listbox, index: int, is_shadowed: bool) -> None:
        color = "#888888" if is_shadowed else listbox.cget("foreground")
        listbox.itemconfigure(index, foreground=color)

    def selected_keymap_list_index(self) -> int | None:
        """アクティブな keymap の一覧上の位置を返す。"""
        active_id = self._app.keymap_service.get_active_keymap_id(self._app.data)
        return next(
            (
                index
                for index, keymap in enumerate(self._app.keymap_service.get_keymaps(self._app.data))
                if normalize_identifier(keymap.get("id", "")) == active_id
            ),
            None,
        )

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

    def refresh_keymap_list_ui(
        self, preferred_index: int | None = None, *, overlap: KeyOverlapAnalysis | None = None,
        select: tuple[int, int] | None = None,
    ) -> None:
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
        if overlap is None:
            overlap = self._app._refresh_key_overlap_report()
        if not keymaps:
            listbox.insert(tk.END, tr("keymap_panel.empty"))
            listbox.selection_clear(0, tk.END)
            self.sync_keymap_manage_buttons()
            return

        active_id = self._app.keymap_service.get_active_keymap_id(self._app.data)
        for index, keymap in enumerate(keymaps):
            listbox.insert(tk.END, self.format_keymap_list_entry(index, keymap, overlap))
            keymap_id = normalize_identifier(keymap.get("id", ""))
            switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id)
            conflict = overlap.keymap_switch_conflict(keymap_id, switch_key)
            self._set_keymap_row_color(listbox, index, conflict is not None)

        target_index = preferred_index
        if target_index is None:
            active_index = next(
                (
                    index
                    for index, keymap in enumerate(keymaps)
                    if normalize_identifier(keymap.get("id", "")) == active_id
                ),
                0,
            )
            target_index = active_index

        target_index = max(0, min(int(target_index), len(keymaps) - 1))
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(target_index)
        listbox.activate(target_index)
        listbox.see(target_index)
        if select is not None and not getattr(self._app, "_compact_mode", False):
            active_index = next((index for index, row in enumerate(keymaps)
                                 if normalize_identifier(row.get("id", "")) == active_id), 0)
            select_range(listbox, *select, active=active_index)
            listbox.see(select[1])
        self.sync_keymap_manage_buttons()

    def on_keymap_list_select(self, _event=None, *, prefer_selection: bool = True) -> None:
        self._keymap_list_edit.commit_selection()

    def on_keymap_list_move(self, start: int, end: int, target_start: int) -> bool:
        return self._keymap_list_edit.move_keymap_range(start, end, target_start)

    def can_start_keymap_drag(self) -> bool:
        return self._keymap_list_edit.can_start_drag()

    def copy_keymaps(self, event=None) -> str:
        return self._keymap_list_edit.copy_keymaps(event)

    def paste_keymaps(self, event=None) -> str:
        return self._keymap_list_edit.paste_keymaps(event)

    def on_keymap_list_focus_index_change(self, _event=None) -> None:
        self.on_keymap_list_select(prefer_selection=False)

    def on_keymap_list_mouse_release(self, _listbox: tk.Listbox) -> None:
        self.on_keymap_list_select(prefer_selection=True)

    def on_keymap_list_double_click(self, _event=None) -> None:
        """一覧ダブルクリックで選択中 keymap の編集導線を開く。"""
        self.edit_selected_keymap()

    def validate_keymap_switch_assignment(
        self,
        key: str,
        *,
        target_id: str,
        exclude_switch_key: str = "",
        message_parent: tk.Misc | None = None,
    ) -> bool:
        if (
            is_prohibited_assign_key(key)
            and normalize_key_name(key) != normalize_key_name(exclude_switch_key)
        ):
            messagebox.showerror(
                tr("capture.error.title"),
                tr("keymap_panel.switch_key.prohibited", key=key),
                parent=message_parent,
            )
            return False
        if self._app.trigger_service.is_stop_key_conflict(self._app.data, key):
            messagebox.showerror(
                tr("capture.error.title"), tr("keymap_panel.switch_key.conflict_stop", key=key), parent=message_parent
            )
            return False
        if self._app.trigger_service.is_toggle_key_conflict(self._app.data, key):
            messagebox.showerror(
                tr("capture.error.title"), tr("keymap_panel.switch_key.conflict_toggle", key=key), parent=message_parent
            )
            return False
        if normalize_key_name(key) in self._app._key_overlap_report().all_trigger_keys:
            messagebox.showerror(
                tr("capture.error.title"), tr("keymap_panel.switch_key.conflict_trigger", key=key), parent=message_parent
            )
            return False
        if normalize_key_name(key) in self._app._key_overlap_report().all_source_keys:
            messagebox.showerror(
                tr("capture.error.title"), tr("keymap_panel.switch_key.conflict_mapping", key=key), parent=message_parent
            )
            return False

        existing_target_id = self._app.keymap_service.get_keymap_by_switch_key(self._app.data, key)
        normalized_target_id = normalize_identifier(target_id)
        excluded_key = normalize_key_name(exclude_switch_key)
        if existing_target_id and key != excluded_key:
            existing_name = self.format_keymap_display_name(self._app.keymap_service.find_keymap(self._app.data, existing_target_id)) or existing_target_id
            messagebox.showerror(
                tr("capture.error.title"), tr("keymap_panel.switch_key.in_use", key=key, name=existing_name),
                parent=message_parent,
            )
            return False

        existing_switch_key = self._app.keymap_service.find_switch_key_for_keymap(
            self._app.data,
            normalized_target_id,
            exclude_key=excluded_key,
        )
        if existing_switch_key and existing_switch_key != key:
            target_name = self.format_keymap_display_name(self._app.keymap_service.find_keymap(self._app.data, normalized_target_id)) or normalized_target_id
            messagebox.showerror(
                tr("capture.error.title"), tr("keymap_panel.switch_key.already_assigned", key=existing_switch_key, name=target_name),
                parent=message_parent,
            )
            return False

        try:
            self._app.input_gateway.validate_key_name(key)
        except Exception as e:
            messagebox.showerror(tr("capture.error.title"), tr("capture.error.unknown_key", key=key, error=e), parent=message_parent)
            return False

        return True

    def add_keymap(self) -> None:
        """必要な切替キーを確認してから、新しいキーマップを追加する。"""
        self._keymap_add_flow.add_keymap()

    def add_imported_keymap(self, keymap: dict) -> bool:
        """個別読込を追加フローとして実行し、取消時は runtime を変えない。"""
        return self._keymap_add_flow.add_imported_keymap(keymap)

    def _refresh_after_keymap_change(self) -> None:
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()

    def rename_keymap_label(self) -> None:
        """選択中 keymap の表示ラベルだけを更新する。"""
        index = self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo(tr("keymap_panel.rename.title"), tr("keymap_panel.rename.select"))
            return

        target = keymaps[index]
        keymap_id = normalize_identifier(target.get("id", ""))
        current_label = str(target.get("label") or "").strip()
        self._app.hook.suspend_hook_for_dialog()
        try:
            new_label = simpledialog.askstring(
                tr("keymap_panel.rename.title"),
                tr("keymap_panel.rename.prompt", keymap_id=keymap_id),
                initialvalue=current_label,
                parent=self._app,
            )
        finally:
            self._app.hook.resume_hook_after_dialog()
        if new_label is None:
            return

        normalized_label = str(new_label).strip()
        if normalized_label == current_label:
            self._app._set_flash_message(tr("keymap_panel.rename.unchanged", name=self.format_keymap_display_name(target) or keymap_id))
            return

        target["label"] = normalized_label
        self.refresh_keymap_list_ui(preferred_index=index)
        self._app.layout.refresh_keyboard_window()
        self._app.trigger_panel.update_status()
        self._app.mark_keymap_dirty(target)
        if normalized_label:
            self._app._set_flash_message(tr("keymap_panel.rename.changed", name=normalized_label))
        else:
            self._app._set_flash_message(tr("keymap_panel.rename.cleared", keymap_id=keymap_id))

    def delete_keymap(self) -> None:
        """選択中の keymap を削除する。"""
        bounds = self._keymap_list_edit.selection_bounds()
        if bounds is not None and bounds[0] != bounds[1]:
            self._keymap_list_edit.delete_keymap_range()
            return
        index = bounds[0] if bounds is not None else self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo(tr("common.delete"), tr("keymap_panel.delete.select"))
            return
        if len(keymaps) == 1:
            messagebox.showerror(tr("keymap_panel.delete.error_title"), tr("keymap_panel.delete.only_one"))
            return

        target = keymaps[index]
        target_id = normalize_identifier(target.get("id", ""))
        if target_id == self._app.keymap_service.get_active_keymap_id(self._app.data):
            if not self._app.state.can_switch_keymap(
                target_id, self._app.keymap_service.get_active_keymap_id(self._app.data), changes_active=True
            ):
                self.show_keymap_switch_blocked()
                self.refresh_keymap_list_ui()
                return
        target_name = self.format_keymap_display_name(target) or normalize_identifier(target.get("id", ""))
        prompt = tr("keymap_panel.delete.confirm", name=target_name)
        if self._has_unsaved_children(target):
            prompt = tr("keymap_panel.delete.confirm_unsaved", name=target_name)
        confirm_title = tr("keyboard.layout.confirm_title")
        if not messagebox.askyesno(confirm_title, prompt):
            return
        deleted, next_active_id, discarded = self._delete_keymap_confirmed(target)
        if not deleted:
            return
        self._keymap_list_edit._finish(None)
        if discarded:
            return
        if next_active_id:
            current_name = self.get_active_keymap_text()
            self._app._set_flash_message(tr("keymap_panel.deleted.with_current", name=target_name, current=current_name))
        else:
            self._app._set_flash_message(tr("keymap_panel.deleted", name=target_name))

    def _delete_keymap_confirmed(self, target: dict) -> tuple[bool, str, tuple]:
        """単件・範囲の両方から使う、確認後の削除と実行状態の後始末。"""
        target_id = normalize_identifier(target.get("id", ""))
        trigger_set_id = self._app.keymap_service.get_trigger_set_id(self._app.data, target_id)
        members = trigger_set_members(self._app.data, target_id)
        drops_trigger_set = len(members) <= 1
        next_trigger_set_id = next(
            (normalize_identifier(member.get("id", "")) for member in members if member is not target), "",
        )
        discarded = ()
        if target_id == self._app.keymap_service.get_active_keymap_id(self._app.data):
            discarded = self._app.sequence_runner.discard_paused()
            self._app.sequence_runner.cancel_pending_waits()
            self._app.sequence_runner.release_all_held()

        deleted, next_active_id = self._app.keymap_service.delete_keymap(self._app.data, target.get("id", ""))
        if not deleted:
            messagebox.showerror(tr("keymap_panel.delete.error_title"), tr("keymap_panel.delete.failed"))
            return False, next_active_id, discarded
        legacy = self._app.data.get(self._app.config_service.INTERNAL_LEGACY_TRIGGER_SET, {})
        if legacy.get("state") == "migrated" and legacy.get("keymap_id") == target_id:
            self._app.data[self._app.config_service.INTERNAL_LEGACY_TRIGGER_SET] = {
                "state": "none", "path": "", "keymap_id": "",
            }
        if drops_trigger_set:
            self._app.state.forget_trigger_set(trigger_set_id)
        elif trigger_set_id == target_id and next_trigger_set_id:
            self._app.state.rekey_trigger_set(trigger_set_id, next_trigger_set_id)

        return True, next_active_id, discarded

    def _has_unsaved_children(self, keymap: dict, *, deleting_members: bool = False) -> bool:
        keymap_id = normalize_identifier(keymap.get("id", ""))
        members = trigger_set_members(self._app.data, keymap_id)
        if len(members) > 1 and not deleting_members:
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
        self._app._set_flash_message(tr(self.SWITCH_BLOCKED_MESSAGE))

    def edit_selected_keymap(self) -> None:
        """選択中の keymap をダイアログで編集する。"""
        index = self.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo(tr("common.edit_title"), tr("keymap_panel.edit.select"))
            return

        target = keymaps[index]
        target_id = normalize_identifier(target.get("id", ""))
        if not target_id:
            messagebox.showerror(tr("keymap_panel.edit.error_title"), tr("keymap_panel.edit.not_found"))
            return

        current_switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, target_id)
        dlg = KeymapEditDialog(
            self._app,
            title=tr("keymap_panel.edit.title"),
            initial_key=current_switch_key,
            initial_label=str(target.get("label") or "").strip(),
            initial_grid_enabled=(
                isinstance(target.get("grid"), dict) and target["grid"].get("enabled") is True
            ),
            initial_grid=target.get("grid") if isinstance(target.get("grid"), dict) else None,
            grid_editor_context=lambda: self._grid_editor_context(target_id),
            key_name_from_event=self._grid_key_name_from_event,
        )
        dlg.wait_window()
        result = getattr(dlg, "result", None)
        if not result:
            return

        self.apply_keymap_edit(
            target,
            new_label=result.get("label", ""),
            new_key=result.get("key", ""),
            new_grid_enabled=result.get("grid_enabled"),
            new_grid_shapes=result.get("grid"),
            preferred_index=index,
        )

    def _grid_editor_context(self, editing_keymap_id: str = "") -> tuple[list[MonitorInfo], str, set[str]]:
        monitors = self._app.screen_grid.list_monitors()
        x, y = self._app.input_gateway.cursor_position()
        monitor = next(
            (item for item in monitors
             if item.rect[0] <= x < item.rect[2] and item.rect[1] <= y < item.rect[3]),
            None,
        )
        if monitor is None:
            monitor = next((item for item in monitors if item.primary), None)
        if monitor is None and monitors:
            monitor = monitors[0]

        own_switch_key = self._app.keymap_service.find_switch_key_for_keymap(
            self._app.data, editing_keymap_id
        ) if editing_keymap_id else ""
        own_switch_key = normalize_key_name(own_switch_key)
        reserved = {
            normalize_key_name(self._app.data.get("hook_stop_key", "")),
            normalize_key_name(self._app.data.get("hook_toggle_key", "")),
        }
        reserved.update(
            normalize_key_name(key)
            for key in self._app.data.get("keymap_switch_keys", {})
            if normalize_key_name(key) != own_switch_key
        )
        reserved.discard("")
        return monitors, monitor.id if monitor is not None else "", reserved

    def _grid_key_name_from_event(self, event: object) -> str:
        numpad_name = numpad_name_from_tk_event(
            getattr(event, "keycode", None), getattr(event, "state", 0)
        )
        if numpad_name:
            return numpad_name
        scan_code = win32_window.vk_to_scan_code(getattr(event, "keycode", 0))
        if scan_code:
            key_name = self._app.layout.resolve_key_name_from_scan_code(scan_code)
            if key_name:
                return key_name
        # 配列にスキャンコードが無いときは、フック（keyboard）と同じく修飾なしの文字を名前にする。
        char = win32_window.vk_to_char(getattr(event, "keycode", 0))
        if char:
            return normalize_key_name(char)
        return normalize_tk_key_event(event)

    def apply_keymap_edit(
        self, keymap: dict, *, new_label: str, new_key: str,
        new_grid_enabled: bool | None = None, new_grid_shapes: dict | None = None,
        preferred_index: int | None = None,
    ) -> bool:
        keymap_id = normalize_identifier(keymap.get("id", ""))
        if not keymap_id:
            return False

        normalized_label = str(new_label or "").strip()
        normalized_key = normalize_key_name(new_key)
        current_label = str(keymap.get("label") or "").strip()
        current_switch_key = self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id)

        if not normalized_key and len(self._app.keymap_service.get_keymaps(self._app.data)) > 1:
            messagebox.showerror(tr("capture.error.title"), tr("keymap_panel.switch_key.required"))
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

        if isinstance(new_grid_shapes, dict):
            grid = keymap.get("grid")
            if not isinstance(grid, dict):
                grid = {"enabled": False, "monitors": {}, "sub": {}}
                keymap["grid"] = grid
                changed = True
            monitors = deepcopy(new_grid_shapes.get("monitors", {}))
            sub = deepcopy(new_grid_shapes.get("sub", {}))
            if grid.get("monitors") != monitors or grid.get("sub") != sub:
                grid["monitors"] = monitors
                grid["sub"] = sub
                changed = True
            if "label_position" in new_grid_shapes:
                if grid.get("label_position") != "top_left":
                    grid["label_position"] = "top_left"
                    changed = True
            elif "label_position" in grid:
                del grid["label_position"]
                changed = True
            if "ops" in new_grid_shapes:
                ops = deepcopy(new_grid_shapes["ops"])
                if grid.get("ops") != ops:
                    grid["ops"] = ops
                    changed = True
            elif "ops" in grid:
                del grid["ops"]
                changed = True

        if new_grid_enabled is not None:
            grid = keymap.get("grid")
            current_grid_enabled = isinstance(grid, dict) and grid.get("enabled") is True
            if bool(new_grid_enabled) != current_grid_enabled:
                if isinstance(grid, dict):
                    grid["enabled"] = bool(new_grid_enabled)
                elif new_grid_enabled:
                    keymap["grid"] = new_enabled_grid()
                changed = True

        if not changed:
            name = self.format_keymap_display_name(keymap) or keymap_id
            self._app._set_flash_message(tr("keymap_panel.edit.unchanged", name=name))
            return False

        self.refresh_keymap_list_ui()
        self._app.trigger_panel.refresh_triggers()
        self._app.mark_keymap_dirty(keymap)
        name = self.format_keymap_display_name(keymap) or keymap_id
        self._app._set_flash_message(tr("keymap_panel.edit.changed", name=name))
        return True

    def activate_keymap_by_id(
        self,
        keymap_id: str,
        *,
        preferred_index: int | None = None,
        show_flash: bool = True,
    ) -> bool:
        target_id = normalize_identifier(keymap_id)
        if not target_id:
            return False
        active_before = self._app.keymap_service.get_active_keymap_id(self._app.data)
        if not self._app.state.can_switch_keymap(target_id, active_before):
            self.show_keymap_switch_blocked()
            self.refresh_keymap_list_ui()
            return False
        discarded = self._app.sequence_runner.discard_paused() if target_id != active_before else ()
        if target_id != active_before and any(
            normalize_identifier(item.get("id", "")) == target_id
            for item in self._app.keymap_service.get_keymaps(self._app.data)
        ):
            self._app.sequence_runner.cancel_pending_waits()

        changed = self._app.keymap_service.set_active_keymap_id(self._app.data, target_id)
        active_id = self._app.keymap_service.get_active_keymap_id(self._app.data)
        if active_id != target_id:
            return False
        if target_id != active_before:
            self._app.sequence_runner.release_all_held()

        if preferred_index is None:
            keymaps = self._app.keymap_service.get_keymaps(self._app.data)
            preferred_index = next(
                (index for index, keymap in enumerate(keymaps) if normalize_identifier(keymap.get("id", "")) == target_id),
                None,
            )

        self.refresh_keymap_list_ui(preferred_index=preferred_index)
        if changed:
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
        else:
            self._app.layout.refresh_keyboard_window()
            self._app.trigger_panel.update_status()
        if show_flash and not discarded:
            if changed:
                name = self.get_active_keymap_text()
                self._app._set_flash_message(tr("keymap_panel.active.changed", name=name))
            else:
                name = self.get_active_keymap_text()
                self._app._set_flash_message(tr("keymap_panel.active.unchanged", name=name))
        return True

    def get_active_keymap_text(self) -> str:
        label = self._app.keymap_service.get_active_keymap_label(self._app.data)
        if not label:
            return tr("common.none")
        if not self._app.hook.hook_active:
            return tr("keymap_panel.active.hook_off", name=label)
        if not self._app.hook.custom_input_enabled:
            return tr("keymap_panel.active.paused", name=label)
        return label

    def get_active_keymap_name(self) -> str:
        label = self._app.keymap_service.get_active_keymap_label(self._app.data)
        return label or tr("common.none")

    def assign_keymap_from_keyboard_ui(self, source_key: str, target_key: str) -> bool:
        source = normalize_key_name(source_key)
        target = normalize_key_name(target_key)
        if not source or not target:
            return False
        if is_prohibited_assign_key(source):
            messagebox.showerror(
                tr("capture.error.title"),
                tr("keymap_panel.mapping.prohibited_source"),
            )
            return False
        if "+" in target:
            messagebox.showerror(tr("capture.error.title"), tr("keymap_panel.mapping.single_target"))
            return False
        if source in {
            normalize_key_name(self._app.data.get("hook_stop_key", "")),
            normalize_key_name(self._app.data.get("hook_toggle_key", "")),
        }:
            messagebox.showerror(tr("capture.error.title"), tr("keymap_panel.mapping.reserved_source", key=source))
            return False
        if self._app.keymap_service.get_keymap_by_switch_key(self._app.data, source):
            messagebox.showerror(tr("capture.error.title"), tr("trigger_panel.add.switch_key", key=source))
            return False
        if source in self._app._key_overlap_report().active_trigger_keys:
            messagebox.showerror(tr("capture.error.title"), tr("keymap_panel.mapping.trigger_source", key=source))
            return False

        try:
            self._app.input_gateway.validate_key_name(target)
        except Exception as e:
            messagebox.showerror(tr("capture.error.title"), tr("capture.error.unknown_key", key=target, error=e))
            return False

        keymap_id, changed = self._app.keymap_service.set_mapping(self._app.data, source, target)
        self._app.trigger_panel.refresh_triggers()
        if changed:
            self._app.mark_keymap_dirty(self._app.keymap_service.find_keymap(self._app.data, keymap_id))
            self._app._set_flash_message(tr("keymap_panel.mapping.updated", source=source, target=target, keymap_id=keymap_id))
        else:
            self._app._set_flash_message(tr("keymap_panel.mapping.unchanged", source=source, target=target))
        return True

    def clear_keymap_from_keyboard_ui(self, source_key: str) -> bool:
        source = normalize_key_name(source_key)
        if not source:
            return False
        keymap_id, changed = self._app.keymap_service.clear_mapping(self._app.data, source)
        self._app.trigger_panel.refresh_triggers()
        if changed:
            self._app.mark_keymap_dirty(self._app.keymap_service.find_keymap(self._app.data, keymap_id))
            self._app._set_flash_message(tr("keymap_panel.mapping.cleared", source=source, keymap_id=keymap_id))
            return True

        self._app._set_flash_message(tr("keymap_panel.mapping.nothing_to_clear", source=source))
        return False
