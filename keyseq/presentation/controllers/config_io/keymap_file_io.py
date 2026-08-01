import os
from tkinter import filedialog, messagebox

from keyseq.domain.config import normalize_key_name


class KeymapFileIo:
    def __init__(self, app) -> None:
        self._app = app

    def selected_keymap_for_io(self) -> "tuple[int, dict] | tuple[None, None]":
        index = self._app.keymap_panel.selected_keymap_list_index()
        keymaps = self._app.keymap_service.get_keymaps(self._app.data)
        if index is None or not keymaps or not (0 <= index < len(keymaps)):
            messagebox.showinfo("キーマップ", "対象のキーマップを選択してください。")
            return None, None
        return index, keymaps[index]

    def save_selected_keymap(self) -> bool:
        index, keymap = self.selected_keymap_for_io()
        if keymap is None:
            return False
        source_path = str(keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        if source_path and bool(keymap.get(self._app.config_service.INTERNAL_KEYMAP_IMPORTED, False)) and bool(keymap.get(self._app.config_service.INTERNAL_KEYMAP_DIRTY, False)):
            if messagebox.askyesno("保存", "読込で持ってきたキーマップです。\n別名で保存しますか？"):
                return self.save_selected_keymap_as()
        if not source_path:
            label = str(keymap.get("label") or keymap.get("id") or "keymap").strip()
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_keymaps_dir(), label, "keymap")
            source_path = self._app.io_dialogs.choose_save_path_with_collision(title="キーマップを保存", suggested_path=suggested)
            if not source_path:
                return False
        return self.save_keymap_to_path(index, keymap, source_path)

    def save_selected_keymap_as(self) -> bool:
        index, keymap = self.selected_keymap_for_io()
        if keymap is None:
            return False
        source_path = str(keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        label = str(keymap.get("label") or keymap.get("id") or "keymap").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_keymaps_dir(), source_path),
            label,
            "keymap",
        )
        path = filedialog.asksaveasfilename(
            title="キーマップを別名で保存",
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        try:
            if self._app.io_dialogs.ask_link_label_to_filename(title="キーマップ名の連動", path=path):
                keymap["label"] = self._app.paths.filename_stem(path)
        except RuntimeError:
            return False
        return self.save_keymap_to_path(index, keymap, path)

    def save_keymap_to_path(self, index: int, keymap: dict, path: str) -> bool:
        try:
            previous_source_path = str(
                keymap.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or ""
            ).strip()
            saved = self._app.config_service.save_keymap_file(
                path,
                keymap,
                parent_ref=self._app.keymap_set_path,
                config_root=self._app.config_root,
            )
            self._app.keymap_service.get_keymaps(self._app.data)[index] = saved
            self._app.keymap_panel.refresh_keymap_list_ui(preferred_index=index)
            self._app.layout.refresh_keyboard_window()
            source_path_changed = (
                self._app.config_service.canonical_path(
                    previous_source_path,
                    self._app.config_root,
                )
                != self._app.config_service.canonical_path(
                    str(saved.get(self._app.config_service.INTERNAL_KEYMAP_SOURCE_PATH) or ""),
                    self._app.config_root,
                )
            )
            if source_path_changed:
                self._app.dirty_tracker.set_dirty(True)
            self._app.dirty_tracker.sync_dirty_state()
            completion_message = "キーマップを保存しました。"
            info_message = f"キーマップを保存しました:\n{path}"
            if source_path_changed:
                completion_message += "\n上位の索引を保存すると追随します。"
                info_message += "\n上位の索引を保存すると追随します。"
            self._app._set_flash_message(completion_message)
            messagebox.showinfo("保存", info_message)
            return True
        except Exception as e:
            self._app._set_flash_message(f"キーマップ保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def load_keymap_file(self) -> None:
        path = filedialog.askopenfilename(
            title="キーマップを読込",
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_keymaps_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            used_ids = {normalize_key_name(item.get("id", "")) for item in self._app.keymap_service.get_keymaps(self._app.data)}
            keymap = self._app.config_service.load_keymap_file(path, used_keymap_ids=used_ids, imported=True)
            keymaps = self._app.data.setdefault("keymaps", [])
            if not isinstance(keymaps, list):
                keymaps = []
                self._app.data["keymaps"] = keymaps
            keymaps.append(keymap)
            index = len(keymaps) - 1
            if not self._app.data.get("active_keymap_id"):
                self._app.data["active_keymap_id"] = normalize_key_name(keymap.get("id", ""))
            self._app.keymap_panel.refresh_keymap_list_ui(preferred_index=index)
            self._app.layout.refresh_keyboard_window()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("キーマップを読み込みました。")
            messagebox.showinfo("読込", f"キーマップを読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"キーマップ読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))
