from __future__ import annotations

import os
from dataclasses import dataclass

from . import reference_scan, split_loading
from . import path_boundary


ORPHAN_CANDIDATE = "candidate"
ORPHAN_REFERENCED = "referenced"
ORPHAN_PROTECTED = "protected"
ORPHAN_EXCLUDED = "excluded"

KIND_KEYMAP = "keymap"
KIND_TRIGGER_SET = "trigger_set"
KIND_SEQUENCE = "sequence"
KIND_HOTKEY_PRESETS = "hotkey_presets"

_CANDIDATE_SPECS = (
    (KIND_KEYMAP, "user/keymaps", "mappings", dict),
    (KIND_TRIGGER_SET, "user/trigger_sets", "triggers", list),
    (KIND_SEQUENCE, "user/sequences", "actions", list),
    (KIND_HOTKEY_PRESETS, "user/hotkey_presets", "hotkey_presets", list),
)


@dataclass(frozen=True)
class OrphanEntry:
    kind: str
    stored_path: str
    state: str


@dataclass(frozen=True)
class OrphanScanResult:
    entries: tuple[OrphanEntry, ...]
    unreadable_sources: tuple[tuple[str, str], ...]
    non_keymap_set_sources: tuple[str, ...]
    missing_scan_dirs: tuple[str, ...]


def collect_protected_paths(service, runtime, *, keymap_set_path: str) -> tuple[str, ...]:
    """編集中の構成が使うパスを、保存表記と入力順を保って集める。"""
    values = [keymap_set_path]
    if isinstance(runtime, dict):
        keymaps = runtime.get("keymaps")
        if isinstance(keymaps, list):
            values.extend(
                keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH)
                for keymap in keymaps if isinstance(keymap, dict)
            )
        values.append(runtime.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH))
        triggers = runtime.get("triggers")
        if isinstance(triggers, list):
            values.extend(
                trigger.get(service.INTERNAL_SEQUENCE_SOURCE_PATH)
                for trigger in triggers if isinstance(trigger, dict)
            )
        values.append(runtime.get("hotkey_presets_path"))
    paths = (str(value or "").strip() for value in values)
    return tuple(dict.fromkeys(path for path in paths if path))


def normalize_scan_dirs(service, values, *, config_root: str) -> tuple[str, ...]:
    """走査先を保存表記へ揃え、実在を問わず入力順で重複を除く。"""
    if not isinstance(values, (list, tuple)):
        return ()
    paths: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        resolved = service.resolve_config_path(value.strip(), config_root)
        canonical = service.canonical_path(resolved, config_root)
        if canonical in seen:
            continue
        seen.add(canonical)
        paths.append(service.to_config_relative_or_absolute(resolved, config_root))
    return tuple(paths)


def scan_orphans(
    service,
    *,
    config_root: str,
    scan_dirs: list[str],
    startup_keymap_set_path: str,
    current_keymap_set_path: str,
    protected_paths: list[str],
) -> OrphanScanResult:
    """参照元を走査し、既定ディレクトリの子JSONを読み出し専用で分類する。"""
    unreadable_sources: list[tuple[str, str]] = []
    paths, missing_dirs = _collect_source_paths(
        service, config_root, scan_dirs,
        startup_keymap_set_path, current_keymap_set_path, unreadable_sources,
    )
    references = reference_scan.collect_reference_paths(service, paths, config_root=config_root)
    global_path = split_loading.load_global_hotkey_presets_path(service, config_root=config_root)
    referenced = set(references.referenced)
    referenced.update(_canonical_paths(service, [global_path], config_root))
    protected = _canonical_paths(service, protected_paths, config_root)
    return OrphanScanResult(
        entries=_collect_entries(service, config_root, referenced, protected),
        unreadable_sources=tuple(unreadable_sources) + references.unreadable_sources,
        non_keymap_set_sources=references.non_keymap_set_sources,
        missing_scan_dirs=tuple(missing_dirs),
    )


