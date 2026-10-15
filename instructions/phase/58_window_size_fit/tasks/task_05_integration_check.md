# task_05_integration_check

## 目的

phase 58（task_01〜04）を統合として確認する。全体の退行テストと二次レビュー（`deep-reviewer` + `codex-reviewer`）を行う（暫定 42 §9）。
**確認のみ。実装コードは変えない**（レビューで修正が要ると判断したら枝番タスク task_05a 以降で行う）。

## 対象範囲（確認のみ）

- 退行テスト: compileall / tests / tests_ui / smoke（task_04 の最終検証は HEAD `da679a3` と同じコードで全 pass 済み = tests 1662 OK・tests_ui 1072 OK・smoke OK。コードを変えていないため本タスクの退行テストとして扱う）
- 統合レビュー: `deep-reviewer`（phase 58 の全差分 `git diff 33dea2a..HEAD`・暫定 42 v0.3 との適合・タスクをまたぐ整合）+ `codex-reviewer`（同じ範囲の標準レビュー）
- 重点: 暫定 42 §9 の受け入れ条件 1〜11 / phase.md「レビュー方針」の重点（今の最小以上で見た目が今と同じ・`<Configure>` の無限ループなし・ホイールを他の窓へ漏らさない・`compact_header_view` が無い / 不正でも起動しファイルを書き換えない・閉じた枠に見えないフォーカスを残さない・一時メッセージの文言が不変）/
  task_04 の追加修正（`app.show_full_view` で復元前に最小の大きさを解除）の副作用

## 読むファイル

- `instructions/history/42_window_size_fit.md`（全体）
- `instructions/phase/58_window_size_fit/phase.md`・`tasks/task_01〜04`
- `git diff 33dea2a..HEAD`

## 含まない

- 実装コードの変更（要修正なら task_05a として起票）
- 正本反映（task_06）

## 確認

- 上記の退行テストが全 pass（既知の実行順依存は current.md「テスト負債」のとおり切り分け）
- `deep-reviewer` と `codex-reviewer` の結果を受け取り、事実主張を `ファイル:行` で裏取りする

## 完了条件

- 上記確認 pass・**deep-reviewer と codex-reviewer の指摘の採否をユーザーと決め、要修正分を反映**（Codex 指摘の採否はユーザー確認）
