from __future__ import annotations

from tkinter import messagebox

from keyseq.domain.config import normalize_key_name


class HookController:
    """フック開始/停止・サスペンドカウンタ・入力イベント入口という安全機構の中枢。"""

    def __init__(self, app) -> None:
        self._app = app
        self.hook_active = False
        self.custom_input_enabled = True
        self.hook_suspend_count = 0
        self.hook_was_active_before_dialog = False
        self.error_dialog_open = False
        self._hook_button_pairs = []

    def register_hook_buttons(self, hook_btn, trigger_btn) -> None:
        self._hook_button_pairs.append((hook_btn, trigger_btn))

    # ---------------- Hook suspend/resume for modal dialogs ----------------
    def suspend_hook_for_dialog(self):
        """編集系ダイアログ表示中の誤爆を防ぐため、フックを一時停止（ネスト対応）"""
        self.hook_suspend_count += 1
        if self.hook_suspend_count == 1:
            self.hook_was_active_before_dialog = bool(self.hook_active)
            if self.hook_was_active_before_dialog:
                self.stop_hook(reset_custom_input_mode=False)

    def resume_hook_after_dialog(self):
        """一時停止したフックを元に戻す（ネスト対応。最後のダイアログが閉じた時だけ復帰）"""
        if self.hook_suspend_count <= 0:
            self.hook_suspend_count = 0
            return
        self.hook_suspend_count -= 1
        if self.hook_suspend_count == 0:
            was_on = self.hook_was_active_before_dialog
            self.hook_was_active_before_dialog = False
            if was_on:
                self.start_hook()

    def get_hook_pause_count(self) -> int:
        return int(self.hook_suspend_count)

    # ---------------- Hook toggle button sync ----------------
    def sync_hook_toggle_buttons(self):
        text = "停止（フックOFF）" if self.hook_active else "開始（フックON）"
        for hook_btn, _trigger_btn in self._hook_button_pairs:
            try:
                hook_btn.configure(text=text, state="normal")
            except Exception:
                pass

    def sync_trigger_toggle_buttons(self):
        if not self.hook_active:
            text = "通常トリガー無効化"
            state = "disabled"
        elif self.custom_input_enabled:
            text = "通常トリガー無効化"
            state = "normal"
        else:
            text = "通常トリガー有効化"
            state = "normal"

        for _hook_btn, trigger_btn in self._hook_button_pairs:
            try:
                trigger_btn.configure(text=text, state=state)
            except Exception:
                pass

    # ---------------- Hook logic ----------------
    def start_hook(self):
        desired_custom_input_state = bool(self.custom_input_enabled)
        if self.hook_active:
            self.stop_hook(reset_custom_input_mode=False)

        if not self.validate_hook_configuration():
            self.sync_hook_toggle_buttons()
            self.sync_trigger_toggle_buttons()
            return

        def _on_error(title: str, msg: str) -> None:
            self._app.after(0, lambda: messagebox.showerror(title, msg))

        self._app.key_state_manager.clear()
        started = self._app.hook_coordinator.start(
            triggers=self._app.data.get("triggers", []),
            on_input_event=self.on_input_event,
            on_error=_on_error,
            has_keymaps=self._app.keymap_service.has_any_mapping(self._app.data),
        )

        if not started:
            self.sync_hook_toggle_buttons()
            self.sync_trigger_toggle_buttons()
            return

        self.hook_active = True
        self.custom_input_enabled = desired_custom_input_state
        self.sync_hook_toggle_buttons()
        self.sync_trigger_toggle_buttons()
        self._app.layout.refresh_keyboard_window()
        self._app.trigger_panel.update_status()

    def stop_hook(self, *, reset_custom_input_mode: bool = True):
        self._app.sequence_runner.stop_run_to_end()
        self._app.hook_coordinator.stop()
        self._app.key_state_manager.clear()
        self.hook_active = False
        if reset_custom_input_mode:
            self.custom_input_enabled = True

        self.sync_hook_toggle_buttons()
        self.sync_trigger_toggle_buttons()
        self._app.layout.refresh_keyboard_window()
        self._app.trigger_panel.update_status()

    def toggle_hook(self):
        if self.hook_active:
            self.stop_hook()
        else:
            self.start_hook()

    def toggle_custom_input_enabled(self):
        if not self.hook_active:
            return

        if self.custom_input_enabled:
            # 無効化した瞬間に連続実行中を止める
            self._app.sequence_runner.stop_run_to_end()
            self.custom_input_enabled = False
        else:
            def _on_error(title: str, msg: str) -> None:
                self._app.after(0, lambda: messagebox.showerror(title, msg))

            enabled = self._app.hook_coordinator.can_enable_custom_input(
                triggers=self._app.data.get("triggers", []),
                on_error=_on_error,
                has_keymaps=self._app.keymap_service.has_any_mapping(self._app.data),
            )
            if not enabled:
                self.sync_trigger_toggle_buttons()
                self._app.trigger_panel.update_status()
                return
            self.custom_input_enabled = True

        if not getattr(self._app, "_compact_mode", False):
            self._app.trigger_panel.refresh_actions()
        self.sync_trigger_toggle_buttons()
        self._app.layout.refresh_keyboard_window()
        self._app.trigger_panel.update_status()

    def toggle_triggers_enabled(self):
        self.toggle_custom_input_enabled()

    def validate_hook_configuration(self) -> bool:
        control_keys = {
            "停止キー": normalize_key_name(self._app.data.get("hook_stop_key", "")),
            "有効/無効トグルキー": normalize_key_name(self._app.data.get("hook_toggle_key", "")),
        }
        seen_control_keys: dict[str, str] = {}
        for label, key in control_keys.items():
            if not key:
                continue
            if key in seen_control_keys:
                messagebox.showerror("開始できません", f"{seen_control_keys[key]}と{label}が重複しています:\n{key}")
                return False
            seen_control_keys[key] = label

        keymap_source_keys = self._app.keymap_service.collect_source_keys(self._app.data)
        trigger_keys = {
            normalize_key_name(t.get("key", ""))
            for t in self._app.data.get("triggers", [])
            if normalize_key_name(t.get("key", ""))
        }

        for label, key in control_keys.items():
            if not key:
                continue
            if key in trigger_keys:
                messagebox.showerror("開始できません", f"{label}が通常トリガーと重複しています:\n{key}")
                return False
            if key in keymap_source_keys:
                messagebox.showerror("開始できません", f"{label}がキーマップ元キーと重複しています:\n{key}")
                return False

        return True

    def on_input_event(self, event: object):
        resolved_key = self._app.layout.resolve_key_name_from_scan_code(getattr(event, "scan_code", None))
        if self._app.layout.should_debug_special_key_event(event, resolved_key):
            self._app.layout.debug_special_key_event(event, resolved_key)
        route = self._app.input_router.handle(event)
        for action in route.actions:
            self._app.after(0, lambda aa=action: self._app.action_executor.execute_router_action(aa))
        return route.accept

    def show_action_error(self, trigger_key: str, action: dict, err: Exception):
        """送信エラーをUIスレッドで表示（多重表示は抑止）"""
        if self.error_dialog_open:
            return
        self.error_dialog_open = True
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
            self.error_dialog_open = False
