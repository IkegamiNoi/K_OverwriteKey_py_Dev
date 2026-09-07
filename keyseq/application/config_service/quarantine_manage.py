from __future__ import annotations

import os
import shutil

from . import contracts
from . import candidate_dirs, path_boundary, quarantine


def _is_redirected(path: str) -> bool:
    """リンクとジャンクションを、走査・移動・後始末で辿らない。"""
    return (os.path.islink(path)
            or os.path.normcase(os.path.realpath(path)) != os.path.normcase(os.path.abspath(path)))


def _unit_directory(unit_id: str, config_root: str) -> str:
    if not isinstance(unit_id, str) or quarantine.UNIT_ID_PATTERN.fullmatch(unit_id) is None:
        return ""
    root = quarantine.quarantine_root(config_root)
    path = os.path.join(root, unit_id)
    try:
        if (os.path.isdir(path) and not _is_redirected(path)
                and path_boundary.is_real_path_within(path, root)):
            return path
    except (OSError, ValueError):
        return ""
    return ""


def _read_manifest(service, unit_dir: str) -> dict | None:
    path = os.path.join(unit_dir, quarantine.MANIFEST_FILE_NAME)
    try:
        if _is_redirected(path):
            return None
        manifest = service._load_optional_json(path)
    except (OSError, ValueError):
        return None
    if isinstance(manifest, dict) and isinstance(manifest.get("entries"), list):
        return manifest
    return None


def _entry_text(entry, key: str) -> str:
    value = entry.get(key) if isinstance(entry, dict) else None
    return value if isinstance(value, str) else ""


def _source_path(service, entry, config_root: str, unit_dir: str) -> str:
    stored = _entry_text(entry, "quarantined_path")
    if not stored.strip():
        return ""
    source = service.resolve_config_path(stored, config_root)
    manifest = os.path.join(unit_dir, quarantine.MANIFEST_FILE_NAME)
    if (not service.is_path_within(source, unit_dir, config_root)
            or service.canonical_path(source, config_root) in (
                service.canonical_path(unit_dir, config_root),
                service.canonical_path(manifest, config_root),
            ) or not path_boundary.is_real_path_within(source, unit_dir)
            or _is_redirected(source)):
        raise ValueError("quarantined_path is outside the unit or is redirected")
    return source


def _remaining_count(service, entries: list, config_root: str, unit_dir: str) -> int:
    remaining = 0
    for entry in entries:
        try:
            source = _source_path(service, entry, config_root, unit_dir)
            remaining += bool(source and os.path.exists(source))
        except (OSError, ValueError):
            # 不正な隔離パスは復元可能件数に含めない。復元時は理由コードで報告する。
            continue
    return remaining


def list_quarantine_units(service, *, config_root: str) -> tuple[contracts.QuarantineUnit, ...]:
    """実在する直下の実行単位を、マニフェスト不正も含めて昇順に返す。"""
    root = quarantine.quarantine_root(config_root)
    if not os.path.isdir(root) or _is_redirected(root):
        return ()
    units: list[contracts.QuarantineUnit] = []
    for unit_id in sorted(os.listdir(root)):
        unit_dir = _unit_directory(unit_id, config_root)
        if not unit_dir:
            continue
        manifest = _read_manifest(service, unit_dir)
        if manifest is None:
            units.append(contracts.QuarantineUnit(unit_id, "", 0, 0, False))
            continue
        entries = manifest["entries"]
        units.append(contracts.QuarantineUnit(
            unit_id, _entry_text(manifest, "created_at"), len(entries),
            _remaining_count(service, entries, config_root, unit_dir), True,
        ))
    return tuple(units)


def _target_is_allowed(service, target: str, config_root: str) -> bool:
    reserved = service.resolve_config_path(candidate_dirs.RESERVED_DIR, config_root)
    if not target or service.is_path_within(target, reserved, config_root):
        return False
    for stored_dir in candidate_dirs.CANDIDATE_DIRS:
        directory = service.resolve_config_path(stored_dir, config_root)
        if (service.is_path_within(target, directory, config_root)
                and service.canonical_path(target, config_root)
                != service.canonical_path(directory, config_root)
                and not _is_redirected(target)
                and path_boundary.is_real_path_within(target, directory)):
            return True
    return False


def _restore_entry(service, entry, config_root: str, unit_dir: str) -> str:
    """state は参照せず、実体・復元先・衝突の順で検査する。"""
    try:
        source = _source_path(service, entry, config_root, unit_dir)
        if not source or not os.path.exists(source):
            return contracts.RESTORE_SOURCE_MISSING
        target = service.resolve_config_path(_entry_text(entry, "original_path"), config_root)
        if not _target_is_allowed(service, target, config_root):
            return contracts.RESTORE_REJECTED_TARGET
        if os.path.lexists(target):
            return contracts.RESTORE_SKIPPED_EXISTS
        if not os.path.isfile(source):
            return contracts.RESTORE_FAILED
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.move(source, target)
    except (OSError, ValueError, shutil.Error):
        return contracts.RESTORE_FAILED
    return ""


