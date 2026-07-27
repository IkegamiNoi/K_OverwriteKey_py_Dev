# CLAUDE.md

## ■ 読込順序（厳守）

セッション再開時は以下の順番で読む（**過去会話履歴は参照しない**）:

1. `.claude_data/state/handoff.md` — 再開プロンプト（最優先）
2. `.claude_data/state/session.md` — 現在状態スナップショット
3. `.claude_data/state/decisions.md`（あれば） — 過去の判断履歴
4. プロンプトで指定されたフェーズフォルダ配下のファイル
5. `.claude/rules/` 配下の共通ポリシー

フェーズフォルダは `instructions/phase/` を起点とする。
`instructions/phase/current.md` を参照して現在やるべきフェーズがどれか判別する。
プロンプトの指定と `instructions/phase/current.md` の内容が異なった場合ユーザーへ確認する。

アプリ全体仕様は `instructions/common/` 配下に格納されている。
各フェーズフォルダの `instructions/phase/XXX/phase.md` から必要に応じて参照すること。

---

## ■ 状態記録（state recording system）

セッション中断時にトークン消費を抑えて再開できるよう、以下を維持する:

- `.claude_data/state/session.md` — 現在状態。`/save_state` で手動セーブ
- `.claude_data/state/handoff.md` — 再開プロンプト。`/save_handoff` で再生成
- `.claude_data/state/decisions.md` — 採用/修正採用/保留/除外 の判断履歴

フェーズ / タスクの進捗記録は `instructions/phase/current.md` へ一本化する。

詳細は `.claude/commands/save_state.md` / `save_handoff.md` 参照。

タスク完了時のコミットは `/task_commit`（`.claude/commands/task_commit.md`）で行う。
自動保存モード（`instructions/save_mode/` の auto_save 系設定）では、Stop hook がタスク完了を
検知した際に `/save_state` に続けて実行を促す（手動保存モードでは任意実行）。

フェーズ完了時は `/refactor_check`（`.claude/commands/refactor_check.md`）でリファクタ要否を
判定する（判定と提案書起票のみ。実施はユーザー承認後）。

正本仕様書（`instructions/common/spec_detail/`）が肥大化した場合の分割は `/spec_split`
（`.claude/commands/spec_split.md`）に従う（節番号保持の INDEX 分割・ユーザー承認必須）。

起票系の定型作業はスキルに従う: idea 起票 = `/idea` / 暫定仕様書の起票 = `/spec_draft` /
新フェーズの起票 = `/phase_start` / タスク定義の起票 = `/task_new`
（いずれも `.claude/commands/` 同名ファイル）。

## ■ 実装ルール（常時有効）

- 作業は小さく分け、1タスクごとに完結させる
- 実装後は必ず確認し、未確認のまま次へ進まない
- タスク外の機能追加・無関係なリファクタ・大規模構造変更をしない
- 実装は原則、既定の実装エージェントへ委任する（既定エージェントとフォールバック条件は
  `.claude/rules/agent_selection.md`。エージェント構成は `instructions/agent_mode/` で
  Codex 併用 / Claude のみ を切り替える）。
  ここで定義された委任はユーザー確定済みの運用であり、都度の許可確認は不要。
  一方、**定義外の委任・多重起動は行わない**（量の抑制は `.claude/rules/output_style.md`）

---

## ■ レビュー（必須）

各タスクで必ず別視点レビューを1回実施すること。

- 実装方針確定前 または 完了判定前のいずれかで実施
- 確認観点: 仕様逸脱 / 責務分離 / 依存方向 / 過剰実装
- 未実施のタスクは完了扱いにしない
- レビュー結果を完了報告に含めること
- 統合テスト時・フェーズ区切りでは二次レビューを併用する
- 暫定仕様書はユーザー確定前に敵対的レビューを実施する
  （担当エージェントの使い分けは `.claude/rules/agent_selection.md` のレビュー表）

---

## ■ 共通ルール参照

`.claude/rules/` 配下は毎セッション自動読込されるため**要点版**として維持する。
外出しした詳細（例・テンプレート・手順詳説）は `instructions/common/rules_detail/` に置き、
必要時のみ読む（要点版が規範の正）。

- `.claude/rules/agent_selection.md` — メイン/サブエージェントの分担（実装エージェントの既定とフォールバック / 起票=メイン + 調査=Explore / 統合確認・メトリクス収集=verifier / レビューのタイミング別使い分け。構成は `instructions/agent_mode/` で Codex 併用 / Claude のみ を切り替え）
- `.claude/rules/anti_patterns.md`
- `.claude/rules/file_organization_rules.md` — ファイル配置・肥大化対策（分割時の親フォルダ方式 / 昇格ルール / 恒久互換レイヤー禁止）
- `.claude/rules/python_rules.md` — 言語別ルール（Python）
- `.claude/rules/implementation.md` — 実装ポリシー
- `.claude/rules/output_style.md` — 応答・進捗報告・文書分量・委任量の作法（出力の量と形）
- `.claude/rules/review.md`
- `.claude/rules/spec_change_workflow.md` — 仕様変更は2モード（直接改訂 / 暫定仕様先行）。多岐・探索的なら暫定仕様書から（境界は同ファイル「モードの選択」節）
- `.claude/rules/task_execution.md`

---

<tone_preference>
応答・進捗報告・文書成果物はいずれも簡潔に。結論から述べ、委任は必要最小限にとどめる
（詳細は `.claude/rules/output_style.md`）。
</tone_preference>
