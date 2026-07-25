from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from keyseq.presentation.controllers.config_io.keymap_file_io import KeymapFileIo
from keyseq.presentation.controllers.config_io.sequence_file_io import SequenceFileIo
from keyseq.presentation.controllers.config_io.trigger_set_file_io import TriggerSetFileIo
from keyseq.presentation.theme import coerce_font_delta


class ConfigIoController:
    """構成セット・個別JSON（keymap / trigger_set / sequence）の保存・読込フロー。"""

    def __init__(self, app) -> None:
        self._app = app
        self._keymap_io = KeymapFileIo(app)
        self._trigger_set_io = TriggerSetFileIo(app)
        self._sequence_io = SequenceFileIo(app)

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
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
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
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
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
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
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
            self._app.trigger_panel.refresh_triggers()
            self._app.trigger_panel.refresh_actions()
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
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
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
        base["ui_font_delta_pt"] = coerce_font_delta(base.get("ui_font_delta_pt", 0))

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

    # Temporary migration-era wrappers; scheduled for removal in task_05.
    def selected_keymap_for_io(self) -> "tuple[int, dict] | tuple[None, None]":
        return self._keymap_io.selected_keymap_for_io()

    def save_selected_keymap(self) -> bool:
        return self._keymap_io.save_selected_keymap()

    def save_selected_keymap_as(self) -> bool:
        return self._keymap_io.save_selected_keymap_as()

    def save_keymap_to_path(self, index: int, keymap: dict, path: str) -> bool:
        return self._keymap_io.save_keymap_to_path(index, keymap, path)

    def load_keymap_file(self) -> None:
        self._keymap_io.load_keymap_file()

    def save_trigger_set_file(self) -> bool:
        return self._trigger_set_io.save_trigger_set_file()

    def save_trigger_set_file_as(self) -> bool:
        return self._trigger_set_io.save_trigger_set_file_as()

    def save_trigger_set_to_path(self, path: str) -> bool:
        return self._trigger_set_io.save_trigger_set_to_path(path)

    def load_trigger_set_file(self) -> None:
        self._trigger_set_io.load_trigger_set_file()

    def save_selected_sequence(self) -> bool:
        return self._sequence_io.save_selected_sequence()

    def save_selected_sequence_as(self) -> bool:
        return self._sequence_io.save_selected_sequence_as()

    def save_sequence_to_path(self, trigger: dict, path: str) -> bool:
        return self._sequence_io.save_sequence_to_path(trigger, path)

    def load_sequence_file(self) -> None:
        self._sequence_io.load_sequence_file()
