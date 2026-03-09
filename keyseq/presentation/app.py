import os
import copy
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from keyseq.presentation.dialogs import ActionDialog, PresetDialog, PresetManagerDialog, TriggerDialog
from keyseq.presentation.views import CompactView, FullView


from keyseq.application.config_service import ConfigService
from keyseq.application.app_state import AppState
from keyseq.application.hook_coordinator import HookCoordinator
from keyseq.application.sequence_runner import SequenceRunner
from keyseq.application.trigger_service import TriggerService
from keyseq.domain.config import (
    format_action_list_item,
    format_trigger_list_item,
)
from keyseq.infrastructure.input_gateway import InputGateway
from keyseq.infrastructure.json_repository import JsonRepository


def normalize_key_name(s: str) -> str:
    return (s or "").strip().lower()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Key Replacer Sequencer (Multi Trigger)")
        self.geometry("780x660")

        self.repository = JsonRepository()
        self.config_service = ConfigService(self.repository)
        self.trigger_service = TriggerService()
        self.input_gateway = InputGateway()
        self.state = AppState()

        self.hook_coordinator = HookCoordinator(self.input_gateway)
        self.sequence_runner = SequenceRunner(
            state=self.state,
            find_trigger=self._find_trigger_by_key,
            perform_action=self._perform_action,
            select_trigger=self._select_trigger_by_key,
            refresh_actions=self._refresh_actions,
            update_status=self._update_status,
            after=self.after,
            after_cancel=self.after_cancel,
        )

        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(self.base_dir, r"settings\config.json")  # 実際に読込/保存する本体JSON（既定）
        self.startup_path = os.path.join(self.base_dir, r"settings\startup.json")  # 起動時に参照する“外部指定”ファイル
        self.data = self.config_service.new_default_data()

        self.hook_active = False
        self.always_on_top_var = tk.BooleanVar(value=False)
        self._compact_mode = False
        self._full_geometry = None  # 省略表示へ入る前の geometry を記憶
        self._selected_trigger_idx = 0  # Full/Compact で選択を共有する

        # ダイアログのネストに対応するためカウンタ方式にする
        self._hook_suspend_count = 0
        self._hook_was_active_before_dialog = False
        self._programmatic_action_select = False  # action_list選択をコード側で変更中か
        self._error_dialog_open = False           # エラーダイアログ多重表示防止
        self._capturing_stop_key = False
        self._capturing_toggle_key = False
        self.triggers_enabled = True
        self._is_dirty = False
        self._flash_after_id = None

        self._build_ui()
        self._load_startup_and_config()
        self._refresh_triggers()
        self._refresh_actions()
        self._update_status()
        self._sync_hook_toggle_buttons()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
    # ---------------- State compatibility aliases ----------------
    @property
    def _selected_trigger_idx(self) -> int:
        return self.state.get_selected_index()

    @_selected_trigger_idx.setter
    def _selected_trigger_idx(self, value: int) -> None:
        self.state.update_selected_index(value)

    @property
    def _indices(self) -> dict[str, int]:
        return self.state.indices

    @_indices.setter
    def _indices(self, value: dict[str, int]) -> None:
        self.state.indices = dict(value) if isinstance(value, dict) else {}

    @property
    def _lock(self):
        return self.state.lock

    @property
    def _reentry_guard(self) -> set[str]:
        return self.state.reentry_guard

    @property
    def _run_to_end_key(self) -> str | None:
        return self.state.run_to_end_key

    @_run_to_end_key.setter
    def _run_to_end_key(self, value: str | None) -> None:
        self.state.run_to_end_key = value

    @property
    def _run_to_end_paused(self) -> bool:
        return self.state.run_to_end_paused

    @_run_to_end_paused.setter
    def _run_to_end_paused(self, value: bool) -> None:
        self.state.run_to_end_paused = bool(value)

    @property
    def _run_to_end_after_id(self):
        return self.state.run_to_end_after_id

    @_run_to_end_after_id.setter
    def _run_to_end_after_id(self, value) -> None:
        self.state.run_to_end_after_id = value

    @property
    def _chain_running(self) -> bool:
        return self.state.chain_running

    @_chain_running.setter
    def _chain_running(self, value: bool) -> None:
        self.state.chain_running = bool(value)

    @property
    def _chain_paused(self) -> bool:
        return self.state.chain_paused

    @_chain_paused.setter
    def _chain_paused(self, value: bool) -> None:
        self.state.chain_paused = bool(value)

    @property
    def _chain_key(self) -> str | None:
        return self.state.chain_key

    @_chain_key.setter
    def _chain_key(self, value: str | None) -> None:
        self.state.chain_key = value

    @property
    def _chain_thread(self):
        return self.state.chain_thread

    @_chain_thread.setter
    def _chain_thread(self, value) -> None:
        self.state.chain_thread = value

    @property
    def _chain_stop_event(self):
        return self.state.chain_stop_event

    @property
    def _chain_pause_event(self):
        return self.state.chain_pause_event
    # ---------------- Hook suspend/resume for modal dialogs ----------------
    def suspend_hook_for_dialog(self):
        """編集系ダイアログ表示中の誤爆を防ぐため、フックを一時停止（ネスト対応）"""
        self._hook_suspend_count += 1
        if self._hook_suspend_count == 1:
            self._hook_was_active_before_dialog = bool(self.hook_active)
            if self._hook_was_active_before_dialog:
                self.stop_hook(reset_trigger_mode=False)

    def resume_hook_after_dialog(self):
        """一時停止したフックを元に戻す（ネスト対応。最後のダイアログが閉じた時だけ復帰）"""
        if self._hook_suspend_count <= 0:
            self._hook_suspend_count = 0
            return
        self._hook_suspend_count -= 1
        if self._hook_suspend_count == 0:
            was_on = self._hook_was_active_before_dialog
            self._hook_was_active_before_dialog = False
            if was_on:
                self.start_hook()

    # ---------------- UI ----------------
    def _build_ui(self):
        self.outer = ttk.Frame(self, padding=12)
        self.outer.pack(fill="both", expand=True)

        # 共有Var（両Viewで同じ状態を参照）
        self.stop_key_var = tk.StringVar(value=str(self.data.get("hook_stop_key", "")))
        self.toggle_key_var = tk.StringVar(value=str(self.data.get("hook_toggle_key", "")))
        self.status_var = tk.StringVar(value="")
        self.file_status_var = tk.StringVar(value="")
        self.flash_message_var = tk.StringVar(value="")
        self.suppress_var = tk.BooleanVar(value=True)
        self.run_to_end_var = tk.BooleanVar(value=False)
        self.run_to_end_delay_var = tk.StringVar(value="300")
        self.run_to_end_delay_entry: ttk.Entry
        self.hook_toggle_btn: ttk.Button
        self.trigger_toggle_btn: ttk.Button
        self.compact_hook_toggle_btn: ttk.Button
        self.compact_trigger_toggle_btn: ttk.Button
        self.stop_key_entry: ttk.Entry
        self.stop_key_capture_btn: ttk.Button
        self.stop_key_clear_btn: ttk.Button
        self.topmost_chk: ttk.Checkbutton
        self.compact_btn: ttk.Button
        self.suppress_chk: ttk.Checkbutton
        self.run_to_end_chk: ttk.Checkbutton
        self.toggle_key_entry: ttk.Entry
        self.toggle_key_capture_btn: ttk.Button
        self.toggle_key_clear_btn: ttk.Button
        
        # 2画面（フル/省略）を用意し、pack_forgetで切替
        self.full_view = FullView(self.outer, app=self)
        self.compact_view = CompactView(self.outer, app=self)

        self.full_view.pack(fill="both", expand=True)
        # compact_view は最初は非表示
        self._build_menu()
        self._bind_menu_shortcuts()
        self._build_status_area()

    def _build_status_area(self):
        # フック/トリガー状態表示（1行または2行）
        self.runtime_status_frame = ttk.LabelFrame(self, text="ステータス", padding=(10, 6))
        self.runtime_status_frame.pack(side="top", fill="x", padx=12, pady=(0, 4))
        ttk.Label(self.runtime_status_frame, textvariable=self.status_var, anchor="w", justify="left").pack(fill="x")
        
        # 共通ステータスバー（左: ファイル状態 / 中央: 一時メッセージ）
        self.status_bar = tk.Frame(self, bd=1, relief="sunken", bg="#f3f3f3")
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_columnconfigure(1, weight=1)
        self.status_bar.grid_columnconfigure(2, weight=1)
        tk.Label(self.status_bar, textvariable=self.file_status_var, bg="#f3f3f3", anchor="w", justify="left").grid(row=0, column=0, sticky="w")
        tk.Label(self.status_bar, textvariable=self.flash_message_var, bg="#f3f3f3", anchor="center", justify="center").grid(row=0, column=1, sticky="ew")
        tk.Label(self.status_bar, text="", anchor="e").grid(row=0, column=2, sticky="e")

        self._update_file_status()

    def _update_file_status(self):
        name = os.path.basename(self.config_path or "") or "(未設定)"
        save_state = "未保存" if self._is_dirty else "保存済み"
        self.file_status_var.set(f"ファイル: {name} / {save_state}")

    def _set_dirty(self, value: bool):
        self._is_dirty = bool(value)
        self._update_file_status()

    def _clear_flash_message(self):
        self._flash_after_id = None
        self.flash_message_var.set("")

    def _set_flash_message(self, msg: str, *, auto_clear: bool = True):
        try:
            if self._flash_after_id:
                self.after_cancel(self._flash_after_id)
                self._flash_after_id = None
        except Exception:
            self._flash_after_id = None
        self.flash_message_var.set(str(msg or ""))
        if auto_clear and msg:
            self._flash_after_id = self.after(4000, self._clear_flash_message)

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="保存", command=self.save_config, accelerator="Ctrl+S")
        file_menu.add_command(label="別名で保存…", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="読込…", command=self.load_from, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="起動時に読むJSONを指定…", command=self.set_startup_config)
        file_menu.add_command(label="例を復元", command=self.restore_default)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_close)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=False)
        settings_menu.add_command(label="プリセット編集…", command=self.open_preset_manager, accelerator="Ctrl+Alt+P")
        menubar.add_cascade(label="設定", menu=settings_menu)

        self.config(menu=menubar)
        self.menubar = menubar

    def _bind_menu_shortcuts(self):
        self.bind("<Control-s>", self._on_shortcut_save, add="+")
        self.bind("<Control-S>", self._on_shortcut_save, add="+")
        self.bind("<Control-o>", self._on_shortcut_load, add="+")
        self.bind("<Control-O>", self._on_shortcut_load, add="+")
        self.bind("<Control-Shift-s>", self._on_shortcut_save_as, add="+")
        self.bind("<Control-Shift-S>", self._on_shortcut_save_as, add="+")
        self.bind("<Control-Alt-p>", self._on_shortcut_open_preset_manager, add="+")
        self.bind("<Control-Alt-P>", self._on_shortcut_open_preset_manager, add="+")

    def _is_menu_shortcut_enabled(self) -> bool:
        if getattr(self, "_capturing_stop_key", False) or getattr(self, "_capturing_toggle_key", False):
            return False
        try:
            return self.focus_displayof() is not None
        except Exception:
            return False

    def _on_shortcut_save(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.save_config()
        return "break"

    def _on_shortcut_save_as(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.save_as()
        return "break"

    def _on_shortcut_load(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.load_from()
        return "break"

    def _on_shortcut_open_preset_manager(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.open_preset_manager()
        return "break"

    def show_compact_view(self):
        if getattr(self, "_capturing_stop_key", False) or getattr(self, "_capturing_toggle_key", False):
            # 制御キーキャプチャ中に切替すると紛らわしいので止める（安全）
            return
        if self._compact_mode:
            return
        try:
            self._full_geometry = self.geometry()
        except Exception:
            self._full_geometry = None
        self._compact_mode = True
        try:
            self.full_view.pack_forget()
        except Exception:
            pass
        self.compact_view.pack(fill="both", expand=True)
        self._apply_compact_geometry()
        self._sync_trigger_selection_to_views()
        self._update_status()

    def show_full_view(self):
        if not self._compact_mode:
            return
        self._compact_mode = False
        try:
            self.compact_view.pack_forget()
        except Exception:
            pass
        self.full_view.pack(fill="both", expand=True)
        self._restore_full_geometry()
        self._sync_trigger_selection_to_views()
        self._refresh_actions()  # full側のシーケンス表示を復帰
        self._update_status()

    def _apply_compact_geometry(self):
        """省略表示時のサイズ（細め）へ"""
        try:
            # 高さは現状維持、幅だけ細めに寄せる（トリガー一覧程度）
            self.update_idletasks()
            h = max(360, int(self.winfo_height() or 560))
            w = 270
            self.geometry(f"{w}x{h}")
        except Exception:
            pass

    def _restore_full_geometry(self):
        """省略表示に入る前のサイズへ復元（取れていれば）"""
        if not self._full_geometry:
            return
        try:
            self.geometry(self._full_geometry)
        except Exception:
            pass

    def _sync_trigger_selection_to_views(self):
        """現在の選択idxを、Full/Compact両方のトリガーListboxへ反映"""
        idx = int(getattr(self, "_selected_trigger_idx", 0) or 0)
        # Full
        try:
            lb = self.full_view.trigger_list
            lb.selection_clear(0, tk.END)
            if lb.size() > 0:
                idx = max(0, min(idx, lb.size() - 1))
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)
        except Exception:
            pass
        # Compact
        try:
            lb = self.compact_view.trigger_list
            lb.selection_clear(0, tk.END)
            if lb.size() > 0:
                idx = max(0, min(idx, lb.size() - 1))
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)
        except Exception:
            pass

    def _set_selected_trigger_index(self, idx: int):
        self._selected_trigger_idx = int(idx)
        self._sync_trigger_selection_to_views()
        # フル画面なら右側も追従
        if not self._compact_mode:
            self._refresh_actions()
        self._update_status()

    def _find_trigger_by_key(self, key: str):
        return self.trigger_service.find_trigger_by_key(self.data, key)

    def _select_trigger_by_key(self, key: str):
        """押されたトリガーキーに対応する行をトリガー一覧で選択し、右側表示も更新する（UI専用）"""
        key = normalize_key_name(key)
        triggers = self.data.get("triggers", [])
        target_idx = None
        for i, t in enumerate(triggers):
            if normalize_key_name(t.get("key", "")) == key:
                target_idx = i
                break

        if target_idx is None:
            self._update_status()
            return

        self._selected_trigger_idx = int(target_idx)
        self._sync_trigger_selection_to_views()
        self._refresh_actions()
        self._update_status()
    def _apply_always_on_top(self):
        """チェック状態に応じてウィンドウを常に手前にする"""
        try:
            self.attributes("-topmost", bool(self.always_on_top_var.get()))
        except Exception:
            # 失敗してもアプリは止めない
            pass

    # ---------------- Startup config ----------------
    def _load_startup_and_config(self):
        """
        startup.json があればそれを読み、そこに書かれた config_path を起動時に読み込む。
        無い場合は従来通り self.config_path（= ./config.json）を読み込む。
        """
        startup = {}
        try:
            startup = self.config_service.load_startup(self.startup_path)
        except Exception as e:
            startup = {}
            messagebox.showwarning("startup.json 読込失敗", f"startup.json の読込に失敗しました。\n{e}\n\n既定の config.json を読み込みます。")

        if isinstance(startup, dict):
            cfg = startup.get("config_path")
            prompt_if_missing = bool(startup.get("prompt_if_missing", True))
            if cfg:
                cfg_path = cfg if os.path.isabs(cfg) else os.path.join(self.base_dir, cfg)
                if os.path.exists(cfg_path):
                    self.config_path = cfg_path
                elif prompt_if_missing:
                    picked = filedialog.askopenfilename(
                        title="起動時に読み込むJSONが見つかりません。別のJSONを選択してください。",
                        filetypes=[("JSON", "*.json"), ("All", "*.*")],
                    )
                    if picked:
                        self.config_path = picked
                        self._write_startup(
                            {
                                "config_path": self.config_service.resolve_startup_relative_path(
                                    picked,
                                    self.base_dir,
                                ),
                                "prompt_if_missing": True,
                            }
                        )

        self._load_if_exists()

    def _write_startup(self, data: dict[str, any]):
        try:
            self.config_service.save_startup(self.startup_path, data)
        except Exception as e:
            messagebox.showerror("startup.json 保存失敗", str(e))

    def _to_rel_if_possible(self, path: str) -> str:
        return self.config_service.resolve_startup_relative_path(path, self.base_dir)

    def set_startup_config(self):
        """ユーザーが起動時に読み込む本体JSON（出力シーケンス）を選び、startup.json に保存する"""
        path = filedialog.askopenfilename(
            title="起動時に読み込むJSONを選択",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return

        self.config_path = path
        self._write_startup(
            {
                "config_path": self._to_rel_if_possible(path),
                "prompt_if_missing": True,
            }
        )

        self._load_if_exists()
        self.state.reset_indices()
        self._refresh_triggers()
        self._refresh_actions()
        self._set_dirty(False)
        self._set_flash_message("起動時読み込み設定を更新しました。")
        messagebox.showinfo("設定", f"次回起動時はこのJSONを読み込みます:\n{path}")

    def _update_status(self):
        hook_state = "ON" if self.hook_active else "OFF"
        trigger_state = "ON" if self.triggers_enabled else "OFF"
        sel_key = self._selected_trigger_key() or "(未選択)"
        if getattr(self, "_compact_mode", False):
            # 省略表示：ON/OFF + 通常トリガー有効状態 + 選択中トリガー + 次に実行（行の内容）
            line = self._get_next_action_summary(sel_key)
            self.status_var.set(f"フック: {hook_state} / 通常トリガー: {trigger_state} \n選択: {sel_key} / 次: {line}")
            return

        triggers = self.data.get("triggers", [])
        keys = [normalize_key_name(t.get("key", "")) for t in triggers if t.get("key")]
        keys_text = ", ".join(keys) if keys else "(未設定)"
        # 「次」は run_to_end の場合、終端（len）なら次回は先頭なので 1 を出す
        next_i = 0
        try:
            trig = self._find_trigger_by_key(sel_key) if sel_key and sel_key != "(未選択)" else None
            actions = trig.get("actions", []) if trig else []
            idx = int(self._indices.get(sel_key, 0) or 0) if sel_key in self._indices else 0
            if actions:
                if bool(trig.get("run_to_end", False)) and idx >= len(actions):
                    next_i = 1
                else:
                    # 通常は idx+1（=次に実行される行番号）
                    next_i = min(idx, len(actions)-1) + 1
            else:
                next_i = 0
        except Exception:
            next_i = 0
        self.status_var.set(
            f"フック: {hook_state} / 通常トリガー: {trigger_state} / トリガー: {keys_text} / 選択中: {sel_key} / 選択中の次: {next_i}"
        )

    def _get_next_action_summary(self, trigger_key: str) -> str:
        """省略表示用：次に実行されるアクションを1行で返す"""
        key = normalize_key_name(trigger_key or "")
        trig = self._find_trigger_by_key(key) if key and key != "(未選択)" else None
        if not trig:
            return "(なし)"
        actions = trig.get("actions", [])
        if not actions:
            return "(なし)"
        idx_raw = int(self._indices.get(key, 0) or 0)
        # run_to_end で終端にいる（len）なら、次回は先頭から
        if bool(trig.get("run_to_end", False)) and idx_raw >= len(actions):
            idx = 0
        else:
            idx = idx_raw % len(actions)
        a = actions[idx] if 0 <= idx < len(actions) else None
        if not isinstance(a, dict):
            return "(なし)"

        t = (a.get("type") or "").strip().lower()
        if t == "mouse_click":
            x = a.get("x", "")
            y = a.get("y", "")
            btn = a.get("button", "left")
            clicks = a.get("clicks", 1)
            return f"{idx+1:02d}. [mouse_click] ({x}, {y}) {btn} x{clicks}"
        else:
            v = a.get("value", "")
            return f"{idx+1:02d}. [{t}] {v}"

    def _refresh_triggers(self):
        # Full/Compact 両方に反映
        try:
            self.full_view.trigger_list.delete(0, tk.END)
        except Exception:
            pass
        try:
            self.compact_view.trigger_list.delete(0, tk.END)
        except Exception:
            pass
        triggers = self.data.get("triggers", [])
        for i, t in enumerate(triggers):
            k = normalize_key_name(t.get("key", ""))
            s = format_trigger_list_item(i, t)
            try:
                self.full_view.trigger_list.insert(tk.END, s)
            except Exception:
                pass
            try:
                self.compact_view.trigger_list.insert(tk.END, s)
            except Exception:
                pass
            if k not in self._indices:
                self._indices[k] = 0

        # 選択を維持/補正（共通idx）
        if triggers:
            if getattr(self, "_selected_trigger_idx", None) is None:
                self._selected_trigger_idx = 0
            self._selected_trigger_idx = max(0, min(int(self._selected_trigger_idx), len(triggers) - 1))
            self._sync_trigger_selection_to_views()
        self._sync_suppress_checkbox()
        self._sync_run_to_end_ui()
        self._update_status()

    def _refresh_actions(self):
        # 省略画面では右側（action_list）が無いので、フル側のみ更新
        try:
            self.full_view.action_list.delete(0, tk.END)
        except Exception:
            self._sync_suppress_checkbox()
            self._sync_run_to_end_ui()
            self._update_status()
            return
        trig = self._selected_trigger()
        if not trig:
            self._sync_suppress_checkbox()
            self._sync_run_to_end_ui()
            self._update_status()
            return
        actions = trig.get("actions", [])
        for i, a in enumerate(actions):
            self.full_view.action_list.insert(tk.END, format_action_list_item(i, a))

        key = normalize_key_name(trig.get("key", ""))
        if key not in self._indices:
            self._indices[key] = 0
        # index補正
        if not actions:
            self._indices[key] = 0
        else:
            if bool(trig.get("run_to_end", False)):
                # run_to_end: 0..len を許す（lenは「終端＝次回は先頭」）
                idx = int(self._indices.get(key, 0) or 0)
                if idx < 0:
                    idx = 0
                if idx > len(actions):
                    idx = len(actions)
                self._indices[key] = idx
            else:
                # 従来: 循環
                self._indices[key] %= len(actions)
        # 「次に実行する行」を選択状態にする
        self._select_next_action_row(key)
        self._sync_suppress_checkbox()
        self._sync_run_to_end_ui()
        self._update_status()

    def _select_next_action_row(self, key: str):
        """現在の next index（self._indices[key]）を action_list 上で選択表示する（UIスレッド専用）"""
        key = normalize_key_name(key)
        actions = self._find_trigger_by_key(key).get("actions", []) if self._find_trigger_by_key(key) else []
        if not actions:
            self.full_view.action_list.selection_clear(0, tk.END)
            return
        trig = self._find_trigger_by_key(key)
        idx_raw = int(self._indices.get(key, 0) or 0)
        # run_to_end で終端（len）なら次回は先頭なので、先頭をハイライト
        if trig and bool(trig.get("run_to_end", False)) and idx_raw >= len(actions):
            idx = 0
        else:
            idx = idx_raw
            if idx < 0:
                idx = 0
            if idx >= len(actions):
                idx = len(actions) - 1
                self._indices[key] = idx
        self._programmatic_action_select = True
        try:
            self.full_view.action_list.selection_clear(0, tk.END)
            self.full_view.action_list.selection_set(idx)
            self.full_view.action_list.activate(idx)
            self.full_view.action_list.see(idx)
        finally:
            self._programmatic_action_select = False

    def _on_action_list_select(self, _event=None):
        """ユーザーが action_list の行を選んだら、その行を『次に実行』として indices に反映"""
        if self._programmatic_action_select:
            return
        key = self._selected_trigger_key()
        if not key:
            return
        sel = self.full_view.action_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        trig = self._find_trigger_by_key(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return
        if 0 <= idx < len(actions):
            self._indices[key] = idx
            self._update_status()

    def _on_trigger_double_click(self, _event=None):
        """トリガー一覧をダブルクリックしたらトリガー変更（rename_trigger）を開く"""
        self.rename_trigger()

    def _on_action_double_click(self, _event=None):
        """シーケンス一覧をダブルクリックしたら編集を開く"""
        # 選択行が無いときは何もしない
        if not self.full_view.action_list.curselection():
            return
        self.edit_action()

    # ---------------- Config IO ----------------
    def _load_if_exists(self):
        try:
            self.data, _ = self.config_service.load_if_exists(self.config_path)
        except Exception as e:
            messagebox.showwarning("読込失敗", f"config.json の読込に失敗しました。\n{e}\n\n例の設定で起動します。")
            self.data = self.config_service.new_default_data()

        # UIへ反映（UI生成後に呼ばれる場合はガード）
        if hasattr(self, "stop_key_var"):
            self.stop_key_var.set(str(self.data.get("hook_stop_key", "")))
        if hasattr(self, "toggle_key_var"):
            self.toggle_key_var.set(str(self.data.get("hook_toggle_key", "")))
        self._set_dirty(False)

    def save_config(self):
        try:
            self.data = self.config_service.save(self.config_path, self.data)
            self._set_dirty(False)
            self._set_flash_message("保存しました。")
            messagebox.showinfo("保存", f"保存しました:\n{self.config_path}")
        except Exception as e:
            self._set_flash_message(f"保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="別名で保存",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            self.data = self.config_service.save(path, self.data)
            self.config_path = path
            self._set_dirty(False)
            self._set_flash_message("別名で保存しました。")
            messagebox.showinfo("保存", f"保存しました:\n{path}")
        except Exception as e:
            self._set_flash_message(f"保存失敗: {e}", auto_clear=False)
            messagebox.showerror("保存失敗", str(e))

    def load_from(self):
        path = filedialog.askopenfilename(
            title="読込",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            self.data = self.config_service.load(path)
            self.config_path = path
            if hasattr(self, "stop_key_var"):
                self.stop_key_var.set(str(self.data.get("hook_stop_key", "")))
            if hasattr(self, "toggle_key_var"):
                self.toggle_key_var.set(str(self.data.get("hook_toggle_key", "")))

            # フックON中なら制御キーのフックも更新
            if getattr(self, "hook_active", False):
                self._install_stop_hook()
                self._install_toggle_hook()
            self._indices = {}
            self._refresh_triggers()
            self._refresh_actions()
            self._set_dirty(False)
            self._set_flash_message("読み込みました。")
            messagebox.showinfo("読込", f"読み込みました:\n{path}")
        except Exception as e:
            self._set_flash_message(f"読込失敗: {e}", auto_clear=False)
            messagebox.showerror("読込失敗", str(e))

    def open_preset_manager(self):
        before = copy.deepcopy(self.data.get("hotkey_presets", []))
        PresetManagerDialog(self, title="ホットキープリセット編集").wait_window()
        after = self.data.get("hotkey_presets", [])
        if before != after:
            self._set_dirty(True)
            self._set_flash_message("プリセットを更新しました。")


    def restore_default(self):
        if messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？"):
            self.data = self.config_service.new_default_data()
            if hasattr(self, "stop_key_var"):
                self.stop_key_var.set(str(self.data.get("hook_stop_key", "")))
            if hasattr(self, "toggle_key_var"):
                self.toggle_key_var.set(str(self.data.get("hook_toggle_key", "")))
            self._indices = {}
            self._refresh_triggers()
            self._refresh_actions()
            self._set_dirty(True)
            self._set_flash_message("例の設定に戻しました（未保存）。")

    # ---------------- Trigger selection/helpers ----------------
    def _selected_trigger_index(self):
        # Full/Compact どちらのListboxでも選択は共通idxとして扱う
        idx = getattr(self, "_selected_trigger_idx", None)
        if idx is None:
            return None
        return int(idx)

    def _selected_trigger(self):
        idx = self._selected_trigger_index()
        if idx is None:
            return None
        triggers = self.data.get("triggers", [])
        if idx < 0 or idx >= len(triggers):
            return None
        return triggers[idx]

    def _selected_trigger_key(self):
        t = self._selected_trigger()
        if not t:
            return None
        return normalize_key_name(t.get("key", ""))

    def _sync_suppress_checkbox(self):
        t = self._selected_trigger()
        if not t:
            self.suppress_var.set(True)
            return
        self.suppress_var.set(bool(t.get("suppress", True)))

    # ---------------- run_to_end UI sync/update ----------------
    def _sync_run_to_end_ui(self):
        """選択中トリガーの run_to_end / delay を UI へ反映"""
        t = self._selected_trigger()
        if not t:
            self.run_to_end_var.set(False)
            self.run_to_end_delay_var.set("300")
            try:
                if hasattr(self, "run_to_end_delay_entry"):
                    self.run_to_end_delay_entry.configure(state="disabled")
            except Exception:
                pass
            return

        self.run_to_end_var.set(bool(t.get("run_to_end", False)))
        d = t.get("run_to_end_delay_ms", 300)
        try:
            d = int(d)
        except Exception:
            d = 300
        if d < 0:
            d = 0
        self.run_to_end_delay_var.set(str(d))
        try:
            if hasattr(self, "run_to_end_delay_entry"):
                self.run_to_end_delay_entry.configure(state=("normal" if self.run_to_end_var.get() else "disabled"))
        except Exception:
            pass

    def update_run_to_end_delay(self, _event=None):
        """間隔(ms) を選択中トリガーへ保存（トリガーごと）"""
        t = self._selected_trigger()
        if not t:
            return
        s = (self.run_to_end_delay_var.get() or "").strip()
        try:
            v = int(s)
        except Exception:
            v = 300
        if v < 0:
            v = 0
        old_v = int(t.get("run_to_end_delay_ms", 300) or 300)
        t["run_to_end_delay_ms"] = v
        # 表示を正規化（"00300" 等を "300" に）
        self.run_to_end_delay_var.set(str(v))
        if old_v != v:
            self._set_dirty(True)

    def update_suppress(self):
        t = self._selected_trigger()
        if not t:
            return
        new_v = bool(self.suppress_var.get())
        old_v = bool(t.get("suppress", True))
        t["suppress"] = new_v
        if old_v != new_v:
            self._set_dirty(True)
        # フックON中なら再登録が必要（設定反映）
        if self.hook_active:
            self.start_hook()

    def update_run_to_end(self):
        """連続実行（run_to_end）を現在のトリガーへ反映"""
        t = self._selected_trigger()
        if not t:
            return
        new_v = bool(self.run_to_end_var.get())
        old_v = bool(t.get("run_to_end", False))
        t["run_to_end"] = new_v
        if old_v != new_v:
            self._set_dirty(True)
        self._sync_run_to_end_ui()
        # UI表示（次の行ハイライト/ステータス）を即反映
        if not getattr(self, "_compact_mode", False):
            self._refresh_actions()
        self._update_status()

    # ---------------- Trigger CRUD ----------------
    def add_trigger(self):
        dlg = TriggerDialog(self, title="トリガー追加")
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        key = normalize_key_name(res.get("key", ""))
        label = (res.get("label") or "").strip()
        if not key:
            return
        triggers = self.data.setdefault("triggers", [])
        # 重複チェック
        if self.trigger_service.key_exists(self.data, key):
            messagebox.showerror("追加できません", f"すでに存在します: {key}")
            return
        # フック停止トリガーとの重複チェック
        if self.trigger_service.is_stop_key_conflict(self.data, key):
            messagebox.showerror("追加できません", f"このキーはフック停止トリガーに設定されています:\n{key}")
            return
        if self.trigger_service.is_toggle_key_conflict(self.data, key):
            messagebox.showerror("追加できません", f"このキーは有効/無効トグルキーに設定されています:\n{key}")
            return
        triggers.append({"key": key, "label": label, "suppress": True, "run_to_end": False, "actions": []})
        self._indices.setdefault(key, 0)
        self._refresh_triggers()
        self._set_dirty(True)
        # 末尾を選択
        try:
            self.full_view.trigger_list.selection_clear(0, tk.END)
            self.full_view.trigger_list.selection_set(len(triggers) - 1)
        except Exception:
            pass
        if self.hook_active:
            self.start_hook()

    def rename_trigger(self):
        t = self._selected_trigger()
        if not t:
            messagebox.showinfo("変更", "変更したいトリガーを選択してください。")
            return
        old = normalize_key_name(t.get("key", ""))
        cur_label = (t.get("label") or "").strip()
        dlg = TriggerDialog(self, title="トリガー変更", initial_key=old, initial_label=cur_label)
        dlg.wait_window()
        res = getattr(dlg, "result", None)
        if not res:
            return
        new = normalize_key_name(res.get("key", ""))
        new_label = (res.get("label") or "").strip()
        if not new:
            return
        if self.trigger_service.key_exists(self.data, new, exclude_trigger=t):
            messagebox.showerror("変更できません", f"すでに存在します: {new}")
            return
        if self.trigger_service.is_stop_key_conflict(self.data, new):
            messagebox.showerror("変更できません", f"このキーはフック停止トリガーに設定されています:\n{new}")
            return
        if self.trigger_service.is_toggle_key_conflict(self.data, new):
            messagebox.showerror("変更できません", f"このキーは有効/無効トグルキーに設定されています:\n{new}")
            return
        # indices の移し替え
        self._indices.setdefault(old, 0)
        self._indices.setdefault(new, self._indices.get(old, 0))
        if old in self._indices:
            del self._indices[old]
        t["key"] = new
        t["label"] = new_label
        self._refresh_triggers()
        self._set_dirty(True)
        if self.hook_active:
            self.start_hook()

    def delete_trigger(self):
        idx = self._selected_trigger_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したいトリガーを選択してください。")
            return
        triggers = self.data.get("triggers", [])
        if idx < 0 or idx >= len(triggers):
            return
        key = normalize_key_name(triggers[idx].get("key", ""))
        if messagebox.askyesno("確認", f"トリガー {key} を削除しますか？"):
            del triggers[idx]
            self._indices.pop(key, None)
            self._refresh_triggers()
            self._refresh_actions()
            self._set_dirty(True)
            if self.hook_active:
                self.start_hook()

    # ---------------- Actions CRUD (selected trigger) ----------------
    def _selected_action_index(self):
        sel = self.full_view.action_list.curselection()
        if not sel:
            return None
        return int(sel[0])

    def add_action(self):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("追加", "まずトリガーを選択してください。")
            return
        ActionDialog(self, title="追加").wait_window()
        if getattr(self, "_dialog_result", None):
            trig.setdefault("actions", []).append(self._dialog_result)
            self._refresh_actions()
            self._set_dirty(True)
            self._dialog_result = None

    def edit_action(self):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("編集", "まずトリガーを選択してください。")
            return
        idx = self._selected_action_index()
        if idx is None:
            messagebox.showinfo("編集", "編集したい行を選択してください。")
            return
        current = trig.get("actions", [])[idx]
        ActionDialog(self, title="編集", initial=current).wait_window()
        if getattr(self, "_dialog_result", None):
            trig["actions"][idx] = self._dialog_result
            self._refresh_actions()
            self._set_dirty(True)
            # action_list は FullView 側にある（選択表示を復帰）
            try:
                self.full_view.action_list.selection_clear(0, tk.END)
                self.full_view.action_list.selection_set(idx)
                self.full_view.action_list.activate(idx)
                self.full_view.action_list.see(idx)
            except Exception:
                pass
            self._dialog_result = None

    def delete_action(self):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("削除", "まずトリガーを選択してください。")
            return
        idx = self._selected_action_index()
        if idx is None:
            messagebox.showinfo("削除", "削除したい行を選択してください。")
            return
        if messagebox.askyesno("確認", "選択した行を削除しますか？"):
            del trig["actions"][idx]
            self._refresh_actions()
            self._set_dirty(True)

    def move_action(self, delta: int):
        trig = self._selected_trigger()
        if not trig:
            messagebox.showinfo("移動", "まずトリガーを選択してください。")
            return
        idx = self._selected_action_index()
        if idx is None:
            messagebox.showinfo("移動", "移動したい行を選択してください。")
            return
        actions = trig.get("actions", [])
        j = idx + delta
        if j < 0 or j >= len(actions):
            return
        actions[idx], actions[j] = actions[j], actions[idx]
        key = self._selected_trigger_key()
        if key:
            self._indices[key] = j
        self._refresh_actions()
        self._set_dirty(True)

    # ---------------- Hook logic ----------------
    def _sync_hook_toggle_buttons(self):
        if not hasattr(self, "hook_toggle_btn"):
            return

        text = "停止（フックOFF）" if self.hook_active else "開始（フックON）"
        try:
            self.hook_toggle_btn.configure(text=text, state="normal")
        except Exception:
            pass
        try:
            if hasattr(self, "compact_hook_toggle_btn"):
                self.compact_hook_toggle_btn.configure(text=text, state="normal")
        except Exception:
            pass

    def _sync_trigger_toggle_buttons(self):
        if not hasattr(self, "trigger_toggle_btn"):
            return

        if not self.hook_active:
            text = "通常トリガー無効化"
            state = "disabled"
        elif self.triggers_enabled:
            text = "通常トリガー無効化"
            state = "normal"
        else:
            text = "通常トリガー有効化"
            state = "normal"

        try:
            self.trigger_toggle_btn.configure(text=text, state=state)
        except Exception:
            pass
        try:
            if hasattr(self, "compact_trigger_toggle_btn"):
                self.compact_trigger_toggle_btn.configure(text=text, state=state)
        except Exception:
            pass

    def start_hook(self):
        desired_trigger_state = bool(self.triggers_enabled)
        if self.hook_active:
            self.stop_hook(reset_trigger_mode=False)

        def _on_error(title: str, msg: str) -> None:
            self.after(0, lambda: messagebox.showerror(title, msg))

        started = self.hook_coordinator.start(
            triggers=self.data.get("triggers", []),
            on_key_event=self._on_trigger_key,
            stop_key=self.data.get("hook_stop_key", ""),
            on_stop=lambda: self.after(0, self.stop_hook),
            toggle_key=self.data.get("hook_toggle_key", ""),
            on_toggle=lambda: self.after(0, self.toggle_triggers_enabled),
            on_error=_on_error,
            enable_triggers=desired_trigger_state,
        )

        if not started:
            self._sync_hook_toggle_buttons()
            self._sync_trigger_toggle_buttons()
            return

        self.hook_active = True
        self.triggers_enabled = desired_trigger_state
        self._sync_hook_toggle_buttons()
        self._sync_trigger_toggle_buttons()
        self._update_status()

    def stop_hook(self, *, reset_trigger_mode: bool = True):
        self.sequence_runner.stop_run_to_end()
        self.sequence_runner.stop_chain(force=True)
        self.hook_coordinator.stop()
        self.hook_active = False
        if reset_trigger_mode:
            self.triggers_enabled = True

        self._sync_hook_toggle_buttons()
        self._sync_trigger_toggle_buttons()
        self._update_status()

    def toggle_hook(self):
        if self.hook_active:
            self.stop_hook()
        else:
            self.start_hook()

    def toggle_triggers_enabled(self):
        if not self.hook_active:
            return

        if self.triggers_enabled:
            # 無効化した瞬間に連続実行中を止める
            self.sequence_runner.stop_run_to_end()
            self.sequence_runner.stop_chain(force=True)
            self.hook_coordinator.disable_trigger_hooks()
            self.triggers_enabled = False
        else:
            def _on_error(title: str, msg: str) -> None:
                self.after(0, lambda: messagebox.showerror(title, msg))

            enabled = self.hook_coordinator.enable_trigger_hooks(
                triggers=self.data.get("triggers", []),
                on_key_event=self._on_trigger_key,
                on_error=_on_error,
            )
            if not enabled:
                self._sync_trigger_toggle_buttons()
                self._update_status()
                return
            self.triggers_enabled = True

        if not getattr(self, "_compact_mode", False):
            self._refresh_actions()
        self._sync_trigger_toggle_buttons()
        self._update_status()

    def _install_stop_hook(self):
        """停止トリガーを（設定されていれば）suppress=True で登録"""
        key = normalize_key_name(self.data.get("hook_stop_key", ""))
        if not key:
            return

        self.hook_coordinator.install_stop_hook(
            key,
            on_stop=lambda: self.after(0, self.stop_hook),
            on_error=lambda title, msg: self.after(0, lambda: messagebox.showerror(title, msg)),
        )

    def _uninstall_stop_hook(self):
        self.hook_coordinator.uninstall_stop_hook()

    def _install_toggle_hook(self):
        """通常トリガー有効/無効トグルキーを（設定されていれば）suppress=True で登録"""
        key = normalize_key_name(self.data.get("hook_toggle_key", ""))
        if not key:
            return

        self.hook_coordinator.install_toggle_hook(
            key,
            on_toggle=lambda: self.after(0, self.toggle_triggers_enabled),
            on_error=lambda title, msg: self.after(0, lambda: messagebox.showerror(title, msg)),
        )

    def _uninstall_toggle_hook(self):
        self.hook_coordinator.uninstall_toggle_hook()

    def _on_trigger_key(self, key: str):
        """
        keyboard callback is potentially called from hook thread;
        execute app actions on the Tk UI thread.
        """
        k = normalize_key_name(key)
        self.after(0, lambda kk=k: self.sequence_runner.handle_key(kk))

    def _perform_action(self, action: dict):
        t = (action.get("type") or "").strip().lower()
        v = action.get("value") or ""

        # 送信中にトリガーが混ざっても暴走しないように、短時間だけ抑制したい場合はここで工夫可能。
        # まずはシンプルに送信。
        if t == "hotkey":
            err_msg, normalized = self.validate_hotkey(v)
            if err_msg:
                # アプリを止めない。UIスレッドで原因を表示
                self.after(0, lambda kk=t, aa=action, ee=err_msg: self._show_action_error(kk, aa, ee))
                return
            # keyboard は "ctrl+c" のような表記でOK（打ち間違いだと例外が出ることがある）
            self.input_gateway.send_hotkey(normalized)
        elif t == "text":
            self.input_gateway.write_text(v)
        elif t == "mouse_click":
            # 例: {"type":"mouse_click","x":100,"y":200,"button":"left","clicks":1}
            try:
                x = int(action.get("x"))
                y = int(action.get("y"))
            except Exception:
                self.after(0, lambda: messagebox.showerror("送信エラー", "mouse_click の x/y が不正です（整数で指定してください）。"))
                return
            button = (action.get("button") or "left").strip().lower()
            clicks = action.get("clicks", 1)
            try:
                clicks = int(clicks)
            except Exception:
                clicks = 1
            if clicks < 1:
                clicks = 1
            if button not in ("left", "right", "middle"):
                button = "left"
            # 実行
            try:
                self.input_gateway.click_mouse(x=x, y=y, button=button, clicks=clicks)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("送信エラー", f"mouse_click の実行に失敗しました。\n{type(e).__name__}: {e}"))
        else:
            # 不明タイプはテキスト扱い
            self.input_gateway.write_text(str(v))
            
    def validate_hotkey(self, hotkey: str) -> tuple[str, str]:
        """
        hotkey を検証し、(エラーメッセージ, 正規化したhotkey) を返す。
        エラーなしならエラーメッセージは ""。
        """
        s = (hotkey or "").strip()
        if not s:
            return "hotkey が空です。", ""

        # split結果を保持して空要素を検出する（ctrl++c / +ctrl+c / ctrl+c+ を弾く）
        raw = s.split("+")
        parts = [p.strip().lower() for p in raw]

        if any(p == "" for p in parts):
            return "hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。", ""

        # ここで正規化（余分な空白・大文字を吸収）
        normalized = "+".join(parts)

        # 同一キーの重複を弾く（例: ctrl+ctrl+c）
        if len(set(parts)) != len(parts):
            return "hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", ""

        # キー名の妥当性チェック（各キー単体が解決できるか）
        try:
            for p in parts:
                self.input_gateway.validate_key_name(p)
        except Exception as e:
            return f"不明なキー名があります: '{p}'（詳細: {e}）", ""

        return "", normalized

    def _show_action_error(self, trigger_key: str, action: dict, err: Exception):
        """送信エラーをUIスレッドで表示（多重表示は抑止）"""
        if self._error_dialog_open:
            return
        self._error_dialog_open = True
        try:
            t = (action.get("type") or "").strip().lower()
            v = action.get("value") or ""
            msg = (
                "キー送信中にエラーが発生しました。\n"
                f"送信キーに間違いがあります。修正してください。\n\n"
                #f"トリガー: {normalize_key_name(trigger_key)}\n"
                f"種別: {t}\n"
                f"値: {v}\n\n"
                f"エラー: {err}"
            )
            messagebox.showerror("送信エラー", msg)
        finally:
            self._error_dialog_open = False

    # ---------------- Control key capture logic ----------------
    def _toggle_stop_key_capture(self):
        if self._capturing_stop_key:
            self._stop_stop_key_capture(cancel=True)
        else:
            self._start_stop_key_capture()

    def _start_stop_key_capture(self):
        """停止トリガーをキャプチャ開始（キャプチャ中はフックを一時停止）"""
        if getattr(self, "_capturing_toggle_key", False):
            self._stop_toggle_key_capture(cancel=True)

        self._capturing_stop_key = True
        if hasattr(self, "stop_key_capture_btn"):
            self.stop_key_capture_btn.configure(text="取得中…（Escで停止）")
        if hasattr(self, "stop_key_clear_btn"):
            self.stop_key_clear_btn.configure(state="disabled")

        # キャプチャ中なのでフックを一時停止（開始中なら止まる / 終了時に元に戻る）
        self.suspend_hook_for_dialog()

        # フォーカスは表示欄に（入力はしないが、キーを拾いやすくする）
        if hasattr(self, "stop_key_entry"):
            self.stop_key_entry.focus_set()

        # ルートで拾う
        self.bind("<KeyPress>", self._on_stop_key_capture_keypress, add="+")

    def _stop_stop_key_capture(self, cancel: bool = False):
        if not getattr(self, "_capturing_stop_key", False):
            return
        self._capturing_stop_key = False
        try:
            self.unbind("<KeyPress>")
        except Exception:
            pass

        if hasattr(self, "stop_key_capture_btn"):
            self.stop_key_capture_btn.configure(text="キー入力で取得")
        if hasattr(self, "stop_key_clear_btn"):
            self.stop_key_clear_btn.configure(state="normal")

        # 一時停止していたフックを元に戻す
        self.resume_hook_after_dialog()

        if cancel:
            return

    def _on_stop_key_capture_keypress(self, event):
        """停止トリガーのキャプチャ（単キー）"""
        if not self._capturing_stop_key:
            return

        key = self._normalize_tk_key_for_trigger(event.keysym)

        # Esc はキャンセル
        if key == "esc":
            self._stop_stop_key_capture(cancel=True)
            return "break"

        # 修飾キー単体は無視
        if key in ("ctrl", "shift", "alt", "windows"):
            return "break"

        # 単キーのみ（ここに来る時点で "+" は入らないが保険）
        if "+" in key:
            messagebox.showerror("設定できません", "停止トリガーは単キーのみ対応です（例: f12）。")
            return "break"

        # トリガー一覧との重複禁止（キャプチャ確定時にチェック）
        if self.trigger_service.key_exists(self.data, key):
            messagebox.showerror("設定できません", f"停止トリガーがトリガー一覧と重複しています:\n{key}")
            return "break"
        if self.trigger_service.is_toggle_key_conflict(self.data, key):
            messagebox.showerror("設定できません", f"停止トリガーがトグルキーと重複しています:\n{key}")
            return "break"

        # 妥当性チェック
        try:
            self.input_gateway.validate_key_name(key)
        except Exception as e:
            messagebox.showerror("設定できません", f"不明なキー名です:\n{key}\n\n{e}")
            return "break"

        # 重複OKならそのまま適用（保存→表示更新）
        self.data["hook_stop_key"] = key
        if hasattr(self, "stop_key_var"):
            self.stop_key_var.set(key)
        self._set_dirty(True)

        # キャプチャ終了（この時点で resume により、元がONなら start_hook が呼ばれる）
        self._stop_stop_key_capture(cancel=False)
        return "break"

    def _toggle_toggle_key_capture(self):
        if self._capturing_toggle_key:
            self._stop_toggle_key_capture(cancel=True)
        else:
            self._start_toggle_key_capture()

    def _start_toggle_key_capture(self):
        """有効/無効トグルキーをキャプチャ開始（キャプチャ中はフックを一時停止）"""
        if getattr(self, "_capturing_stop_key", False):
            self._stop_stop_key_capture(cancel=True)

        self._capturing_toggle_key = True
        if hasattr(self, "toggle_key_capture_btn"):
            self.toggle_key_capture_btn.configure(text="取得中…（Escで停止）")
        if hasattr(self, "toggle_key_clear_btn"):
            self.toggle_key_clear_btn.configure(state="disabled")

        self.suspend_hook_for_dialog()

        if hasattr(self, "toggle_key_entry"):
            self.toggle_key_entry.focus_set()

        self.bind("<KeyPress>", self._on_toggle_key_capture_keypress, add="+")

    def _stop_toggle_key_capture(self, cancel: bool = False):
        if not getattr(self, "_capturing_toggle_key", False):
            return
        self._capturing_toggle_key = False
        try:
            self.unbind("<KeyPress>")
        except Exception:
            pass

        if hasattr(self, "toggle_key_capture_btn"):
            self.toggle_key_capture_btn.configure(text="キー入力で取得")
        if hasattr(self, "toggle_key_clear_btn"):
            self.toggle_key_clear_btn.configure(state="normal")

        self.resume_hook_after_dialog()

        if cancel:
            return

    def _on_toggle_key_capture_keypress(self, event):
        """通常トリガー有効/無効トグルキーのキャプチャ（単キー）"""
        if not self._capturing_toggle_key:
            return

        key = self._normalize_tk_key_for_trigger(event.keysym)

        if key == "esc":
            self._stop_toggle_key_capture(cancel=True)
            return "break"

        if key in ("ctrl", "shift", "alt", "windows"):
            return "break"

        if "+" in key:
            messagebox.showerror("設定できません", "トグルキーは単キーのみ対応です（例: f11）。")
            return "break"

        if self.trigger_service.key_exists(self.data, key):
            messagebox.showerror("設定できません", f"トグルキーがトリガー一覧と重複しています:\n{key}")
            return "break"
        if self.trigger_service.is_stop_key_conflict(self.data, key):
            messagebox.showerror("設定できません", f"トグルキーが停止キーと重複しています:\n{key}")
            return "break"

        try:
            self.input_gateway.validate_key_name(key)
        except Exception as e:
            messagebox.showerror("設定できません", f"不明なキー名です:\n{key}\n\n{e}")
            return "break"

        self.data["hook_toggle_key"] = key
        if hasattr(self, "toggle_key_var"):
            self.toggle_key_var.set(key)
        self._set_dirty(True)

        self._stop_toggle_key_capture(cancel=False)
        return "break"

    def _normalize_tk_key_for_trigger(self, keysym: str) -> str:
        """Tk keysym を keyboard 用の単キー名に寄せる（制御トリガー/通常トリガー用）"""
        k = (keysym or "").lower()
        mapping = {
            "control_l": "ctrl", "control_r": "ctrl",
            "shift_l": "shift", "shift_r": "shift",
            "alt_l": "alt", "alt_r": "alt",
            "super_l": "windows", "super_r": "windows",
            "win_l": "windows", "win_r": "windows",
            "return": "enter",
            "escape": "esc",
            "space": "space",
            "tab": "tab",
            "backspace": "backspace",
            "prior": "page up",
            "next": "page down",
        }
        return mapping.get(k, k)

    def clear_stop_key(self):
        """停止トリガーを未設定（空）に戻す"""
        if getattr(self, "_capturing_stop_key", False):
            self._stop_stop_key_capture(cancel=True)

        old = str(self.data.get("hook_stop_key", ""))
        self.data["hook_stop_key"] = ""
        if hasattr(self, "stop_key_var"):
            self.stop_key_var.set("")
        if old:
            self._set_dirty(True)

        # フックON中なら停止トリガーのフックだけ解除（他のフックは維持）
        if getattr(self, "hook_active", False):
            self._uninstall_stop_hook()

    def clear_toggle_key(self):
        """有効/無効トグルキーを未設定（空）に戻す"""
        if getattr(self, "_capturing_toggle_key", False):
            self._stop_toggle_key_capture(cancel=True)

        old = str(self.data.get("hook_toggle_key", ""))
        self.data["hook_toggle_key"] = ""
        if hasattr(self, "toggle_key_var"):
            self.toggle_key_var.set("")
        if old:
            self._set_dirty(True)

        # フックON中ならトグルキーのフックだけ解除（他のフックは維持）
        if getattr(self, "hook_active", False):
            self._uninstall_toggle_hook()


    # ---------------- Close ----------------
    def on_close(self):
        try:
            self.stop_hook()
        finally:
            self.destroy()



if __name__ == "__main__":
    app = App()
    app.mainloop()
