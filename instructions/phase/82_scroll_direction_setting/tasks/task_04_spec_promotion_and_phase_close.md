# task_04_spec_promotion_and_phase_close

## 目的

暫定 62 v0.4 を正本 `instructions/common/spec_detail/` へ昇格して凍結し、フェーズ 82 を完了する（`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書のみ・コードは変えない**。

## 対象範囲（文書限定）

### 正本の昇格（暫定 62 §9・統合レビュー ④）

- `data_schema.md` §5.4:
  - config.json を作る契機の列挙に「設定メニューでスクロールの向きを切り替えたとき〔phase 82〕」を足す。
  - `scroll_invert`（phase 82）の項を `compact_header_view` と同じ書き方で足す（値ごとに判定・bool 以外 / 欠けはその値だけ false・dict でなければ両方 false・エラー表示なし・ファイルは書き換えない / 書き込み契機・常に両方を書く・保存済みと同じなら書かない / 未知のキーは保持しない〔本設定を書いたとき〕/ 他の設定・構成セットの保存では不正な値もそのまま残す）。
- `data_schema.md` §5.11.10: 実行③に反転を足す（符号の 3 段 = アプリ内の符号 → 設定による反転 → OS へ渡す値・macOS の横は OS へ渡すときに符号を入れ替える・反転は保存の成功の後に実行する行から効く・一覧 / ダイアログ / JSON の `direction` は書いた向き）。
- `features.md` §4.6: 設定メニューに「スクロールの向き」の項（位置・2 つのチェック・保存と失敗時の戻し・構成セットを未保存にしない・即時反映・失敗の知らせの間はフックが止まる）を「言語」の前に足す。
- `features.md` §4.8「メニューの処理」: 遅らせる処理の列挙にスクロールの向きのチェックボタンの保存を足し、「待ちの間も選んだ値を示し、失敗したら保存済みの値へ戻す」の文にも本設定を含める。
- `codebase_map.md`: `ActionExecutor` の `mouse_scroll` の項（`get_scroll_invert`・`apply_scroll_invert`）・マウスのホイールの節（domain の `ScrollInvert` ほか・presentation の `App.set_scroll_invert`・`ui_vars`・メニュー・テスト）。
- `ui_terms.md`: 用語の表は足さない（メニューの項目名は文言キーで足りる・既存の用語に当たらない）。

### 凍結と記録

- 暫定 62 のヘッダを「凍結（2026-11-26・正本反映済）」へ。
- `.claude_data/state/decisions_archive/82_scroll_direction_setting.md` を作り、`decisions.md` の phase 82 節を移して索引に 1 行。
- `instructions/phase/current.md`: アクティブなフェーズ = なし・直前の完了フェーズ = phase 82・直近の領域の数行・次採番（phase 83 / 暫定 63 / decisions 83 / 提案書 30 / idea 71）・次採番節の phase 82 の完了記載。
- `instructions/backlog/INDEX.md` の idea_58 行を完了にして `INDEX_done.md` へ移す。
- `/refactor_check`（メトリクスは verifier）を実行し、判定を完了報告に書く。

## 読むファイル

- `instructions/history/62_scroll_direction_setting.md`（全体）
- `instructions/common/spec_detail/data_schema.md` §5.4（109〜175 行付近）・§5.11.10
- `instructions/common/spec_detail/features.md` §4.6 の設定メニュー（990〜1020 行付近）・§4.8「メニューの処理」（1385 行付近）
- `instructions/common/codebase_map.md`（713〜716 行・951〜955 行付近）
- phase 81 の完了時の書き方（`decisions_archive/81_*.md`・current.md の完了記載）

## 含まない

- コードの変更・多重起動の問題（idea_70）

## 確認

- 正本の追記が暫定 62 §3〜§5 と食い違わない（完了判定前レビューで確認）
- リンク・番号の実在
- `/refactor_check` の判定

## 完了条件

- 完了判定前レビュー（`deep-reviewer` + Codex 敵対的レビュー）の指摘の採否がユーザーで決まり、採用分を反映済み・**reviewer 採用**（本タスクの差分の整合確認）。
- 実機目視は不要（task_03 で完了済み）。
