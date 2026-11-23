# task_03_integration_and_promotion

## 目的

phase 79 の統合確認と正本反映（暫定 60 §9・`task_execution.md`「フェーズ完了時」）。コードは変えない。

## 対象範囲（文書のみ・メインが行う）

1. 統合確認: task_01（Windows・tests 2279 / test_help_window 25 / smoke・実機目視 25 行）と task_02（Mac・tests 2217 / test_help_window 25 / smoke・実機目視 21 行）の結果を最終のコードで得ている（task_02 の検証は最終の状態）。追加の実行はしない
2. 正本 `instructions/common/spec_detail/features.md`「バージョン情報・ライセンス」へ昇格（暫定 60 §3・§4・§4.1・§6 Q1〜Q5 と PSL の扱い）: 各 OS の件数と C ライブラリの行・行の決め方・照合と除外・出荷ごとの棚卸し・README の VC++ の一文・「idea_65（未決）」の置き換え
3. `instructions/common/codebase_map.md` の third_party の件数の追従（14 → 32 個 / 35 行）
4. 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（`agent_selection.md`）。指摘の採否はユーザー
5. 暫定 60 の凍結（v0.7・状態の行）・`decisions_archive/79_bundled_c_library_licenses.md`・`decisions.md` のアーカイブ索引
6. `instructions/phase/current.md` の完了記載（次採番 phase 80 / 暫定 61 / decisions 80）・暫定 60 の凍結表記
7. idea_65 を `instructions/backlog/INDEX.md` → `INDEX_done.md`
8. `/refactor_check`

## 含まない

- コード・データ・テストの変更（task_01 / 02 で完了）・`.spec`・ビルドの手順

## 完了条件

- レビューの指摘の採否が済み、上の 2〜8 が反映されている
