from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from keyseq.domain.config import format_preset_list_item, safe_deepcopy
from keyseq.presentation.dialogs.preset_dialog import PresetDialog
from keyseq.presentation.modal import grab_modal

if TYPE_CHECKING:
    from keyseq.presentation.app import App


def format_preset_manager_source_labels(
    *,
    individual_for_save: bool,
    individual_state: str,
    displayed_source: str,
    individual_path: str,
    default_individual_path: str,
    global_path: str,
    keymap_set_saved: bool,
) -> tuple[str, str, str]:
    """プリセットマネージャの保存先・出どころ・可否の文言を組み立てる。"""
    if individual_for_save and individual_path:
        save_destination = f"保存先: {individual_path}"
    else:
        save_destination = f"保存先: グローバル（{global_path}）"

    source_messages = []
    if individual_state == "external":
        source_messages.append(
            "config 外のファイルを読み込み中。次の保存で管理下へ移ります。"
            f"{default_individual_path} へ保存します"
        )
    elif individual_state == "external_missing":
        if individual_for_save:
            source_messages.append(
                "記録されていた個別の保存先は config 外にあり、読み込めません。"
                f"{default_individual_path} へ保存します"
            )
        else:
            source_messages.append(
                "記録されていた個別の保存先は config 外にあり、読み込めません。"
                "専用を再度有効にすると、"
                f"{default_individual_path} へ保存します"
            )
    if not individual_for_save and displayed_source == "builtin":
        source_messages.append(
            "グローバルを読み込めませんでした。組込既定を表示中"
            "（OK でグローバルを作成します）"
        )
    elif displayed_source == "global" and individual_state != "off":
        source_messages.append("グローバルを表示中")
    elif displayed_source == "builtin":
        source_messages.append("読み込めませんでした（既定を表示中）")

    availability = "" if keymap_set_saved else "構成セットを保存すると専用にできます"
    return save_destination, " / ".join(source_messages), availability


