from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime

from . import orphan_scan


QUARANTINE_DIR_NAME = "quarantine"
MANIFEST_FILE_NAME = "manifest.json"

ENTRY_PLANNED = "planned"
ENTRY_MOVED = "moved"
ENTRY_FAILED = "failed"

QUARANTINE_MANIFEST_WRITE_FAILED = "manifest_write_failed"
QUARANTINE_MOVE_FAILED = "move_failed"
QUARANTINE_UNIT_DIR_FAILED = "unit_dir_failed"
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


@dataclass(frozen=True)
class _PlannedMove:
    kind: str
    original_path: str
    source_path: str
    destination_path: str
    quarantined_path: str


def quarantine_orphans(
    service,
    presented_paths: list[str],
    *,
    config_root: str,
    scan_dirs: list[str],
    startup_keymap_set_path: str,
    current_keymap_set_path: str,
    protected_paths: list[str],
) -> QuarantineResult:
    """提示済みかつ再判定でも孤児の候補だけを、計画を先に残してから隔離する。"""
    entries, dropped_paths, newly_orphan_count, unreadable_sources = _select_targets(
        service,
        presented_paths,
        config_root=config_root,
        scan_dirs=scan_dirs,
        startup_keymap_set_path=startup_keymap_set_path,
        current_keymap_set_path=current_keymap_set_path,
        protected_paths=protected_paths,
    )
    unit_id, moved, failed, reason = _execute_quarantine(service, entries, config_root)
    return QuarantineResult(
        unit_id, moved, failed, dropped_paths, newly_orphan_count, reason, unreadable_sources,
    )


def _execute_quarantine(
    service, entries: tuple[orphan_scan.OrphanEntry, ...], config_root: str,
) -> tuple[str, tuple[tuple[str, str], ...], tuple[tuple[str, str], ...], str]:
    """対象があるときだけ実行単位と先行記録を作り、移動を実行する。"""
    if not entries:
        return "", (), (), ""
    created_at = _now()
    unit_id = _allocate_unit_id(config_root, created_at)
    unit_dir = os.path.join(_quarantine_root(config_root), unit_id)
    manifest_path = os.path.join(unit_dir, MANIFEST_FILE_NAME)
    moves = tuple(_plan_move(service, entry, config_root, unit_dir) for entry in entries)
    states = [ENTRY_PLANNED] * len(moves)
    reason = _prepare_unit_dir(service, manifest_path, created_at, moves, states)
    if reason:
        return "", (), (), reason
    moved, failed = _apply_moves(
        service, moves, states,
        manifest_path=manifest_path, created_at=created_at, config_root=config_root,
    )
    return unit_id, moved, failed, ""


def _select_targets(
    service,
    presented_paths: list[str],
    *,
    config_root: str,
    **scan_arguments,
) -> tuple[
    tuple[orphan_scan.OrphanEntry, ...], tuple[str, ...], int, tuple[tuple[str, str], ...],
]:
    """隔離直前に走査をやり直し、提示済みかつ再判定でも候補のものだけへ絞る。"""
    result = orphan_scan.scan_orphans(service, config_root=config_root, **scan_arguments)
    candidates = {
        _canonical(service, entry.stored_path, config_root): entry
        for entry in result.entries
        if entry.state == orphan_scan.ORPHAN_CANDIDATE
    }
    entries: list[orphan_scan.OrphanEntry] = []
    dropped_paths: list[str] = []
    presented: set[str] = set()
    for value in presented_paths or ():
        stored_path = str(value or "").strip()
        if not stored_path:
            continue
        canonical = _canonical(service, stored_path, config_root)
        if canonical in presented:
            continue
        presented.add(canonical)
        entry = candidates.get(canonical)
        if entry is None:
            dropped_paths.append(stored_path)
        else:
            entries.append(entry)
    newly_orphan_count = sum(canonical not in presented for canonical in candidates)
    return tuple(entries), tuple(dropped_paths), newly_orphan_count, result.unreadable_sources


def _canonical(service, stored_path: str, config_root: str) -> str:
    return service.canonical_path(
        service.resolve_config_path(stored_path, config_root), config_root,
    )


def _now() -> datetime:
    return datetime.now()


def _quarantine_root(config_root: str) -> str:
    return os.path.join(os.path.abspath(config_root), QUARANTINE_DIR_NAME)


def _allocate_unit_id(config_root: str, created_at: datetime) -> str:
    """同じ秒に実行しても既存の実行単位を上書きしないよう連番を付す。"""
    root = _quarantine_root(config_root)
    base = created_at.strftime("%Y%m%d_%H%M%S")
    unit_id = base
    index = 2
    while os.path.exists(os.path.join(root, unit_id)):
        unit_id = f"{base}_{index}"
        index += 1
    return unit_id


