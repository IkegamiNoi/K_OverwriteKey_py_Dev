from keyseq.application.config_service import contracts
from keyseq.presentation.child_kind_labels import KIND_LABELS
from keyseq.shared.i18n import tr


ORPHAN_SWEEP_EMPTY_MESSAGE: str = "orphan_sweep.empty"

_KIND_LABELS = {
    **KIND_LABELS,
    contracts.KIND_HOTKEY_PRESETS: "child_kind.hotkey_presets",
}

_SOURCE_REASON_LABELS = {
    contracts.SOURCE_MISSING: "orphan_sweep.source_missing",
    contracts.SOURCE_UNREADABLE: "orphan_sweep.source_unreadable",
    contracts.SOURCE_REDIRECTED: "orphan_sweep.source_redirected",
    contracts.SOURCE_DIRECTORY_UNREADABLE: "orphan_sweep.source_directory_unreadable",
}

_QUARANTINE_REASON_LABELS = {
    contracts.QUARANTINE_MANIFEST_WRITE_FAILED: "orphan_sweep.quarantine_manifest_write_failed",
    contracts.QUARANTINE_MOVE_FAILED: "orphan_sweep.quarantine_move_failed",
    contracts.QUARANTINE_SOURCE_REJECTED: "orphan_sweep.quarantine_source_rejected",
    contracts.QUARANTINE_UNIT_DIR_FAILED: "orphan_sweep.quarantine_unit_dir_failed",
    contracts.QUARANTINE_ROOT_REDIRECTED: "orphan_sweep.quarantine_root_redirected",
}

SCAN_SCOPE_NOTE: str = "orphan_sweep.scan_scope_note"


def _label(labels: dict[str, str], value: str) -> str:
    key = labels.get(value)
    return tr(key) if key is not None else value


def _kind_path(kind: str, path: str) -> str:
    kind_text = _label(_KIND_LABELS, kind)
    return tr("orphan_sweep.kind_path", kind=kind_text, path=path)


def _path_reason(path: str, reason: str, labels: dict[str, str]) -> str:
    reason_text = _label(labels, reason)
    return tr("orphan_sweep.path_reason", path=path, reason=reason_text)


def format_scan_warnings(result: contracts.OrphanScanResult) -> tuple[str, ...]:
    """走査の不完全性を、読めなかった参照側の警告から順に示す。"""
    lines: list[str] = []
    if result.unreadable_sources:
        unreadable_count = len(result.unreadable_sources)
        lines.extend((
            tr("orphan_sweep.unreadable_sources_warning", count=unreadable_count),
            tr("orphan_sweep.possible_orphan_misclassification"),
        ))
        lines.extend(
            _path_reason(path, reason, _SOURCE_REASON_LABELS)
            for path, reason in result.unreadable_sources
        )
    if result.missing_scan_dirs:
        missing_count = len(result.missing_scan_dirs)
        lines.append(tr("orphan_sweep.missing_scan_dirs", count=missing_count))
        lines.extend(tr("orphan_sweep.indented_path", path=path) for path in result.missing_scan_dirs)
    if result.non_keymap_set_sources:
        source_count = len(result.non_keymap_set_sources)
        lines.append(tr("orphan_sweep.unrecognized_json_count", count=source_count))
    lines.append(tr(SCAN_SCOPE_NOTE))
    return tuple(lines)


def format_orphan_plan(result: contracts.OrphanScanResult) -> tuple[str, ...]:
    """警告に続けて、孤児候補だけを保存表記で列挙する。"""
    candidates = [entry for entry in result.entries if entry.state == contracts.ORPHAN_CANDIDATE]
    candidate_count = len(candidates)
    lines = [*format_scan_warnings(result), tr("orphan_sweep.candidate_count", count=candidate_count)]
    lines.extend(
        _kind_path(entry.kind, entry.stored_path)
        for entry in candidates
    )
    excluded_count = sum(entry.state == contracts.ORPHAN_EXCLUDED for entry in result.entries)
    if excluded_count:
        lines.append(tr("orphan_sweep.excluded_count", count=excluded_count))
    return tuple(lines)


def format_orphan_notice(result: contracts.OrphanScanResult) -> tuple[str, ...]:
    """候補がない場合も、走査範囲と読めなかった参照側を通知する。"""
    return (tr(ORPHAN_SWEEP_EMPTY_MESSAGE), *format_scan_warnings(result))


def format_quarantine_result(result: contracts.QuarantineResult) -> tuple[str, ...]:
    """隔離の実行結果を、中止か実績かを先頭に置いて通知用の行へ組み立てる。"""
    lines = [*_format_rescan_warnings(result), *_format_quarantine_headline(result)]
    lines.extend(_format_quarantine_failures(result))
    if result.dropped_paths:
        dropped_count = len(result.dropped_paths)
        lines.append(tr("orphan_sweep.dropped_paths_count", count=dropped_count))
    if result.newly_orphan_count:
        newly_orphan_count = result.newly_orphan_count
        lines.append(tr("orphan_sweep.newly_orphan_count", count=newly_orphan_count))
    return tuple(lines)


def _format_rescan_warnings(result: contracts.QuarantineResult) -> tuple[str, ...]:
    if not result.rescan_unreadable_sources:
        return ()
    unreadable_count = len(result.rescan_unreadable_sources)
    return (
        tr("orphan_sweep.rescan_unreadable_sources_warning", count=unreadable_count),
        tr("orphan_sweep.possible_orphan_misclassification"),
        *(_path_reason(path, reason, _SOURCE_REASON_LABELS)
          for path, reason in result.rescan_unreadable_sources),
    )


def _format_quarantine_failures(result: contracts.QuarantineResult) -> tuple[str, ...]:
    move_failures = [(path, reason) for path, reason in result.failed
                     if reason != contracts.QUARANTINE_MANIFEST_WRITE_FAILED]
    manifest_failures = [path for path, reason in result.failed
                         if reason == contracts.QUARANTINE_MANIFEST_WRITE_FAILED]
    lines: list[str] = []
    if move_failures:
        lines.append(tr("orphan_sweep.quarantine_failed_files"))
        for path, reason in move_failures:
            lines.append(_path_reason(path, reason, _QUARANTINE_REASON_LABELS))
    if manifest_failures:
        lines.append(tr("orphan_sweep.manifest_write_warning"))
        manifest_reason_key = _QUARANTINE_REASON_LABELS[contracts.QUARANTINE_MANIFEST_WRITE_FAILED]
        manifest_reason = tr(manifest_reason_key)
        for path in manifest_failures:
            lines.append(tr("orphan_sweep.path_reason", path=path, reason=manifest_reason))
    return tuple(lines)


def _format_quarantine_headline(result: contracts.QuarantineResult) -> tuple[str, ...]:
    unit_id = result.unit_id
    if result.aborted_reason:
        reason = _label(_QUARANTINE_REASON_LABELS, result.aborted_reason)
        return (tr("orphan_sweep.quarantine_aborted", reason=reason),
                tr("orphan_sweep.quarantine_aborted_no_files"))
    if not result.moved and result.failed:
        if unit_id:
            return (tr("orphan_sweep.quarantine_failed_zero_with_unit", unit_id=unit_id),)
        return (tr("orphan_sweep.quarantine_failed_zero"),)
    moved_count = len(result.moved)
    if unit_id:
        headline = tr("orphan_sweep.quarantine_succeeded_with_unit", count=moved_count,
                      unit_id=unit_id)
    else:
        headline = tr("orphan_sweep.quarantine_succeeded", count=moved_count)
    return (
        headline,
        *(_kind_path(kind, path) for kind, path in result.moved),
    )
