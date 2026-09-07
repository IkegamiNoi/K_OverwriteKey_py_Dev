from collections import Counter

from keyseq.application.config_service import contracts


_REASON_LABELS = {
    contracts.RESTORE_SKIPPED_EXISTS: "復元先に同名ファイルがあります",
    contracts.RESTORE_REJECTED_TARGET: "復元先が対象外です",
    contracts.RESTORE_SOURCE_MISSING: "隔離側にファイルがありません（復元済み等）",
    contracts.RESTORE_FAILED: "復元できませんでした",
    contracts.RESTORE_ABORTED_INVALID_ID: "実行単位 ID が不正、または実在しません",
    contracts.RESTORE_ABORTED_NO_MANIFEST: "マニフェストが読めません",
}


def format_unit_list(units: tuple[contracts.QuarantineUnit, ...]) -> tuple[str, ...]:
    """実行単位の表示行を、入力と同じ順で返す。"""
    return tuple(
        f"{unit.unit_id}  作成: {unit.created_at}  残り {unit.remaining_count}/{unit.entry_count} 件"
        + ("" if unit.manifest_valid else "  マニフェスト不正（復元できません）")
        for unit in units
    )


def format_restore_plan(unit: contracts.QuarantineUnit) -> tuple[str, ...]:
    """確認用に実行単位と実体の残数、同名ファイルの扱いを示す。"""
    return (
        *format_unit_list((unit,)),
        f"隔離側に残っている {unit.remaining_count} 件を元の場所へ復元します。",
        "復元先に同名ファイルがある場合は上書きせずスキップします。",
    )


def format_restore_result(result: contracts.QuarantineRestoreResult) -> tuple[str, ...]:
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


def format_delete_plan(
    unit: contracts.QuarantineUnit, paths: tuple[str, ...], *, manifest_valid: bool,
) -> tuple[str, ...]:
    """不可逆の警告と全件を、保存表記のまま提示する。"""
    lines = ["この操作は取り消せません。", f"削除する実行単位: {unit.unit_id}"]
    if not manifest_valid:
        lines.extend(("マニフェストが読めないため、中身を確認できません。",
                      "ディレクトリごと削除します。"))
    lines.extend(f"  {path}" for path in paths)
    return tuple(lines)


def format_delete_result(result: contracts.QuarantineDeleteResult) -> tuple[str, ...]:
    """拒否と I/O の部分失敗を区別し、未知コードも表示する。"""
    if result.deleted:
        return (f"削除しました: {result.unit_id}",)
    labels = {
        contracts.DELETE_REJECTED_INVALID_ID: "実行単位 ID が不正、または実在しません",
        contracts.DELETE_REJECTED_IS_ROOT: "隔離ルート自身、または隔離ルート外を指しています",
        contracts.DELETE_REJECTED_NO_MANIFEST: "マニフェストが読めません",
        contracts.DELETE_FAILED: "削除できませんでした",
    }
    reason = labels.get(result.aborted_reason, result.aborted_reason)
    notice = ("一部が削除されている可能性があります。" if result.aborted_reason == contracts.DELETE_FAILED
              else "削除していません。")
    return (f"削除を中止しました: {reason}", notice)
