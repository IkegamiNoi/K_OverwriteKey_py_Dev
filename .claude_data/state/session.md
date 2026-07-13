# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: <ISO 8601 timestamp / 例: 2025-05-02T15:00:00>
phase: <現在のフェーズフォルダ / 例: instructions/phase/01_mvp>
worktree: <worktree 名やブランチ名 / 任意>

## current
focus: <現在の作業内容を 1 行で / 例: task_28 の reviewer レビュー待ち>
mode: implementing               # implementing | pending_review | completed | blocked

## last_action
ts: <ISO 8601 timestamp>
who: main                        # main | implementer | reviewer | user | <他エージェント名>
summary: |
  <直前のターンで何をしたかを 2-5 行で要約>
  <例: 修正A〜Dを順に適用、analyze/test を確認>
result_files:
  - <変更/作成したファイルのプロジェクト相対パス>
  - <例: lib/foo/bar.dart>
verified:
  analyze: <clean | <N> issues | not_run>
  test: <pass <N> | fail <N> | not_run>

## next_action
- <次セッションが新規セッションでも実行可能な粒度で具体的に書く>
- <例: reviewer エージェントに lib/foo/bar.dart のレビューを依頼>

## blockers
- <あれば、なければ「なし」と明記>

## resume_hints
- <次セッション再開時に役立つメモ>
- <例: 既存の類似実装は lib/foo/baz.dart を参照>
