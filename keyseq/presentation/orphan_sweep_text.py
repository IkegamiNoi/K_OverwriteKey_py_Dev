from keyseq.application.config_service.orphan_scan import (
    KIND_HOTKEY_PRESETS,
    KIND_KEYMAP,
    KIND_SEQUENCE,
    KIND_TRIGGER_SET,
    ORPHAN_CANDIDATE,
    ORPHAN_EXCLUDED,
    OrphanScanResult,
)
from keyseq.application.config_service.quarantine import (
    QUARANTINE_MANIFEST_WRITE_FAILED,
    QUARANTINE_MOVE_FAILED,
    QUARANTINE_SOURCE_REJECTED,
    QUARANTINE_UNIT_DIR_FAILED,
    QuarantineResult,
)
from keyseq.application.config_service.reference_scan import SOURCE_MISSING, SOURCE_UNREADABLE


ORPHAN_SWEEP_EMPTY_MESSAGE: str = "隔離できる孤児ファイルはありません。"

_KIND_LABELS = {
    KIND_KEYMAP: "キーマップ",
    KIND_TRIGGER_SET: "トリガー一覧",
    KIND_SEQUENCE: "出力シーケンス",
    KIND_HOTKEY_PRESETS: "個別プリセット",
}

_SOURCE_REASON_LABELS = {
    SOURCE_MISSING: "ファイルが見つかりません",
    SOURCE_UNREADABLE: "読み取り / JSON 解析に失敗しました",
}

_QUARANTINE_REASON_LABELS = {
    QUARANTINE_MANIFEST_WRITE_FAILED: "マニフェストを書き込めませんでした",
    QUARANTINE_MOVE_FAILED: "移動できませんでした",
    QUARANTINE_SOURCE_REJECTED: "移動直前の安全確認で対象外になりました",
    QUARANTINE_UNIT_DIR_FAILED: "隔離の実行単位ディレクトリを作成できませんでした",
}

SCAN_SCOPE_NOTE: str = (
    "注意: 走査範囲外に保存された構成セットから参照されている可能性があります。"
)


def format_scan_warnings(result: OrphanScanResult) -> tuple[str, ...]:
    """走査の不完全性を、読めなかった参照側の警告から順に示す。"""
    lines: list[str] = []
    if result.unreadable_sources:
        lines.extend((
            f"警告: 読めなかった構成セット / トリガー一覧が {len(result.unreadable_sources)} 件あります。",
            "それらが参照していた子ファイルを孤児と誤判定している可能性があります。",
        ))
        lines.extend(
            f"  {path}: {_SOURCE_REASON_LABELS.get(reason, reason)}"
            for path, reason in result.unreadable_sources
        )
    if result.missing_scan_dirs:
        lines.append(f"見つからなかった走査ディレクトリ: {len(result.missing_scan_dirs)} 件")
        lines.extend(f"  {path}" for path in result.missing_scan_dirs)
    if result.non_keymap_set_sources:
        lines.append(f"構成セットとして解釈できなかった JSON: {len(result.non_keymap_set_sources)} 件")
    lines.append(SCAN_SCOPE_NOTE)
    return tuple(lines)


def format_orphan_plan(result: OrphanScanResult) -> tuple[str, ...]:
    """警告に続けて、孤児候補だけを保存表記で列挙する。"""
    candidates = [entry for entry in result.entries if entry.state == ORPHAN_CANDIDATE]
    lines = [*format_scan_warnings(result), f"孤児候補: {len(candidates)} 件"]
    lines.extend(
        f"{_KIND_LABELS.get(entry.kind, entry.kind)}: {entry.stored_path}"
        for entry in candidates
    )
    excluded_count = sum(entry.state == ORPHAN_EXCLUDED for entry in result.entries)
    if excluded_count:
        lines.append(f"対象外: {excluded_count} 件")
    return tuple(lines)


def format_orphan_notice(result: OrphanScanResult) -> tuple[str, ...]:
    """候補がない場合も、走査範囲と読めなかった参照側を通知する。"""
    return (ORPHAN_SWEEP_EMPTY_MESSAGE, *format_scan_warnings(result))


def format_quarantine_result(result: QuarantineResult) -> tuple[str, ...]:
    """隔離の実行結果を、中止か実績かを先頭に置いて通知用の行へ組み立てる。"""
    lines = [*_format_rescan_warnings(result), *_format_quarantine_headline(result)]
    lines.extend(_format_quarantine_failures(result))
    if result.dropped_paths:
        lines.append(f"提示後に対象外になったため隔離しなかった: {len(result.dropped_paths)} 件")
    if result.newly_orphan_count:
        lines.append(
            "再判定で新たに孤児候補になったため今回は隔離しなかった: "
            f"{result.newly_orphan_count} 件"
        )
    return tuple(lines)


def _format_rescan_warnings(result: QuarantineResult) -> tuple[str, ...]:
    if not result.rescan_unreadable_sources:
        return ()
    return (
        f"警告: 隔離の直前にも読めない参照側が {len(result.rescan_unreadable_sources)} 件ありました。",
        "それらが参照していた子ファイルを孤児と誤判定している可能性があります。",
        *(f"  {path}: {_SOURCE_REASON_LABELS.get(reason, reason)}"
          for path, reason in result.rescan_unreadable_sources),
    )


def _format_quarantine_failures(result: QuarantineResult) -> tuple[str, ...]:
    move_failures = [(path, reason) for path, reason in result.failed
                     if reason != QUARANTINE_MANIFEST_WRITE_FAILED]
    manifest_failures = [path for path, reason in result.failed
                         if reason == QUARANTINE_MANIFEST_WRITE_FAILED]
    lines: list[str] = []
    if move_failures:
        lines.append("移動できなかったファイル:")
        lines.extend(f"  {path}: {_QUARANTINE_REASON_LABELS.get(reason, reason)}"
                     for path, reason in move_failures)
    if manifest_failures:
        lines.append("警告: マニフェストを書き込めず、隔離の記録が古い可能性があります。")
        lines.extend(f"  {path}: {_QUARANTINE_REASON_LABELS[QUARANTINE_MANIFEST_WRITE_FAILED]}"
                     for path in manifest_failures)
    return tuple(lines)


def _format_quarantine_headline(result: QuarantineResult) -> tuple[str, ...]:
    if result.aborted_reason:
        reason = _QUARANTINE_REASON_LABELS.get(result.aborted_reason, result.aborted_reason)
        return (f"隔離を中止しました: {reason}", "ファイルは 1 件も移動していません。")
    unit_note = f"（実行単位: {result.unit_id}）" if result.unit_id else ""
    if not result.moved and result.failed:
        return (f"隔離できませんでした: 0 件{unit_note}",)
    return (
        f"隔離しました: {len(result.moved)} 件{unit_note}",
        *(f"{_KIND_LABELS.get(kind, kind)}: {path}" for kind, path in result.moved),
    )
