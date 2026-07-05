from __future__ import annotations

import os
from tkinter import filedialog, messagebox

from keyseq.domain.config import normalize_key_name
from keyseq.domain.key_identifiers import SPECIAL_KEY_NAMES, is_special_key_name
from keyseq.presentation.dialogs import LayoutDeleteDialog
from keyseq.presentation.keyboard_layouts import (
    DEFAULT_LAYOUT_ID,
    collect_keyboard_layouts,
    load_layout_from_json,
    resolve_key_id_from_scan_code,
    resolve_keyboard_layout,
    resolve_registered_layout_path,
)
from keyseq.presentation.keyboard_window import KeyboardWindow


class LayoutController:
    """キーボードレイアウト辞書・表示名マップと KeyboardWindow のライフサイクル管理。"""

    def __init__(self, app) -> None:
        self._app = app
        self.keyboard_layout_id = DEFAULT_LAYOUT_ID
        self._keyboard_layout_entries = {}
        self._keyboard_layout_display_to_id = {}
        self._keyboard_layout_id_to_display = {}
        self.keyboard_window = None
        self.keyboard_layouts_dir = app.paths.resolve_keylayout_dir()

    def open_keyboard_window(self):
        layout = self.get_current_keyboard_layout()
        window = self.keyboard_window
        if window is not None:
            try:
                if window.winfo_exists():
                    window.update_layout(layout)
                    window.deiconify()
                    window.lift()
                    window.focus_force()
                    self.refresh_keyboard_window()
                    return
            except Exception:
                self.keyboard_window = None

        self.keyboard_window = KeyboardWindow(
            self._app,
            layout=layout,
            on_close=self.on_keyboard_window_closed,
            on_assign_keymap=self._app.keymap_panel.assign_keymap_from_keyboard_ui,
            on_clear_keymap=self._app.keymap_panel.clear_keymap_from_keyboard_ui,
        )
        self.refresh_keyboard_window()

    def on_keyboard_window_closed(self):
        self.keyboard_window = None

    def refresh_keyboard_window(self):
        window = self.keyboard_window
        if window is None:
            return
        try:
            if not window.winfo_exists():
                self.keyboard_window = None
                return
            window.update_layout(self.get_current_keyboard_layout())
            window.update_from_config(
                self._app.data,
                custom_enabled=True,
                show_physical_key_labels=bool(self._app.keyboard_show_physical_key_labels_var.get()),
            )
        except Exception:
            pass

    def get_current_keyboard_layout(self):
        entry = self._keyboard_layout_entries.get(str(self.keyboard_layout_id).strip())
        if entry is not None:
            if entry.source == "external" and entry.path:
                try:
                    return load_layout_from_json(
                        resolve_registered_layout_path(entry.path, base_dir=self._app.base_dir)
                    )
                except Exception as e:
                    self._app._set_flash_message(
                        f"構成セットの読込に失敗したため、空の状態で起動しました: {e}",
                        auto_clear=False,
                    )
            return entry.layout
        return resolve_keyboard_layout(layout_id=self.keyboard_layout_id)

    def get_fallback_keyboard_layout_id(self, *, exclude: str | None = None) -> str:
        excluded = (exclude or "").strip()
        if DEFAULT_LAYOUT_ID in self._keyboard_layout_entries and DEFAULT_LAYOUT_ID != excluded:
            return DEFAULT_LAYOUT_ID
        for layout_id in self._keyboard_layout_entries.keys():
            if layout_id != excluded:
                return layout_id
        return DEFAULT_LAYOUT_ID

    def reload_keyboard_layouts(self):
        self._keyboard_layout_entries = collect_keyboard_layouts(
            self._app.data.get("external_keyboard_layouts", []),
            base_dir=self._app.base_dir,
        )
        self.sync_keyboard_layout_controls()

    def sync_keyboard_layout_controls(self):
        self.rebuild_keyboard_layout_display_maps()
        display_values = list(self._keyboard_layout_display_to_id.keys())
        selected = str(self._app.data.get("keyboard_layout", self.keyboard_layout_id or DEFAULT_LAYOUT_ID)).strip()
        if selected not in self._keyboard_layout_entries:
            selected = self.get_fallback_keyboard_layout_id()

        self.keyboard_layout_id = selected
        self._app.data["keyboard_layout"] = selected
        if hasattr(self._app, "keyboard_layout_var"):
            self._app.keyboard_layout_var.set(self._keyboard_layout_id_to_display.get(selected, ""))

        state = "readonly" if display_values else "disabled"
        for name in ("keyboard_layout_combo", "compact_keyboard_layout_combo"):
            combo = getattr(self._app, name, None)
            if combo is None:
                continue
            try:
                combo.configure(values=display_values, state=state)
                combo.set(self._keyboard_layout_id_to_display.get(selected, ""))
            except Exception:
                pass

        self.refresh_keyboard_window()

    def persist_keyboard_layout_selection(self):
        if not self._app.keymap_set_path:
            self._app.dirty_tracker.set_dirty(True)
            return True
        try:
            return self._app.config_io.save_keymap_set(show_success_dialog=False)
        except Exception as e:
            self._app._set_flash_message(f"保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def toggle_keyboard_show_physical_key_labels(self):
        self._app.data["keyboard_show_physical_key_labels"] = bool(self._app.keyboard_show_physical_key_labels_var.get())
        self.refresh_keyboard_window()
        self.persist_keyboard_layout_selection()

    def set_keyboard_layout_selection(self, layout_id: str, *, persist: bool = False):
        selected = str(layout_id or "").strip()
        if selected not in self._keyboard_layout_entries:
            selected = self.get_fallback_keyboard_layout_id()

        self.keyboard_layout_id = selected
        self._app.data["keyboard_layout"] = selected
        if hasattr(self._app, "keyboard_layout_var"):
            self._app.keyboard_layout_var.set(self._keyboard_layout_id_to_display.get(selected, ""))

        for name in ("keyboard_layout_combo", "compact_keyboard_layout_combo"):
            combo = getattr(self._app, name, None)
            if combo is None:
                continue
            try:
                combo.set(self._keyboard_layout_id_to_display.get(selected, ""))
            except Exception:
                pass

        self.refresh_keyboard_window()
        if persist:
            return self.persist_keyboard_layout_selection()
        return True

    def on_keyboard_layout_selected(self, _event=None):
        selected = self._keyboard_layout_display_to_id.get(str(self._app.keyboard_layout_var.get() or "").strip(), "")
        self.set_keyboard_layout_selection(selected, persist=True)

    def add_external_keyboard_layout(self):
        path = filedialog.askopenfilename(
            title="外部レイアウトを追加",
            initialdir=self.keyboard_layouts_dir if os.path.isdir(self.keyboard_layouts_dir) else self._app.base_dir,
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            layout = load_layout_from_json(path, existing_layout_ids=set(self._keyboard_layout_entries.keys()))
            registrations = list(self._app.data.get("external_keyboard_layouts", []))
            stored_path = self._app.paths.to_rel_if_possible(path)
            if any(str(item.get("path") or "").strip() == stored_path for item in registrations if isinstance(item, dict)):
                raise ValueError("同じJSONファイルは既に登録されています。")
            registrations.append({"path": stored_path})
            self._app.data["external_keyboard_layouts"] = registrations
        except Exception as e:
            messagebox.showerror("レイアウト追加失敗", str(e))
            return

        self.reload_keyboard_layouts()
        self.persist_keyboard_layout_selection()
        self._app._set_flash_message(f"外部レイアウトを追加しました: {layout.layout_id}")

    def delete_keyboard_layout(self):
        items = [
            (layout_id, entry.layout.display_name)
            for layout_id, entry in self._keyboard_layout_entries.items()
            if entry.source == "external" and entry.path
        ]
        if not items:
            messagebox.showinfo("レイアウト削除", "削除できる外部レイアウトがありません。")
            return

        dlg = LayoutDeleteDialog(self._app, title="レイアウトを削除", items=items)
        dlg.wait_window()
        target_id = getattr(dlg, "result", None)
        if not target_id:
            return

        entry = self._keyboard_layout_entries.get(target_id)
        if entry is None or entry.source != "external" or not entry.path:
            messagebox.showerror("レイアウト削除", "削除対象のレイアウト情報を取得できませんでした。")
            return

        if not messagebox.askyesno("確認", f"外部レイアウト '{target_id}' を削除しますか？"):
            return

        registrations = list(self._app.data.get("external_keyboard_layouts", []))
        self._app.data["external_keyboard_layouts"] = [
            item
            for item in registrations
            if str(item.get("path") or "").strip() != str(entry.path or "").strip()
        ]

        if target_id == self.keyboard_layout_id:
            changed = self.set_keyboard_layout_selection(
                self.get_fallback_keyboard_layout_id(exclude=target_id),
                persist=True,
            )
            if not changed:
                return
        else:
            if not self.persist_keyboard_layout_selection():
                return

        self.reload_keyboard_layouts()
        self._app._set_flash_message(f"外部レイアウトを削除しました: {target_id}")

    def rebuild_keyboard_layout_display_maps(self):
        self._keyboard_layout_display_to_id = {}
        self._keyboard_layout_id_to_display = {}
        display_counts: dict[str, int] = {}

        for entry in self._keyboard_layout_entries.values():
            display_name = (entry.layout.display_name or "").strip() or entry.layout.layout_id
            display_counts[display_name] = display_counts.get(display_name, 0) + 1

        for layout_id, entry in self._keyboard_layout_entries.items():
            display_name = (entry.layout.display_name or "").strip() or layout_id
            if display_counts.get(display_name, 0) > 1:
                display_name = f"{display_name} [{layout_id}]"
            self._keyboard_layout_display_to_id[display_name] = layout_id
            self._keyboard_layout_id_to_display[layout_id] = display_name

    def resolve_key_name_from_scan_code(self, scan_code: object) -> str:
        return normalize_key_name(resolve_key_id_from_scan_code(self.get_current_keyboard_layout(), scan_code))

    def should_debug_special_key_event(self, event: object, resolved_key: str) -> bool:
        if not bool(self._app.data.get("debug_jis_special_key_events", False)):
            return False
        if normalize_key_name(str(getattr(event, "event_type", "") or "")) != "down":
            return False

        raw_name = normalize_key_name(str(getattr(event, "name", "") or ""))
        if is_special_key_name(raw_name) or is_special_key_name(resolved_key):
            return True

        try:
            scan_code = int(getattr(event, "scan_code", None))
        except Exception:
            return False

        layout = self.get_current_keyboard_layout()
        for key_spec in getattr(layout, "keys", ()) or ():
            if str(getattr(key_spec, "id", "") or "").strip() not in SPECIAL_KEY_NAMES:
                continue
            try:
                if int(getattr(key_spec, "scan_code", None)) == scan_code:
                    return True
            except Exception:
                continue
        return False

    def debug_special_key_event(self, event: object, resolved_key: str) -> None:
        print(
            "[JIS special key debug] "
            f"event.name={getattr(event, 'name', '')!r} "
            f"event.scan_code={getattr(event, 'scan_code', None)!r} "
            f"resolved_key={resolved_key!r}"
        )
