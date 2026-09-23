# task_03_spec_promotion_and_close

## 目的

phase 31 の**正本反映と記録**（フェーズ最終タスク）。暫定仕様 24（v0.5）§4 を正本へ昇格し、暫定仕様を凍結、
判断履歴・ルーティング・起票元 idea のクローズ・`/refactor_check`・完了判定前レビューまでを行う。

**文書作業のみ（メインセッション）**。コード変更なし（レビュー指摘で必要になった場合はユーザー確認のうえ枝番タスク化）。

## 対象範囲（文書のみ）

1. 正本 `instructions/common/spec_detail/data_schema.md`
   - §5.11.1: phase 30 の「`type` が無い / 空 / 上表以外 → `value` を文字列入力」条項を暫定 24 §4 の文言へ置換
     （何も送らず通知・シーケンスは止まる・要素は除去しない・一覧は `value` を表示・ダイアログは空 `type` を `hotkey` で開く・
     §5.1 意味変更の設計変更による例外の注記）。
   - §5.11.5: 既知の制約へ「通知の表示中もフックは止まらず、ユーザー操作の正常なアクション・キーは前面の窓へ送られる」を 1 項追加。
2. `instructions/common/codebase_map.md`: 「フック関連」節にアクション実行（`ActionExecutor.execute` の戻り値 / `SequenceRunner` の停止）の小節を追加。
3. 暫定仕様 24 のヘッダを「**凍結（2026-09-24・正本反映済）**」へ。
4. `.claude_data/state/decisions_archive/31_unknown_action_type_handling.md`（新規）: `decisions.md` の暫定 24 節を集約し、
   索引へ 1 行・本文の節を削除。
5. `instructions/phase/current.md`: phase 31 を完了記載へ・「直近の一連の作業が扱っている領域」を更新・次採番（phase 32 / 暫定 25）は再変更しない。
6. `instructions/backlog/INDEX.md` → `INDEX_done.md`: idea_35 を完了状態で移動。
7. `phase.md` のタスク一覧を完了へ。
8. `/refactor_check`（メトリクスは `verifier`・PHASE_BASE = `6c20dd6`）。
9. 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（指摘の採否はユーザー確認）。

## 読むファイル

1. 暫定仕様 `instructions/history/24_unknown_action_type_handling.md` §4 / §8
2. 正本 `data_schema.md` §5.11.1（`:388-396`）/ §5.11.5（`:443-447`）
3. `instructions/common/codebase_map.md:564-584`
4. `.claude_data/state/decisions_archive/30_action_and_internal_key_type_coercion.md`（書式の手本）

## 含まない

- コード変更（task_01 / task_02 で完了）
- 暫定 24 §7 のスコープ外項目

## 確認

- 正本の新文言が実装（`action_executor.py:50-81` / `sequence_runner.py:57-72,146-160`）と一致する（レビューで確認）。
- 相対リンクの実在（変更した `.md` のリンクを機械確認）。
- コード差分ゼロ（`git diff 31466fc -- keyseq tests tests_ui main.py` が空）。

## 完了条件

- 上記確認・`/refactor_check` 判定・完了判定前レビュー（deep-reviewer + codex-adversarial）の指摘をユーザー確認のうえ反映。
- 実機目視は**任意**（ユーザー判断で省略・2026-09-24）。
