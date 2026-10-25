# task_05_integration_review

## 目的

task_01〜04 をまとめた状態で統合確認（tests / tests_ui / smoke）と統合レビューを行い、暫定 52 §9 の受け入れ条件のうち自動で確かめられるものを満たしていることを確認する。
**コードは原則変えない（指摘への対応は枝番タスクで起票）。**

## 対象範囲（確認とレビューのみ）

- verifier: compileall / tests 全体 / tests_ui 全体（1 本だけ）/ smoke / 実 `config/` を汚していないこと
- 統合レビュー（`agent_selection.md` の「統合テスト・複数タスクを跨ぐ動作確認時」）: `deep-reviewer` + `codex-reviewer`。対象 = phase 69 の差分（`git diff <phase 69 起票直前のコミット>..HEAD`・コード）
  - 観点: 暫定 52 §3〜§8 との適合 / タスク間のつなぎ（task_03 の「目標の幅を決める 1 か所」と task_04 の記録の幅・表示名と文字合わせ）/ phase 55 の縦横比の補正の規則の維持 / config.json の書き手が増えていないこと
- §9 の受け入れ条件と自動テストの対応表を作り、実機目視でしか確かめられないもの（§9-1 の読めるか・§9-2a・実際の窓の大きさ）を task_06 の目視項目へ渡す

## 読むファイル

- `instructions/history/52_keyboard_ui_key_labels.md` §9
- 各タスク定義（task_01〜04）の確認節

## 含まない

- 実機目視・正本反映（task_06）

## 確認

- tests / tests_ui / smoke pass・件数が減らない
- 統合レビュー 2 本の指摘の採否をユーザーへ提示（修正が要るものは task_05a 等で起票）

## 完了条件

- 上記確認 pass・統合レビュー 2 本の結果の反映（または採否の確定）
