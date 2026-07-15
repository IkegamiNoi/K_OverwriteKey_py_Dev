---
description: 直前のやりとりから .claude_data/state/session.md を更新する
---

直前の会話と作業内容を整理して `.claude_data/state/session.md` を更新してください。

## 更新ルール
- 既存の `session.md` を Read してから差分のあるフィールドのみ Edit で上書き
- `last_updated` は現在時刻（ISO 8601、例: `2026-05-07T14:32:00`）
- `phase` は現在のフェーズフォルダパス（連番プレフィックス付き。例: `instructions/phase/11_node_move`）
- `next_action` は「**次セッションが新規セッションでも実行可能**」な粒度で具体的に書く
  - 例: 「実装エージェント（`agent_selection.md` の既定）に `src/presentation/canvas_widget.py` の task_03 実装を依頼」
  - 例: 「reviewer に `src/domain/models.py` のレビューを依頼（観点: 依存方向）」
  - NG例: 「続きをやる」「タスク2の続行」
- フィールドが該当なしならその項目は省略可（空文字でなく「なし」と明記してもよい）

### 肥大化防止ルール（厳守）

- `current.focus` は **必ず 1 行で現フェーズの状態を書く**（handoff.md の 1 行サマリの直接ソース）
- `last_action.summary` は **直近 1 ターン分のみ** を保持する。過去ターンのログを「（以下は前ターンまでの作業ログ）」として残してはならない
  - 過去のタスク詳細は `decisions_archive/<phase>.md` や `instructions/phase/<phase>/integration_result.md` に既に書かれているため、session.md には残さない
  - サマリは「実施内容」「ユーザー判断」「reviewer 判定」「完了判定」など最大 5 セクション程度で完結させる
- `last_action.result_files` は **最新 1 ターン分のみ** を保持する。`last_action_result_files (<過去 task> で touched)` のようなセクションを残してはならない
- `next_action` は最新のみ。「（以下は前タスクの next_action 履歴）」のようなセクションは作らない
- `resume_hints` は次フェーズ着手に必要な事項のみ残す。完了済みフェーズに固有の hints は積極的に削る
- **完了フェーズの進捗詳細（`### phase NN 進捗` 等の節）は、そのフェーズのアーカイブ化
  （`decisions_archive/<phase>.md` 作成）が済んだら session.md から削除する**。session.md に残す
  完了フェーズの言及は「直近 1 件の 1 行要約 + アーカイブへの参照」まで（handoff.md の
  完了フェーズ上限〔直近 3 件〕の入力源になるため、ここで溜めない）
- 過去の作業内容を辿る必要が出たら以下を参照する（session.md に詰め込まない）:
  - `decisions_archive/<phase>.md` — 判断履歴
  - `instructions/phase/<phase>/integration_result.md` — フェーズ最終結果
  - `git log` — 変更経緯

### フェーズ完了時の追加運用

- 完了フェーズの判断履歴は `decisions.md` 本体に蓄積し続けず、`decisions_archive/<phase>.md` へ切り出す
  - 本体には「アーカイブ索引」セクションに 1 行リンク（例: `- decisions_archive/<phase>.md — <概要>`）を残す
- session.md の `resume_hints` から、完了フェーズに固有の hints を整理する

## 必須フィールド（汎用スキーマ）
- `last_updated`
- `phase`
- `current.focus` / `current.mode`（`implementing` | `pending_review` | `completed` | `blocked`）
- `last_action.{ts, who, summary}`（who: `main` | `implementer` | `reviewer` | `user`）
- `next_action`（リスト、最低 1 項目）
- `blockers`（無ければ「なし」と明記）

## 推奨フィールド
- `last_commit_location`（最終コミットを行ったブランチ / worktree 名。**現在の作業場所ではない**。
  現在地はセッション開始時に SessionStart hook が注入する git 実測値〔branch / worktree_root〕が正。
  `worktree:` という名前でこのフィールドを書いてはならない — 現在地と誤読される）
- `last_action.result_files`（変更したファイルのプロジェクト相対パス）
- `last_action.verified`（最新のチェック結果。キーはプロジェクトのチェック項目に合わせる。
  例〔Python の場合〕: `compile` / `ruff` / `mypy` / `pytest`、
  値: `clean` | `<N> issues` | `pass <N>` | `fail <N>` | `not_run` | `not_configured`）
- `resume_hints`（次セッション再開時に役立つメモ。例: 「類似実装は `src/presentation/painters.py` を参照」）

## チェックコマンド（参考・EDIT REQUIRED）
> プロジェクト初期化時に、状態更新の根拠とするチェックコマンドをここに記載する。
> 導入されていないものは `not_configured` とする。
> 例（Python）: `python -m compileall -q src` / `python -m ruff check src` /
> `python -m mypy src` / `python -m pytest -q`

## プロジェクト固有指示の連携
プロジェクト固有の補足指示は `.claude/commands/save_state.project.md`（任意ファイル）に書く運用。
存在すれば併せて参照し、`decisions.md` / `instructions/phase/current.md` などへの連動更新を行う。

タスク完了時は以下も更新すること。
- `instructions/phase/current.md`: 該当フェーズ項へ完了タスクと次タスクを簡潔に反映
  （進捗記録は current.md へ一本化する）
- `.claude_data/state/decisions.md`: 想定外差分を発見した場合の `採用 / 修正して採用 / 保留 / 除外` 判定を追記

## 副次操作
- 更新後、変更した内容を **3 行以内**で要約して出力する
- 過剰な要約や説明は不要（トークン節約）

## 注意
- このコマンドは「明示的な区切り」のタイミングで使う想定
- 自動セーブ（SubagentStop / PreCompact hook）と機能的に重複するが、ユーザーが任意のタイミングで叩けることを優先する
- アーキテクチャ層の境界を跨いだ変更は `last_action.summary` に明記する
