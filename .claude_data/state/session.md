# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-12T20:30:00
phase: instructions/phase/56_screen_grid_cursor（画面の枠でカーソル移動・クリック・暫定 40 v0.6 ユーザー確定済）。次採番 = phase 57 / 暫定 41 / decisions 57 / 提案書 22
直前の完了フェーズ = **phase 55**（キーボードUIのウィンドウ改善・`decisions_archive/55_keyboard_ui_window.md`）
last_commit_location: `claude/virtual-monitor-resolution-1c744e`（task_01 のコミット）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 56 task_01（画面・座標の検証スパイク）完了。次は task_02（`grid` の domain と JSON 全経路）の起票と実装。**
mode: implementing

## last_action
ts: 2026-10-12T20:30:00
who: main
summary: |
  実施: task_01 を起票し、scratchpad のプローブ（コミットしない）でユーザーの実機（VirtualBox ゲスト・主 (0,0)-(1920,966) / 主の上 (0,-768)-(1024,0)・100%）を測定。結果は task_01「結果」節。
  結論: 既定案（SYSTEM_AWARE のまま）で列挙の矩形・窓の位置・カーソル移動・クリック・フォーカスを取らない・クリック素通し・構成の変化の検出・連打がすべて OK（ユーザー目視も全項目問題なし）。
  ユーザー判断: カーソル移動・クリックの手段 = pyautogui（Mac 対応の予定のため既存のクリックと経路をそろえる・`_pause=False`・FAILSAFE は一時的に外す）。識別子は暫定 40 §3 のまま（矩形由来・`szDevice` は補助）。
  レビュー: reviewer = 修正して採用（識別子の書き方・記録漏れ・時間の注記を反映済）。
result_files:
  - instructions/phase/56_screen_grid_cursor/tasks/task_01_display_coordinate_spike.md（新規）
  - instructions/history/40_screen_grid_cursor.md（§6 に実構成を追記）/ .claude_data/state/decisions.md
verified:
  compile: not_run（文書のみ・製品コード変更なし）
  tests: not_run（文書のみ）
  review: reviewer 修正して採用 → 反映済

## next_action
- `/task_new` で task_02（`grid` の domain〔形のモデル・既定・正規化・セルの矩形・細分化・自動割当 / 振り直し・検証の純関数〕と JSON 全経路の保持・暫定 40 §3・§5）を起票し codex-implementer へ
- task_04 への申し送り: 自アプリの窓が前面のとき `tk.Toplevel` の作成で前面を取られる / フック動作中のクリック所要時間を一度測る / 右クリックを実機目視

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
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜39）の条項を実装の根拠に引かない。
