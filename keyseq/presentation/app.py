import os
import copy
import tkinter as tk
from typing import Callable
from tkinter import messagebox, ttk

from keyseq.presentation.dialogs import (
    PresetManagerDialog,
)
from keyseq.presentation.controllers.config_io import (
    HotkeyPresetsIo,
    IoDialogs,
    KeymapFileIo,
    KeymapSetIo,
    SequenceFileIo,
    StartupIo,
    TriggerSetFileIo,
)
from keyseq.presentation.controllers.config_io.child_save_dialog import ChildSaveDialog
from keyseq.presentation.controllers.config_io.reference_cleanup_io import ReferenceCleanupIo
from keyseq.presentation.controllers.config_io.orphan_sweep_io import OrphanSweepIo
from keyseq.presentation.controllers.config_io.keymap_set_history_io import KeymapSetHistoryIo
from keyseq.presentation.controllers.config_io.quarantine_manage_io import QuarantineManageIo
from keyseq.presentation.config_paths import ConfigPaths
from keyseq.presentation.controllers.dirty_state import DirtyStateTracker
from keyseq.presentation.controllers.hook_controller import HookController
from keyseq.presentation.controllers.key_capture import SingleKeyCaptureController
from keyseq.presentation.controllers.keymap_panel_controller import KeymapPanelController
from keyseq.presentation.controllers.layout_controller import LayoutController
from keyseq.presentation.controllers.pane_layout import PaneLayoutController
from keyseq.presentation.controllers.trigger_panel_controller import TriggerPanelController
from keyseq.presentation.pane_width_rules import (
    DEFAULT_WINDOW_WIDTH, WINDOW_WIDTH_KEY, parse_saved_window_width,
)
from keyseq.presentation.ui_vars import UiVars
from keyseq.presentation.views.compact_view.compact_view import CompactView
from keyseq.presentation.views.full_view.full_view import FullView
from keyseq.presentation.views.menu_bar import build_menu_bar, bind_menu_shortcuts
from keyseq.presentation.views.status_bar import build_status_area
from keyseq.presentation.startup_settings import load_startup_settings
from keyseq.presentation.theme import apply_global_theme, coerce_font_delta
from keyseq.presentation.modal import install_minimize_grab_custody


