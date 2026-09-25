from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

from keyseq.domain.keymap_triggers import iter_trigger_sets
from . import contracts


def prune_parent_refs(
    service,
    inspections: list[contracts.ParentRefsCleanupInspection],
    *,
    runtime: Any,
    config_root: str,
    keymap_set_path: str,
) -> contracts.ParentRefsPruneResult:
    """検査済みの子JSONから、読み直し時点で陳腐化した参照元だけを除去する。"""
    updated_files: list[tuple[str, int]] = []
    failed_files: list[tuple[str, str]] = []
    for inspection in inspections:
        if inspection.state not in (contracts.CLEANUP_TARGET, contracts.CLEANUP_ALL_STALE):
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
    return contracts.ParentRefsPruneResult(
        updated_files=tuple(updated_files),
        failed_files=tuple(failed_files),
    )


def _prune_inspection(
    service,
    inspection: contracts.ParentRefsCleanupInspection,
    runtime: Any,
    *,
    config_root: str,
    keymap_set_path: str,
) -> tuple[int, str]:
    resolved_path = service.resolve_config_path(inspection.stored_path, config_root)
    data = service._load_optional_json(resolved_path)
    if data is None:
        return 0, contracts.PRUNE_FAILURE_UNREADABLE
    if not isinstance(data, dict):
        return 0, contracts.PRUNE_FAILURE_INVALID_DATA

    refs = service._normalize_parent_refs(data.get(service.PARENT_REFS_KEY))
    if refs is None:
        return 0, ""
    protected_paths = _protected_parent_path(
        service,
        inspection.kind,
        runtime,
        keymap_set_path,
        inspection.stored_path,
        config_root,
    )
    _, stale_refs, _ = _classify_parent_refs(
        service,
        refs,
        config_root=config_root,
        protected_paths=protected_paths,
    )
    if not stale_refs:
        return 0, ""

    data[service.PARENT_REFS_KEY] = [ref for ref in refs if ref not in stale_refs]
    try:
        service.repository.save_json(resolved_path, data)
    except Exception:
        return 0, contracts.PRUNE_FAILURE_SAVE_FAILED
    return len(stale_refs), ""


def inspect_parent_refs(
    service,
    runtime: Any,
    *,
    config_root: str,
    keymap_set_path: str,
) -> list[contracts.ParentRefsCleanupInspection]:
    """現在の runtime が参照する子の陳腐化した参照元を検査する。"""
    inspections: list[contracts.ParentRefsCleanupInspection] = []
    for kind, stored_path in _iter_child_paths(service, runtime, config_root):
        inspection = _inspect_child(
            service,
            kind,
            stored_path,
            runtime,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
        )
        if inspection.state != contracts.CLEANUP_SKIP:
            inspections.append(inspection)
    return inspections


def _iter_child_paths(service, runtime: Any, config_root: str):
    if not isinstance(runtime, dict):
        return
    seen_paths: set[str] = set()
    keymaps = runtime.get("keymaps")
    if isinstance(keymaps, list):
        for keymap in keymaps:
            if isinstance(keymap, dict):
                stored_path = _nonempty_path(
                    keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH)
                )
                if stored_path and _mark_child_path(
                    service, stored_path, config_root, seen_paths
                ):
                    yield "keymap", stored_path

    trigger_sets = list(iter_trigger_sets(runtime))
    for _, members, _ in trigger_sets:
        for keymap in members:
            stored_path = _nonempty_path(
                keymap.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH)
            )
            if stored_path and _mark_child_path(
                service, stored_path, config_root, seen_paths
            ):
                yield "trigger_set", stored_path
    for _, _, triggers in trigger_sets:
        for trigger in triggers:
            if isinstance(trigger, dict):
                stored_path = _nonempty_path(
                    trigger.get(service.INTERNAL_SEQUENCE_SOURCE_PATH)
                )
                if stored_path and _mark_child_path(
                    service, stored_path, config_root, seen_paths
                ):
                    yield "sequence", stored_path


def _mark_child_path(service, stored_path: str, config_root: str, seen_paths: set[str]) -> bool:
    canonical_path = service.canonical_path(stored_path, config_root)
    if not canonical_path or canonical_path in seen_paths:
        return False
    seen_paths.add(canonical_path)
    return True


