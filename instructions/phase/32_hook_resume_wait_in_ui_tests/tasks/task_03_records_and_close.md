# task_03_records_and_close

## 目的

phase 32 の記録とクローズ（`.claude/rules/task_execution.md`「フェーズ完了時」）。直接改訂モードだが**正本 `spec_detail/` の改訂は無い**
（テストのみ・production 不変）。文書作業のためメインセッションが直接行う（`agent_selection.md`）。

## 対象範囲（文書のみ）

### `instructions/common/codebase_map.md`

- tests_ui ヘルパの記載（`:326-328` 付近・`escape_delivery.py` の `send_escape` の説明の近く）へ 1〜2 行:
  `tests_ui/hook_resume_wait.py` の `wait_for_hook_pause_count`（破棄後のフック再開は `after(0)` 予約のため、確かめる前に実時間の期限つきで待つ。
  **破棄直後の未解除・解除が起きないこと・同期解除の確認には使わない**）。

### `.claude_data/state/decisions_archive/32_hook_resume_wait_in_ui_tests.md`（新規）+ `decisions.md` 索引 1 行

- 問題 / 確定した判断（案 A・適用範囲・A/B 測定なし・escape_binding の「0 回」は本 family）/ 実施結果（task_01〜03 のコミット）/
  置き換えない確認の分類 / 実測（負荷測定を含む）/ 完了判定前レビュー / refactor_check。

### `instructions/phase/current.md`

- 「現在の参照先」を「アクティブなフェーズ = なし」へ差し替え、直前の完了フェーズに phase 32 をリンクのみで追加。
- 「直近の一連の作業が扱っている領域」は JSON 型不正・アクション実行の段落を残し、**本フェーズはテスト基盤の単発**である旨を 1 行添える。
- 次採番の「phase 32 は起票」→「完了」。「別タスク化候補 > テスト負債」の idea_33 行を削除（完了 idea は INDEX_done が正）。

### backlog

- `instructions/backlog/INDEX.md` の idea_33 行を完了状態にして `INDEX_done.md` へ移動・`idea_33_*.md` の「状態」節を完了へ。

### phase.md

- task_03 を完了に。

## 読むファイル

1. `.claude_data/state/decisions_archive/31_unknown_action_type_handling.md`（書式の手本）
2. `instructions/phase/current.md`（「現在の参照先」「次採番」「別タスク化候補 > テスト負債」「フェーズ完了時の指示」）
3. `instructions/common/codebase_map.md:318-330`
4. `instructions/backlog/INDEX.md` / `INDEX_done.md`（idea_33 行・末尾）

## 含まない

- コード・テストの変更。正本 `spec_detail/` の改訂（本フェーズに仕様変更は無い）。
- 残るリスク（`update()` を伴わないテスト冒頭の `== 0`）への対処（記録のみ）。

## 確認

- `git diff --stat` が文書のみ（`keyseq/`・`tests/`・`tests_ui/` の差分なし）。
- 追加・変更したリンクの参照先が実在する（`ls` で確認）。
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（`agent_selection.md`「フェーズ完了判定前」）。
- `/refactor_check` の判定を decisions_archive/32 と完了報告に記載。

## 完了条件

- 上記確認 pass・完了判定前レビューの指摘の採否をユーザーが確認済み。
- 実機目視は不要（テストのみ）。
