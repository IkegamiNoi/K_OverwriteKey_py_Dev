from keyseq.application.config_service.parent_refs_cleanup import (
    CLEANUP_ALL_STALE,
    CLEANUP_TARGET,
    PRUNE_FAILURE_INVALID_DATA,
    PRUNE_FAILURE_SAVE_FAILED,
    PRUNE_FAILURE_UNREADABLE,
    ParentRefsCleanupInspection,
    ParentRefsPruneResult,
)


CLEANUP_EMPTY_MESSAGE: str = "掃除する項目はありません。"

_KIND_LABELS = {
    "keymap": "キーマップ",
    "trigger_set": "トリガー一覧",
    "sequence": "出力シーケンス",
}

_FAILURE_MESSAGES = {
    PRUNE_FAILURE_UNREADABLE: "読み直せませんでした",
    PRUNE_FAILURE_INVALID_DATA: "JSON の形式が不正です",
    PRUNE_FAILURE_SAVE_FAILED: "保存できませんでした",
}


def format_cleanup_plan(
    inspections: list[ParentRefsCleanupInspection],
) -> tuple[str, ...]:
    """参照元の掃除で提示する行を組み立てる。"""
    if not inspections:
        return (CLEANUP_EMPTY_MESSAGE,)

    target_count = sum(
        inspection.state in (CLEANUP_TARGET, CLEANUP_ALL_STALE)
        for inspection in inspections
    )
    stale_count = sum(len(inspection.stale_refs) for inspection in inspections)
    lines = [f"対象ファイル: {target_count} 件、消える参照元: {stale_count} 件"]
    for inspection in inspections:
        kind_label = _KIND_LABELS.get(inspection.kind, inspection.kind)
        lines.append(f"{kind_label}: {inspection.stored_path}")
        if inspection.state in (CLEANUP_TARGET, CLEANUP_ALL_STALE):
            lines.extend(["消える参照元:", *(f"  {path}" for path in inspection.stale_refs)])
        if inspection.protected_refs:
            lines.extend(
                [
                    "保護のため残す参照元:",
                    *(f"  {path}" for path in inspection.protected_refs),
                ]
            )
        if inspection.state == CLEANUP_ALL_STALE:
            lines.extend(
                [
                    "警告: この掃除で参照元が 0 件になります。",
                    "子ファイル自体は削除しません。孤児かどうかは「孤児ファイルの棚卸し」で確認できます。",
                ]
            )
    return tuple(lines)


def format_cleanup_result(result: ParentRefsPruneResult) -> tuple[str, ...]:
    """参照元の掃除の実行結果を通知用の行へ組み立てる。"""
    removed_count = sum(count for _, count in result.updated_files)
    lines = [
        f"更新したファイル: {len(result.updated_files)} 件、除去した参照元: {removed_count} 件"
    ]
    if result.failed_files:
        lines.append("失敗したファイル:")
        lines.extend(
            f"  {path}: {_FAILURE_MESSAGES.get(reason, '不明な理由で失敗しました')}"
            for path, reason in result.failed_files
        )
    return tuple(lines)
