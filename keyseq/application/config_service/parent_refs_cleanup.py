from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


CLEANUP_TARGET = "target"
CLEANUP_ALL_STALE = "all_stale"
CLEANUP_PROTECTED = "protected"
CLEANUP_SKIP = "skip"


@dataclass(frozen=True)
class ParentRefsCleanupInspection:
    kind: str
    stored_path: str
    alive_refs: tuple[str, ...]
    stale_refs: tuple[str, ...]
    protected_refs: tuple[str, ...]
    state: str


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
