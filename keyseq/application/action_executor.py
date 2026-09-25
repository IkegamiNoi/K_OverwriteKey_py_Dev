from __future__ import annotations

import math
import threading
from typing import Callable

from keyseq.application.key_overlap import AssignmentConflict
from keyseq.application.input_router import (
    SendKeyAction,
    SelectKeymapAction,
    StopHookAction,
    ToggleModeAction,
    TriggerAction,
)
from keyseq.domain.config import DEFAULT_DRAG_SPEED_PX_PER_SEC


MIN_DRAG_DURATION_SEC = 0.15
MAX_DRAG_DURATION_SEC = 5.0


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
        on_select_keymap: Callable[[str], None],
        on_trigger: Callable[[str], None],
        on_shadowed_action: Callable[[object, tuple[AssignmentConflict, ...]], None] | None = None,
    ) -> None:
        self.input_gateway = input_gateway
        self._validate_hotkey = validate_hotkey
        self._on_action_error = on_action_error
        self._on_runtime_error = on_runtime_error
        self._on_stop_hook = on_stop_hook
        self._on_toggle_mode = on_toggle_mode
        self._on_select_keymap = on_select_keymap
        self._on_trigger = on_trigger
        self._on_shadowed_action = on_shadowed_action
        self._send_guard_count = 0
        self._send_guard_lock = threading.RLock()

    @property
    def send_guard_count(self) -> int:
        with self._send_guard_lock:
            return int(self._send_guard_count)

    def execute(self, action: dict) -> bool:
        raw = action.get("type")
        type_text = raw.strip() if isinstance(raw, str) else ""
        action_type = type_text.lower()
        value = action.get("value") or ""

        if action_type == "hotkey":
            self._execute_hotkey(action, str(value))
            return True
        if action_type == "text":
            self._write_text(str(value))
            return True
        if action_type == "mouse_click":
            self._execute_mouse_click(action)
            return True

        notified_action = action.copy()
        notified_action["type"] = type_text
        err = self._invalid_type_message(type_text, action)
        self._on_action_error(notified_action, err)
        return False

    @staticmethod
    def _invalid_type_message(type_text: str, action: dict) -> str:
        err = (
            "種類が不正です（hotkey / text / mouse_click のいずれか）。"
            f"種類: {type_text or '(なし)'}"
        )
        label = action.get("label")
        if isinstance(label, str) and label.strip():
            err += f" / ラベル: {label.strip()}"
        return err

    def execute_router_action(
        self, action: object, *, shadowed: tuple[AssignmentConflict, ...] = ()
    ) -> None:
        handled = True
        if isinstance(action, StopHookAction):
            self._on_stop_hook()
        elif isinstance(action, ToggleModeAction):
            self._on_toggle_mode()
        elif isinstance(action, SelectKeymapAction):
            self._on_select_keymap(action.keymap_id)
        elif isinstance(action, TriggerAction):
            self._on_trigger(action.key)
        elif isinstance(action, SendKeyAction):
            self._send_mapped_key(action.target_key)
        else:
            handled = False
        if handled and shadowed and self._on_shadowed_action is not None:
            self._on_shadowed_action(action, shadowed)

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

        drag = bool(action.get("drag"))
        try:
            if drag:
                self._execute_mouse_drag(action, x, y, button)
            else:
                self.input_gateway.click_mouse(x=x, y=y, button=button, clicks=clicks)
        except Exception as e:
            self._on_runtime_error("送信エラー", f"mouse_click の実行に失敗しました。\n{type(e).__name__}: {e}")

    def _execute_mouse_drag(self, action: dict, x: int, y: int, button: str) -> None:
        try:
            to_x = int(action.get("to_x"))
            to_y = int(action.get("to_y"))
        except Exception:
            self._on_runtime_error("送信エラー", "mouse_click の to_x/to_y が不正です（ドラッグの離す位置を整数で指定してください）。")
            return
        try:
            speed = float(action.get("drag_speed", DEFAULT_DRAG_SPEED_PX_PER_SEC))
        except Exception:
            speed = DEFAULT_DRAG_SPEED_PX_PER_SEC
        if not (speed > 0):
            speed = DEFAULT_DRAG_SPEED_PX_PER_SEC
        duration_sec = math.hypot(to_x - x, to_y - y) / speed
        duration_sec = min(max(duration_sec, MIN_DRAG_DURATION_SEC), MAX_DRAG_DURATION_SEC)
        self.input_gateway.drag_mouse(
            x=x, y=y, to_x=to_x, to_y=to_y, button=button, duration_sec=duration_sec
        )

    def _enter_send_guard(self) -> None:
        with self._send_guard_lock:
            self._send_guard_count += 1

    def _exit_send_guard(self) -> None:
        with self._send_guard_lock:
            if self._send_guard_count > 0:
                self._send_guard_count -= 1
