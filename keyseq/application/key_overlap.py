from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from keyseq.domain.config import normalize_key_name


OverlapWinner = Literal["stop", "toggle", "switch", "mapping"]
AssignmentKind = Literal["trigger", "keymap_switch"]


@dataclass(frozen=True)
class AssignmentConflict:
    key: str
    kind: AssignmentKind
    winner: OverlapWinner
    keymap_id: str = ""
    keymap_label: str = ""


@dataclass(frozen=True)
class KeyOverlapAnalysis:
    active_keymap_id: str
    trigger_conflicts: tuple[AssignmentConflict, ...]
    keymap_switch_conflicts: tuple[AssignmentConflict, ...]
    all_trigger_keys: frozenset[str]
    active_trigger_keys: frozenset[str]
    all_source_keys: frozenset[str]
    active_source_keys: frozenset[str]
    all_triggers: tuple[dict[str, Any], ...]
    stop_toggle_conflict: bool

    def trigger_conflict(self, key: str) -> AssignmentConflict | None:
        normalized = normalize_key_name(key)
        return next((item for item in self.trigger_conflicts if item.key == normalized), None)

    def keymap_switch_conflict(self, keymap_id: str, key: str) -> AssignmentConflict | None:
        normalized_id = normalize_key_name(keymap_id)
        normalized_key = normalize_key_name(key)
        return next(
            (item for item in self.keymap_switch_conflicts
             if item.keymap_id == normalized_id and item.key == normalized_key),
            None,
        )

    def shadowed_for_key(self, key: str) -> tuple[AssignmentConflict, ...]:
        normalized = normalize_key_name(key)
        conflicts = [item for item in self.trigger_conflicts if item.key == normalized]
        conflicts.extend(item for item in self.keymap_switch_conflicts if item.key == normalized)
        return tuple(conflicts)


def analyze_key_overlaps(
    runtime: dict[str, Any], stop_key: str, toggle_key: str
) -> KeyOverlapAnalysis:
    """Resolve loaded key overlaps once for routing, validation, notices, and list styling."""
    keymaps = _valid_keymaps(runtime)
    active = _active_keymap(runtime, keymaps)
    active_id = normalize_key_name(active.get("id", "")) if active else ""
    stop = normalize_key_name(stop_key)
    toggle = normalize_key_name(toggle_key)
    all_triggers, all_trigger_keys, active_trigger_keys = _collect_triggers(keymaps, active_id)
    all_sources, active_sources = _collect_sources(keymaps, active_id)
    switches, keymap_labels = _collect_switches(runtime, keymaps)
    trigger_conflicts = _analyze_trigger_conflicts(active_trigger_keys, stop, toggle, switches, active_sources)
    switch_conflicts = _analyze_switch_conflicts(switches, keymap_labels, stop, toggle)
    return KeyOverlapAnalysis(
        active_keymap_id=active_id,
        trigger_conflicts=trigger_conflicts,
        keymap_switch_conflicts=switch_conflicts,
        all_trigger_keys=frozenset(all_trigger_keys),
        active_trigger_keys=frozenset(active_trigger_keys),
        all_source_keys=frozenset(all_sources),
        active_source_keys=frozenset(active_sources),
        all_triggers=tuple(all_triggers),
        stop_toggle_conflict=bool(stop and stop == toggle),
    )


def _analyze_trigger_conflicts(
    trigger_keys: set[str], stop: str, toggle: str, switches: dict[str, str], sources: set[str]
) -> tuple[AssignmentConflict, ...]:
    conflicts = []
    for key in sorted(trigger_keys):
        winner = _trigger_winner(key, stop, toggle, switches, sources)
        if winner:
            conflicts.append(AssignmentConflict(key, "trigger", winner))
    return tuple(conflicts)


def _analyze_switch_conflicts(
    switches: dict[str, str], labels: dict[str, str], stop: str, toggle: str
) -> tuple[AssignmentConflict, ...]:
    conflicts = []
    for key, target_id in sorted(switches.items()):
        winner = _switch_winner(key, stop, toggle)
        if winner:
            conflicts.append(AssignmentConflict(key, "keymap_switch", winner, target_id, labels[target_id]))
    return tuple(conflicts)


def _valid_keymaps(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    keymaps = runtime.get("keymaps") if isinstance(runtime, dict) else None
    if not isinstance(keymaps, list):
        return []
    return [item for item in keymaps if isinstance(item, dict) and normalize_key_name(item.get("id", ""))]


def _active_keymap(runtime: dict[str, Any], keymaps: list[dict[str, Any]]) -> dict[str, Any] | None:
    active_id = normalize_key_name(runtime.get("active_keymap_id", ""))
    return next(
        (item for item in keymaps if normalize_key_name(item.get("id", "")) == active_id),
        keymaps[0] if keymaps else None,
    )


def _collect_triggers(
    keymaps: list[dict[str, Any]], active_id: str
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    all_triggers: list[dict[str, Any]] = []
    all_keys: set[str] = set()
    active_keys: set[str] = set()
    for keymap in keymaps:
        is_active = normalize_key_name(keymap.get("id", "")) == active_id
        triggers = keymap.get("triggers")
        if not isinstance(triggers, list):
            continue
        for trigger in triggers:
            if not isinstance(trigger, dict):
                continue
            all_triggers.append(trigger)
            key = normalize_key_name(trigger.get("key", ""))
            if key:
                all_keys.add(key)
                if is_active:
                    active_keys.add(key)
    return all_triggers, all_keys, active_keys


def _collect_sources(keymaps: list[dict[str, Any]], active_id: str) -> tuple[set[str], set[str]]:
    all_sources: set[str] = set()
    active_sources: set[str] = set()
    for keymap in keymaps:
        mappings = keymap.get("mappings")
        if not isinstance(mappings, dict):
            continue
        sources = {normalize_key_name(str(source or "")) for source in mappings}
        sources.discard("")
        all_sources.update(sources)
        if normalize_key_name(keymap.get("id", "")) == active_id:
            active_sources.update(sources)
    return all_sources, active_sources


def _collect_switches(runtime: dict[str, Any], keymaps: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    valid_ids = {normalize_key_name(item.get("id", "")) for item in keymaps}
    labels = {
        normalize_key_name(item.get("id", "")): str(item.get("label") or "").strip()
        or normalize_key_name(item.get("id", ""))
        for item in keymaps
    }
    raw_switches = runtime.get("keymap_switch_keys") if isinstance(runtime, dict) else None
    if not isinstance(raw_switches, dict):
        return {}, labels
    switches: dict[str, str] = {}
    for raw_key, raw_target in raw_switches.items():
        key = normalize_key_name(str(raw_key or ""))
        target_id = normalize_key_name(str(raw_target or ""))
        if key and target_id in valid_ids:
            switches[key] = target_id
    return switches, labels


def _trigger_winner(key: str, stop: str, toggle: str, switches: dict[str, str], sources: set[str]) -> OverlapWinner | None:
    if key == stop and stop:
        return "stop"
    if key == toggle and toggle:
        return "toggle"
    if key in switches:
        return "switch"
    if key in sources:
        return "mapping"
    return None


def _switch_winner(key: str, stop: str, toggle: str) -> OverlapWinner | None:
    if key == stop and stop:
        return "stop"
    if key == toggle and toggle:
        return "toggle"
    return None
