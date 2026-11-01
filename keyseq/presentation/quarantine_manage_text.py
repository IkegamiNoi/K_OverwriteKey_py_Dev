from collections import Counter

from keyseq.application.config_service import contracts
from keyseq.shared.i18n import tr


_REASON_LABELS = {
    contracts.RESTORE_SKIPPED_EXISTS: "quarantine_manage.restore_skipped_exists",
    contracts.RESTORE_REJECTED_TARGET: "quarantine_manage.restore_rejected_target",
    contracts.RESTORE_SOURCE_MISSING: "quarantine_manage.restore_source_missing",
    contracts.RESTORE_FAILED: "quarantine_manage.restore_failed",
    contracts.RESTORE_ABORTED_INVALID_ID: "quarantine_manage.restore_aborted_invalid_id",
    contracts.RESTORE_ABORTED_NO_MANIFEST: "quarantine_manage.restore_aborted_no_manifest",
}


def _reason_label(reason: str) -> str:
    key = _REASON_LABELS.get(reason)
    return tr(key) if key is not None else reason


def format_unit_list(units: tuple[contracts.QuarantineUnit, ...]) -> tuple[str, ...]:
    """実行単位の表示行を、入力と同じ順で返す。"""
    lines: list[str] = []
    for unit in units:
        unit_id = unit.unit_id
        created_at = unit.created_at
        remaining = unit.remaining_count
        total = unit.entry_count
        key = ("quarantine_manage.unit_list_line"
               if unit.manifest_valid else "quarantine_manage.unit_list_line_invalid")
        lines.append(tr(key, unit_id=unit_id, created_at=created_at,
                        remaining=remaining, total=total))
    return tuple(lines)


def format_restore_plan(unit: contracts.QuarantineUnit) -> tuple[str, ...]:
    """確認用に実行単位と実体の残数、同名ファイルの扱いを示す。"""
    remaining_count = unit.remaining_count
    return (
        *format_unit_list((unit,)),
        tr("quarantine_manage.restore_plan_count", count=remaining_count),
        tr("quarantine_manage.restore_plan_no_overwrite"),
    )


def format_restore_result(result: contracts.QuarantineRestoreResult) -> tuple[str, ...]:
    """実績と理由別件数を示し、保存表記のまま各ファイルを列挙する。"""
    lines: list[str] = []
    if result.aborted_reason:
        reason = _reason_label(result.aborted_reason)
        lines.extend((tr("quarantine_manage.restore_aborted", reason=reason),
                      tr("quarantine_manage.restore_aborted_no_files")))
    restored_count = len(result.restored)
    lines.append(tr("quarantine_manage.restore_succeeded", count=restored_count))
    lines.extend(tr("quarantine_manage.indented_path", path=path) for _kind, path in result.restored)
    counts = Counter(reason for _path, reason in result.skipped)
    skipped_count = len(result.skipped)
    lines.append(tr("quarantine_manage.skipped_count", count=skipped_count))
    for reason, count in counts.items():
        reason_text = _reason_label(reason)
        lines.append(tr("quarantine_manage.reason_count", reason=reason_text, count=count))
    for path, reason in result.skipped:
        reason_text = _reason_label(reason)
        lines.append(tr("quarantine_manage.path_reason", path=path, reason=reason_text))
    lines.append(tr("quarantine_manage.unit_removed") if result.unit_removed
                 else tr("quarantine_manage.unit_remaining"))
    return tuple(lines)


def format_delete_plan(
    unit: contracts.QuarantineUnit, paths: tuple[str, ...], *, manifest_valid: bool,
) -> tuple[str, ...]:
    """不可逆の警告と全件を、保存表記のまま提示する。"""
    unit_id = unit.unit_id
    lines = [tr("quarantine_manage.delete_irreversible"),
             tr("quarantine_manage.delete_unit", unit_id=unit_id)]
    if not manifest_valid:
        lines.extend((tr("quarantine_manage.delete_manifest_unreadable"),
                      tr("quarantine_manage.delete_entire_folder")))
    lines.extend(tr("quarantine_manage.indented_path", path=path) for path in paths)
    return tuple(lines)


def format_delete_result(result: contracts.QuarantineDeleteResult) -> tuple[str, ...]:
    """拒否と I/O の部分失敗を区別し、未知コードも表示する。"""
    if result.deleted:
        unit_id = result.unit_id
        return (tr("quarantine_manage.delete_succeeded", unit_id=unit_id),)
    labels = {
        contracts.DELETE_REJECTED_INVALID_ID: "quarantine_manage.delete_rejected_invalid_id",
        contracts.DELETE_REJECTED_IS_ROOT: "quarantine_manage.delete_rejected_is_root",
        contracts.DELETE_REJECTED_NO_MANIFEST: "quarantine_manage.delete_rejected_no_manifest",
        contracts.DELETE_FAILED: "quarantine_manage.delete_failed",
    }
    key = labels.get(result.aborted_reason)
    reason = tr(key) if key is not None else result.aborted_reason
    notice = (tr("quarantine_manage.delete_partial_warning")
              if result.aborted_reason == contracts.DELETE_FAILED
              else tr("quarantine_manage.delete_not_performed"))
    return (tr("quarantine_manage.delete_aborted", reason=reason), notice)
