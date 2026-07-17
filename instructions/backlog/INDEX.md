# instructions/backlog/

実装予定（または検討中）の改善ネタを蓄積する場所。

このフォルダのファイルは **正式なフェーズ／タスクではない**。
着手時は `instructions/phase/<phase>/tasks/` へ正式タスクとして起票し直すこと。
起票手順は `/idea`（`.claude/commands/idea.md`）。

---

## 運用ルール

- 1 ネタ 1 ファイル
- ファイル名: `idea_<連番>_<topic_snake_case>.md`
- 各ファイルは「概要 / 起票経緯 / 現状 / 提案 / 想定スコープ」を含む
- 着手時は状態列を「**着手**（→ 暫定仕様 / phase へのリンク）」へ更新し、行は本 INDEX に残す
- 完了・クローズ（対応不要 / 除外）が確定したものは、判定理由と対応フェーズへのリンクを
  状態列に残した上で、行を [INDEX_done.md](INDEX_done.md) へ移動する
  （フェーズ完了時の更新は `.claude/rules/task_execution.md`「フェーズ完了時」に従う）
- 「保留」は判定理由を状態列に残して本 INDEX に残す
- 仕様変更を伴うネタは `.claude/rules/spec_change_workflow.md` に従う
- 採番はフォルダ実体（`idea_*.md` の最大番号 + 1）が正。本表を基準にしない

---

## ネタ一覧

| ID | ファイル | 概要 | 状態 |
|---|---|---|---|
| idea_01 | [idea_01_hotkey_validation_to_domain.md](idea_01_hotkey_validation_to_domain.md) | App に住む hotkey 検証ロジック（約31行）を domain / application へ移し、App は dialogs 契約の薄い委譲に留める。application → presentation の逆転を解消し、`tk.Tk` なしで単体テストできるようにする。 | **着手**（→ 暫定仕様 [01](../history/01_hotkey_validation.md)・v1.0 ユーザー確定済 / phase [02_hotkey_validation](../phase/02_hotkey_validation/phase.md)）|
| idea_02 | [idea_02_startup_font_settings_cleanup.md](idea_02_startup_font_settings_cleanup.md) | 起動設定/フォントの3メソッド（`_load_startup_settings` / `_coerce_font_delta` / `set_ui_font_delta`）の責務混在と controller → App private 逆参照を解消。初期化順序の解決が前提。 | 未着手（検討段階・計画04 W7 の残留ロジック分類から分離）|
