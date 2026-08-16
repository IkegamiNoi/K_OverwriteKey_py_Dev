from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


CLEANUP_TARGET = "target"
CLEANUP_ALL_STALE = "all_stale"
CLEANUP_PROTECTED = "protected"
CLEANUP_SKIP = "skip"

PRUNE_FAILURE_UNREADABLE = "unreadable"
PRUNE_FAILURE_INVALID_DATA = "invalid_data"
PRUNE_FAILURE_SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class ParentRefsCleanupInspection:
    kind: str
    stored_path: str
    alive_refs: tuple[str, ...]
    stale_refs: tuple[str, ...]
    protected_refs: tuple[str, ...]
    state: str


@dataclass(frozen=True)
class ParentRefsPruneResult:
    updated_files: tuple[tuple[str, int], ...]
    failed_files: tuple[tuple[str, str], ...]


def prune_parent_refs(
    service,
    inspections: list[ParentRefsCleanupInspection],
    *,
    runtime: Any,
    config_root: str,
    keymap_set_path: str,
) -> ParentRefsPruneResult:
    """検査済みの子JSONから、読み直し時点で陳腐化した参照元だけを除去する。"""
    updated_files: list[tuple[str, int]] = []
    failed_files: list[tuple[str, str]] = []
    for inspection in inspections:
        if inspection.state not in (CLEANUP_TARGET, CLEANUP_ALL_STALE):
            continue
        removed_count, failure_reason = _prune_inspection(
            service,
            inspection,
            runtime,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
        )
        if failure_reason:
            failed_files.append((inspection.stored_path, failure_reason))
        elif removed_count:
            updated_files.append((inspection.stored_path, removed_count))
    return ParentRefsPruneResult(
        updated_files=tuple(updated_files),
        failed_files=tuple(failed_files),
    )


def _prune_inspection(
    service,
    inspection: ParentRefsCleanupInspection,
    runtime: Any,
    *,
    config_root: str,
    keymap_set_path: str,
) -> tuple[int, str]:
    resolved_path = service.resolve_config_path(inspection.stored_path, config_root)
    data = service._load_optional_json(resolved_path)
    if data is None:
        return 0, PRUNE_FAILURE_UNREADABLE
    if not isinstance(data, dict):
        return 0, PRUNE_FAILURE_INVALID_DATA

    refs = service._normalize_parent_refs(data.get(service.PARENT_REFS_KEY))
    if refs is None:
        return 0, ""
    protected_path = _protected_parent_path(
        service,
        inspection.kind,
        runtime,
        keymap_set_path,
    )
    _, stale_refs, _ = _classify_parent_refs(
        service,
        refs,
        config_root=config_root,
        protected_path=protected_path,
    )
    if not stale_refs:
        return 0, ""

    data[service.PARENT_REFS_KEY] = [ref for ref in refs if ref not in stale_refs]
    try:
        service.repository.save_json(resolved_path, data)
    except Exception:
        return 0, PRUNE_FAILURE_SAVE_FAILED
    return len(stale_refs), ""


def inspect_parent_refs(
    service,
    runtime: Any,
    *,
    config_root: str,
    keymap_set_path: str,
) -> list[ParentRefsCleanupInspection]:
    """現在の runtime が参照する子の陳腐化した参照元を検査する。"""
    inspections: list[ParentRefsCleanupInspection] = []
    seen_paths: set[str] = set()
    for kind, stored_path in _iter_child_paths(service, runtime):
        canonical_stored_path = service.canonical_path(stored_path, config_root)
        if not canonical_stored_path or canonical_stored_path in seen_paths:
            continue
        seen_paths.add(canonical_stored_path)
        inspection = _inspect_child(
            service,
            kind,
            stored_path,
            runtime,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
        )
        if inspection.state != CLEANUP_SKIP:
            inspections.append(inspection)
    return inspections


def _iter_child_paths(service, runtime: Any):
    if not isinstance(runtime, dict):
        return
    keymaps = runtime.get("keymaps")
    if isinstance(keymaps, list):
        for keymap in keymaps:
            if isinstance(keymap, dict):
                stored_path = _nonempty_path(
                    keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH)
                )
                if stored_path:
                    yield "keymap", stored_path

    stored_path = _nonempty_path(runtime.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH))
    if stored_path:
        yield "trigger_set", stored_path

    triggers = runtime.get("triggers")
    if isinstance(triggers, list):
        for trigger in triggers:
            if isinstance(trigger, dict):
                stored_path = _nonempty_path(
                    trigger.get(service.INTERNAL_SEQUENCE_SOURCE_PATH)
                )
                if stored_path:
                    yield "sequence", stored_path


def _inspect_child(
    service,
    kind: str,
    stored_path: str,
    runtime: Any,
    *,
    config_root: str,
    keymap_set_path: str,
) -> ParentRefsCleanupInspection:
    refs = service.read_parent_refs(
        service.resolve_config_path(stored_path, config_root)
    )
    if refs is None or refs == []:
        return ParentRefsCleanupInspection(
            kind=kind,
            stored_path=stored_path,
            alive_refs=(),
            stale_refs=(),
            protected_refs=(),
            state=CLEANUP_SKIP,
        )

    protected_path = _protected_parent_path(
        service,
        kind,
        runtime,
        keymap_set_path,
    )
    alive_refs, stale_refs, protected_refs = _classify_parent_refs(
        service,
        refs,
        config_root=config_root,
        protected_path=protected_path,
    )

    state = _cleanup_state(alive_refs, stale_refs, protected_refs)
    return ParentRefsCleanupInspection(
        kind=kind,
        stored_path=stored_path,
        alive_refs=tuple(alive_refs),
        stale_refs=tuple(stale_refs),
        protected_refs=tuple(protected_refs),
        state=state,
    )


def _protected_parent_path(service, kind: str, runtime: Any, keymap_set_path: str) -> str:
    if kind in ("keymap", "trigger_set"):
        return _nonempty_path(keymap_set_path)
    if kind == "sequence" and isinstance(runtime, dict):
        return _nonempty_path(runtime.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH))
    return ""


def _classify_parent_refs(
    service,
    refs: list[str],
    *,
    config_root: str,
    protected_path: str,
) -> tuple[list[str], list[str], list[str]]:
    protected_canonical_path = (
        service.canonical_path(protected_path, config_root)
        if protected_path
        else ""
    )
    alive_refs: list[str] = []
    stale_refs: list[str] = []
    protected_refs: list[str] = []
    for ref in refs:
        resolved_ref = service.resolve_config_path(ref, config_root)
        if os.path.exists(resolved_ref):
            alive_refs.append(ref)
        elif (
            protected_canonical_path
            and service.canonical_path(ref, config_root) == protected_canonical_path
        ):
            protected_refs.append(ref)
        else:
            stale_refs.append(ref)
    return alive_refs, stale_refs, protected_refs


def _cleanup_state(
    alive_refs: list[str],
    stale_refs: list[str],
    protected_refs: list[str],
) -> str:
    if stale_refs and not alive_refs and not protected_refs:
        return CLEANUP_ALL_STALE
    if stale_refs:
        return CLEANUP_TARGET
    if protected_refs:
        return CLEANUP_PROTECTED
    return CLEANUP_SKIP


def _nonempty_path(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value if value.strip() else ""
