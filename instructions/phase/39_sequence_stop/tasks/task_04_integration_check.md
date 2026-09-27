# task_04_integration_check

## 目的

phase 39（task_01〜03）の差分全体を統合確認する（暫定 28 §6）。**コード変更なし**（指摘は枝番タスクへ）。

## 対象範囲（確認のみ）

- 範囲: `275ed4f..HEAD`（phase 39 起票の後から）
- 自動確認（verifier）: `compileall` / `unittest discover -s tests` / `-s tests_ui` / `tests.smoke_app`
- 統合レビュー: `deep-reviewer` + `codex-reviewer`（標準・`--base 275ed4f`）

## 完了条件

- 両レビューの結果を記録し、採用した指摘を枝番タスクで解消（結果: deep-reviewer 修正して採用 → task_04b / Codex 指摘なし）。
