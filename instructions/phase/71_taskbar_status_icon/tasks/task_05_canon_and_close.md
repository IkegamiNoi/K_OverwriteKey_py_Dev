# task_05_canon_and_close

## 目的

phase 71 の実機目視・正本反映・フェーズ完了処理（`.claude/rules/task_execution.md`「フェーズ完了時」）。**文書のみ・コード不変**。

## 対象範囲（文書のみ）

- 実機目視（ユーザー）: 起動直後の赤■・開始 / 一時停止 / 停止でステータス欄と一致・簡易表示で追従・子窓（キーボードUI・ヘルプ）も追従・タスクバーの大きさで判別。
- 正本反映: `features.md` §4.5「タスクバーのアイコン」（暫定 54 の確定内容）・「バージョン情報・ライセンス」の `bundled_paths` のパスと土台の画像のライセンスの扱い〔暫定 54 §12〕 / `architecture.md`（presentation の同梱データ・status_icon・AppUserModelID）/ `codebase_map.md`（エントリーポイント・ツリー・`status_text`・ステータス・`win32_window`）。
- 暫定 54 の凍結・`decisions_archive/71_taskbar_status_icon.md`・`decisions.md` の索引・`current.md` の完了記載と次採番・idea_55 を `INDEX.md` → `INDEX_done.md`。
- `/refactor_check`（判定と記録）。

## 読むファイル

- `instructions/history/54_taskbar_status_icon.md`・上記の正本の該当節

## 含まない

- コードの変更（保留 2 件は `current.md`「別タスク化候補」）

## 確認

- `git grep "help/bundled_paths\|help.bundled_paths" -- instructions/common keyseq tests tests_ui` が 0 件
- 完了判定前レビュー（deep-reviewer + Codex 敵対的）

## 完了条件

- 実機目視 OK（2026-11-01 ユーザー）・完了判定前レビューの採用分を反映・**reviewer 採用**（完了判定前レビューで代替）。
