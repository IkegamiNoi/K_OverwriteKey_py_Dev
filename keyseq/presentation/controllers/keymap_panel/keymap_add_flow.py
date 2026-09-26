from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import messagebox

from keyseq.domain.config import normalize_key_name
from keyseq.presentation.dialogs import KeymapEditDialog


class KeymapAddFlow:
    """キーマップ追加時の切替キー設定・編集ダイアログをまとめる。"""

    def __init__(self, keymap_panel) -> None:
        self._keymap_panel = keymap_panel
        self._app = keymap_panel._app

    def add_keymap(self) -> None:
        """必要な切替キーを確認してから、新しいキーマップを追加する。"""
        if not self._app.keymap_service.get_keymaps(self._app.data):
            created = self._app.keymap_service.create_keymap(self._app.data)
            self._app.mark_keymap_dirty(created)
            self._keymap_panel._refresh_after_keymap_change()
            self._app._set_flash_message(f"キーマップを追加しました: {normalize_key_name(created.get('id', ''))}")
            return

        original_active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        pending = self._collect_missing_switch_edits(original_active)
        if pending is None:
            self._restore_active_keymap(original_active)
            return
        candidate_id = self._app.keymap_service.next_keymap_id(self._app.data)
        result = self._prompt_keymap_edit(
            "キーマップ追加",
            "",
            validate=lambda values, parent: self._validate_addition_key(
                values.get("key", ""), candidate_id, pending, message_parent=parent
            ),
        )
        if not result:
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
        self._keymap_panel._refresh_after_keymap_change()
        self._app._set_flash_message(f"キーマップを追加しました: {normalize_key_name(created.get('id', ''))}")

    def add_imported_keymap(self, keymap: dict) -> bool:
        """個別読込を追加フローとして実行し、取消時は runtime を変えない。"""
        original_active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if not keymaps:
            self._append_keymap(keymap)
            self._keymap_panel._refresh_after_keymap_change()
            return True

        pending = self._collect_missing_switch_edits(original_active)
        if pending is None:
            self._restore_active_keymap(original_active)
            return False
        keymap_id = normalize_key_name(keymap.get("id", ""))
        result = self._prompt_keymap_edit(
            "読込キーマップの追加",
            str(keymap.get("label") or ""),
            validate=lambda values, parent: self._validate_addition_key(
                values.get("key", ""), keymap_id, pending, message_parent=parent
            ),
        )
        if not result:
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
        self._keymap_panel._refresh_after_keymap_change()
        return True

    def _collect_missing_switch_edits(self, original_active: str) -> list[tuple[dict, dict, int]] | None:
        pending = []
        for index, keymap in enumerate(self._app.keymap_service.get_keymaps(self._app.data)):
            keymap_id = normalize_key_name(keymap.get("id", ""))
            if self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap_id):
                continue
            if keymap_id != self._app.keymap_service.get_active_keymap_id(self._app.data):
                if not self._keymap_panel.activate_keymap_by_id(
                    keymap_id, preferred_index=index, show_flash=False
                ):
                    return None
            name = self._keymap_panel.format_keymap_display_name(keymap) or keymap_id
            messagebox.showerror("切替キーが必要です", f"{name} に切替キーを設定してください")
            result = self._prompt_keymap_edit(
                "キーマップ変更",
                keymap,
                is_existing_keymap=True,
                validate=lambda values, parent: self._validate_addition_key(
                    values.get("key", ""), keymap_id, pending, message_parent=parent
                ),
            )
            if not result:
                return None
            pending.append((keymap, result, index))
        self._restore_active_keymap(original_active)
        return pending

    def _prompt_keymap_edit(
        self,
        title: str,
        keymap_or_label,
        *,
        is_existing_keymap: bool = False,
        validate: Callable[[dict[str, str], tk.Misc], bool] | None = None,
    ) -> dict[str, str] | None:
        keymap = keymap_or_label if isinstance(keymap_or_label, dict) else None
        label = str(keymap.get("label") or "") if keymap else str(keymap_or_label or "")
        dialog_ref: dict[str, tk.Misc] = {}
        dialog_validate: Callable[[dict[str, str]], bool] | None = None
        if validate is not None:
            def validate_dialog(values: dict[str, str]) -> bool:
                return validate(values, dialog_ref["dialog"])

            dialog_validate = validate_dialog

        dlg = KeymapEditDialog(
            self._app,
            title=title,
            initial_key=(
                self._app.keymap_service.find_switch_key_for_keymap(self._app.data, keymap.get("id", ""))
                if is_existing_keymap and keymap
                else ""
            ),
            initial_label=label,
            validate=dialog_validate,
        )
        dialog_ref["dialog"] = dlg
        dlg.wait_window()
        result = getattr(dlg, "result", None)
        return result if isinstance(result, dict) else None

    def _validate_addition_key(
        self,
        key: str,
        target_id: str,
        pending: list[tuple[dict, dict, int]],
        *,
        message_parent: tk.Misc | None = None,
    ) -> bool:
        normalized = normalize_key_name(key)
        if not normalized:
            messagebox.showerror("設定できません", "切替キーは必須です。", parent=message_parent)
            return False
        if any(normalize_key_name(item[1].get("key", "")) == normalized for item in pending):
            messagebox.showerror(
                "設定できません", f"直接切替キーは既に使用されています:\n{normalized}", parent=message_parent
            )
            return False
        return self._keymap_panel.validate_keymap_switch_assignment(
            normalized, target_id=target_id, message_parent=message_parent
        )

    def _apply_pending_switch_edits(self, pending: list[tuple[dict, dict, int]]) -> bool:
        original_active = self._app.keymap_service.get_active_keymap_id(self._app.data)
        for keymap, result, index in pending:
            keymap_id = normalize_key_name(keymap.get("id", ""))
            if keymap_id != self._app.keymap_service.get_active_keymap_id(self._app.data):
                if not self._keymap_panel.activate_keymap_by_id(
                    keymap_id, preferred_index=index, show_flash=False
                ):
                    return False
            if not self._keymap_panel.apply_keymap_edit(
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
            self._keymap_panel.activate_keymap_by_id(keymap_id, show_flash=False)
