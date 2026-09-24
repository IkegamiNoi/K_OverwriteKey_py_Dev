# task_02_records_and_close

## 目的

phase 33 の記録とクローズ（`.claude/rules/task_execution.md`「フェーズ完了時」）。直接改訂モードだが**正本 `spec_detail/` の改訂は無い**
（テストのみ・production 不変）。文書作業のためメインセッションが直接行う（`agent_selection.md`）。

## 対象範囲（文書のみ）

### `instructions/common/codebase_map.md`

- `:343-345`（`grab_modal` の「呼び出しは初期化の最後の文」と静的検査の記載）へ 1〜2 行:
  静的検査は**発見ベース**（`dialogs/` 直下の `Toplevel` 継承クラス + `controllers/config_io/` で `grab_modal` を呼ぶファイル集合・
  呼び出し場所はこの 2 か所だけ）で、**新しいダイアログは列挙へ足さなくても検査対象に入る**。
  `dialogs/` に非モーダルの `Toplevel` を置くと検査が落ちる／config_io に呼び出しを足したら期待件数の辞書へ追加する。
- （task_01b 追加分）HookController 節へ: フック停止の静的検査も発見ベース・ネストした子を足したら `NESTED_CHILD_DIALOGS` へ追加する。

### `.claude_data/state/decisions_archive/33_grab_modal_static_check_discovery.md`（新規）+ `decisions.md` 索引 1 行

- 問題 / 確定した判断（案 A'・発見条件を `grab_modal` の有無にしない理由・案 B / C を採らない理由・呼び出し場所の検査はメインの追加）/
  完了判定前レビュー 1 回目と追加確定（呼び出し発見の補強・phase 15 側の static_1・2 の発見ベース化 = task_01b）の経緯 /
  残るリスク（別名 import・多段継承・サブフォルダ非走査）/ 実施結果（task_01・01b・01c・02 のコミット）/ 実測（発見 11 件・一時改変 task_01 = 3 + task_01b = 7 パターン）/ 完了判定前レビュー / refactor_check。

### `instructions/phase/current.md`

- 「現在の参照先」を「アクティブなフェーズ = なし」へ差し替え、直前の完了フェーズに phase 33 をリンクのみで追加（phase 31 は落とし「それ以前」へ）。
- phase 32 の「テスト基盤の単発」の 1 行を phase 33 も含む形へ。
- 次採番の「phase 33 は起票」→「完了」。「別タスク化候補 > テスト負債」の idea_32 行を削除。

### backlog

- `instructions/backlog/INDEX.md` の idea_32 行を完了状態にして `INDEX_done.md` 末尾へ移動・`idea_32_*.md` に「状態」節を追加。

### phase.md / state

- phase.md の task_02 を完了に。`session.md` を更新。

## 読むファイル

1. `.claude_data/state/decisions_archive/32_hook_resume_wait_in_ui_tests.md`（書式の手本）
2. `instructions/phase/current.md`（「現在の参照先」「次採番」「別タスク化候補 > テスト負債」）
3. `instructions/common/codebase_map.md:336-346`
4. `instructions/backlog/INDEX.md` / `INDEX_done.md`（idea_32 行・末尾）

## 含まない

- コード・テストの変更。正本 `spec_detail/` の改訂（本フェーズに仕様変更は無い）。
- `T2_DIALOG_FILES`（static_3）の変更。

## 確認

- `git diff --stat` が文書のみ（`keyseq/`・`tests/`・`tests_ui/` の差分なし）。
- 追加・変更したリンクの参照先が実在する（`ls` で確認）。
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（`agent_selection.md`「フェーズ完了判定前」）。
  1 回目の指摘で task_01b を追加したため、task_01b と記録の更新後に 2 回目を行う。
- `/refactor_check` の判定を decisions_archive/33 と完了報告に記載（PHASE_BASE = `d65a6fa`）。

## 完了条件

- 上記確認 pass・完了判定前レビューの指摘の採否をユーザーが確認済み（指摘なしならそのまま完了）。
- 実機目視は不要（テストのみ）。
