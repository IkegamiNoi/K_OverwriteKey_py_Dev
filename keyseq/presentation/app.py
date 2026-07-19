import os
import copy
import tkinter as tk
from tkinter import messagebox, ttk

from keyseq.presentation.dialogs import (
    PresetManagerDialog,
)
from keyseq.presentation.controllers.config_io_controller import ConfigIoController
from keyseq.presentation.config_paths import ConfigPaths
from keyseq.presentation.controllers.dirty_state import DirtyStateTracker
from keyseq.presentation.controllers.hook_controller import HookController
from keyseq.presentation.controllers.key_capture import SingleKeyCaptureController
from keyseq.presentation.controllers.keymap_panel_controller import KeymapPanelController
from keyseq.presentation.controllers.layout_controller import LayoutController
from keyseq.presentation.controllers.trigger_panel_controller import TriggerPanelController
from keyseq.presentation.ui_vars import UiVars
from keyseq.presentation.views.compact_view.compact_view import CompactView
from keyseq.presentation.views.full_view.full_view import FullView
from keyseq.presentation.views.menu_bar import build_menu_bar, bind_menu_shortcuts
from keyseq.presentation.views.status_bar import build_status_area
from keyseq.presentation.startup_settings import load_startup_settings
from keyseq.presentation.theme import apply_global_theme, coerce_font_delta


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
        self.ui_vars = UiVars(self, ui_font_delta_pt=self._ui_font_delta_pt)

        self.title("Key Replacer Sequencer (Multi Trigger)")
        self.geometry("780x820")

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
            data_key="hook_toggle_key",
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
        self.config_io.load_startup_and_config()
        self.layout.reload_keyboard_layouts()
        self.trigger_panel.refresh_triggers()
        self.trigger_panel.refresh_actions()
        self.trigger_panel.update_status()
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

    def _apply_font_delta(self, delta: int) -> bool:
        new_delta = coerce_font_delta(delta)
        if new_delta == int(getattr(self, "_ui_font_delta_pt", 0)):
            return False

        self._ui_font_delta_pt = new_delta
        self.ui_vars.ui_font_delta_var.set(int(new_delta))
        apply_global_theme(self, font_delta_pt=new_delta)
        self.config_io.write_startup({"ui_font_delta_pt": new_delta})
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
        self.ui_vars.stop_key_var.set(str(self.data.get("hook_stop_key", "")))
        self.ui_vars.toggle_key_var.set(str(self.data.get("hook_toggle_key", "")))
        self.ui_vars.keyboard_show_physical_key_labels_var.set(
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

    def _perform_action(self, action: dict):
        self.action_executor.execute(action)
            
    def validate_hotkey(self, hotkey: str) -> tuple[str, str]:
        """
        hotkey を検証し、(エラーメッセージ, 正規化したhotkey) を返す。
        エラーなしならエラーメッセージは ""。
        """
        return self.hotkey_service.validate(hotkey)

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


