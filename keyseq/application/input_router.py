from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable

from keyseq.application.key_overlap import AssignmentConflict, KeyOverlapAnalysis
from keyseq.domain.config import normalize_key_name
from keyseq.domain.key_hold import MODIFIER_KEY_NAMES
from keyseq.domain.numpad_keys import is_numpad_key_name, numpad_name_from_event


@dataclass(frozen=True)
class StopHookAction:
    pass


@dataclass(frozen=True)
class ToggleModeAction:
    pass


@dataclass(frozen=True)
class SelectKeymapAction:
    keymap_id: str


@dataclass(frozen=True)
class TriggerAction:
    key: str
    repeat: bool = False


@dataclass(frozen=True)
class GridKeyAction:
    key: str
    generation: int
    shift: bool
    repeat: bool


@dataclass(frozen=True)
class SendKeyAction:
    source_key: str
    target_key: str


@dataclass(frozen=True)
class InputRoute:
    actions: tuple[object, ...] = ()
    accept: bool = True
    shadowed: tuple[AssignmentConflict, ...] = ()


class InputRouter:
    def __init__(
        self,
        *,
        key_state_manager,
        get_send_guard_count: Callable[[], int],
        get_hook_pause_count: Callable[[], int],
        get_stop_key: Callable[[], str],
        get_toggle_key: Callable[[], str],
        get_key_overlap_report: Callable[[], KeyOverlapAnalysis],
        get_custom_input_enabled: Callable[[], bool],
        find_keymap_switch_target: Callable[[str], str],
        find_trigger: Callable[[str], dict[str, Any] | None],
        find_keymap_target: Callable[[str], str],
        keymap_switch_in_progress: threading.Event | None = None,
        resolve_scan_code: Callable[[object], str] | None = None,
        get_grid_snapshot: Callable[[], object] | None = None,
    ) -> None:
        self._key_state_manager = key_state_manager
        self._get_send_guard_count = get_send_guard_count
        self._get_hook_pause_count = get_hook_pause_count
        self._get_stop_key = get_stop_key
        self._get_toggle_key = get_toggle_key
        self._get_key_overlap_report = get_key_overlap_report
        self._get_custom_input_enabled = get_custom_input_enabled
        self._find_keymap_switch_target = find_keymap_switch_target
        self._find_trigger = find_trigger
        self._find_keymap_target = find_keymap_target
        self._keymap_switch_in_progress = keymap_switch_in_progress
        self._resolve_scan_code = resolve_scan_code
        self._get_grid_snapshot = get_grid_snapshot

    def handle(self, event: object) -> InputRoute:
        switching = self._is_keymap_switch_in_progress()
        if not switching and self._get_send_guard_count() > 0:
            return InputRoute()
        if not switching and self._get_hook_pause_count() > 0:
            return InputRoute()

        event_type = normalize_key_name(str(getattr(event, "event_type", "")))
        key = self._extract_key_name(event) if event_type == "down" else ""
        repeat = event_type == "down" and self._key_state_manager.is_pressed(key)
        self._key_state_manager.handle_event(event)

        if event_type != "down":
            return InputRoute()

        if not key:
            return InputRoute()

        stop_key = normalize_key_name(self._get_stop_key())
        toggle_key = normalize_key_name(self._get_toggle_key())
        custom_enabled = bool(self._get_custom_input_enabled())
        shadowed = ()
        if custom_enabled:
            analysis = self._get_key_overlap_report()
            shadowed = analysis.shadowed_for_key(key)
        if stop_key and key == stop_key:
            return InputRoute(actions=(StopHookAction(),), accept=False, shadowed=shadowed)

        if toggle_key and key == toggle_key:
            return InputRoute(actions=(ToggleModeAction(),), accept=False, shadowed=shadowed)

        if self._is_keymap_switch_in_progress():
            return InputRoute()

        if not custom_enabled:
            return InputRoute()

        direct_keymap_id = normalize_key_name(self._find_keymap_switch_target(key))
        if direct_keymap_id:
            if self._keymap_switch_in_progress is not None:
                self._keymap_switch_in_progress.set()
            return InputRoute(
                actions=(SelectKeymapAction(keymap_id=direct_keymap_id),),
                accept=False,
                shadowed=shadowed,
            )

        grid_route = self._route_grid_key(key, repeat, shadowed)
        if grid_route is not None:
            return grid_route

        trigger = self._find_trigger(key)
        if self._has_actions(trigger):
            suppress = bool(trigger.get("suppress", True))
            return InputRoute(actions=(TriggerAction(key=key, repeat=repeat),), accept=not suppress, shadowed=shadowed)

        keymap_target = normalize_key_name(self._find_keymap_target(key))
        if keymap_target:
            return InputRoute(
                actions=(SendKeyAction(source_key=key, target_key=keymap_target),),
                accept=False,
                shadowed=shadowed,
            )

        return InputRoute()

    def _route_grid_key(self, key: str, repeat: bool, shadowed: tuple) -> InputRoute | None:
        if self._get_grid_snapshot is None:
            return None
        snapshot = self._get_grid_snapshot()
        if not getattr(snapshot, "visible", False):
            return None
        passthrough_modifiers = (
            "ctrl", "left ctrl", "right ctrl", "alt", "left alt", "right alt",
            "alt gr", "windows", "left windows", "right windows",
        )
        if any(self._key_state_manager.is_pressed(name) for name in passthrough_modifiers):
            return InputRoute()
        if key in MODIFIER_KEY_NAMES:
            return InputRoute()
        if key not in getattr(snapshot, "suppress_keys", frozenset()):
            return InputRoute()
        shift = any(self._key_state_manager.is_pressed(name) for name in (
            "shift", "left shift", "right shift",
        ))
        return InputRoute(
            actions=(GridKeyAction(key, snapshot.generation, shift, repeat),),
            accept=False,
            shadowed=shadowed,
        )

    def _is_keymap_switch_in_progress(self) -> bool:
        return bool(
            self._keymap_switch_in_progress is not None
            and self._keymap_switch_in_progress.is_set()
        )

    def _extract_key_name(self, event: object) -> str:
        numpad_name = numpad_name_from_event(
            getattr(event, "scan_code", None), getattr(event, "is_keypad", False)
        )
        if numpad_name:
            return numpad_name
        if callable(self._resolve_scan_code):
            normalized = normalize_key_name(str(self._resolve_scan_code(getattr(event, "scan_code", None)) or ""))
            if normalized and not is_numpad_key_name(normalized):
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
