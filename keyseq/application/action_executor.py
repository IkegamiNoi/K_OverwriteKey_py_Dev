from __future__ import annotations

import math
import threading
from dataclasses import dataclass
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
    pick_file_line,
    validate_file_line_request,
)
from keyseq.application.file_line_loader import FileLineLoadRequest, FileLineLoader
from keyseq.application.held_inputs import HeldInputs
from keyseq.domain.config import DEFAULT_DRAG_SPEED_PX_PER_SEC
from keyseq.domain.key_hold import EDGE_DOWN, parse_key_hold


MIN_DRAG_DURATION_SEC = 0.15
MAX_DRAG_DURATION_SEC = 5.0


@dataclass(frozen=True)
class FileLineHandle:
    request: FileLineLoadRequest
    line_number: int
    out_of_range: str
    resolved_path: str
    action: dict


def _file_line_error_message(action: dict, exc: BaseException) -> str:
    values = ", ".join(
        f"{key}={action.get(key)!r}"
        for key in ("path", "counter", "encoding", "out_of_range")
        if key in action
    ) or "(値なし)"
    message = f"file_line 実行エラー（種類: file_line / 値: {values}）: {exc}"
    label = action.get("label")
    if isinstance(label, str) and label.strip():
        message += f" / ラベル: {label.strip()}"
    return message


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
        on_trigger: Callable[[str, bool], None],
        resolve_file_line_path: Callable[[str], str] | None = None,
        get_counter: Callable[[str], int] | None = None,
        file_line_loader: FileLineLoader | None = None,
        on_shadowed_action: Callable[[object, tuple[AssignmentConflict, ...]], None] | None = None,
        can_switch_keymap: Callable[[str], bool] | None = None,
        on_keymap_switch_blocked: Callable[[], None] | None = None,
        keymap_switch_in_progress: threading.Event | None = None,
        held_inputs: HeldInputs | None = None,
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
        self._file_line_loader = file_line_loader
        self._on_shadowed_action = on_shadowed_action
        self._can_switch_keymap = can_switch_keymap or (lambda _keymap_id: True)
        self._on_keymap_switch_blocked = on_keymap_switch_blocked or (lambda: None)
        self._keymap_switch_in_progress = keymap_switch_in_progress
        self._send_guard_count = 0
        self._send_guard_lock = threading.RLock()
        self.held_inputs = held_inputs if held_inputs is not None else HeldInputs(input_gateway)
        self.held_inputs.set_send_guard(self._enter_send_guard, self._exit_send_guard)

    @property
    def send_guard_count(self) -> int:
        with self._send_guard_lock:
            return int(self._send_guard_count)

    def execute(self, action: dict, owner: str | None = None) -> bool:
        raw = action.get("type")
        type_text = raw.strip() if isinstance(raw, str) else ""
        action_type = type_text.lower()
        value = action.get("value") or ""

        if action_type == "hotkey":
            self._execute_hotkey(action, str(value))
            return True
        if action_type == "text":
            try:
                self._write_text(str(value))
            except Exception as exc:
                self._report_held_error(action, owner, f"text の送信に失敗しました: {exc}")
                return False
            return True
        if action_type == "key_hold":
            return self._execute_key_hold(action, owner or "")
        if action_type == "file_line":
            self._on_action_error(
                action,
                _file_line_error_message(
                    action,
                    FileLineError(
                        "file_line は読込の経路（begin_file_line / poll_file_line）で実行します"
                    ),
                ),
            )
            return False
        if action_type == "mouse_click":
            self._execute_mouse_click(action)
            return True

        notified_action = action.copy()
        notified_action["type"] = type_text
        err = self._invalid_type_message(type_text, action)
        self._on_action_error(notified_action, err)
        return False

    def begin_file_line(self, action: dict) -> FileLineHandle | None:
        try:
            path, counter_name, encoding, out_of_range = normalize_file_line_options(action)
            if not counter_name:
                raise FileLineError("カウンター名が空です")
            if self._get_counter is None:
                raise FileLineError("カウンター取得コールバックが未設定です")
            if self._resolve_file_line_path is None:
                raise FileLineError("ファイルパス解決コールバックが未設定です")
            if self._file_line_loader is None:
                raise FileLineError("ファイル読込の仕組みが未設定です")
            line_number = self._get_counter(counter_name)
            resolved_path = self._resolve_file_line_path(path)
            validate_file_line_request(
                resolved_path, line_number, encoding=encoding, out_of_range=out_of_range,
            )
            request = self._file_line_loader.request(resolved_path, encoding)
            return FileLineHandle(request, line_number, out_of_range, resolved_path, action)
        except Exception as exc:
            self._on_action_error(action, _file_line_error_message(action, exc))
            return None

    def poll_file_line(self, handle: FileLineHandle, owner: str | None = None) -> bool | None:
        try:
            if self._file_line_loader is None:
                raise FileLineError("ファイル読込の仕組みが未設定です")
            result = self._file_line_loader.poll(handle.request)
            if result.status == "pending":
                return None
            if result.status == "error":
                raise result.error or FileLineError("ファイル読込に失敗しました")
            if result.status != "done":
                raise FileLineError("ファイル読込の結果が不正です")
            line = pick_file_line(
                result.lines or [], handle.line_number,
                out_of_range=handle.out_of_range, path=handle.resolved_path,
            )
            if line:
                self._write_text(line)
            return True
        except Exception as exc:
            self._report_held_error(handle.action, owner, _file_line_error_message(handle.action, exc))
            return False

    @staticmethod
    def _invalid_type_message(type_text: str, action: dict) -> str:
        err = (
            "種類が不正です（hotkey / text / mouse_click / system / file_line / key_hold のいずれか）。"
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
            self._on_trigger(action.key, action.repeat)
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
            self.held_inputs.suspend_keyboard()
            try:
                self.input_gateway.write_text(text)
            except Exception:
                # 一時的に離した他の持ち主の分も押し直さず、集合を OS の実態にそろえる。
                self.held_inputs.release_keyboard()
                raise
            self.held_inputs.resume_keyboard()
        finally:
            self._exit_send_guard()

    def _report_held_error(self, action: dict, owner: str | None, message: str) -> None:
        release_errors = self.held_inputs.release_owner(owner or "")
        if release_errors:
            message += " / 解放エラー: " + "; ".join(str(exc) for exc in release_errors)
        self._on_action_error(action, message)

    def _execute_key_hold(self, action: dict, owner: str) -> bool:
        parsed = parse_key_hold(action)
        if isinstance(parsed, str):
            self._report_held_error(action, owner, parsed)
            return False
        try:
            if parsed.key is not None:
                self.input_gateway.validate_key_name(parsed.key)
                if parsed.edge == EDGE_DOWN:
                    self.held_inputs.press_key(owner, parsed.key)
                else:
                    self.held_inputs.release_key(parsed.key)
            else:
                if parsed.edge == EDGE_DOWN:
                    self.held_inputs.press_mouse(owner, parsed.button, parsed.position)
                else:
                    self.held_inputs.release_mouse(parsed.button, parsed.position)
        except Exception as exc:
            self._report_held_error(action, owner, f"key_hold の実行に失敗しました: {exc}")
            return False
        return True

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
