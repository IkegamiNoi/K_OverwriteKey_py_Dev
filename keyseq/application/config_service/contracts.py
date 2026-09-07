from __future__ import annotations

from dataclasses import dataclass


# parent_refs_cleanup
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


# reference_scan
SOURCE_MISSING = "missing"
SOURCE_UNREADABLE = "unreadable"
SOURCE_REDIRECTED = "redirected"
SOURCE_DIRECTORY_UNREADABLE = "directory_unreadable"


@dataclass(frozen=True)
class ReferenceScanResult:
    referenced: frozenset[str]
    unreadable_sources: tuple[tuple[str, str], ...]
    non_keymap_set_sources: tuple[str, ...]


# orphan_scan
ORPHAN_CANDIDATE = "candidate"
ORPHAN_REFERENCED = "referenced"
ORPHAN_PROTECTED = "protected"
ORPHAN_EXCLUDED = "excluded"
KIND_KEYMAP = "keymap"
KIND_TRIGGER_SET = "trigger_set"
KIND_SEQUENCE = "sequence"
KIND_HOTKEY_PRESETS = "hotkey_presets"


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


# quarantine
QUARANTINE_MANIFEST_WRITE_FAILED = "manifest_write_failed"
QUARANTINE_MOVE_FAILED = "move_failed"
QUARANTINE_UNIT_DIR_FAILED = "unit_dir_failed"
QUARANTINE_ROOT_REDIRECTED = "quarantine_root_redirected"
QUARANTINE_SOURCE_REJECTED = "source_rejected"


@dataclass(frozen=True)
class QuarantineResult:
    unit_id: str
    moved: tuple[tuple[str, str], ...]
    failed: tuple[tuple[str, str], ...]
    dropped_paths: tuple[str, ...]
    newly_orphan_count: int
    aborted_reason: str
    rescan_unreadable_sources: tuple[tuple[str, str], ...] = ()


# quarantine_manage
RESTORE_SKIPPED_EXISTS = "already_exists"
RESTORE_REJECTED_TARGET = "rejected_target"
RESTORE_SOURCE_MISSING = "source_missing"
RESTORE_FAILED = "restore_failed"
RESTORE_ABORTED_INVALID_ID = "invalid_unit_id"
RESTORE_ABORTED_NO_MANIFEST = "no_manifest"
DELETE_REJECTED_INVALID_ID = "invalid_unit_id"
DELETE_REJECTED_IS_ROOT = "is_quarantine_root"
DELETE_REJECTED_NO_MANIFEST = "no_manifest"
DELETE_FAILED = "delete_failed"


@dataclass(frozen=True)
class QuarantineUnit:
    unit_id: str
    created_at: str
    entry_count: int
    remaining_count: int
    manifest_valid: bool


@dataclass(frozen=True)
class QuarantineRestoreResult:
    unit_id: str
    restored: tuple[tuple[str, str], ...]
    skipped: tuple[tuple[str, str], ...]
    unit_removed: bool
    aborted_reason: str


@dataclass(frozen=True)
class QuarantineDeleteResult:
    unit_id: str
    deleted: bool
    aborted_reason: str
