from keyseq.application.config_service import contracts
from keyseq.presentation.child_kind_labels import kind_label
from keyseq.shared.i18n import tr


CLEANUP_EMPTY_MESSAGE: str = "reference_cleanup.empty"

_FAILURE_MESSAGES = {
    contracts.PRUNE_FAILURE_UNREADABLE: "reference_cleanup.failure_unreadable",
    contracts.PRUNE_FAILURE_INVALID_DATA: "reference_cleanup.failure_invalid_data",
    contracts.PRUNE_FAILURE_SAVE_FAILED: "reference_cleanup.failure_save_failed",
}


def format_cleanup_plan(
    inspections: list[contracts.ParentRefsCleanupInspection],
) -> tuple[str, ...]:
    """参照元の掃除で提示する行を組み立てる。"""
    if not inspections:
        return (tr("reference_cleanup.empty"),)

    target_count = sum(
        inspection.state in (contracts.CLEANUP_TARGET, contracts.CLEANUP_ALL_STALE)
        for inspection in inspections
    )
    stale_count = sum(len(inspection.stale_refs) for inspection in inspections)
    lines = [tr("reference_cleanup.target_and_stale_count", target_count=target_count,
                stale_count=stale_count)]
    for inspection in inspections:
        kind_text = kind_label(inspection.kind)
        stored_path = inspection.stored_path
        lines.append(tr("reference_cleanup.kind_path", kind=kind_text, path=stored_path))
        if inspection.state in (contracts.CLEANUP_TARGET, contracts.CLEANUP_ALL_STALE):
            lines.extend([tr("reference_cleanup.stale_refs_heading"),
                          *(tr("reference_cleanup.indented_path", path=path)
                            for path in inspection.stale_refs)])
        if inspection.protected_refs:
            lines.extend(
                [
                    tr("reference_cleanup.protected_refs_heading"),
                    *(tr("reference_cleanup.indented_path", path=path)
                      for path in inspection.protected_refs),
                ]
            )
        if inspection.state == contracts.CLEANUP_ALL_STALE:
            lines.extend(
                [
                    tr("reference_cleanup.no_refs_warning"),
                    tr("reference_cleanup.child_file_not_deleted"),
                ]
            )
    return tuple(lines)


def format_cleanup_result(result: contracts.ParentRefsPruneResult) -> tuple[str, ...]:
    """参照元の掃除の実行結果を通知用の行へ組み立てる。"""
    removed_count = sum(count for _, count in result.updated_files)
    updated_file_count = len(result.updated_files)
    lines = [
        tr("reference_cleanup.result_count", file_count=updated_file_count,
           removed_count=removed_count)
    ]
    if result.failed_files:
        lines.append(tr("reference_cleanup.failed_files_heading"))
        for path, reason in result.failed_files:
            reason_key = _FAILURE_MESSAGES.get(reason)
            reason_text = tr(reason_key) if reason_key is not None else tr("reference_cleanup.unknown_failure")
            lines.append(tr("reference_cleanup.path_reason", path=path, reason=reason_text))
    return tuple(lines)
