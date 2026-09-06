from keyseq.application.config_service.orphan_scan import (
    KIND_HOTKEY_PRESETS,
    KIND_KEYMAP,
    KIND_SEQUENCE,
    KIND_TRIGGER_SET,
    ORPHAN_CANDIDATE,
    ORPHAN_EXCLUDED,
    OrphanScanResult,
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
        lines.append(f"形状検証で対象外: {excluded_count} 件")
    return tuple(lines)


def format_orphan_notice(result: OrphanScanResult) -> tuple[str, ...]:
    """候補がない場合も、走査範囲と読めなかった参照側を通知する。"""
    return (ORPHAN_SWEEP_EMPTY_MESSAGE, *format_scan_warnings(result))
