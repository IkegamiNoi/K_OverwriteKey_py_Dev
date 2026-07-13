# instructions/history/

**暫定仕様書**（暫定仕様先行モードの主入力）の置き場。

- 起票は `/spec_draft`（`.claude/commands/spec_draft.md`）に従う。
  ファイル名は `NN_<topic_snake_case>.md`（phase 番号・decisions 番号とは独立採番）
- フェーズ中は暫定仕様書がそのフェーズの**確定設計**（正本 `instructions/common/spec_detail/` は
  直接改訂しない）
- フェーズ末の正本反映タスクで正本へ昇格し、本フォルダの文書は**凍結**する
  （凍結後は経緯記録。編集禁止）
- モードの選択基準は `.claude/rules/spec_change_workflow.md`「モードの選択」
