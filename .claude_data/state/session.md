# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-14T00:30:00
phase: instructions/phase/57_grid_crosshair_nudge（画面の枠の十字マーク・矢印でクリック位置の微調整・操作キーの任意化。主入力 = 暫定 41 v0.4・ユーザー確定済）。次採番 = phase 58 / 暫定 42 / decisions 58 / 提案書 23
直前の完了フェーズ = **phase 56**（画面の枠でカーソル移動・クリック・`decisions_archive/56_screen_grid_cursor.md`）
last_commit_location: `claude/crosshair-selection-frame-f4b464`（phase 57 の起票）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 57 起票済（暫定 41 v0.4 確定・phase.md・current.md）。次は task_01（domain の `grid.ops`）のタスク定義の起票と実装。**
mode: implementing

## last_action
ts: 2026-10-14T00:30:00
who: main
summary: |
  ユーザー要望（選んだ枠に十字・矢印でクリック位置の微調整・操作キーの任意化）を暫定 41 に起票。deep-reviewer「修正して採用」→ v0.2 / ユーザー判断（各操作のキーは 1 つ・Esc と num enter は固定）→ v0.3 /
  Codex 敵対的 needs-attention 2 件を採用 → v0.4 → ユーザー確定（2026-10-14）。
  phase 57 を起票（phase.md・current.md・decisions.md）。reviewer の整合チェック = 採用（軽微 1 件を反映）。
result_files:
  - instructions/history/41_grid_crosshair_nudge.md
  - instructions/phase/57_grid_crosshair_nudge/phase.md
  - instructions/phase/current.md
  - .claude_data/state/decisions.md
verified:
  compile/tests: not_run（文書のみ）
  review: deep-reviewer 修正して採用→反映 / codex-adversarial needs-attention→反映 / reviewer（整合）採用

## next_action
- `/task_new` で `instructions/phase/57_grid_crosshair_nudge/tasks/task_01_grid_ops_domain.md` を起票（暫定 41 §4・§8 の検査の純関数・既存の固定予約テストの書き換え）→ `codex-implementer` に実装を依頼 → verifier → reviewer
- 以降 phase.md のタスク順（task_02 振り分けとクリック点 → task_03 十字の描画〔実機目視〕→ task_04 操作キーの欄〔実機目視〕→ task_05 ドラッグ中の十字〔実機目視〕→ task_06 統合 → task_07 正本反映）

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- phase 56 の要点: 入力の振り分け = `application/input_router.py:76`（直接切替キーの後・トリガーの前に枠の判定を入れる）/ 開始・再開の判定 = `application/hook_coordinator.py:78` `_can_process_input` /
  keymap の `grid` が落ちる経路 4 つ = `domain/config.py:311`・`config_service/__init__.py:156-186`・`split_loading.py:439-455`・`split_payloads.py:507-521`（複製・貼り付けは既存のまま写る）/
  追加は `KeymapSwitchBatchDialog`（`keymap_add_flow.py`）・編集は `KeymapEditDialog` / Win32 は `infrastructure/win32_window.py` に置き presentation から ctypes を呼ばない
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜40）の条項を実装の根拠に引かない。
