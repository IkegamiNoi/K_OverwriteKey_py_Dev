from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


SOURCE_MISSING = "missing"
SOURCE_UNREADABLE = "unreadable"


@dataclass(frozen=True)
class ReferenceScanResult:
    referenced: frozenset[str]
    unreadable_sources: tuple[tuple[str, str], ...]
    non_keymap_set_sources: tuple[str, ...]


def collect_reference_paths(
    service,
    keymap_set_paths: list[str],
    *,
    config_root: str,
) -> ReferenceScanResult:
    """keymap_set 群が参照する子ファイルの比較用パス集合を読み出し専用で集める。"""
    referenced: set[str] = set()
    unreadable_sources: list[tuple[str, str]] = []
    non_keymap_set_sources: list[str] = []
    cache: dict[str, dict[str, Any] | None] = {}
    trigger_set_paths = _collect_keymap_set_references(
        service,
        keymap_set_paths,
        config_root,
        cache,
        unreadable_sources,
        non_keymap_set_sources,
        referenced,
    )
    _collect_sequence_paths(
        service,
        trigger_set_paths,
        config_root,
        cache,
        unreadable_sources,
        referenced,
    )
    return ReferenceScanResult(
        referenced=frozenset(referenced),
        unreadable_sources=tuple(unreadable_sources),
        non_keymap_set_sources=tuple(non_keymap_set_sources),
    )


def _collect_keymap_set_references(
    service,
    keymap_set_paths: list[str],
    config_root: str,
    cache: dict[str, dict[str, Any] | None],
    unreadable_sources: list[tuple[str, str]],
    non_keymap_set_sources: list[str],
    referenced: set[str],
) -> list[str]:
    trigger_set_paths: list[str] = []
    for value in keymap_set_paths:
        stored_path = _source_path(value)
        if not stored_path:
            continue
        keymap_set = _load_source(
            service, stored_path, config_root, cache, unreadable_sources
        )
        if keymap_set is None:
            continue
        if not _is_keymap_set(keymap_set):
            non_keymap_set_sources.append(stored_path)
            continue
        trigger_set_paths.extend(
            _collect_keymap_set_paths(service, keymap_set, config_root, referenced)
        )
    return trigger_set_paths


def _load_source(
    service,
    stored_path: str,
    config_root: str,
    cache: dict[str, dict[str, Any] | None],
    unreadable_sources: list[tuple[str, str]],
) -> dict[str, Any] | None:
    resolved_path = service.resolve_config_path(stored_path, config_root)
    canonical_path = service.canonical_path(resolved_path, config_root)
    if canonical_path in cache:
        return cache[canonical_path]
    if not os.path.exists(resolved_path):
        unreadable_sources.append((stored_path, SOURCE_MISSING))
        cache[canonical_path] = None
        return None
    data = service._load_optional_json(resolved_path)
    if not isinstance(data, dict):
        unreadable_sources.append((stored_path, SOURCE_UNREADABLE))
        cache[canonical_path] = None
        return None
    cache[canonical_path] = data
    return data


def _is_keymap_set(data: dict[str, Any]) -> bool:
    keys = (
        "trigger_set_path",
        "keymaps",
        "active_keymap_path",
        "hotkey_presets_path",
    )
    return any(key in data for key in keys)


def _collect_keymap_set_paths(
    service,
    keymap_set: dict[str, Any],
    config_root: str,
    referenced: set[str],
) -> list[str]:
    trigger_set_path = _path_value(keymap_set.get("trigger_set_path"))
    _add_reference(service, trigger_set_path, config_root, referenced)
    _add_entry_references(service, keymap_set.get("keymaps"), config_root, referenced)
    _add_reference(
        service, _path_value(keymap_set.get("active_keymap_path")), config_root, referenced
    )
    _add_reference(
        service, _path_value(keymap_set.get("hotkey_presets_path")), config_root, referenced
    )
    _add_external_layout_references(
        service, keymap_set.get("external_keyboard_layouts"), config_root, referenced
    )
    return [trigger_set_path] if trigger_set_path else []


def _collect_sequence_paths(
    service,
    trigger_set_paths: list[str],
    config_root: str,
    cache: dict[str, dict[str, Any] | None],
    unreadable_sources: list[tuple[str, str]],
    referenced: set[str],
) -> None:
    for stored_path in trigger_set_paths:
        trigger_set = _load_source(
            service, stored_path, config_root, cache, unreadable_sources
        )
        if trigger_set is None:
            continue
        triggers = trigger_set.get("triggers")
        if not isinstance(triggers, list):
            continue
        for trigger in triggers:
            if isinstance(trigger, dict):
                _add_reference(
                    service,
                    _path_value(trigger.get("sequence_path")),
                    config_root,
                    referenced,
                )


def _add_entry_references(service, entries: Any, config_root: str, referenced: set[str]) -> None:
    if not isinstance(entries, list):
        return
    for entry in entries:
        _add_reference(service, _entry_path(entry), config_root, referenced)


def _add_external_layout_references(
    service,
    entries: Any,
    config_root: str,
    referenced: set[str],
) -> None:
    if not isinstance(entries, list):
        return
    parent_root = os.path.dirname(config_root)
    for entry in entries:
        stored_path = _entry_path(entry)
        _add_reference(service, stored_path, config_root, referenced)
        _add_reference(service, stored_path, parent_root, referenced)


def _add_reference(service, stored_path: str, config_root: str, referenced: set[str]) -> None:
    if not stored_path:
        return
    resolved_path = service.resolve_config_path(stored_path, config_root)
    canonical_path = service.canonical_path(resolved_path, config_root)
    if canonical_path:
        referenced.add(canonical_path)


def _source_path(value: Any) -> str:
    return str(value or "").strip()


def _entry_path(value: Any) -> str:
    if isinstance(value, dict):
        return _source_path(value.get("path"))
    return _source_path(value)


def _path_value(value: Any) -> str:
    return _source_path(value)
