# task_03_record_and_close

## 目的

phase 80 の記録とフェーズの完了処理（`.claude/rules/task_execution.md`「フェーズ完了時」）。
正本 `features.md` §4.6 の改訂（Windows の例外）と `codebase_map.md` の modal.py の節は task_01 / 02 で反映済。**文書のみ・コード変更なし**。

## 対象範囲（文書のみ）

- フェーズ完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（`--base 3f4ef40b`）。指摘の採否はユーザー
- `.claude_data/state/decisions_archive/80_win_d_restore_blank_dialog.md` を作成（decisions.md の phase 80 の節 + 完了レビューの判断を集約）し、decisions.md は「アーカイブ索引」に 1 行を足して phase 80 の節を消す
- `instructions/phase/current.md`: アクティブなフェーズ = なし・直前の完了フェーズ = phase 80・「直近の一連の作業の領域」・次採番の節（phase 80 完了の 1 文・次 = phase 81 / decisions 81）
- `instructions/backlog/INDEX.md` の idea_61 の行を完了にして `INDEX_done.md` へ移動
- `/refactor_check`（メトリクス収集は verifier）と判定の記録

## 読むファイル

- `instructions/phase/80_win_d_restore_blank_dialog/`（phase.md・task01_measurement.md・tasks）
- `.claude_data/state/decisions.md` の末尾（phase 80 の節）と「アーカイブ索引」の直近の行
- `instructions/phase/current.md` の「現在の参照先」と「次採番」
- 手本: `.claude_data/state/decisions_archive/78_action_hotkey_save_validation.md`（直接改訂モードの完了記録）

## 含まない

- コードの変更（レビューで欠陥が出た場合は止めてユーザーへ報告し、枝番タスクで扱う）
- idea_67（OS 標準のダイアログと Win+D・低優先の確認）の着手

## 確認

- decisions_archive/80 と索引の行のリンクが実在する・decisions.md に phase 80 の節が残っていない
- current.md の次採番が phase 81 / 暫定 61 / decisions 81 / 提案書 29 / idea 68 で、他の箇所と食い違わない
- idea_61 の行が INDEX.md に無く INDEX_done.md にある
- refactor_check の判定を完了報告と decisions_archive/80 に書いた

## 完了条件

- 上記確認・**reviewer 採用**（完了判定前レビューは deep-reviewer + Codex 敵対的レビューで実施。文書の整合は reviewer で 1 回）
- 実機目視なし（task_02 で実施済）
