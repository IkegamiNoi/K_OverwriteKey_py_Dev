# task_07_spec_promotion

## 目的

phase 51 の最終タスク。暫定 35（v0.8・ユーザー確定済）を正本 `instructions/common/spec_detail/` へ昇格し、暫定 35 を凍結する（暫定 35 §12・`.claude/rules/task_execution.md`「フェーズ完了時」）。
文書作業のみ（メインセッションが直接行う・`agent_selection.md`）。コード不変。

## 対象範囲（文書のみ）

### 正本
- `data_schema.md`: §5.11.1（種類の表・未知の種類の文言）/ 新節 §5.11.9 key_hold
- `features.md`: §4.2（通常アクションの列挙）/ §4.2.3（押下中の集合）/ §4.2.8（「送った」に key_hold・停止の行では離さない）/ 新節 §4.2.12（数え方・送信・押下中の集合・他の送信との関係・エラー・自動で離す契機の表・スコープ外）/
  §4.5（押下中の表示）/ §4.6（一覧の表示形式・ダイアログ）
- `key_input.md` §7.7（key_hold の送信・keyboard の記録に載せない〔hotkey・直接置換にも効く〕・text の送信後に修飾キーを押し直さない）
- `codebase_map.md`: phase 51 の項（持ち主の受け渡しは `owner_scope` 方式）

### 状態・履歴
- 暫定 35 の冒頭を凍結に
- `.claude_data/state/decisions_archive/51_key_press_release_actions.md`・`decisions.md` のアーカイブ索引（phase 51 の節を移す）・`instructions/phase/current.md`・phase.md
- 起票元 idea_23 を INDEX_done へ移動

## 確認

- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（正本整合・未定義挙動・矛盾）
- `/refactor_check`（メトリクスは verifier・判定はメイン）
- 既存テスト（tests / tests_ui / smoke）は task_06a 時点で pass（本タスクはコード不変）
