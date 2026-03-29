from __future__ import annotations

import threading
from typing import Callable

from keyseq.application.input_router import (
    SendKeyAction,
    SelectKeymapAction,
    StopHookAction,
    SwitchKeymapAction,
    ToggleModeAction,
    TriggerAction,
)


class ActionExecutor:
    def __init__(
        self,
        *,
        input_gateway,
        validate_hotkey: Callable[[str], tuple[str, str]],
        on_action_error: Callable[[dict, str], None],
        on_runtime_error: Callable[[str, str], None],
        on_stop_hook: Callable[[], None],
        on_toggle_mode: Callable[[], None],
        on_switch_keymap: Callable[[], None],
        on_select_keymap: Callable[[str], None],
        on_trigger: Callable[[str], None],
    ) -> None:
        self.input_gateway = input_gateway
        self._validate_hotkey = validate_hotkey
        self._on_action_error = on_action_error
        self._on_runtime_error = on_runtime_error
        self._on_stop_hook = on_stop_hook
        self._on_toggle_mode = on_toggle_mode
        self._on_switch_keymap = on_switch_keymap
        self._on_select_keymap = on_select_keymap
        self._on_trigger = on_trigger
        self._send_guard_count = 0
        self._send_guard_lock = threading.RLock()

    @property
    def send_guard_count(self) -> int:
        with self._send_guard_lock:
            return int(self._send_guard_count)

    def execute(self, action: dict) -> None:
        action_type = (action.get("type") or "").strip().lower()
        value = action.get("value") or ""

        if action_type == "hotkey":
            self._execute_hotkey(action, str(value))
            return
        if action_type == "text":
            self._write_text(str(value))
            return
        if action_type == "mouse_click":
            self._execute_mouse_click(action)
            return

        self._write_text(str(value))

    def execute_router_action(self, action: object) -> None:
        if isinstance(action, StopHookAction):
            self._on_stop_hook()
            return
        if isinstance(action, ToggleModeAction):
            self._on_toggle_mode()
            return
        if isinstance(action, SwitchKeymapAction):
            self._on_switch_keymap()
            return
        if isinstance(action, SelectKeymapAction):
            self._on_select_keymap(action.keymap_id)
            return
        if isinstance(action, TriggerAction):
            self._on_trigger(action.key)
            return
        if isinstance(action, SendKeyAction):
            self._send_mapped_key(action.target_key)

    def _execute_hotkey(self, action: dict, hotkey: str) -> None:
        error_message, normalized = self._validate_hotkey(hotkey)
        if error_message:
            self._on_action_error(action, error_message)
            return

        self._enter_send_guard()
        try:
            self.input_gateway.send_hotkey(normalized)
        finally:
            self._exit_send_guard()

    def _write_text(self, text: str) -> None:
        self._enter_send_guard()
        try:
            self.input_gateway.write_text(text)
        finally:
            self._exit_send_guard()

    def _send_mapped_key(self, key: str) -> None:
        self._enter_send_guard()
        try:
            self.input_gateway.press_key(key)
            self.input_gateway.release_key(key)
        except Exception as e:
            self._on_runtime_error("キー送信エラー", f"キーマップ送信に失敗しました。\n{type(e).__name__}: {e}")
        finally:
            self._exit_send_guard()

    def _execute_mouse_click(self, action: dict) -> None:
        try:
            x = int(action.get("x"))
            y = int(action.get("y"))
        except Exception:
            self._on_runtime_error("送信エラー", "mouse_click の x/y が不正です（整数で指定してください）。")
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

        try:
            self.input_gateway.click_mouse(x=x, y=y, button=button, clicks=clicks)
        except Exception as e:
            self._on_runtime_error("送信エラー", f"mouse_click の実行に失敗しました。\n{type(e).__name__}: {e}")

    def _enter_send_guard(self) -> None:
        with self._send_guard_lock:
            self._send_guard_count += 1

    def _exit_send_guard(self) -> None:
        with self._send_guard_lock:
            if self._send_guard_count > 0:
                self._send_guard_count -= 1