def _collect_source_paths(
    service,
    config_root: str,
    scan_dirs: list[str],
    startup_keymap_set_path: str,
    current_keymap_set_path: str,
    unreadable_sources: list[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    missing_dirs: list[str] = []
    default_dir = os.path.join(os.path.abspath(config_root), "user", "keymap_sets")
    paths = _list_json_files(service, default_dir, config_root, unreadable_sources)
    for value in (startup_keymap_set_path, current_keymap_set_path):
        stored_path = str(value or "").strip()
        if stored_path:
            paths.append(stored_path)
    for directory in scan_dirs:
        paths.extend(_scan_source_directory(
            service, directory, config_root, missing_dirs, unreadable_sources,
        ))
    return paths, missing_dirs


def _scan_source_directory(
    service, directory: str, config_root: str, missing_dirs: list[str],
    unreadable_sources: list[tuple[str, str]],
) -> list[str]:
    stored_dir = str(directory or "").strip()
    if not stored_dir:
        return []
    resolved_dir = service.resolve_config_path(stored_dir, config_root)
    if not os.path.isdir(resolved_dir):
        missing_dirs.append(directory)
        return []
    return _list_json_files(service, stored_dir, config_root, unreadable_sources)


def _list_json_files(
    service, directory: str, config_root: str,
    unreadable_sources: list[tuple[str, str]] | None = None,
) -> list[str]:
    resolved_dir = service.resolve_config_path(directory, config_root)
    if not os.path.isdir(resolved_dir):
        return []
    paths: list[str] = []
    try:
        filenames = sorted(os.listdir(resolved_dir))
    except OSError:
        if unreadable_sources is not None:
            unreadable_sources.append((
                service.to_config_relative_or_absolute(resolved_dir, config_root),
                reference_scan.SOURCE_DIRECTORY_UNREADABLE,
            ))
        return []
    for filename in filenames:
        if not filename.lower().endswith(".json"):
            continue
        absolute_path = os.path.abspath(os.path.join(resolved_dir, filename))
        if os.path.islink(absolute_path) or not os.path.isfile(absolute_path):
            if unreadable_sources is not None and os.path.islink(absolute_path):
                unreadable_sources.append((
                    service.to_config_relative_or_absolute(absolute_path, config_root),
                    reference_scan.SOURCE_REDIRECTED,
                ))
            continue
        paths.append(absolute_path)
    return paths


def _canonical_paths(service, paths: list[str], config_root: str) -> set[str]:
    canonical_paths: set[str] = set()
    for value in paths:
        stored_path = str(value or "").strip()
        if stored_path:
            resolved_path = service.resolve_config_path(stored_path, config_root)
            canonical_paths.add(service.canonical_path(resolved_path, config_root))
    return canonical_paths


def _collect_entries(
    service, config_root: str, referenced: set[str], protected: set[str],
) -> tuple[OrphanEntry, ...]:
    entries: list[OrphanEntry] = []
    for kind, directory, required_key, required_type in _CANDIDATE_SPECS:
        for absolute_path in _list_json_files(service, directory, config_root):
            state = _classify_candidate(
                service, absolute_path, config_root, referenced, protected,
                required_key, required_type,
            )
            entries.append(OrphanEntry(
                kind=kind,
                stored_path=service.to_config_relative_or_absolute(absolute_path, config_root),
                state=state,
            ))
    return tuple(entries)


def _classify_candidate(
    service,
    absolute_path: str,
    config_root: str,
    referenced: set[str],
    protected: set[str],
    required_key: str,
    required_type: type,
) -> str:
    canonical_path = service.canonical_path(absolute_path, config_root)
    if canonical_path in protected:
        return ORPHAN_PROTECTED
    if canonical_path in referenced:
        return ORPHAN_REFERENCED
    if not path_boundary.is_real_path_within(absolute_path, config_root):
        return ORPHAN_EXCLUDED
    data = service._load_optional_json(absolute_path)
    if not isinstance(data, dict) or not isinstance(data.get(required_key), required_type):
        return ORPHAN_EXCLUDED
    return ORPHAN_CANDIDATE