def _empty_directories(unit_dir: str) -> list[str] | None:
    """未記載のファイルも残存扱いにし、リンクを辿らず空の木だけを認める。"""
    pending = [unit_dir]
    directories: list[str] = []
    manifest = os.path.join(unit_dir, quarantine.MANIFEST_FILE_NAME)
    while pending:
        directory = pending.pop()
        directories.append(directory)
        with os.scandir(directory) as entries:
            for entry in entries:
                if _is_redirected(entry.path):
                    return None
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                elif entry.path != manifest:
                    return None
    return directories


def _cleanup_unit(unit_dir: str) -> bool:
    try:
        directories = _empty_directories(unit_dir)
        if directories is None:
            return False
        # 空の子ディレクトリを先に片付け、失敗時はマニフェストを残す。
        for directory in reversed(directories[1:]):
            os.rmdir(directory)
        os.remove(os.path.join(unit_dir, quarantine.MANIFEST_FILE_NAME))
        os.rmdir(unit_dir)
    except (OSError, ValueError):
        return False
    return True


def restore_quarantine_unit(
    service, unit_id: str, *, config_root: str,
) -> contracts.QuarantineRestoreResult:
    """1 件ずつ戻し、部分失敗と後始末の結果を保存表記で返す。"""
    unit_dir = _unit_directory(unit_id, config_root)
    if not unit_dir:
        return contracts.QuarantineRestoreResult(unit_id, (), (), False, contracts.RESTORE_ABORTED_INVALID_ID)
    manifest = _read_manifest(service, unit_dir)
    if manifest is None:
        return contracts.QuarantineRestoreResult(unit_id, (), (), False, contracts.RESTORE_ABORTED_NO_MANIFEST)
    restored: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []
    for entry in manifest["entries"]:
        reason = _restore_entry(service, entry, config_root, unit_dir)
        original = _entry_text(entry, "original_path")
        if reason:
            skipped.append((original, reason))
        else:
            restored.append((_entry_text(entry, "kind"), original))
    return contracts.QuarantineRestoreResult(
        unit_id, tuple(restored), tuple(skipped), _cleanup_unit(unit_dir), "",
    )


def _delete_directory(service, unit_id: str, config_root: str) -> tuple[str, str]:
    """①②、③の順で検証する。manifest の許可で境界を緩和しない。"""
    if not isinstance(unit_id, str) or quarantine.UNIT_ID_PATTERN.fullmatch(unit_id) is None:
        return "", contracts.DELETE_REJECTED_INVALID_ID
    root = quarantine.quarantine_root(config_root)
    path = os.path.join(root, unit_id)
    try:
        if not os.path.isdir(path) or os.path.dirname(path) != root:
            return "", contracts.DELETE_REJECTED_INVALID_ID
        if (service.canonical_path(path, config_root) == service.canonical_path(root, config_root)
                or service.canonical_path(os.path.realpath(path), config_root)
                == service.canonical_path(os.path.realpath(root), config_root)
                or not path_boundary.is_real_path_within(path, root)
                or _is_redirected(root)):
            return "", contracts.DELETE_REJECTED_IS_ROOT
    except (OSError, ValueError):
        return "", contracts.DELETE_REJECTED_IS_ROOT
    return path, ""


def collect_unit_paths(service, unit_id: str, *, config_root: str) -> tuple[str, ...]:
    """全ファイルとリンク自体を stored 表記で列挙する。列挙失敗は送出する。"""
    unit_dir, reason = _delete_directory(service, unit_id, config_root)
    if reason:
        return ()
    paths: list[str] = []
    pending = [unit_dir]
    if _is_redirected(unit_dir):
        return (service.to_config_relative_or_absolute(unit_dir, config_root),)
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if not _is_redirected(entry.path) and entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                else:
                    paths.append(service.to_config_relative_or_absolute(entry.path, config_root))
    return tuple(sorted(paths))


def delete_quarantine_unit(
    service, unit_id: str, *, config_root: str, allow_invalid_manifest: bool = False,
) -> contracts.QuarantineDeleteResult:
    """ID から再検証し、通常削除する。リンクの参照先は削除しない。"""
    unit_dir, reason = _delete_directory(service, unit_id, config_root)
    if reason:
        return contracts.QuarantineDeleteResult(unit_id, False, reason)
    if _read_manifest(service, unit_dir) is None and not allow_invalid_manifest:
        return contracts.QuarantineDeleteResult(unit_id, False, contracts.DELETE_REJECTED_NO_MANIFEST)
    try:
        if os.path.islink(unit_dir):
            os.unlink(unit_dir)
        else:
            # Python 3.14 の rmtree は子の symlink / junction を辿らない。
            shutil.rmtree(unit_dir)
    except (OSError, ValueError, shutil.Error):
        return contracts.QuarantineDeleteResult(unit_id, False, contracts.DELETE_FAILED)
    try:
        os.rmdir(quarantine.quarantine_root(config_root))
    except OSError:
        # 他の単位が残る場合も含む。単位の削除成功とは分けて扱う。
        return contracts.QuarantineDeleteResult(unit_id, True, "")
    return contracts.QuarantineDeleteResult(unit_id, True, "")
