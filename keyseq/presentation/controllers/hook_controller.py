from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from keyseq.application.input_router import StopHookAction
from keyseq.application.key_overlap import AssignmentConflict, KeyOverlapAnalysis, analyze_key_overlaps
from keyseq.domain.config import HOOK_STOP_KEY, HOOK_TOGGLE_KEY, normalize_key_name
from keyseq.presentation.controllers.button_width import apply_fixed_button_width
from keyseq.presentation.hook_button_texts import (
    HOOK_START_TEXT, HOOK_STOP_TEXT, HOOK_TOGGLE_TEXTS,
    TRIGGER_DISABLE_TEXT, TRIGGER_ENABLE_TEXT, TRIGGER_TOGGLE_TEXTS,
)


class HookController:
    """フック開始/停止・サスペンドカウンタ・入力イベント入口という安全機構の中枢。"""

    def __init__(self, app) -> None:
        self._app = app
        self.hook_active = False
        self.custom_input_enabled = True
        self.hook_suspend_count = 0
        self.hook_was_active_before_dialog = False
        self.error_dialog_open = False
        self._shutting_down = False
        self._hook_button_pairs = []
        self._fixed_width_button_pairs = []
        self._status_before_shadowed_notice: str | None = None
        self._last_shadowed_status: str | None = None

    def register_hook_buttons(self, hook_btn, trigger_btn, *, fixed_width: bool = False) -> None:
        self._hook_button_pairs.append((hook_btn, trigger_btn))
        if fixed_width:
            self._fixed_width_button_pairs.append((hook_btn, trigger_btn))
            apply_fixed_button_width(hook_btn, HOOK_TOGGLE_TEXTS)
            apply_fixed_button_width(trigger_btn, TRIGGER_TOGGLE_TEXTS)

    def apply_fixed_button_widths(self) -> None:
        for hook_btn, trigger_btn in self._fixed_width_button_pairs:
            apply_fixed_button_width(hook_btn, HOOK_TOGGLE_TEXTS)
            apply_fixed_button_width(trigger_btn, TRIGGER_TOGGLE_TEXTS)

    # ---------------- Hook suspend/resume for modal dialogs ----------------
    def suspend_hook_for_dialog(self, window: tk.Misc | None = None) -> None:
        """フックを一時停止し、window 指定時は破棄後に自動解除する（ネスト対応）。"""
        self.hook_suspend_count += 1
        if self.hook_suspend_count == 1:
            self.hook_was_active_before_dialog = bool(self.hook_active)
            if self.hook_was_active_before_dialog:
                self.stop_hook(reset_custom_input_mode=False)

        if window is not None:
            resume_scheduled = False

            def schedule_resume(event):
                nonlocal resume_scheduled
                if event.widget is not window or resume_scheduled:
                    return
                resume_scheduled = True
                self._app.after(0, self.resume_hook_after_dialog)

            window.bind("<Destroy>", schedule_resume, "+")

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
            elif not self._shutting_down:
                self._app.trigger_panel.refresh_triggers()

    def get_hook_pause_count(self) -> int:
        return int(self.hook_suspend_count)

    # ---------------- Hook toggle button sync ----------------
    def sync_hook_toggle_buttons(self):
        text = HOOK_STOP_TEXT if self.hook_active else HOOK_START_TEXT
        for hook_btn, _trigger_btn in self._hook_button_pairs:
            try:
                hook_btn.configure(text=text, state="normal")
            except Exception:
                pass

    def sync_trigger_toggle_buttons(self):
        if not self.hook_active:
            text = TRIGGER_DISABLE_TEXT
            state = "disabled"
        elif self.custom_input_enabled:
            text = TRIGGER_DISABLE_TEXT
            state = "normal"
        else:
            text = TRIGGER_ENABLE_TEXT
            state = "normal"

        for _hook_btn, trigger_btn in self._hook_button_pairs:
            try:
                trigger_btn.configure(text=text, state=state)
            except Exception:
                pass

    # ---------------- Hook logic ----------------
    def begin_shutdown(self) -> None:
        """終了確定後は、同期・遅延のどちらの解除経路でもフックを再開しない。"""
        self._shutting_down = True

    def start_hook(self):
        if self._shutting_down:
            return
        desired_custom_input_state = bool(self.custom_input_enabled)
        if self.hook_active:
            self.stop_hook(reset_custom_input_mode=False)

        if not self.validate_hook_configuration():
            self.sync_hook_toggle_buttons()
            self.sync_trigger_toggle_buttons()
            return

        overlap = self._key_overlap_report()

        def _on_error(title: str, msg: str) -> None:
            self._app.after(0, lambda: messagebox.showerror(title, msg))

        self._app.key_state_manager.clear()
        started = self._app.hook_coordinator.start(
            triggers=overlap.all_triggers,
            on_input_event=self.on_input_event,
            on_error=_on_error,
            has_keymaps=bool(overlap.all_source_keys),
            has_trigger_keys=bool(overlap.all_trigger_keys),
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

            overlap = self._key_overlap_report()
            enabled = self._app.hook_coordinator.can_enable_custom_input(
                triggers=overlap.all_triggers,
                on_error=_on_error,
                has_keymaps=bool(overlap.all_source_keys),
                has_trigger_keys=bool(overlap.all_trigger_keys),
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
        overlap = self._key_overlap_report()
        if not overlap.stop_toggle_conflict:
            return True
        stop_key = normalize_key_name(self._app.data.get(HOOK_STOP_KEY, ""))
        messagebox.showerror(
            "開始できません",
            f"停止キーと一時停止/再開キーが重複しています:\n{stop_key}",
        )
        return False

    def _key_overlap_report(self) -> KeyOverlapAnalysis:
        data = self._app.data
        return analyze_key_overlaps(data, data.get(HOOK_STOP_KEY, ""), data.get(HOOK_TOGGLE_KEY, ""))

    def show_shadowed_assignments(
        self, action: object, conflicts: tuple[AssignmentConflict, ...]
    ) -> None:
        notices = [self._format_shadowed_assignment(item) for item in conflicts]
        if not notices:
            return
        status_var = self._app.ui_vars.status_var
        current = str(status_var.get() or "")
        if current == self._last_shadowed_status:
            current = self._status_before_shadowed_notice or ""
        if isinstance(action, StopHookAction):
            current = f"停止しました\n{current}" if current else "停止しました"
        self._status_before_shadowed_notice = current
        self._last_shadowed_status = "\n".join(part for part in (current, *notices) if part)
        status_var.set(self._last_shadowed_status)

    @staticmethod
    def _format_shadowed_assignment(conflict: AssignmentConflict) -> str:
        reason = {
            "stop": "停止キー",
            "toggle": "一時停止/再開キー",
            "switch": "切替キー",
            "mapping": "置換",
        }.get(conflict.winner, "上位の割り当て")
        if conflict.kind == "keymap_switch":
            name = conflict.keymap_label or conflict.keymap_id
            return (
                f"{conflict.key} は{reason}と重複しているため、キーマップ {name} へ切り替えられません。"
                "切替キーを変更してください"
            )
        return f"{conflict.key} は{reason}と重複しているため、トリガーは実行されません。トリガーのキーを変更してください"

    def on_input_event(self, event: object):
        resolved_key = self._app.layout.resolve_key_name_from_scan_code(getattr(event, "scan_code", None))
        if self._app.layout.should_debug_special_key_event(event, resolved_key):
            self._app.layout.debug_special_key_event(event, resolved_key)
        route = self._app.input_router.handle(event)
        for action in route.actions:
            self._app.after(
                0,
                lambda aa=action, ss=route.shadowed: self._app.action_executor.execute_router_action(
                    aa, shadowed=ss
                ),
            )
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
