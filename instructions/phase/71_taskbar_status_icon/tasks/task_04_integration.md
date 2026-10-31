# task_04_integration

## 目的

task_02・03 を通した統合確認。暫定 54 §10 の受け入れ条件のうち、テストと静的な確認で示せるもの（1・3〔`-default` の 1 回〕・4・5・5a・6・7）を確かめ、二次レビューを行う。
**新規の機能は足さない**（指摘の修正だけ）。

## 対象範囲（確認と指摘の修正のみ）

- verifier: `compileall` / tests / tests_ui / smoke（tests_ui は 1 回だけ）。
- 二次レビュー: `deep-reviewer`（複数タスクを跨ぐ差分 `666c03b..HEAD`）+ `codex-reviewer`（同範囲の標準レビュー）。
- 指摘の修正（採否はユーザー確認を経る・Codex 指摘は提示のみ）。

## 読むファイル

- `instructions/history/54_taskbar_status_icon.md` §10
- `git diff 666c03b..HEAD -- keyseq main.py tests tests_ui`

## 含まない

- 実機目視・正本反映・凍結・フェーズ完了（task_05）

## 確認

- `compileall -q keyseq main.py tests tests_ui` clean / tests 全 pass / tests_ui 全 pass / `-m tests.smoke_app` OK
- 二次レビュー 2 種の結果と採否の記録

## 完了条件

- 上記確認 pass・二次レビューの採用分を反映・**reviewer 採用**（修正があった場合はその差分）。
- 実機目視は task_05。
