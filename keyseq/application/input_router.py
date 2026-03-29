from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from keyseq.domain.config import normalize_key_name


@dataclass(frozen=True)
class StopHookAction:
    pass


@dataclass(frozen=True)
class ToggleModeAction:
    pass


@dataclass(frozen=True)
class SwitchKeymapAction:
    pass


@dataclass(frozen=True)
class SelectKeymapAction:
    keymap_id: str


@dataclass(frozen=True)
class TriggerAction:
    key: str


@dataclass(frozen=True)
class SendKeyAction:
    source_key: str
    target_key: str


@dataclass(frozen=True)
class InputRoute:
    actions: tuple[object, ...] = ()
    accept: bool = True


class InputRouter:
    def __init__(
        self,
        *,
        key_state_manager,
        get_send_guard_count: Callable[[], int],
        get_hook_pause_count: Callable[[], int],
        get_stop_key: Callable[[], str],
        get_toggle_key: Callable[[], str],
        get_keymap_toggle_key: Callable[[], str],
        get_custom_input_enabled: Callable[[], bool],
        find_keymap_switch_target: Callable[[str], str],
        find_trigger: Callable[[str], dict[str, Any] | None],
        find_keymap_target: Callable[[str], str],
        resolve_scan_code: Callable[[object], str] | None = None,
    ) -> None:
        self._key_state_manager = key_state_manager
        self._get_send_guard_count = get_send_guard_count
        self._get_hook_pause_count = get_hook_pause_count
        self._get_stop_key = get_stop_key
        self._get_toggle_key = get_toggle_key
        self._get_keymap_toggle_key = get_keymap_toggle_key
        self._get_custom_input_enabled = get_custom_input_enabled
        self._find_keymap_switch_target = find_keymap_switch_target
        self._find_trigger = find_trigger
        self._find_keymap_target = find_keymap_target
        self._resolve_scan_code = resolve_scan_code

    def handle(self, event: object) -> InputRoute:
        if self._get_send_guard_count() > 0:
            return InputRoute()
        if self._get_hook_pause_count() > 0:
            return InputRoute()

        self._key_state_manager.handle_event(event)

        event_type = normalize_key_name(str(getattr(event, "event_type", "")))
        if event_type != "down":
            return InputRoute()

        key = self._extract_key_name(event)
        if not key:
            return InputRoute()

        stop_key = normalize_key_name(self._get_stop_key())
        if stop_key and key == stop_key:
            return InputRoute(actions=(StopHookAction(),), accept=False)

        toggle_key = normalize_key_name(self._get_toggle_key())
        if toggle_key and key == toggle_key:
            return InputRoute(actions=(ToggleModeAction(),), accept=False)

        keymap_toggle_key = normalize_key_name(self._get_keymap_toggle_key())
        if keymap_toggle_key and key == keymap_toggle_key:
            return InputRoute(actions=(SwitchKeymapAction(),), accept=False)

        if not self._get_custom_input_enabled():
            return InputRoute()

        direct_keymap_id = normalize_key_name(self._find_keymap_switch_target(key))
        if direct_keymap_id:
            return InputRoute(actions=(SelectKeymapAction(keymap_id=direct_keymap_id),), accept=False)

        trigger = self._find_trigger(key)
        if self._has_actions(trigger):
            suppress = bool(trigger.get("suppress", True))
            return InputRoute(actions=(TriggerAction(key=key),), accept=not suppress)

        keymap_target = normalize_key_name(self._find_keymap_target(key))
        if keymap_target:
            return InputRoute(
                actions=(
                    SendKeyAction(
                        source_key=key,
                        target_key=keymap_target,
                    ),
                ),
                accept=False,
            )

        return InputRoute()

    def _extract_key_name(self, event: object) -> str:
        if callable(self._resolve_scan_code):
            normalized = normalize_key_name(str(self._resolve_scan_code(getattr(event, "scan_code", None)) or ""))
            if normalized:
                return normalized
        for value in (getattr(event, "name", ""), getattr(event, "key", "")):
            normalized = normalize_key_name(str(value or ""))
            if normalized:
                return normalized
        return ""

    def _has_actions(self, trigger: dict[str, Any] | None) -> bool:
        if not isinstance(trigger, dict):
            return False
        actions = trigger.get("actions", [])
        return isinstance(actions, list) and len(actions) > 0