def _plan_move(
    service, entry: orphan_scan.OrphanEntry, config_root: str, unit_dir: str,
) -> _PlannedMove:
    """元の相対構造を保った移動先を決める。config 外なら移動先を持たせない。"""
    source_path = service.resolve_config_path(entry.stored_path, config_root)
    relative_path = _relative_to_config_root(service, source_path, config_root)
    destination_path = os.path.join(unit_dir, relative_path) if relative_path else ""
    return _PlannedMove(
        kind=entry.kind,
        original_path=entry.stored_path,
        source_path=source_path,
        destination_path=destination_path,
        quarantined_path=(
            service.to_config_relative_or_absolute(destination_path, config_root)
            if destination_path else ""
        ),
    )


def _relative_to_config_root(service, path: str, config_root: str) -> str:
    if not service.is_path_within(path, config_root, config_root):
        return ""
    return os.path.relpath(os.path.abspath(path), os.path.abspath(config_root))


def _write_manifest(
    service,
    manifest_path: str,
    created_at: datetime,
    moves: tuple[_PlannedMove, ...],
    states: list[str],
) -> None:
    service.repository.save_json(manifest_path, {
        "created_at": created_at.isoformat(timespec="seconds"),
        "entries": [
            {
                "kind": move.kind,
                "original_path": move.original_path,
                "quarantined_path": move.quarantined_path,
                "state": state,
            }
            for move, state in zip(moves, states)
        ],
    })


def _try_write_manifest(
    service,
    manifest_path: str,
    created_at: datetime,
    moves: tuple[_PlannedMove, ...],
    states: list[str],
) -> bool:
    """記録の成否を返し、中止するか継続するかは呼び出し側が決める。"""
    try:
        _write_manifest(service, manifest_path, created_at, moves, states)
    except Exception:
        return False
    return True


def _prepare_unit_dir(
    service, manifest_path: str, created_at: datetime,
    moves: tuple[_PlannedMove, ...], states: list[str],
) -> str:
    """既存単位を上書きせず、移動前の記録を作成する。"""
    unit_dir = os.path.dirname(manifest_path)
    try:
        os.makedirs(unit_dir, exist_ok=False)
    except OSError:
        return QUARANTINE_UNIT_DIR_FAILED
    if _try_write_manifest(service, manifest_path, created_at, moves, states):
        return ""
    if _discard_manifest_tmp(manifest_path):
        _discard_empty_unit_dir(unit_dir)
    return QUARANTINE_MANIFEST_WRITE_FAILED


def _discard_manifest_tmp(manifest_path: str) -> bool:
    """先行記録の一時ファイルを best-effort で除去し、成否を返す。"""
    try:
        os.remove(f"{manifest_path}.tmp")
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def _discard_empty_unit_dir(unit_dir: str) -> None:
    """1 件も動かさずに中止したときだけ、空になったディレクトリを残さない。"""
    for directory in (unit_dir, os.path.dirname(unit_dir)):
        try:
            os.rmdir(directory)
        except OSError:
            return


def _apply_moves(
    service,
    moves: tuple[_PlannedMove, ...],
    states: list[str],
    *,
    manifest_path: str,
    created_at: datetime,
    config_root: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    """1 件ずつ移動し、失敗しても継続してマニフェストへ進捗を残す。"""
    moved: list[tuple[str, str]] = []
    failed: list[tuple[str, str]] = []
    manifest_write_failed = False
    for index, move in enumerate(moves):
        reason = _move_file(move, config_root)
        states[index] = ENTRY_FAILED if reason else ENTRY_MOVED
        if reason:
            failed.append((move.original_path, reason))
        else:
            moved.append((move.kind, move.original_path))
        if not _try_write_manifest(service, manifest_path, created_at, moves, states):
            manifest_write_failed = True
    if manifest_write_failed:
        failed.append((
            service.to_config_relative_or_absolute(manifest_path, config_root),
            QUARANTINE_MANIFEST_WRITE_FAILED,
        ))
    return tuple(moved), tuple(failed)


def _is_real_path_within(path: str, root: str) -> bool:
    """realpath で実体解決したうえで root 配下かを判定する。"""
    try:
        real_path = os.path.normcase(os.path.realpath(path))
        real_root = os.path.normcase(os.path.realpath(root))
        return os.path.commonpath((real_path, real_root)) == real_root
    except (OSError, ValueError):
        return False


def _source_is_allowed(source: str, config_root: str) -> bool:
    try:
        return (os.path.isfile(source) and not os.path.islink(source)
                and _is_real_path_within(source, config_root))
    except (OSError, ValueError):
        return False


def _move_file(move: _PlannedMove, config_root: str) -> str:
    """移動できなければ理由コードを返す（成功時は空文字）。"""
    if not move.destination_path:
        return QUARANTINE_MOVE_FAILED
    try:
        os.makedirs(os.path.dirname(move.destination_path), exist_ok=True)
        if not _source_is_allowed(move.source_path, config_root):
            return QUARANTINE_SOURCE_REJECTED
        shutil.move(move.source_path, move.destination_path)
    except (OSError, shutil.Error):
        return QUARANTINE_MOVE_FAILED
    return ""
