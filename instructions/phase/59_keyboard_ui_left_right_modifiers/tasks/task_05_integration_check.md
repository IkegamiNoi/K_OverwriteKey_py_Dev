# task_05_integration_check

## 目的

phase 59（task_01〜04b）を統合として確認する。全体の退行テストと二次レビュー（`deep-reviewer` + `codex-reviewer`）を行う（暫定 43 v0.6 §5）。
**確認のみ。実装コードは変えない**（レビューで修正が要ると判断したら枝番タスク task_05a 以降で行う）。

## 対象範囲（確認のみ）

- 退行テスト: compileall / tests / tests_ui / smoke（task_04b の最終検証は HEAD `9e13d20` と同じコードで全 pass 済み = tests 1671 OK・tests_ui 1091 OK・smoke OK。コードを変えていないため本タスクの退行テストとして扱う）
- 統合レビュー: `deep-reviewer`（phase 59 の全差分 `git diff 224762e..HEAD`・暫定 43 v0.6 との適合・タスクをまたぐ整合）+ `codex-reviewer`（同じ範囲の標準レビュー）
- 重点: phase.md「レビュー方針」の重点（左の枠のキー名は今のまま・判定はキー名で・禁止の判定は 1 か所・切替キーの検査は変えたときだけ・既存データを拒否しない / 消さない・入力の経路 / フック / 送信を変えていない）/
  task_04a / 04b（`??` の無視と案内）の他の取得のダイアログへの影響の有無 / `de.json`・`jis.json` の追跡（.gitignore の config/ に当たるため強制追加）

## 読むファイル

- `instructions/history/43_keyboard_ui_left_right_modifiers.md`（全体）
- `instructions/phase/59_keyboard_ui_left_right_modifiers/phase.md`・`tasks/task_01〜04b`
- `git diff 224762e..HEAD`

## 含まない

- 実装コードの変更（要修正なら task_05a として起票）/ 正本反映（task_06）

## 確認

- 上記の退行テストが全 pass
- `deep-reviewer` と `codex-reviewer` の結果を受け取り、事実主張を `ファイル:行` で裏取りする

## 完了条件

- 上記確認 pass・**deep-reviewer と codex-reviewer の指摘の採否をユーザーと決め、要修正分を反映**（Codex 指摘の採否はユーザー確認）
