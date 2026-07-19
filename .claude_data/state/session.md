# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-20T01:05:00
phase: （アクティブなし）フェーズ 03_startup_font_settings_cleanup 完了 2026-07-20。次フェーズ未確定（次採番 04）
last_commit_location: claude/phase-03-task-01-a60716（worktree: priceless-fermat-2a15c1）※現在地はセッション開始時の git 実測値が正

## current
focus: **フェーズ 03_startup_font_settings_cleanup 完了（task_01〜05・挙動不変・実機目視 OK）。次フェーズ未確定（ユーザー方針確認待ち）**。
mode: completed                  # phase 03 完了。次フェーズ着手はユーザー方針確認から。

## last_action
ts: 2026-07-20T01:05:00
who: main
summary: |
  【phase 03 task_05_finalize_records 完了 → フェーズ 03 完了】
  正本反映・記録（文書のみ・コード無変更）。実機目視ユーザー OK（2026-07-20）を受け最終化:
  - 正本昇格判断: **spec_detail 昇格不要**（startup/font_delta/coerce の担当層記述なし・grep 0件。
    担当層は architecture.md §3.5 により codebase_map.md が正）。暫定仕様 02 を **v1.0 で凍結**。
  - codebase_map.md 更新（startup_settings.py 追記 / theme.coerce_font_delta / App のフォント適用分割・
    起動設定読込委譲 / UiVars 引数化）/ decisions_archive/03 作成 + decisions.md 索引 / current.md 完了記載・次採番04 /
    backlog INDEX の idea_02 を INDEX_done へ移動。
  - **【罠再発・修正済】codebase_map.md / INDEX / INDEX_done を最初 main リポジトリ側パスへ誤編集**（worktree 未反映）→
    reviewer 差戻し（NG 2件）→ worktree 側へ再適用・main 側 revert → **reviewer 再レビュー採用（完了可）**。
  - /refactor_check: **不要**（M1〜M6 非該当。verifier がメトリクス収集・判定はメイン）。
result_files:
  - instructions/history/02_startup_font_settings_cleanup.md（凍結）
  - instructions/common/codebase_map.md（責務反映）
  - .claude_data/state/decisions_archive/03_startup_font_settings_cleanup.md（新規）
  - .claude_data/state/decisions.md（索引）/ instructions/phase/current.md（完了・次採番）
  - instructions/backlog/INDEX.md / INDEX_done.md（idea_02 移動）
  - instructions/phase/03_startup_font_settings_cleanup/tasks/task_05_finalize_records.md（新規・起票）
verified:
  compile: clean                 # task_05 はコード無変更。task_04 時点の全緑を維持
  test(tests): pass 86
  test(tests_ui): pass 20
  smoke: pass

## next_action
- **フェーズ 03 完了。次フェーズは未確定** → ユーザーに方針確認する。着手候補は `instructions/backlog/INDEX.md`:
  - [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化・優先度低・要設計）。
  - 案B（FontSettingsController 新設）: phase 03 で見送り。フォント設定拡張が必要になった時点で初期化順序設計を詰めて idea 化。
- 次フェーズ着手時は `/phase_start` で起票（次採番 phase 04）。暫定仕様が必要なら独立採番の暫定 03 を起票。

## blockers
- なし（フェーズ 03 完了・全緑・実機目視 OK・git は task_05 コミット待ちのみ）。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **設計の正は暫定仕様 `instructions/history/02_startup_font_settings_cleanup.md`（v1.0）**。phase.md は設計を再定義していない（参照のみ）。
  番号対応: phase 03 / 暫定 02 / decisions `decisions_archive/03_startup_font_settings_cleanup.md`（暫定仕様は独立採番）。
- **【罠】state ファイル（`.claude_data/`）は worktree のパスで編集する**。main リポジトリ側の絶対パスへ編集すると
  worktree の追跡ファイルに反映されず commit から漏れる（phase 02 で複数回遭遇）。
- 実装は codex-implementer が既定（agent_selection.md）。Codex は sandbox から `.venv` python を起動できないため、
  標準検証はメイン側/verifier が `.venv` で実行する分担。**Codex 申告のテスト結果は信用せず必ず verifier で実行する**。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- **app.py の行数計測は `wc -l`**（phase 03 完了時 448 行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元。
- **【罠再発・要徹底】codebase_map.md / backlog INDEX 等の instructions 配下も worktree のパスで編集する**。
  Read/Grep で main リポジトリ側の絶対パス（`...\K_OverwriteKey_py_Dev\instructions\...`）を掴むと、そのまま
  main 側を編集して worktree に反映されない（phase 03 task_05 で再発・reviewer が検出）。編集は必ず worktree ルート配下のパスで行う。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済: 計画04 / 01_view_ref_cleanup（2026-07-17）/ 02_hotkey_validation（2026-07-18）/ 03_startup_font_settings_cleanup（2026-07-20）。
- 未着手 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化・優先度低）。
  将来 idea 候補: 案B（FontSettingsController・初期化順序設計が前提）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