class PresetManagerDialog(tk.Toplevel):
    """App.data['hotkey_presets'] を編集する"""
    def __init__(self, parent: App, title: str = "プリセット編集"):
        super().__init__(parent)
        self._init_preset_manager_state(parent, title)
        self._build_preset_manager_widgets()
        self._bind_preset_manager_events()
        self._sync_initial_presets()
        self._update_source_labels()
        grab_modal(self, parent)

    def _init_preset_manager_state(self, parent: App, title: str) -> None:
        self.parent = parent
        self.title(title)
        self.resizable(False, False)

        # 編集中の誤爆防止
        self.parent.hook.suspend_hook_for_dialog()

        self._temp = safe_deepcopy(parent.data.get("hotkey_presets", []))
        if not isinstance(self._temp, list):
            self._temp = []
        self._loaded_temp = safe_deepcopy(self._temp)

        source = parent.config_service.describe_hotkey_presets_source(
            parent.data,
            config_root=parent.config_root,
        )
        self._individual_state = source["individual_state"]
        self._displayed_source = source["displayed_source"]
        self._global_hotkey_presets_path = parent.config_service.load_global_hotkey_presets_path(
            config_root=parent.config_root,
        )
        self._keymap_set_saved = bool(parent.keymap_set_path)
        self.individual_var = tk.BooleanVar(
            value=parent.data.get("hotkey_presets_individual") is True,
        )
        self.save_destination_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.individual_unavailable_var = tk.StringVar()

    def _build_preset_manager_widgets(self) -> None:
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="プリセット一覧").grid(row=0, column=0, sticky="w")
        self.listbox = tk.Listbox(frm, height=12, width=56, exportselection=False)
        self.listbox.grid(row=1, column=0, rowspan=6, sticky="nsew", padx=(0, 0))

        # スクロールバー（プリセット一覧）
        presets_sb = ttk.Scrollbar(frm, orient="vertical", command=self.listbox.yview)
        presets_sb.grid(row=1, column=1, rowspan=6, sticky="ns", padx=(6, 10))
        self.listbox.configure(yscrollcommand=presets_sb.set)

        btns = ttk.Frame(frm)
        btns.grid(row=1, column=2, sticky="n")
        ttk.Button(btns, text="追加", width=14, command=self.add).pack(pady=(0, 6))
        ttk.Button(btns, text="編集", width=14, command=self.edit).pack(pady=6)
        ttk.Button(btns, text="削除", width=14, command=self.delete).pack(pady=6)
        ttk.Separator(btns).pack(fill="x", pady=10)
        ttk.Button(btns, text="上へ", width=14, command=lambda: self.move(-1)).pack(pady=6)
        ttk.Button(btns, text="下へ", width=14, command=lambda: self.move(+1)).pack(pady=6)

        source_frame = ttk.Frame(frm)
        source_frame.grid(row=7, column=0, columnspan=3, sticky="we", pady=(12, 0))
        self.individual_check = ttk.Checkbutton(
            source_frame,
            text="この構成セット専用にする",
            variable=self.individual_var,
        )
        self.individual_check.grid(row=0, column=0, sticky="w")
        if not self._keymap_set_saved:
            self.individual_check.configure(state="disabled")
        ttk.Label(source_frame, textvariable=self.save_destination_var).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 0),
        )
        ttk.Label(source_frame, textvariable=self.source_var).grid(
            row=2,
            column=0,
            sticky="w",
        )
        ttk.Label(source_frame, textvariable=self.individual_unavailable_var).grid(
            row=3,
            column=0,
            sticky="w",
        )

        bottom = ttk.Frame(frm)
        bottom.grid(row=8, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(bottom, text="OK", command=self.on_ok).pack(side="left", padx=(0, 8))
        ttk.Button(bottom, text="キャンセル", command=self.destroy).pack(side="left")

        frm.grid_columnconfigure(0, weight=1)
        frm.grid_rowconfigure(1, weight=1)

    def _bind_preset_manager_events(self) -> None:
        # ダブルクリックで編集
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        self.individual_check.configure(command=self._reload_presets_for_individual_toggle)

    def _sync_initial_presets(self) -> None:
        if self.parent.data.get("hotkey_presets_individual") is not True:
            replacement = self._toggle_preset_replacement(False)
            self._temp = safe_deepcopy(replacement)
            self._loaded_temp = safe_deepcopy(replacement)
        self._refresh()

    def _update_source_labels(self):
        individual_for_save = bool(self.individual_var.get())
        individual_path = self.parent.config_service.resolve_hotkey_presets_save_path(
            self.parent.data,
            config_root=self.parent.config_root,
            keymap_set_path=self.parent.keymap_set_path,
            individual=individual_for_save,
        )
        default_individual_path = individual_path
        if self._individual_state in {"external", "external_missing"} and not default_individual_path:
            default_individual_path = self.parent.config_service.resolve_hotkey_presets_save_path(
                self.parent.data,
                config_root=self.parent.config_root,
                keymap_set_path=self.parent.keymap_set_path,
                individual=True,
            )
        save_destination, source, availability = format_preset_manager_source_labels(
            individual_for_save=individual_for_save,
            individual_state=self._individual_state,
            displayed_source=self._displayed_source,
            individual_path=individual_path,
            default_individual_path=default_individual_path,
            global_path=self._global_hotkey_presets_path,
            keymap_set_saved=self._keymap_set_saved,
        )
        self.save_destination_var.set(save_destination)
        self.source_var.set(source)
        self.individual_unavailable_var.set(availability)

    def _reload_presets_for_individual_toggle(self):
        individual_for_save = bool(self.individual_var.get())
        replacement = self._toggle_preset_replacement(individual_for_save)
        if replacement is None:
            self._update_toggle_source(individual_for_save)
            self._update_source_labels()
            return

        if self._temp != self._loaded_temp and self._temp != replacement:
            if not messagebox.askyesno(
                "プリセットの切替",
                "編集中の内容は破棄されます。切り替えますか？",
                parent=self,
            ):
                self.individual_var.set(not individual_for_save)
                return

        self._temp = safe_deepcopy(replacement)
        self._loaded_temp = safe_deepcopy(replacement)
        self._update_toggle_source(individual_for_save)
        self._refresh()
        self._update_source_labels()

    def _toggle_preset_replacement(self, individual_for_save: bool) -> list | None:
        if individual_for_save:
            runtime = {**self.parent.data, "hotkey_presets_individual": True}
            return self.parent.config_service.load_individual_hotkey_presets(
                runtime,
                config_root=self.parent.config_root,
            )

        presets = self.parent.config_service.load_global_hotkey_presets(
            config_root=self.parent.config_root,
        )
        if presets is not None:
            return presets
        return self.parent.config_service.new_default_data()["hotkey_presets"]

    def _update_toggle_source(self, individual_for_save: bool) -> None:
        runtime = {
            **self.parent.data,
            "hotkey_presets_individual": individual_for_save,
        }
        source = self.parent.config_service.describe_hotkey_presets_source(
            runtime,
            config_root=self.parent.config_root,
        )
        self._individual_state = source["individual_state"]
        self._displayed_source = source["displayed_source"]

    def _on_double_click(self, _event=None):
        """プリセット一覧をダブルクリックしたら編集を開く"""
        if not self.listbox.curselection():
            return
        self.edit()

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for i, p in enumerate(self._temp):
            self.listbox.insert(tk.END, format_preset_list_item(i, p))

    def _sel(self):
        s = self.listbox.curselection()
        return int(s[0]) if s else None
    
    def _norm_label(self, s: str) -> str:
        return (s or "").strip().lower()

    def _label_exists(self, label: str, exclude_index: int | None = None) -> bool:
        target = self._norm_label(label)
        if not target:
            return False
        for i, p in enumerate(self._temp):
            if exclude_index is not None and i == exclude_index:
                continue
            if self._norm_label(str(p.get("label", ""))) == target:
                return True
        return False

    def add(self):
        dlg = PresetDialog(self, title="プリセット追加")
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return

        value = (res.get("value") or "").strip()
        label = (res.get("label") or "").strip()

        # label 重複チェック（同名プリセット禁止）
        if self._label_exists(label):
            messagebox.showerror("追加できません", f"同名のプリセットが既に存在します。\n\nlabel: {label}")
            return

        # hotkey を検証して不正なら弾く（即時UIエラー）
        err_msg, normalized = self.parent.validate_hotkey(value)
        if err_msg:
            messagebox.showerror("不正なhotkey", f"プリセットの hotkey 値が不正です。\n\n入力: {value}\n理由: {err_msg}")
            return

        self._temp.append({"label": label, "value": normalized})
        self._refresh()
        self.listbox.selection_set(len(self._temp) - 1)

    def edit(self):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        cur = self._temp[idx]
        dlg = PresetDialog(
            self,
            title="プリセット編集",
            initial_value=str(cur.get("value", "")),
            initial_label=str(cur.get("label", "")),
        )
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return

        value = (res.get("value") or "").strip()
        label = (res.get("label") or "").strip()

        # label 重複チェック（自分以外）
        if self._label_exists(label, exclude_index=idx):
            messagebox.showerror("変更できません", f"同名のプリセットが既に存在します。\n\nlabel: {label}")
            return

        # hotkey を検証して不正なら弾く（即時UIエラー）
        err_msg, normalized = self.parent.validate_hotkey(value)
        if err_msg:
            messagebox.showerror("不正なhotkey", f"プリセットの hotkey 値が不正です。\n\n入力: {value}\n理由: {err_msg}")
            return

        self._temp[idx] = {"label": label, "value": normalized}
        self._refresh()
        self.listbox.selection_set(idx)

    def delete(self):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        if messagebox.askyesno("確認", "選択したプリセットを削除しますか？"):
            del self._temp[idx]
            self._refresh()

    def move(self, delta: int):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        j = idx + delta
        if j < 0 or j >= len(self._temp):
            return
        self._temp[idx], self._temp[j] = self._temp[j], self._temp[idx]
        self._refresh()
        self.listbox.selection_set(j)

    def on_ok(self):
        def on_overwrite_conflict(stored_path: str, existing: list | None) -> str:
            choice = self.parent.hotkey_presets_io.confirm_overwrite(
                stored_path=stored_path,
                existing=existing,
            )
            if choice == "adopt" and existing is not None:
                self._temp = safe_deepcopy(existing)
                self._loaded_temp = safe_deepcopy(existing)
                self._refresh()
                self._update_source_labels()
            return choice

        if self.parent.save_hotkey_presets(
            self._temp,
            individual=bool(self.individual_var.get()),
            loaded_presets=self._loaded_temp,
            on_overwrite_conflict=on_overwrite_conflict,
        ):
            self.destroy()

    def destroy(self):
        # ダイアログ終了でフックを必要なら再開
        self.parent.hook.resume_hook_after_dialog()
        super().destroy()
