# instructions/history/

**暫定仕様書**（暫定仕様先行モードの主入力）の置き場。

- 起票は `/spec_draft`（`.claude/commands/spec_draft.md`）に従う。
  ファイル名は `NN_<topic_snake_case>.md`（phase 番号・decisions 番号とは独立採番）
- フェーズ中は暫定仕様書がそのフェーズの**確定設計**（正本 `instructions/common/spec_detail/` は
  直接改訂しない）
- フェーズ末の正本反映タスクで正本へ昇格し、本フォルダの文書は**凍結**する
  （凍結後は経緯記録。編集禁止）
- モードの選択基準は `.claude/rules/spec_change_workflow.md`「モードの選択」

---

## archive/ について

`archive/` 配下はテンプレート導入（2026-07 の template 合流）**以前**の仕様・計画の凍結履歴。
`NN_<topic>` 採番の対象外であり、編集禁止（経緯記録としてのみ参照する）。

- `archive/json_separate/` — 分離JSON化の仕様検討
- `archive/keyboard_ui/` — キーボードUI関連の仕様検討・修正履歴

過去のリファクタ計画・提案書（01〜04）は `instructions/modified_proposal/`
（`/refactor_check` の提案書置き場。次採番 05）にある。
