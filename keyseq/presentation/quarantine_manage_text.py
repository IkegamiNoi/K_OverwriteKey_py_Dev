from collections import Counter

from keyseq.application.config_service.quarantine_manage import (
    RESTORE_ABORTED_INVALID_ID,
    RESTORE_ABORTED_NO_MANIFEST,
    RESTORE_FAILED,
    RESTORE_REJECTED_TARGET,
    RESTORE_SKIPPED_EXISTS,
    RESTORE_SOURCE_MISSING,
    QuarantineRestoreResult,
    QuarantineUnit,
)


_REASON_LABELS = {
    RESTORE_SKIPPED_EXISTS: "復元先に同名ファイルがあります",
    RESTORE_REJECTED_TARGET: "復元先が対象外です",
    RESTORE_SOURCE_MISSING: "隔離側にファイルがありません（復元済み等）",
    RESTORE_FAILED: "復元できませんでした",
    RESTORE_ABORTED_INVALID_ID: "実行単位 ID が不正、または実在しません",
    RESTORE_ABORTED_NO_MANIFEST: "マニフェストが読めません",
}


def format_unit_list(units: tuple[QuarantineUnit, ...]) -> tuple[str, ...]:
    """実行単位の表示行を、入力と同じ順で返す。"""
    return tuple(
        f"{unit.unit_id}  作成: {unit.created_at}  残り {unit.remaining_count}/{unit.entry_count} 件"
        + ("" if unit.manifest_valid else "  マニフェスト不正（復元できません）")
        for unit in units
    )


def format_restore_plan(unit: QuarantineUnit) -> tuple[str, ...]:
    """確認用に実行単位と実体の残数、同名ファイルの扱いを示す。"""
    return (
        *format_unit_list((unit,)),
        f"隔離側に残っている {unit.remaining_count} 件を元の場所へ復元します。",
        "復元先に同名ファイルがある場合は上書きせずスキップします。",
    )


def format_restore_result(result: QuarantineRestoreResult) -> tuple[str, ...]:
    """実績と理由別件数を示し、保存表記のまま各ファイルを列挙する。"""
    lines: list[str] = []
    if result.aborted_reason:
        reason = _REASON_LABELS.get(result.aborted_reason, result.aborted_reason)
        lines.extend((f"復元を中止しました: {reason}", "1 件も戻していません。"))
    lines.append(f"復元しました: {len(result.restored)} 件")
    lines.extend(f"  {path}" for _kind, path in result.restored)
    counts = Counter(reason for _path, reason in result.skipped)
    lines.append(f"スキップ: {len(result.skipped)} 件")
    lines.extend(f"  {_REASON_LABELS.get(reason, reason)}: {count} 件"
                 for reason, count in counts.items())
    lines.extend(f"  {path}: {_REASON_LABELS.get(reason, reason)}"
                 for path, reason in result.skipped)
    lines.append("実行単位を片付けました。" if result.unit_removed else "実行単位は残っています。")
    return tuple(lines)
