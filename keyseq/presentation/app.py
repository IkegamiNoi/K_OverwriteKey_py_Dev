import os
import copy
import tkinter as tk
from tkinter import messagebox, ttk

from keyseq.presentation.dialogs import (
    PresetManagerDialog,
)
from keyseq.presentation.keyboard_layouts import (
    DEFAULT_LAYOUT_ID,
)
from keyseq.presentation.config_io_controller import ConfigIoController
from keyseq.presentation.config_paths import ConfigPaths
from keyseq.presentation.dirty_state import DirtyStateTracker
from keyseq.presentation.hook_controller import HookController
from keyseq.presentation.key_capture import SingleKeyCaptureController
from keyseq.presentation.keymap_panel_controller import KeymapPanelController
from keyseq.presentation.layout_controller import LayoutController
from keyseq.presentation.trigger_panel_controller import TriggerPanelController
from keyseq.presentation.listbox_utils import (
    focused_listbox_index,
    sync_listbox_selection_to_focus,
)
from keyseq.presentation.views import CompactView, FullView
from keyseq.presentation.theme import apply_global_theme


from keyseq.application.action_executor import ActionExecutor
from keyseq.application.config_service import ConfigService
from keyseq.application.app_state import AppState
from keyseq.application.hook_coordinator import HookCoordinator
from keyseq.application.input_router import InputRouter
from keyseq.application.keymap_service import KeymapService
from keyseq.application.key_state_manager import KeyStateManager
from keyseq.application.sequence_runner import SequenceRunner
from keyseq.application.trigger_service import TriggerService
from keyseq.domain.config import (
    DEFAULT_RUN_TO_END_DELAY_MS,
)
from keyseq.infrastructure.input_gateway import InputGateway
from keyseq.infrastructure.json_repository import JsonRepository

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.repository = JsonRepository()
        self.config_service = ConfigService(self.repository)

        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_root = os.path.join(self.base_dir, "config")
        self.user_root = os.path.join(self.config_root, "user")
        os.makedirs(self.user_root, exist_ok=True)
        self.paths = ConfigPaths(
            base_dir=self.base_dir,
            config_root=self.config_root,
            user_root=self.user_root,
            config_service=self.config_service,
        )
        self.startup_path = self.paths.resolve_startup_path()
        self.keymap_set_path = self.paths.resolve_keymap_set_path()
        self._startup_settings = self._load_startup_settings()
        self._ui_font_delta_pt = self._coerce_font_delta(self._startup_settings.get("ui_font_delta_pt", 0))
        apply_global_theme(self, font_delta_pt=self._ui_font_delta_pt)

        self.title("Key Replacer Sequencer (Multi Trigger)")
        self.geometry("780x820")

        self.trigger_service = TriggerService()
        self.keymap_service = KeymapService()
        self.input_gateway = InputGateway()
        self.key_state_manager = KeyStateManager(resolve_scan_code=lambda sc: self.layout.resolve_key_name_from_scan_code(sc))
        self.action_executor = ActionExecutor(
            input_gateway=self.input_gateway,
            validate_hotkey=self.validate_hotkey,
            on_action_error=lambda action, err: self.hook.show_action_error("", action, err),
            on_runtime_error=lambda title, msg: messagebox.showerror(title, msg),
            on_stop_hook=lambda: self.hook.stop_hook(),
            on_toggle_mode=lambda: self.hook.toggle_custom_input_enabled(),
            on_select_keymap=lambda keymap_id: self.activate_keymap_by_id(keymap_id, mark_dirty=False, show_flash=True),
            on_trigger=lambda key: self.sequence_runner.handle_key(key),
        )
        self.input_router = InputRouter(
            key_state_manager=self.key_state_manager,
            get_send_guard_count=self._get_send_guard_count,
            get_hook_pause_count=lambda: self.hook.get_hook_pause_count(),
            get_stop_key=lambda: self.data.get("hook_stop_key", ""),
            get_toggle_key=lambda: self.data.get("hook_toggle_key", ""),
            get_custom_input_enabled=lambda: bool(self.hook.custom_input_enabled),
            find_keymap_switch_target=self._find_keymap_switch_target_id,
            find_trigger=self._find_trigger_by_key,
            find_keymap_target=self._find_keymap_target,
            resolve_scan_code=lambda sc: self.layout.resolve_key_name_from_scan_code(sc),
        )
        self.state = AppState()
        # --- controllers (計画02で順次追加) ---
        self.dirty_tracker = DirtyStateTracker(
            get_data=lambda: self.data,
            keymap_service=self.keymap_service,
            config_service=self.config_service,
            on_change=self._update_file_status,
        )
        self.stop_key_capture = SingleKeyCaptureController(
            self,
            data_key="hook_stop_key",
            var_attr="stop_key_var",
            capture_btn_attr="stop_key_capture_btn",
            clear_btn_attr="stop_key_clear_btn",
            focus_entry_attr="stop_key_entry",
            label="停止トリガー",
            single_key_example="f12",
            conflict_checks=[
                (lambda app, key: app.trigger_service.key_exists(app.data, key), "トリガー一覧"),
                (lambda app, key: app.trigger_service.is_toggle_key_conflict(app.data, key), "トグルキー"),
                (lambda app, key: bool(app.keymap_service.get_keymap_by_switch_key(app.data, key)), "キーマップ直接切替キー"),
                (lambda app, key: app.keymap_service.source_key_exists(app.data, key), "キーマップ元キー"),
            ],
        )
        self.toggle_key_capture = SingleKeyCaptureController(
            self,
            data_key="hook_toggle_key",
            var_attr="toggle_key_var",
            capture_btn_attr="toggle_key_capture_btn",
            clear_btn_attr="toggle_key_clear_btn",
            focus_entry_attr="toggle_key_entry",
            label="トグルキー",
            single_key_example="f11",
            conflict_checks=[
                (lambda app, key: app.trigger_service.key_exists(app.data, key), "トリガー一覧"),
                (lambda app, key: app.trigger_service.is_stop_key_conflict(app.data, key), "停止キー"),
                (lambda app, key: bool(app.keymap_service.get_keymap_by_switch_key(app.data, key)), "キーマップ直接切替キー"),
                (lambda app, key: app.keymap_service.source_key_exists(app.data, key), "キーマップ元キー"),
            ],
        )
        self.config_io = ConfigIoController(self)
        self.layout = LayoutController(self)
        self.keymap_panel = KeymapPanelController(self)
        self.trigger_panel = TriggerPanelController(self)
        self.hook = HookController(self)

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

        self.data = self.config_service.new_default_data()

        self.always_on_top_var = tk.BooleanVar(value=False)
        self._compact_mode = False
        self._full_geometry = None  # 省略表示へ入る前の geometry を記憶
        self._selected_trigger_idx = 0  # Full/Compact で選択を共有する

        self._programmatic_action_select = False  # action_list選択をコード側で変更中か
        self._flash_after_id = None
        self._build_ui()
        self.config_io.load_startup_and_config()
        self.layout.reload_keyboard_layouts()
        self._refresh_triggers()
        self._refresh_actions()
        self._update_status()
        self.hook.sync_hook_toggle_buttons()

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


    def _get_send_guard_count(self) -> int:
        return int(self.action_executor.send_guard_count)

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
        self.ui_font_delta_var = tk.IntVar(value=int(self._ui_font_delta_pt))
        self.suppress_var = tk.BooleanVar(value=True)
        self.run_to_end_var = tk.BooleanVar(value=False)
        self.run_to_end_delay_var = tk.StringVar(value=str(DEFAULT_RUN_TO_END_DELAY_MS))
        self.keyboard_layout_var = tk.StringVar(value=str(self.data.get("keyboard_layout", DEFAULT_LAYOUT_ID)))
        self.keyboard_show_physical_key_labels_var = tk.BooleanVar(
            value=bool(self.data.get("keyboard_show_physical_key_labels", False))
        )
        self.run_to_end_delay_entry: ttk.Entry
        self.hook_toggle_btn: ttk.Button
        self.trigger_toggle_btn: ttk.Button
        self.compact_hook_toggle_btn: ttk.Button
        self.compact_trigger_toggle_btn: ttk.Button
        self.stop_key_entry: ttk.Entry
        self.stop_key_capture_btn: ttk.Button
        self.stop_key_clear_btn: ttk.Button
        self.keymap_listbox: tk.Listbox
        self.keymap_add_btn: ttk.Button
        self.keymap_edit_btn: ttk.Button
        self.keymap_delete_btn: ttk.Button
        self.keymap_select_btn: ttk.Button
        self.topmost_chk: ttk.Checkbutton
        self.compact_btn: ttk.Button
        self.suppress_chk: ttk.Checkbutton
        self.run_to_end_chk: ttk.Checkbutton
        self.keyboard_layout_combo: ttk.Combobox
        self.compact_keyboard_layout_combo: ttk.Combobox
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
        self.status_bar = ttk.Frame(self, style="Statusbar.TFrame")
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_columnconfigure(1, weight=1)
        self.status_bar.grid_columnconfigure(2, weight=1)
        ttk.Label(
            self.status_bar,
            textvariable=self.file_status_var,
            style="Statusbar.TLabel",
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.status_bar,
            textvariable=self.flash_message_var,
            style="Statusbar.TLabel",
            anchor="center",
            justify="center",
        ).grid(row=0, column=1, sticky="ew")
        ttk.Label(self.status_bar, text="", style="Statusbar.TLabel", anchor="e").grid(row=0, column=2, sticky="e")

        self._update_file_status()

    def _update_file_status(self):
        name = os.path.basename(self.keymap_set_path or "") or "(未設定)"
        save_state = "未保存" if self.dirty_tracker.has_unsaved_changes() else "保存済み"
        self.file_status_var.set(f"ファイル: {name} / {save_state}")


    def mark_keymap_dirty(self, keymap: dict | None = None) -> None:
        target = keymap if keymap is not None else self.keymap_service.get_active_keymap(self.data)
        self.dirty_tracker.mark_keymap_dirty(target)


    def mark_sequence_dirty(self, trigger: dict | None = None) -> None:
        target = trigger if isinstance(trigger, dict) else self._selected_trigger()
        self.dirty_tracker.mark_sequence_dirty(target)


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

    def set_ui_font_delta(self, delta: int):
        new_delta = self._coerce_font_delta(delta)
        if new_delta == int(getattr(self, "_ui_font_delta_pt", 0)):
            return

        self._ui_font_delta_pt = new_delta
        if hasattr(self, "ui_font_delta_var"):
            self.ui_font_delta_var.set(int(new_delta))
        apply_global_theme(self, font_delta_pt=new_delta)
        self.config_io.write_startup({"ui_font_delta_pt": new_delta})

        if hasattr(self, "menubar"):
            self._build_menu()

        if new_delta == 0:
            self._set_flash_message("フォントサイズを標準にしました。")
        else:
            self._set_flash_message(f"フォントサイズを {new_delta:+d} にしました。")


    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="新規作成", command=self.config_io.new_config, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="保存", command=self.config_io.save_keymap_set, accelerator="Ctrl+S")
        file_menu.add_command(label="別名で保存…", command=self.config_io.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="読込（構成セット）…", command=self.config_io.load_keymap_set_from, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Import...", command=self.config_io.import_config)
        file_menu.add_command(label="Export...", command=self.config_io.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="起動時に読む構成セットを指定…", command=self.config_io.set_startup_keymap_set)
        file_menu.add_command(label="例を復元", command=self.config_io.restore_default)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_close)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=False)
        settings_menu.add_command(label="プリセット編集…", command=self.open_preset_manager, accelerator="Ctrl+Alt+P")
        settings_menu.add_command(label="キーボードUIを開く", command=self.layout.open_keyboard_window)
        settings_menu.add_separator()
        settings_menu.add_command(label="外部レイアウトを追加…", command=self.layout.add_external_keyboard_layout)
        settings_menu.add_command(label="レイアウトを削除…", command=self.layout.delete_keyboard_layout)
        settings_menu.add_separator()
        settings_menu.add_checkbutton(
            label="物理キー名を表示",
            variable=self.keyboard_show_physical_key_labels_var,
            command=self.layout.toggle_keyboard_show_physical_key_labels,
        )
        settings_menu.add_separator()

        font_menu = tk.Menu(settings_menu, tearoff=False)
        for delta in (-3, -2, -1, 0, 1, 2, 3):
            label = "標準 (0)" if delta == 0 else f"{delta:+d}"
            font_menu.add_radiobutton(
                label=label,
                value=delta,
                variable=self.ui_font_delta_var,
                command=lambda d=delta: self.set_ui_font_delta(d),
            )
        settings_menu.add_cascade(label="フォントサイズ", menu=font_menu)

        menubar.add_cascade(label="設定", menu=settings_menu)

        self.config(menu=menubar)
        self.menubar = menubar

    def _bind_menu_shortcuts(self):
        self.bind("<Control-n>", self._on_shortcut_new, add="+")
        self.bind("<Control-N>", self._on_shortcut_new, add="+")
        self.bind("<Control-s>", self._on_shortcut_save, add="+")
        self.bind("<Control-S>", self._on_shortcut_save, add="+")
        self.bind("<Control-o>", self._on_shortcut_load, add="+")
        self.bind("<Control-O>", self._on_shortcut_load, add="+")
        self.bind("<Control-Shift-s>", self._on_shortcut_save_as, add="+")
        self.bind("<Control-Shift-S>", self._on_shortcut_save_as, add="+")
        self.bind("<Control-Alt-p>", self._on_shortcut_open_preset_manager, add="+")
        self.bind("<Control-Alt-P>", self._on_shortcut_open_preset_manager, add="+")

    def _is_menu_shortcut_enabled(self) -> bool:
        if self.stop_key_capture.capturing or self.toggle_key_capture.capturing:
            return False
        try:
            return self.focus_displayof() is not None
        except Exception:
            return False

    def _on_shortcut_save(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.config_io.save_keymap_set()
        return "break"

    def _on_shortcut_new(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.config_io.new_config()
        return "break"

    def _on_shortcut_save_as(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.config_io.save_as()
        return "break"

    def _on_shortcut_load(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.config_io.load_keymap_set_from()
        return "break"

    def _on_shortcut_open_preset_manager(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.open_preset_manager()
        return "break"


    def show_compact_view(self):
        if self.stop_key_capture.capturing or self.toggle_key_capture.capturing:
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
        return self.trigger_panel.sync_trigger_selection_to_views()
    def _set_selected_trigger_index(self, idx: int):
        return self.trigger_panel.set_selected_trigger_index(idx)
    def _focused_listbox_index(self, listbox: tk.Listbox, item_count: int) -> int | None:
        return focused_listbox_index(self, listbox, item_count)

    def _sync_listbox_selection_to_focus(self, listbox: tk.Listbox, item_count: int) -> int | None:
        return sync_listbox_selection_to_focus(self, listbox, item_count)

    def _find_trigger_by_key(self, key: str):
        return self.trigger_service.find_trigger_by_key(self.data, key)

    def _find_keymap_target(self, key: str) -> str:
        return self.keymap_service.find_mapping_target(self.data, key)

    def _find_keymap_switch_target_id(self, key: str) -> str:
        return self.keymap_service.get_keymap_by_switch_key(self.data, key)

    def _selected_keymap_list_index(self) -> int | None:
        return self.keymap_panel.selected_keymap_list_index()

    def _refresh_keymap_list_ui(self, preferred_index: int | None = None) -> None:
        return self.keymap_panel.refresh_keymap_list_ui(preferred_index=preferred_index)

    def _on_keymap_list_select(self, _event=None) -> None:
        return self.keymap_panel.on_keymap_list_select(_event)

    def _on_keymap_list_focus_index_change(self, _event=None) -> None:
        return self.keymap_panel.on_keymap_list_focus_index_change(_event)

    def _on_keymap_list_double_click(self, _event=None) -> None:
        return self.keymap_panel.on_keymap_list_double_click(_event)

    def _add_keymap(self) -> None:
        return self.keymap_panel.add_keymap()

    def _delete_keymap(self) -> None:
        return self.keymap_panel.delete_keymap()

    def _select_keymap(self) -> None:
        return self.keymap_panel.select_keymap()

    def _edit_selected_keymap(self) -> None:
        return self.keymap_panel.edit_selected_keymap()

    def activate_keymap_by_id(
        self,
        keymap_id: str,
        *,
        preferred_index: int | None = None,
        mark_dirty: bool = False,
        show_flash: bool = True,
    ) -> bool:
        return self.keymap_panel.activate_keymap_by_id(
            keymap_id,
            preferred_index=preferred_index,
            mark_dirty=mark_dirty,
            show_flash=show_flash,
        )


    def _get_active_keymap_text(self) -> str:
        return self.keymap_panel.get_active_keymap_text()

    def assign_keymap_from_keyboard_ui(self, source_key: str, target_key: str) -> bool:
        return self.keymap_panel.assign_keymap_from_keyboard_ui(source_key, target_key)

    def clear_keymap_from_keyboard_ui(self, source_key: str) -> bool:
        return self.keymap_panel.clear_keymap_from_keyboard_ui(source_key)

    def _select_trigger_by_key(self, key: str):
        return self.trigger_panel.select_trigger_by_key(key)
    def _apply_always_on_top(self):
        """チェック状態に応じてウィンドウを常に手前にする"""
        try:
            self.attributes("-topmost", bool(self.always_on_top_var.get()))
        except Exception:
            # 失敗してもアプリは止めない
            pass

    # ---------------- Startup config ----------------
    def _coerce_font_delta(self, value: any) -> int:
        try:
            v = int(value)
        except Exception:
            v = 0
        if v < -3:
            v = -3
        if v > 3:
            v = 3
        return v


    def suggest_keymap_set_dialog_path(self) -> str:
        return self.paths.suggest_keymap_set_dialog_path(str(getattr(self, "keymap_set_path", "") or ""))

    def suggest_keymap_set_dialog_dir(self) -> str:
        return self.paths.suggest_keymap_set_dialog_dir(str(getattr(self, "keymap_set_path", "") or ""))


    def _load_startup_settings(self) -> dict[str, any]:
        startup = {}
        try:
            startup = self.config_service.load_startup(self.startup_path)
        except Exception as e:
            startup = {}
            messagebox.showwarning(
                "startup.json 読込失敗",
                f"startup.json の読込に失敗しました。\n{e}\n\n既定設定で起動します。",
            )

        if not isinstance(startup, dict):
            startup = {}

        startup["ui_font_delta_pt"] = self._coerce_font_delta(startup.get("ui_font_delta_pt", 0))
        startup["prompt_if_missing"] = bool(startup.get("prompt_if_missing", True))
        return startup


    def _update_status(self):
        return self.trigger_panel.update_status()
    def _refresh_triggers(self):
        return self.trigger_panel.refresh_triggers()
    def _refresh_actions(self):
        return self.trigger_panel.refresh_actions()
    def _on_action_list_select(self, _event=None):
        return self.trigger_panel.on_action_list_select(_event)
    def _on_action_list_focus_index_change(self, _event=None):
        return self.trigger_panel.on_action_list_focus_index_change(_event)
    def _on_trigger_list_focus_index_change(self, event=None):
        return self.trigger_panel.on_trigger_list_focus_index_change(event)
    def _on_trigger_double_click(self, _event=None):
        return self.trigger_panel.on_trigger_double_click(_event)
    def _on_action_double_click(self, _event=None):
        return self.trigger_panel.on_action_double_click(_event)

    def keymap_set_file_stem(self) -> str:
        return self.paths.keymap_set_file_stem(str(getattr(self, "keymap_set_path", "") or ""))

    def _sync_control_vars_from_data(self) -> None:
        """data の内容を制御キー表示・レイアウト選択などの共有 Var へ反映する。"""
        if hasattr(self, "stop_key_var"):
            self.stop_key_var.set(str(self.data.get("hook_stop_key", "")))
        if hasattr(self, "toggle_key_var"):
            self.toggle_key_var.set(str(self.data.get("hook_toggle_key", "")))
        if hasattr(self, "keyboard_show_physical_key_labels_var"):
            self.keyboard_show_physical_key_labels_var.set(
                bool(self.data.get("keyboard_show_physical_key_labels", False))
            )
        self.layout.sync_keyboard_layout_controls()

    def open_preset_manager(self):
        before = copy.deepcopy(self.data.get("hotkey_presets", []))
        PresetManagerDialog(self, title="ホットキープリセット編集").wait_window()
        after = self.data.get("hotkey_presets", [])
        if before != after:
            self.dirty_tracker.set_dirty(True)
            self._set_flash_message("プリセットを更新しました。")


    # ---------------- Trigger selection/helpers ----------------
    def _selected_trigger(self):
        return self.trigger_panel.selected_trigger()
    # ---------------- run_to_end UI sync/update ----------------
    def update_run_to_end_delay(self, _event=None):
        return self.trigger_panel.update_run_to_end_delay(_event)
    def update_suppress(self):
        return self.trigger_panel.update_suppress()
    def update_run_to_end(self):
        return self.trigger_panel.update_run_to_end()
    # ---------------- Trigger CRUD ----------------
    def add_trigger(self):
        return self.trigger_panel.add_trigger()
    def rename_trigger(self):
        return self.trigger_panel.rename_trigger()
    def delete_trigger(self):
        return self.trigger_panel.delete_trigger()
    # ---------------- Actions CRUD (selected trigger) ----------------
    def add_action(self):
        return self.trigger_panel.add_action()
    def edit_action(self):
        return self.trigger_panel.edit_action()
    def delete_action(self):
        return self.trigger_panel.delete_action()
    def move_action(self, delta: int):
        return self.trigger_panel.move_action(delta)
    def _perform_action(self, action: dict):
        self.action_executor.execute(action)
            
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

    # ---------------- Control key capture logic (相互排他の調整役。App に残す) ----------------
    def toggle_stop_key_capture(self):
        if self.stop_key_capture.capturing:
            self.stop_key_capture.stop(cancel=True)
        else:
            self.start_stop_key_capture()

    def start_stop_key_capture(self):
        self.toggle_key_capture.stop(cancel=True)
        self.stop_key_capture.start()

    def toggle_toggle_key_capture(self):
        if self.toggle_key_capture.capturing:
            self.toggle_key_capture.stop(cancel=True)
        else:
            self.start_toggle_key_capture()

    def start_toggle_key_capture(self):
        self.stop_key_capture.stop(cancel=True)
        self.toggle_key_capture.start()

    # ---------------- Close ----------------
    def on_close(self):
        if not self.config_io.confirm_save_if_dirty("終了"):
            return
        try:
            if self.layout.keyboard_window is not None:
                try:
                    if self.layout.keyboard_window.winfo_exists():
                        self.layout.keyboard_window.destroy()
                except Exception:
                    pass
            self.hook.stop_hook()
        finally:
            self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()


