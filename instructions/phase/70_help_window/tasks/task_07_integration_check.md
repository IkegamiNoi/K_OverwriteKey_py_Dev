# task_07_integration_check

## 目的

phase 70（ヘルプの作成・暫定 53 v0.6）の task_01〜06a を跨いだ統合確認。テストスイート全体・smoke の実測と、複数タスクを跨ぐ差分の二次レビュー
（`.claude/rules/agent_selection.md` のレビュー表「統合テスト」= `deep-reviewer` + `codex-reviewer`）。
**コードの変更は、レビューで採用した指摘の最小の修正だけ。**

## 対象範囲（検証とレビュー・指摘の修正）

- verifier: `compileall` / `unittest discover -s tests` / `unittest discover -s tests_ui`（1 本だけ・並列にしない）/ `-m tests.smoke_app`
  （task_06a の完了時点 6e0badf で全 pass 済み。修正が入った場合に再実測する）
- `deep-reviewer`: phase 70 の全差分（`git diff 4a5b202..HEAD -- keyseq tests tests_ui`）を暫定 53 v0.6 に照らして（5 観点 + 前提・未定義挙動・矛盾・正本整合・代替案）
- `codex-reviewer`: 同じ範囲の標準レビュー
- 持ち越しの確認事項: (1) task_04 の参考 = 空の大分類を開ける分岐 `_category_visible` の要否（本文が入った今）/ (2) task_05 の参考 = 読み取り専用 Text での Ctrl+C（task_08 の実機目視へ回すかを決める）
- 採用した指摘の修正（実装は既定の実装エージェント・数行ならメイン）

## 読むファイル

- `instructions/history/53_help_window.md`（v0.6 全体）・`instructions/phase/70_help_window/phase.md`

## 含まない

- 正本 `spec_detail/`・`ui_terms.md` A22・`codebase_map.md` への昇格・暫定 53 の凍結・decisions_archive・`/refactor_check`・実機目視（task_08）

## 確認

- 上記 4 コマンドが全 pass（修正が入った場合）
- `deep-reviewer` と `codex-reviewer` の指摘を採否（ユーザー判断）で整理し、採用分を修正して再実測

## 完了条件

- 確認 pass・二次レビューの採用分を反映・**reviewer の採用**（統合確認では deep-reviewer の結論を以て代える）
- 実機目視は task_08 でまとめて実施