def _inspect_child(
    service,
    kind: str,
    stored_path: str,
    runtime: Any,
    *,
    config_root: str,
    keymap_set_path: str,
) -> contracts.ParentRefsCleanupInspection:
    refs = service.read_parent_refs(
        service.resolve_config_path(stored_path, config_root)
    )
    if refs is None or refs == []:
        return contracts.ParentRefsCleanupInspection(
            kind=kind,
            stored_path=stored_path,
            alive_refs=(),
            stale_refs=(),
            protected_refs=(),
            state=contracts.CLEANUP_SKIP,
        )

    protected_paths = _protected_parent_path(
        service,
        kind,
        runtime,
        keymap_set_path,
        stored_path,
        config_root,
    )
    alive_refs, stale_refs, protected_refs = _classify_parent_refs(
        service,
        refs,
        config_root=config_root,
        protected_paths=protected_paths,
    )

    state = _cleanup_state(alive_refs, stale_refs, protected_refs)
    return contracts.ParentRefsCleanupInspection(
        kind=kind,
        stored_path=stored_path,
        alive_refs=tuple(alive_refs),
        stale_refs=tuple(stale_refs),
        protected_refs=tuple(protected_refs),
        state=state,
    )


def _protected_parent_path(
    service,
    kind: str,
    runtime: Any,
    keymap_set_path: str,
    child_path: str,
    config_root: str,
) -> tuple[str, ...]:
    if kind == "keymap":
        stored_path = _nonempty_path(keymap_set_path)
        return (stored_path,) if stored_path else ()
    if kind not in ("trigger_set", "sequence") or not isinstance(runtime, dict):
        return ()

    child_key = _canonical_path(service, child_path, config_root)
    parent_paths: list[str] = []
    for _, members, triggers in iter_trigger_sets(runtime):
        parent_paths.extend(
            _group_parent_paths(
                service, kind, members, triggers, child_key, config_root
            )
        )
    if kind == "trigger_set":
        parent_paths.append(_nonempty_path(keymap_set_path))
    return tuple(dict.fromkeys(path for path in parent_paths if path))


def _group_parent_paths(
    service,
    kind: str,
    members: list[dict[str, Any]],
    triggers: list[Any],
    child_key: str,
    config_root: str,
) -> tuple[str, ...]:
    if kind == "trigger_set":
        source_paths = (
            member.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH) for member in members
        )
        parent_key = service.INTERNAL_KEYMAP_SOURCE_PATH
    else:
        source_paths = (
            trigger.get(service.INTERNAL_SEQUENCE_SOURCE_PATH)
            for trigger in triggers if isinstance(trigger, dict)
        )
        parent_key = service.INTERNAL_TRIGGER_SET_SOURCE_PATH
    if not _contains_source_path(service, source_paths, child_key, config_root):
        return ()
    return tuple(_nonempty_path(member.get(parent_key)) for member in members)


def _contains_source_path(
    service,
    paths: Iterable[Any],
    child_key: str,
    config_root: str,
) -> bool:
    return any(
        _canonical_path(service, path, config_root) == child_key
        for path in paths
    )


def _canonical_path(service, path: Any, config_root: str) -> str:
    stored_path = _nonempty_path(path)
    if not stored_path:
        return ""
    resolved_path = service.resolve_config_path(stored_path, config_root)
    return service.canonical_path(resolved_path, config_root)


def _classify_parent_refs(
    service,
    refs: list[str],
    *,
    config_root: str,
    protected_paths: tuple[str, ...],
) -> tuple[list[str], list[str], list[str]]:
    protected_canonical_paths = {
        _canonical_path(service, path, config_root)
        for path in protected_paths
        if path
    }
    alive_refs: list[str] = []
    stale_refs: list[str] = []
    protected_refs: list[str] = []
    for ref in refs:
        resolved_ref = service.resolve_config_path(ref, config_root)
        if os.path.exists(resolved_ref):
            alive_refs.append(ref)
        elif (
            service.canonical_path(ref, config_root) in protected_canonical_paths
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
        return contracts.CLEANUP_ALL_STALE
    if stale_refs:
        return contracts.CLEANUP_TARGET
    if protected_refs:
        return contracts.CLEANUP_PROTECTED
    return contracts.CLEANUP_SKIP


def _nonempty_path(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value if value.strip() else ""
