# task_03_finalize_records

## 目的

フェーズ `01_view_ref_cleanup` の**正本反映・記録タスク（最終）**。
実装（task_01 / task_02）は完了・実機目視 OK 済みのため、本タスクは**文書作業のみ**を行い、
フェーズを完了状態にする（[phase.md](../phase.md)「タスク」3）。

**コード変更なし**。`.claude/rules/agent_selection.md`「メインセッションが直接行ってよい作業」
（フェーズ末の正本反映タスク = 文書作業）に基づき、メインセッションが実施する。

## 対象範囲（文書のみ）

`.claude/rules/task_execution.md`「フェーズ完了時」のチェックリストに従う。

### 1. `/refactor_check` の実行と結果記載

- `.claude/commands/refactor_check.md` に従い、PHASE_BASE = `1ec8873`（フェーズ起票コミット）〜 HEAD で
  M1〜M6 を収集（手順 1〜2 は `verifier` へ委任）→ 判定（手順 3 以降）はメイン。
- 判定結果（不要 / 推奨 + 提案書パス / スキップ + 理由）を**完了報告に記載**する。
- 「推奨」の場合のみ提案書を起票し、ユーザー判断を仰ぐ（**承認前に実装しない**）。

### 2. `.claude_data/state/decisions_archive/01_view_ref_cleanup.md` の作成

本フェーズの判断履歴を集約する（フォルダが無ければ作成）。含める内容:

- フェーズの目的・モード（直接改訂モード・仕様変更なし）と結果
- task_01: status_bar 生やしのローカル変数化 → 判定
- task_02: trigger_list alias 削除 / **`action_list` alias 据え置きの理由**（trigger_list との性質差）→ 判定
- `/refactor_check` の判定結果
- コミット一覧

### 3. `.claude_data/state/decisions.md` の更新

- 「アーカイブ索引」節を設け（無ければ新設）、`decisions_archive/01_view_ref_cleanup.md` への
  1 行リンクを追加する（要約の本体はアーカイブ側が正）。

### 4. `instructions/phase/current.md` の更新

current.md「フェーズ完了時の指示」に従う:

- 「現在の参照先」から**本フェーズの項を削除**し、**次フェーズ未確定**の状態に戻す
  （次の着手候補は「次フェーズ候補」節のリンクで示す）。
- 「別タスク化候補」から**本フェーズで解消した 2 件を削除**する
  （`views/status_bar.py` の生やし / `trigger_list` alias）。
- 「次フェーズ候補」を更新する（本フェーズ完了により、次は
  [idea_01](../../../backlog/idea_01_hotkey_validation_to_domain.md) →
  [idea_02](../../../backlog/idea_02_startup_font_settings_cleanup.md)）。
- 次採番（`02_<topic>`）の記述を確認する（本フェーズ起票時に更新済み・変更不要）。

### 5. `.claude_data/state/session.md` の更新

- フェーズ完了を反映（current / last_action / next_action）。

### 設計メモ / 制約

- **起票元 idea が無いフェーズ**のため、`instructions/backlog/INDEX.md` /
  `INDEX_done.md` の更新は**不要**（本フェーズは current.md「別タスク化候補」由来）。
- **暫定仕様先行モードではない**ため、暫定仕様の昇格・凍結は**不要**（主入力なし）。
- **正本仕様書（`instructions/common/spec_detail/`）の更新は不要**
  （挙動不変・仕様変更なしのフェーズのため）。
- `instructions/common/codebase_map.md` の更新も**不要**
  （生やし/alias はクラス構成・JSON・UI 構成の記載対象ではない。W5 の登録方式の記述は変更なし）。
  ※ 判断根拠を完了報告に 1 行残すこと。

## 含まない

- コード変更全般（task_01 / task_02 で完了済）
- `/refactor_check` が「推奨」判定を出した場合の**リファクタ実施**
  （提案書起票 + ユーザー承認までが範囲。`.claude/commands/refactor_check.md` 禁止事項）
- 次フェーズ（[idea_01](../../../backlog/idea_01_hotkey_validation_to_domain.md)）の起票
  （`/phase_start` は別途・ユーザー指示後）
- 計画04 の decisions 記録の移設（`decisions.md` の「2026-07-15〜07-17 (計画04)」節は
  リファクタ計画であってフェーズではないため、本タスクでは触らない）

## 確認

1. `.claude_data/state/decisions_archive/01_view_ref_cleanup.md` が存在し、
   task_01 / task_02 / refactor_check の判定とコミット一覧を含む
2. `.claude_data/state/decisions.md` に「アーカイブ索引」からのリンクが 1 行ある
3. `instructions/phase/current.md`:
   - 「現在の参照先」に `01_view_ref_cleanup` の項が**残っていない**
   - 「別タスク化候補」に `status_bar` 生やし / `trigger_list` alias の行が**残っていない**
   - 次採番が `02_<topic>` のまま
4. `git status` が**クリーン**（フェーズ完了条件・phase.md）
5. `/refactor_check` の判定結果が完了報告に記載されている

## 完了条件

- 上記「確認」1〜5 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点。CLAUDE.md「レビュー（必須）」。
  本タスクは文書作業のため、記載の事実整合・チェックリスト網羅を中心にレビューする）。
- 実機目視: **不要**（コード変更なし。task_01 / task_02 で実施済・ユーザー確認 OK）。
