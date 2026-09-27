# task_06_integration_check

## 目的

phase 38（task_01〜05）の差分全体を統合確認する（暫定 27 §8 の受け入れ条件）。**コード変更なし**（指摘があれば枝番タスクを起票）。

## 対象範囲（確認のみ）

- 範囲: `734bc8f..HEAD`（phase 38 起票コミットの後から）
- 自動確認（verifier）: `compileall` / `unittest discover -s tests` / `-s tests_ui` / `tests.smoke_app`（task_05 の verifier 実測を流用可: 866 / 615 / SMOKE OK）
- 統合レビュー: `deep-reviewer`（複数タスク跨ぎ）+ `codex-reviewer`（標準レビュー・`--base 734bc8f`）
  - 観点: 暫定 27 §8 の受け入れ条件 1〜10 がテストで担保されているか / スレッド共有状態のロック / 戻す履歴 1 段 / 取り消し・一時停止・停止の全経路 / 待ち合わせ・キャッシュ世代

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §3〜§8
- `git diff 734bc8f..HEAD -- keyseq tests`

## 含まない

- 正本・codebase_map の更新・暫定 27 の凍結・`/refactor_check`（task_07）
- 実機目視（task_05・ユーザー）

## 確認

- 上記自動確認が全 pass・両レビューの指摘の採否をユーザー判断（修正が要るものは枝番タスク `task_06b_*` を起票）

## 完了条件

- 統合レビュー 2 本の結果を報告し、修正要の指摘が解消済み（または保留とユーザー判断済み）。
