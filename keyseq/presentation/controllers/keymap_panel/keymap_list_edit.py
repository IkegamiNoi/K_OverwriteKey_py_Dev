"""Range operations for the full-view keymap list."""

import tkinter as tk
from tkinter import messagebox

from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import iter_trigger_sets
from keyseq.domain.list_editing import move_block
from keyseq.presentation.list_clipboard import CLIP_KEYMAPS
from keyseq.presentation.listbox_range_drag import (
    range_or_index,
    selected_range,
    select_range,
)
from keyseq.presentation.listbox_utils import listbox_mouse_button_is_down


class KeymapListEditFlow:
    def __init__(self, panel) -> None:
        self._panel = panel
        self._app = panel._app

    @property
    def listbox(self):
        box = getattr(getattr(self._app, "full_view", None), "keymap_box", None)
        return getattr(box, "keymap_listbox", None)

    def selection_bounds(self) -> tuple[int, int] | None:
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        return range_or_index(
            self.listbox,
            len(keymaps),
            self._panel.selected_keymap_list_index(),
            compact=getattr(self._app, "_compact_mode", False),
        )

    def commit_selection(self) -> None:
        box = self.listbox
        if box is None or listbox_mouse_button_is_down(box):
            return
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        index = int(box.index(tk.ACTIVE))
        if not 0 <= index < len(keymaps):
            return
        bounds = selected_range(box)
        anchor = int(box.index(tk.ANCHOR))
        key = normalize_key_name(keymaps[index].get("id", ""))
        active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        if key != active and not self._panel.activate_keymap_by_id(
            key, preferred_index=index, show_flash=False
        ):
            return
        if bounds is not None:
            select_range(box, *bounds, active=index)
            box.selection_anchor(anchor)
        self._panel.sync_keymap_manage_buttons()

    def can_start_drag(self) -> bool:
        if self._app.sequence_runner.has_any_active_execution():
            self._app._set_flash_message("実行中のためキーマップを並べ替えられません")
            return False
        box = getattr(getattr(self._app, "full_view", None), "keymap_box", None)
        drag = getattr(box, "keymap_range_drag", None)
        active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        for index, row in enumerate(self._app.keymap_service.get_keymaps(self._app.data)):
            if normalize_key_name(row.get("id", "")) == active and drag is not None:
                # This list's underline follows the active keymap, even on rollback.
                drag._original_active = index
                break
        return True

    def move_keymap_range(self, start: int, end: int, target_start: int) -> bool:
        if not self.can_start_drag():
            return False
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        after = move_block(keymaps, start, end, target_start)
        if all(old is new for old, new in zip(keymaps, after)):
            return True
        representatives = {member.get("id", ""): owner.get("id", "")
                           for owner, members, _ in iter_trigger_sets(self._app.data)
                           for member in members}
        self._app.data["keymaps"][:] = after
        for owner, _, _ in iter_trigger_sets(self._app.data):
            previous = representatives[owner.get("id", "")]
            current = owner.get("id", "")
            if previous != current:
                self._app.state.rekey_trigger_set(previous, current)
        target = max(0, min(target_start, len(keymaps) - (end - start + 1)))
        self._finish((target, target + end - start))
        return True

    def delete_keymap_range(self) -> None:
        bounds = self.selection_bounds()
        if bounds is None:
            return
        start, end = bounds
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        targets = keymaps[start:end + 1]
        if len(targets) >= len(keymaps):
            messagebox.showerror("削除できません", "キーマップをすべて削除することはできません。")
            return
        active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        if any(normalize_key_name(row.get("id", "")) == active for row in targets):
            if not self._app.state.can_switch_keymap(active, active, changes_active=True):
                self._panel.show_keymap_switch_blocked()
                self._panel.refresh_keymap_list_ui()
                return
        prompt = f"キーマップ {len(targets)} 件を削除しますか？"
        if self._range_has_unsaved_children(targets):
            prompt += "\n\n未保存のトリガー一覧・シーケンスも破棄されます。"
        if not messagebox.askyesno("確認", prompt):
            return
        for target in targets:
            deleted, _, _ = self._panel._delete_keymap_confirmed(target)
            if not deleted:
                break
        self._finish(None)

    def _range_has_unsaved_children(self, targets: list) -> bool:
        target_ids = {id(row) for row in targets}
        for _, members, _ in iter_trigger_sets(self._app.data):
            if all(id(row) in target_ids for row in members):
                # The last member's deletion will discard the entire shared list.
                if self._panel._has_unsaved_children(members[0], deleting_members=True):
                    return True
        return False

    def copy_keymaps(self, _event=None) -> str:
        bounds = self.selection_bounds()
        if bounds is not None:
            start, end = bounds
            keymaps = self._app.keymap_service.get_keymaps(self._app.data)
            self._app.list_clipboard.copy(CLIP_KEYMAPS, keymaps[start:end + 1])
        return "break"

    def paste_keymaps(self, _event=None) -> str:
        items = self._app.list_clipboard.paste(CLIP_KEYMAPS)
        if not items:
            return "break"
        bounds = self._panel._keymap_add_flow.paste_keymaps(items)
        if bounds is not None:
            self._finish(select=bounds)
        return "break"

    def _finish(self, select: tuple[int, int] | None) -> None:
        self._panel._refresh_after_keymap_change()
        self._panel.refresh_keymap_list_ui(select=select)
        self._app.dirty_tracker.set_dirty(True)
        if self._app.hook.hook_active:
            self._app.hook.start_hook()
