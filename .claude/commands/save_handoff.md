---
description: session.md から handoff.md を再生成する
---

`.claude_data/state/session.md` を読み、新セッションの最初に渡すための再開プロンプトとして
`.claude_data/state/handoff.md` を生成（または更新）してください。

## 前提（厳守）: 生成前に session.md を最新化する
handoff.md は session.md を唯一の入力にするため、**生成前に session.md が現在の作業状態を反映していること**を必ず確認する。
- `phase` / `current.focus` / `last_action` / `next_action` が、直近の会話・コミット状態・現フェーズ（`instructions/phase/current.md`）と食い違う、または古いフェーズのままなら、**先に `save_state.md` の手順（更新 + 肥大化防止ルール）に従って session.md を最新化してから** handoff.md を生成する。
- stale（陳腐化）と bloat（肥大化）は同じ扱い: どちらも「先に session.md を正す → それから handoff を作る」。
- **stale な session.md からは絶対に handoff を生成しない**（古いフェーズ情報が次セッションへ伝播し事故になる）。

## 含める内容
1. 「過去の会話履歴は参照しない」明示
2. プロジェクト概要（言語 / フレームワーク / アーキテクチャ / `instructions/common/app_overview.md` 参照）
3. 再開手順（読むファイルの順番）
4. 現在の作業の 1 行サマリ（`session.md.current.focus` を写す）
5. 最初に確認するコマンド（下記）
6. 注意点・blockers（`session.md.blockers` から）

### 肥大化防止（厳守）

handoff.md はセッション開始フックで毎回全文注入される固定費のため、以下の上限を守る。

- **完了フェーズの列挙は直近 3 件まで**。それ以前は「`decisions.md`「アーカイブ索引」+
  `decisions_archive/<phase>.md` 参照」の 1 行に置き換える（コミットハッシュの列挙もしない）
- 「直前フェーズの要点」は**直近 1 フェーズ分のみ**。旧フェーズの要点節は再生成時に削除する
- 既存 handoff.md の構造踏襲（下記ルール）より本上限が優先。踏襲元が上限超過していたら削って生成する

## 最初に確認するコマンド（EDIT REQUIRED）
> プロジェクト初期化時に、このプロジェクトの静的解析・テストコマンドを固定テンプレとして
> ここに記載する。導入されていないツールは「スキップしてよい」と明記する。
> 例（Python）:
> ```bash
> python -m compileall -q src                       # 構文チェック
> python -m ruff check src   2>&1 | tail -10        # 静的解析（未導入: スキップしてよい）
> python -m pytest -q        2>&1 | tail -10        # テスト（未導入: スキップしてよい）
> ```

## ルール
- 既存の `handoff.md` を Read して構造を踏襲
- 機械的な再生成で十分（過剰に手を入れない）
- `session.md.last_action.verified` を参照して、ハンドオフ側でも同じキーを使うよう揃える
- 出力後、変更があれば 1 行で要約
- session.md の最新化（stale / bloat の是正）は冒頭「## 前提（厳守）」に統合。入力が現状を反映していることを必ず先に担保する

## プロジェクト固有指示の連携
プロジェクト固有の確認コマンドや注意事項は `.claude/commands/save_handoff.project.md`（任意ファイル）に書く運用を想定。
存在すればそれを優先する。

## 推奨タイミング
- `/save_state` の直後に手動で実行する
- もしくは「今日の作業ここまで」と区切るタイミングで
- フェーズ切替時（例: `instructions/phase/11_node_move` → `instructions/phase/12_<topic>`）も再生成する