from keyseq.application.action_executor import ActionExecutor
from keyseq.application.config_service import ConfigService
from keyseq.application.app_state import AppState
from keyseq.application.hotkey_service import HotkeyService
from keyseq.application.hook_coordinator import HookCoordinator
from keyseq.application.input_router import InputRouter
from keyseq.application.keymap_service import KeymapService
from keyseq.application.key_state_manager import KeyStateManager
from keyseq.application.sequence_runner import SequenceRunner
from keyseq.application.trigger_service import TriggerService
from keyseq.domain.config import HOOK_KEY_FIELDS, HOOK_STOP_KEY, HOOK_TOGGLE_KEY, safe_deepcopy
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
        self.config_service.ensure_split_config_dirs(self.config_root)
        self.paths = ConfigPaths(
            base_dir=self.base_dir,
            config_root=self.config_root,
            user_root=self.user_root,
            config_service=self.config_service,
        )
        self.startup_path = self.paths.resolve_startup_path()
        self.keymap_set_path = self.paths.resolve_keymap_set_path()
        self._startup_settings = load_startup_settings(
            self.config_service,
            self.startup_path,
            on_read_error=lambda exc: messagebox.showwarning(
                "startup.json 読込失敗",
                f"startup.json の読込に失敗しました。\n{exc}\n\n既定設定で起動します。",
            ),
        )
        self._ui_font_delta_pt = coerce_font_delta(self._startup_settings.get("ui_font_delta_pt", 0))
        apply_global_theme(self, font_delta_pt=self._ui_font_delta_pt)
        self.data = self.config_service.new_default_data()
        self.config_service.apply_global_defaults(self.data, config_root=self.config_root)
        self.ui_vars = UiVars(self, ui_font_delta_pt=self._ui_font_delta_pt)
        self._retained_hook_keys: dict[str, str] | None = None

        self.title("Key Replacer Sequencer (Multi Trigger)")
        width = parse_saved_window_width(
            self._startup_settings.get(WINDOW_WIDTH_KEY), self.winfo_screenwidth(),
        )
        self.geometry(f"{DEFAULT_WINDOW_WIDTH if width is None else width}x820")

        self.trigger_service = TriggerService()
        self.keymap_service = KeymapService()
        self.input_gateway = InputGateway()
        self.hotkey_service = HotkeyService(validate_key_name=self.input_gateway.validate_key_name)
        self.key_state_manager = KeyStateManager(resolve_scan_code=lambda sc: self.layout.resolve_key_name_from_scan_code(sc))
        self.action_executor = ActionExecutor(
            input_gateway=self.input_gateway,
            validate_hotkey=self.hotkey_service.validate,
            on_action_error=lambda action, err: self.hook.show_action_error("", action, err),
            on_runtime_error=lambda title, msg: messagebox.showerror(title, msg),
            on_stop_hook=lambda: self.hook.stop_hook(),
            on_toggle_mode=lambda: self.hook.toggle_custom_input_enabled(),
            on_select_keymap=lambda keymap_id: self.keymap_panel.activate_keymap_by_id(keymap_id, mark_dirty=False, show_flash=True),
            on_trigger=lambda key: self.sequence_runner.handle_key(key),
        )
        self.input_router = InputRouter(
            key_state_manager=self.key_state_manager,
            get_send_guard_count=self._get_send_guard_count,
            get_hook_pause_count=lambda: self.hook.get_hook_pause_count(),
            get_stop_key=lambda: self.data.get(HOOK_STOP_KEY, ""),
            get_toggle_key=lambda: self.data.get(HOOK_TOGGLE_KEY, ""),
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
            data_key=HOOK_STOP_KEY,
            var=self.ui_vars.stop_key_var,
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
            data_key=HOOK_TOGGLE_KEY,
            var=self.ui_vars.toggle_key_var,
            label="トグルキー",
            single_key_example="f11",
            conflict_checks=[
                (lambda app, key: app.trigger_service.key_exists(app.data, key), "トリガー一覧"),
                (lambda app, key: app.trigger_service.is_stop_key_conflict(app.data, key), "停止キー"),
                (lambda app, key: bool(app.keymap_service.get_keymap_by_switch_key(app.data, key)), "キーマップ直接切替キー"),
                (lambda app, key: app.keymap_service.source_key_exists(app.data, key), "キーマップ元キー"),
            ],
        )
        self.keymap_set_io = KeymapSetIo(self)
        self.keymap_set_history_io = KeymapSetHistoryIo(self)
        self.startup_io = StartupIo(self)
        self.hotkey_presets_io = HotkeyPresetsIo(self)
        self.io_dialogs = IoDialogs(self)
        self.child_save_dialog = ChildSaveDialog(self)
        self.keymap_io = KeymapFileIo(self)
        self.trigger_set_io = TriggerSetFileIo(self)
        self.sequence_io = SequenceFileIo(self)
        self.reference_cleanup_io = ReferenceCleanupIo(self)
        self.orphan_sweep_io = OrphanSweepIo(self)
        self.quarantine_manage_io = QuarantineManageIo(self)
        self.layout = LayoutController(self)
        self.pane_layout = PaneLayoutController(self)
        self.keymap_panel = KeymapPanelController(self)
        self.trigger_panel = TriggerPanelController(self)
        self.hook = HookController(self)

        self.hook_coordinator = HookCoordinator(self.input_gateway)
        self.sequence_runner = SequenceRunner(
            state=self.state,
            find_trigger=self._find_trigger_by_key,
            perform_action=self._perform_action,
            select_trigger=lambda key: self.trigger_panel.select_trigger_by_key(key),
            refresh_actions=lambda: self.trigger_panel.refresh_actions(),
            update_status=lambda: self.trigger_panel.update_status(),
            after=self.after,
            after_cancel=self.after_cancel,
        )

        self._compact_mode = False
        self._full_geometry = None  # 省略表示へ入る前の geometry を記憶
        self._selected_trigger_idx = 0  # Full/Compact で選択を共有する

        self._programmatic_action_select = False  # action_list選択をコード側で変更中か
        self._flash_after_id = None
        self._build_ui()
        self.pane_layout.install()
        self.startup_io.load_startup_and_config()
        self.layout.reload_keyboard_layouts()
        self.trigger_panel.refresh_triggers()
        self.trigger_panel.refresh_actions()
        self.trigger_panel.update_status()
        self.hook.sync_hook_toggle_buttons()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        install_minimize_grab_custody(self)
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

        # 2画面（フル/省略）を用意し、pack_forgetで切替
        self.full_view = FullView(self.outer, app=self)
        self.compact_view = CompactView(self.outer, app=self)

        self.full_view.pack(fill="both", expand=True)
        # compact_view は最初は非表示
        build_menu_bar(self)
        bind_menu_shortcuts(self)
        build_status_area(self, self)

    def _update_file_status(self):
        name = os.path.basename(self.keymap_set_path or "") or "(未設定)"
        save_state = "未保存" if self.dirty_tracker.has_unsaved_changes() else "保存済み"
        self.ui_vars.file_status_var.set(f"ファイル: {name} / {save_state}")


    def mark_keymap_dirty(self, keymap: dict | None = None) -> None:
        target = keymap if keymap is not None else self.keymap_service.get_active_keymap(self.data)
        self.dirty_tracker.mark_keymap_dirty(target)


    def mark_sequence_dirty(self, trigger: dict | None = None) -> None:
        target = trigger if isinstance(trigger, dict) else self.trigger_panel.selected_trigger()
        self.dirty_tracker.mark_sequence_dirty(target)


    def _clear_flash_message(self):
        self._flash_after_id = None
        self.ui_vars.flash_message_var.set("")

    def _set_flash_message(self, msg: str, *, auto_clear: bool = True):
        try:
            if self._flash_after_id:
                self.after_cancel(self._flash_after_id)
                self._flash_after_id = None
        except Exception:
            self._flash_after_id = None
        self.ui_vars.flash_message_var.set(str(msg or ""))
        if auto_clear and msg:
            self._flash_after_id = self.after(4000, self._clear_flash_message)

    def _apply_fixed_button_widths(self) -> None:
        self.hook.apply_fixed_button_widths()
        self.stop_key_capture.apply_fixed_button_width()
        self.toggle_key_capture.apply_fixed_button_width()

    def _apply_font_delta(self, delta: int) -> bool:
        new_delta = coerce_font_delta(delta)
        if new_delta == int(getattr(self, "_ui_font_delta_pt", 0)):
            return False

        self._ui_font_delta_pt = new_delta
        self.ui_vars.ui_font_delta_var.set(int(new_delta))
        apply_global_theme(self, font_delta_pt=new_delta)
        self._apply_fixed_button_widths()
        self.pane_layout.on_font_changed()
        self.startup_io.write_startup({"ui_font_delta_pt": new_delta})
        return True

    def set_ui_font_delta(self, delta: int):
        if not self._apply_font_delta(delta):
            return
        if hasattr(self, "menubar"):
            build_menu_bar(self)

        new_delta = self._ui_font_delta_pt
        if new_delta == 0:
            self._set_flash_message("フォントサイズを標準にしました。")
        else:
            self._set_flash_message(f"フォントサイズを {new_delta:+d} にしました。")


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
        self.keymap_set_io.save_keymap_set()
        return "break"

    def _on_shortcut_new(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.keymap_set_io.new_config()
        return "break"

    def _on_shortcut_save_as(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.keymap_set_io.save_as()
        return "break"

    def _on_shortcut_load(self, _event=None):
        if not self._is_menu_shortcut_enabled():
            return "break"
        self.keymap_set_io.load_keymap_set_from()
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
        self.pane_layout.release_window_min_size()
        self._apply_compact_geometry()
        self.trigger_panel.sync_trigger_selection_to_views()
        self.trigger_panel.update_status()

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
        self.trigger_panel.sync_trigger_selection_to_views()
        self.trigger_panel.refresh_actions()  # full側のシーケンス表示を復帰
        self.trigger_panel.update_status()
        self.pane_layout.on_full_view_shown()

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

    def _find_trigger_by_key(self, key: str):
        return self.trigger_service.find_trigger_by_key(self.data, key)

    def _find_keymap_target(self, key: str) -> str:
        return self.keymap_service.find_mapping_target(self.data, key)

    def _find_keymap_switch_target_id(self, key: str) -> str:
        return self.keymap_service.get_keymap_by_switch_key(self.data, key)

    def _apply_always_on_top(self):
        """チェック状態に応じてウィンドウを常に手前にする"""
        try:
            self.attributes("-topmost", bool(self.ui_vars.always_on_top_var.get()))
        except Exception:
            # 失敗してもアプリは止めない
            pass

    # ---------------- Startup config ----------------
    def suggest_keymap_set_dialog_path(self) -> str:
        return self.paths.suggest_keymap_set_dialog_path(str(getattr(self, "keymap_set_path", "") or ""))

    def suggest_keymap_set_dialog_dir(self) -> str:
        return self.paths.suggest_keymap_set_dialog_dir(str(getattr(self, "keymap_set_path", "") or ""))


    def keymap_set_file_stem(self) -> str:
        return self.paths.keymap_set_file_stem(str(getattr(self, "keymap_set_path", "") or ""))

    def _sync_control_vars_from_data(self) -> None:
        """data の内容を制御キー表示・レイアウト選択などの共有 Var へ反映する。"""
        self.ui_vars.stop_key_var.set(str(self.data.get(HOOK_STOP_KEY, "")))
        self.ui_vars.toggle_key_var.set(str(self.data.get(HOOK_TOGGLE_KEY, "")))
        self.ui_vars.hook_keys_individual_var.set(bool(self.data.get("hook_keys_individual", False)))
        self.ui_vars.keyboard_show_physical_key_labels_var.set(
            bool(self.data.get("keyboard_show_physical_key_labels", False))
        )
        self.layout.sync_keyboard_layout_controls()

    def open_preset_manager(self):
        before = copy.deepcopy(self.data.get("hotkey_presets", []))
        PresetManagerDialog(self, title="ホットキープリセット編集").wait_window()
        after = self.data.get("hotkey_presets", [])
        if before != after:
            self._set_flash_message("プリセットを更新しました。")

    def save_hotkey_presets(
        self,
        presets: list,
        *,
        individual: bool | None = None,
        loaded_presets: list | None = None,
        on_overwrite_conflict: Callable[[str, list | None], str] | None = None,
    ) -> bool:
        current_individual = self.data.get("hotkey_presets_individual") is True
        target_individual = current_individual if individual is None else individual

        stored_path = self.config_service.resolve_hotkey_presets_save_path(
            self.data,
            config_root=self.config_root,
            keymap_set_path=self.keymap_set_path,
            individual=target_individual,
        )
        if target_individual:
            rejection_reason = self.config_service.individual_hotkey_presets_save_rejection_reason(
                stored_path,
                config_root=self.config_root,
            )
            if rejection_reason:
                self.hotkey_presets_io.show_save_path_rejection(
                    rejection_reason,
                    stored_path=stored_path,
                )
                return False
            overwrite = self.config_service.describe_individual_hotkey_presets_overwrite(
                stored_path,
                loaded_presets,
                config_root=self.config_root,
            )
            if overwrite["conflict"] and on_overwrite_conflict is not None:
                choice = on_overwrite_conflict(stored_path, overwrite["existing"])
                if choice != "overwrite":
                    return False
        previous_path = self.data.get("hotkey_presets_path")
        if not self.hotkey_presets_io.write_presets(presets, stored_path=stored_path):
            return False
        self.data["hotkey_presets"] = safe_deepcopy(presets)
        if stored_path:
            self.data["hotkey_presets_path"] = stored_path
            if previous_path != stored_path:
                self.dirty_tracker.set_dirty(True)
        if individual is not None and target_individual != current_individual:
            self.data["hotkey_presets_individual"] = target_individual
            self.dirty_tracker.set_dirty(True)
        return True

    def _perform_action(self, action: dict) -> bool:
        return self.action_executor.execute(action)
            
    def validate_hotkey(self, hotkey: str) -> tuple[str, str]:
        """
        hotkey を検証し、(エラーメッセージ, 正規化したhotkey) を返す。
        エラーなしならエラーメッセージは ""。
        """
        return self.hotkey_service.validate(hotkey)

    # ---------------- Control key capture logic (相互排他の調整役。App に残す) ----------------
    def toggle_hook_keys_individual(self):
        individual = bool(self.ui_vars.hook_keys_individual_var.get())
        if individual:
            retained = self._retained_hook_keys or {}
            for field in HOOK_KEY_FIELDS:
                self.data[field] = str(retained.get(field, ""))
            self._retained_hook_keys = None
        else:
            self._retained_hook_keys = {
                field: str(self.data.get(field, ""))
                for field in HOOK_KEY_FIELDS
            }
        self.data["hook_keys_individual"] = individual
        if not individual:
            self.config_service.apply_global_hook_key_defaults(self.data, config_root=self.config_root)
        self._sync_control_vars_from_data()
        self.dirty_tracker.set_dirty(True)

    def discard_retained_hook_keys(self) -> None:
        """保持していた個別値を捨てる（保存後・別データ読込後は復活させない）。"""
        self._retained_hook_keys = None

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
        if not self.keymap_set_io.confirm_save_if_dirty("終了"):
            return
        self.pane_layout.cancel_window_width_save()
        self.hook.begin_shutdown()
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


