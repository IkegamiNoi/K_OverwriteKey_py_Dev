# task_04_integration_check

## 目的

phase 60 の task_01〜03（取得中の IME の OFF・`??` の統一）を通しで確かめる（暫定 44 §8）。
**コードは変えない（指摘で修正が要る場合はユーザーへ報告して判断を仰ぐ）。**

## 対象範囲（確認のみ）

* 統合退行: compileall / tests / tests_ui / smoke（`verifier`）
* 複数タスクを跨ぐ差分のレビュー: `deep-reviewer`（Claude 側）+ `codex-reviewer`（Codex 側・標準レビュー）。対象 = `c99719d..HEAD` のコードとテスト

## 読むファイル

1. `instructions/history/44_ime_off_during_key_capture.md`（§3〜§8）
2. `git diff c99719d..HEAD -- keyseq tests tests_ui`

## 含まない

* 正本・`codebase_map.md` の更新・暫定 44 の凍結・decisions_archive（task_05）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `unittest discover -s tests`・`unittest discover -s tests_ui`（同時に 1 本だけ）・`-m tests.smoke_app` が全 pass
* 暫定 44 §8 の 1〜6 の充足（実機目視は task_03 でユーザー OK・2026-10-16）

## 完了条件

- 上記確認 pass・deep-reviewer と codex-reviewer の指摘の採否をユーザーへ提示して決着（**reviewer 採用**相当は deep-reviewer が担う）。
- 実機目視は task_03 で実施済み。
