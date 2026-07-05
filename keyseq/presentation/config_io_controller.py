from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from keyseq.domain.config import normalize_key_name


class ConfigIoController:
    """構成セット・個別JSON（keymap / trigger_set / sequence）の保存・読込フロー。"""

    def __init__(self, app) -> None:
        self._app = app

    # ---------------- 構成セット系 ----------------
    def confirm_save_if_dirty(self, action_name: str) -> bool:
        if not self._app.dirty_tracker.has_unsaved_changes():
            return True

        result = messagebox.askyesnocancel(
            "未保存の変更",
            f"未保存の変更があります。\n{action_name}の前に保存しますか？",
        )
        if result is None:
            return False
        if result is False:
            return True

        if self._app.keymap_set_path:
            return self.save_keymap_set(show_success_dialog=False)
        return self.save_as(show_success_dialog=False)

    def new_config(self):
        if not self.confirm_save_if_dirty("新規作成"):
            return

        self._app.data = self._app.config_service.new_default_data()
        self._app.data["triggers"] = []
        self._app.data = self._app.config_service.normalize_runtime_data(self._app.data)
        self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()

        self._app._sync_control_vars_from_data()

        self._app.state.reset_indices()
        self._app._selected_trigger_idx = 0
        self._app._refresh_triggers()
        self._app._refresh_actions()
        self._app.dirty_tracker.set_dirty(True)
        self._app._set_flash_message("新規作成しました（未保存）。")

    def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
        return self.save_keymap_set_to(
            self._app.keymap_set_path,
            flash_message="保存しました。",
            show_success_dialog=show_success_dialog,
        )

    def save_as(self, *, show_success_dialog: bool = True) -> bool:
        suggested_path = self._app.suggest_keymap_set_dialog_path()
        path = filedialog.asksaveasfilename(
            title="別名で保存（keymap_set）",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            initialfile=os.path.basename(suggested_path),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return False
        return self.save_keymap_set_to(
            path,
            flash_message="別名で保存しました。",
            show_success_dialog=show_success_dialog,
        )

    def save_keymap_set_to(self, path: str, *, flash_message: str, show_success_dialog: bool) -> bool:
        try:
            save_path = self._app.paths.normalize_keymap_set_save_path(path)
            split_base_dir = self.choose_split_base_dir_for_keymap_set(save_path)
            self._app.data, startup_payload = self._app.config_service.save_runtime_data(
                save_path,
                self._app.data,
                config_root=self._app.config_root,
                startup_data=self._app._startup_settings,
                keep_legacy_copy=False,
                split_base_dir=split_base_dir,
            )
            self._app.keymap_set_path = save_path
            self._app.startup_path = self._app.paths.preferred_startup_path()
            self._app._startup_settings = startup_payload
            self._app.dirty_tracker.clear_individual_dirty_flags()
            self._app.dirty_tracker.set_dirty(False)
            self._app._set_flash_message(flash_message)
            if show_success_dialog:
                messagebox.showinfo("保存", f"保存しました:\n{save_path}")
            return True
        except Exception as e:
            self._app._set_flash_message(f"保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def load_keymap_set_from(self):
        if not self.confirm_save_if_dirty("読込"):
            return

        path = filedialog.askopenfilename(
            title="keymap_set.json を読込",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            self._app.data = self._app.config_service.load_runtime_data_from_keymap_set_path(
                path,
                config_root=self._app.config_root,
            )
            self._app.keymap_set_path = path
            self.apply_loaded_data_to_ui()

            self._app._indices = {}
            self._app._selected_trigger_idx = 0
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app.dirty_tracker.set_dirty(False)
            self._app._set_flash_message("読み込みました。")
            messagebox.showinfo("読込", f"読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

    def import_config(self):
        if not self.confirm_save_if_dirty("Import"):
            return

        path = filedialog.askopenfilename(
            title="Import",
            initialdir=self._app.user_root if os.path.isdir(self._app.user_root) else self._app.base_dir,
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            self._app.data = self._app.config_service.load_legacy_runtime_data(path)
            if not self._app.keymap_set_path:
                self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()
            self.apply_loaded_data_to_ui()
            self._app.state.reset_indices()
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("Import しました。")
            messagebox.showinfo("Import", f"単一JSONを取り込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"Import 失敗: {e}", auto_clear=False)
            messagebox.showerror("Import 失敗", str(e))

    def export_config(self):
        path = filedialog.asksaveasfilename(
            title="Export",
            initialdir=self._app.user_root if os.path.isdir(self._app.user_root) else self._app.base_dir,
            initialfile="config.json",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            self._app.config_service.export_runtime_data(path, self._app.data)
            self._app._set_flash_message("Export しました。")
            messagebox.showinfo("Export", f"単一JSONを書き出しました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"Export 失敗: {e}", auto_clear=False)
            messagebox.showerror("Export 失敗", str(e))

    def restore_default(self):
        if messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？"):
            self._app.data = self._app.config_service.new_default_data()
            self._app._sync_control_vars_from_data()
            self._app._indices = {}
            self._app._selected_trigger_idx = 0
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("例の設定に戻しました（未保存）。")

    def set_startup_keymap_set(self):
        """ユーザーが起動時に読み込む keymap_set.json を選び、起動設定へ保存する"""
        if not self.confirm_save_if_dirty("起動時に読むJSONの変更"):
            return

        path = filedialog.askopenfilename(
            title="起動時に読み込む keymap_set.json を選択",
            initialdir=self._app.suggest_keymap_set_dialog_dir(),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            self._app.data = self._app.config_service.load_runtime_data_from_keymap_set_path(
                path,
                config_root=self._app.config_root,
            )
        except Exception as e:
            messagebox.showerror("設定", str(e))
            return

        self._app.keymap_set_path = path
        self.write_startup({"keymap_set_path": self._app.paths.to_config_relative_or_absolute(path), "prompt_if_missing": True})
        self.apply_loaded_data_to_ui()
        self._app.state.reset_indices()
        self._app._refresh_triggers()
        self._app._refresh_actions()
        self._app.dirty_tracker.set_dirty(False)
        self._app._set_flash_message("起動時読み込み設定を更新しました。")
        messagebox.showinfo("設定", f"次回起動時はこの keymap_set を読み込みます:\n{path}")

    def apply_loaded_data_to_ui(self):
        self._app.dirty_tracker.trigger_set_source_path = ""
        self._app.dirty_tracker.trigger_set_imported = False
        self._app.dirty_tracker.trigger_set_dirty = False
        self._app._sync_control_vars_from_data()
        self._app.dirty_tracker.clear_individual_dirty_flags()
        self._app.dirty_tracker.set_dirty(False)

    def choose_split_base_dir_for_keymap_set(self, save_path: str) -> str:
        if self._app.paths.is_within_config_root(save_path):
            return ""
        use_nearby = messagebox.askyesno(
            "保存先の確認",
            "構成セットがデフォルト外に保存されます。\n"
            "keymaps / trigger_sets / sequences も構成セット周辺に保存しますか？\n\n"
            "「いいえ」の場合はデフォルト保存先を使います。",
        )
        if not use_nearby:
            return ""
        return os.path.dirname(os.path.abspath(save_path))

    def load_startup_and_config(self):
        """
        起動設定JSON があれば split 構成の keymap_set を読み込む。
        無い場合や split 構成が読めない場合は空データで起動する。
        """
        startup = dict(getattr(self._app, "_startup_settings", {}) or {})
        stored_keymap_set_path = str(startup.get("keymap_set_path") or "").strip()
        self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()

        if stored_keymap_set_path:
            resolved_keymap_set_path = self._app.paths.resolve_keymap_set_path(stored_keymap_set_path)
            if os.path.exists(resolved_keymap_set_path):
                try:
                    self._app.data = self._app.config_service.load_runtime_data_from_keymap_set_path(
                        resolved_keymap_set_path,
                        config_root=self._app.config_root,
                    )
                    self._app.keymap_set_path = resolved_keymap_set_path
                    self.apply_loaded_data_to_ui()
                    return
                except Exception:
                    pass

        self._app.data = self._app.config_service.new_empty_data()
        self.apply_loaded_data_to_ui()

    def write_startup(self, data: dict[str, any]):
        base = {
            "prompt_if_missing": True,
            "ui_font_delta_pt": 0,
            "last_used_directory": "",
        }
        current = getattr(self._app, "_startup_settings", {})
        if isinstance(current, dict):
            base.update(current)
        if isinstance(data, dict):
            base.update(data)
        base.pop("config_path", None)
        base["ui_font_delta_pt"] = self._app._coerce_font_delta(base.get("ui_font_delta_pt", 0))

        try:
            self._app.startup_path = self._app.paths.preferred_startup_path()
            self._app.config_service.save_startup(self._app.startup_path, base)
            self._app._startup_settings = base
        except Exception as e:
            messagebox.showerror("startup.json 保存失敗", str(e))

    # ---------------- 個別 JSON IO 系 ----------------
    def choose_save_path_with_collision(self, *, title: str, suggested_path: str) -> str:
        path = suggested_path
        if os.path.exists(path):
            result = messagebox.askyesnocancel(
                "保存先の確認",
                f"同名ファイルが既にあります。\n\n{path}\n\n上書きしますか？\n「いいえ」で別名保存します。",
            )
            if result is None:
                return ""
            if result is False:
                path = filedialog.asksaveasfilename(
                    title=title,
                    initialdir=os.path.dirname(os.path.abspath(suggested_path)),
                    initialfile=os.path.basename(suggested_path),
                    defaultextension=".json",
                    filetypes=[("JSON", "*.json"), ("All", "*.*")],
                )
        return path or ""

    def ask_link_label_to_filename(self, *, title: str, path: str) -> bool:
        dialog = tk.Toplevel(self._app)
        dialog.title(title)
        dialog.resizable(False, False)
        self._app.hook.suspend_hook_for_dialog()
        result = {"ok": False, "link": False}
        link_var = tk.BooleanVar(value=False)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=f"保存名: {self._app.paths.filename_stem(path)}").pack(anchor="w")
        ttk.Checkbutton(frame, text="ラベル名も保存名に合わせる", variable=link_var).pack(anchor="w", pady=(10, 0))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))

        def on_ok():
            result["ok"] = True
            result["link"] = bool(link_var.get())
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(buttons, text="OK", command=on_ok).pack(side="right")
        ttk.Button(buttons, text="キャンセル", command=on_cancel).pack(side="right", padx=(0, 8))
        dialog.transient(self._app)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        try:
            dialog.wait_window()
        finally:
            self._app.hook.resume_hook_after_dialog()
        if not result["ok"]:
            raise RuntimeError("キャンセルされました。")
        return bool(result["link"])

    def selected_keymap_for_io(self) -> "tuple[int, dict] | tuple[None, None]":
        index = self._app._selected_keymap_list_index()
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
            source_path = self.choose_save_path_with_collision(title="キーマップを保存", suggested_path=suggested)
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
            if self.ask_link_label_to_filename(title="キーマップ名の連動", path=path):
                keymap["label"] = self._app.paths.filename_stem(path)
        except RuntimeError:
            return False
        return self.save_keymap_to_path(index, keymap, path)

    def save_keymap_to_path(self, index: int, keymap: dict, path: str) -> bool:
        try:
            saved = self._app.config_service.save_keymap_file(path, keymap)
            self._app.keymap_service.get_keymaps(self._app.data)[index] = saved
            self._app._refresh_keymap_list_ui(preferred_index=index)
            self._app.layout.refresh_keyboard_window()
            self._app.dirty_tracker.sync_dirty_state()
            self._app._set_flash_message("キーマップを保存しました。")
            messagebox.showinfo("保存", f"キーマップを保存しました:\n{path}")
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
            self._app._refresh_keymap_list_ui(preferred_index=index)
            self._app.layout.refresh_keyboard_window()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("キーマップを読み込みました。")
            messagebox.showinfo("読込", f"キーマップを読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"キーマップ読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

    def save_trigger_set_file(self) -> bool:
        path = str(getattr(self._app, "_trigger_set_source_path", "") or "").strip()
        if path and self._app.dirty_tracker.trigger_set_imported and self._app.dirty_tracker.trigger_set_dirty:
            if messagebox.askyesno("保存", "読込で持ってきたトリガー一覧です。\n別名で保存しますか？"):
                return self.save_trigger_set_file_as()
        if not path:
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_trigger_sets_dir(), self._app.keymap_set_file_stem(), "trigger_set")
            path = self.choose_save_path_with_collision(title="トリガー一覧を保存", suggested_path=suggested)
            if not path:
                return False
        return self.save_trigger_set_to_path(path)

    def save_trigger_set_file_as(self) -> bool:
        source_path = str(getattr(self._app, "_trigger_set_source_path", "") or "").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_trigger_sets_dir(), source_path),
            self._app.paths.filename_stem(source_path) or self._app.keymap_set_file_stem(),
            "trigger_set",
        )
        path = filedialog.asksaveasfilename(
            title="トリガー一覧を別名で保存",
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        return self.save_trigger_set_to_path(path)

    def save_trigger_set_to_path(self, path: str) -> bool:
        try:
            triggers, _payload = self._app.config_service.save_trigger_set_file(path, self._app.data, config_root=self._app.config_root)
            self._app.data["triggers"] = triggers
            self._app.dirty_tracker.trigger_set_source_path = path
            self._app.dirty_tracker.trigger_set_imported = False
            self._app.dirty_tracker.trigger_set_dirty = False
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app.dirty_tracker.sync_dirty_state()
            self._app._set_flash_message("トリガー一覧を保存しました。")
            messagebox.showinfo("保存", f"トリガー一覧を保存しました:\n{path}")
            return True
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def load_trigger_set_file(self) -> None:
        if not self.confirm_save_if_dirty("トリガー一覧読込"):
            return
        path = filedialog.askopenfilename(
            title="トリガー一覧を読込",
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_trigger_sets_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            self._app.data["triggers"] = self._app.config_service.load_trigger_set_file(
                path,
                config_root=self._app.config_root,
                imported=True,
            )
            self._app.dirty_tracker.trigger_set_source_path = path
            self._app.dirty_tracker.trigger_set_imported = True
            self._app.dirty_tracker.trigger_set_dirty = False
            self._app.state.reset_indices()
            self._app._selected_trigger_idx = 0
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app.dirty_tracker.set_dirty(True)
            self._app._set_flash_message("トリガー一覧を読み込みました。")
            messagebox.showinfo("読込", f"トリガー一覧を読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"トリガー一覧読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

    def save_selected_sequence(self) -> bool:
        trigger = self._app._selected_trigger()
        if not trigger:
            messagebox.showinfo("出力シーケンス", "対象のトリガーを選択してください。")
            return False
        source_path = str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        if source_path and bool(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_IMPORTED, False)) and bool(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_DIRTY, False)):
            if messagebox.askyesno("保存", "読込で持ってきた出力シーケンスです。\n別名で保存しますか？"):
                return self.save_selected_sequence_as()
        if not source_path:
            label = str(trigger.get("label") or trigger.get("key") or "sequence").strip()
            suggested = self._app.paths.suggest_json_path(self._app.paths.preferred_sequences_dir(), label, "sequence")
            source_path = self.choose_save_path_with_collision(title="出力シーケンスを保存", suggested_path=suggested)
            if not source_path:
                return False
        return self.save_sequence_to_path(trigger, source_path)

    def save_selected_sequence_as(self) -> bool:
        trigger = self._app._selected_trigger()
        if not trigger:
            messagebox.showinfo("出力シーケンス", "対象のトリガーを選択してください。")
            return False
        source_path = str(trigger.get(self._app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        label = str(trigger.get("label") or trigger.get("key") or "sequence").strip()
        suggested = self._app.paths.suggest_json_path(
            self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_sequences_dir(), source_path),
            label,
            "sequence",
        )
        path = filedialog.asksaveasfilename(
            title="出力シーケンスを別名で保存",
            initialdir=os.path.dirname(os.path.abspath(suggested)),
            initialfile=os.path.basename(suggested),
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return False
        try:
            if self.ask_link_label_to_filename(title="出力シーケンス名の連動", path=path):
                trigger["label"] = self._app.paths.filename_stem(path)
        except RuntimeError:
            return False
        return self.save_sequence_to_path(trigger, path)

    def save_sequence_to_path(self, trigger: dict, path: str) -> bool:
        try:
            sequence = self._app.config_service.save_sequence_file(path, trigger)
            trigger.update(sequence)
            self._app.dirty_tracker.mark_trigger_set_dirty()
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app._set_flash_message("出力シーケンスを保存しました。")
            messagebox.showinfo("保存", f"出力シーケンスを保存しました:\n{path}")
            return True
        except Exception as e:
            self._app._set_flash_message(f"出力シーケンス保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))
            return False

    def load_sequence_file(self) -> None:
        trigger = self._app._selected_trigger()
        if not trigger:
            messagebox.showinfo("出力シーケンス", "読込先のトリガーを選択してください。")
            return
        path = filedialog.askopenfilename(
            title="出力シーケンスを読込",
            initialdir=self._app.paths.json_dialog_initial_dir(self._app.paths.preferred_sequences_dir()),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            sequence = self._app.config_service.load_sequence_file(path, imported=True)
            trigger.update(sequence)
            self._app.dirty_tracker.mark_trigger_set_dirty()
            self._app._refresh_triggers()
            self._app._refresh_actions()
            self._app._set_flash_message("出力シーケンスを読み込みました。")
            messagebox.showinfo("読込", f"出力シーケンスを読み込みました:\n{path}")
        except Exception as e:
            self._app._set_flash_message(f"出力シーケンス読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))
