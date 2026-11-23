# task_03_integration_and_record

## 目的

phase 78 の統合確認・実機目視・記録を行い、フェーズを完了させる（`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書と検証のみ。コードは変えない（レビューの採用分で修正が要る場合は枝番タスクを起こす）。**

## 対象範囲（記録と検証）

- `instructions/common/codebase_map.md` L912: 「hotkey の通常の未知名は保存時には検査しない」を削り、`ActionDialog.on_ok` が `App.validate_hotkey` で全キー名を検査して正規化値を保存する旨に直す
- 統合確認（verifier）: compileall / `tests` / `tests_ui` 全体 / `tests.smoke_app`
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（base = d7988c67。採否はユーザー）
- 実機目視（ユーザー）: 出力シーケンスの hotkey アクションで、①`Ctrl+ A` を OK すると一覧と保存値が `ctrl+a` になる ②`we+c` のような不明なキー名は OK でエラーになり窓が残る ③記録した hotkey・プリセットの適用は今どおり保存できる
- `.claude_data/state/decisions_archive/78_action_hotkey_save_validation.md` の作成と `decisions.md`「アーカイブ索引」への 1 行
- `instructions/phase/current.md` の完了記載（次採番 phase 79 / decisions 79）
- `instructions/backlog/INDEX.md` の idea_03 行を完了にして `INDEX_done.md` へ移動
- `/refactor_check` の実行と判定の記載

## 読むファイル

- `instructions/phase/78_action_hotkey_save_validation/phase.md`
- `instructions/common/codebase_map.md:912`
- 直近の完了フェーズの記録の手本: `.claude_data/state/decisions_archive/77_sample_in_user_folder.md`

## 含まない

- コードの変更（必要になれば task_03a 等の枝番で起票）
- 既存ファイルの移行（phase 78 の確定で対象外）

## 確認

- verifier の 4 項目が pass（既知の不安定テストは単独の再実行で切り分け）
- 実機目視 ①〜③ がユーザーから OK
- `grep -n "保存時には検査しない" instructions/common/codebase_map.md` が 0 件

## 完了条件

- 上記確認 pass・**完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）の採否をユーザーが確定**。
- 実機目視は本タスクで実施する。
