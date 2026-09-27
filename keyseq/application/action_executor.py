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
from keyseq.application.file_line_reader import (
    FileLineError,
    normalize_file_line_options,
    read_file_line,
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
        resolve_file_line_path: Callable[[str], str] | None = None,
        get_counter: Callable[[str], int] | None = None,
        on_shadowed_action: Callable[[object, tuple[AssignmentConflict, ...]], None] | None = None,
        can_switch_keymap: Callable[[str], bool] | None = None,
        on_keymap_switch_blocked: Callable[[], None] | None = None,
        keymap_switch_in_progress: threading.Event | None = None,
    ) -> None:
        self.input_gateway = input_gateway
        self._validate_hotkey = validate_hotkey
        self._on_action_error = on_action_error
        self._on_runtime_error = on_runtime_error
        self._on_stop_hook = on_stop_hook
        self._on_toggle_mode = on_toggle_mode
        self._on_select_keymap = on_select_keymap
        self._on_trigger = on_trigger
        self._resolve_file_line_path = resolve_file_line_path
        self._get_counter = get_counter
        self._on_shadowed_action = on_shadowed_action
        self._can_switch_keymap = can_switch_keymap or (lambda _keymap_id: True)
        self._on_keymap_switch_blocked = on_keymap_switch_blocked or (lambda: None)
        self._keymap_switch_in_progress = keymap_switch_in_progress
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
        if action_type == "file_line":
            return self._execute_file_line(action)
        if action_type == "mouse_click":
            self._execute_mouse_click(action)
            return True

        notified_action = action.copy()
        notified_action["type"] = type_text
        err = self._invalid_type_message(type_text, action)
        self._on_action_error(notified_action, err)
        return False

    def _execute_file_line(self, action: dict) -> bool:
        try:
            path, counter_name, encoding, out_of_range = normalize_file_line_options(action)
            if not counter_name:
                raise FileLineError("カウンター名が空です")
            if self._get_counter is None:
                raise FileLineError("カウンター取得コールバックが未設定です")
            if self._resolve_file_line_path is None:
                raise FileLineError("ファイルパス解決コールバックが未設定です")
            line_number = self._get_counter(counter_name)
            resolved_path = self._resolve_file_line_path(path)
            line = read_file_line(
                resolved_path,
                line_number,
                encoding=encoding,
                out_of_range=out_of_range,
            )
            if line:
                self._write_text(line)
            return True
        except Exception as exc:
            values = ", ".join(
                f"{key}={action.get(key)!r}"
                for key in ("path", "counter", "encoding", "out_of_range")
                if key in action
            ) or "(値なし)"
            message = f"file_line 実行エラー（種類: file_line / 値: {values}）: {exc}"
            label = action.get("label")
            if isinstance(label, str) and label.strip():
                message += f" / ラベル: {label.strip()}"
            self._on_action_error(action, message)
            return False

    @staticmethod
    def _invalid_type_message(type_text: str, action: dict) -> str:
        err = (
            "種類が不正です（hotkey / text / mouse_click / system / file_line のいずれか）。"
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
            try:
                if self._can_switch_keymap(action.keymap_id):
                    self._on_select_keymap(action.keymap_id)
                else:
                    self._on_keymap_switch_blocked()
            finally:
                if self._keymap_switch_in_progress is not None:
                    self._keymap_switch_in_progress.clear()
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
