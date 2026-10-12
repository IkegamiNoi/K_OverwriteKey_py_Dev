# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-12T18:00:00
phase: instructions/phase/56_screen_grid_cursor（画面の枠でカーソル移動・クリック・暫定 40 v0.6 ユーザー確定済）。次採番 = phase 57 / 暫定 41 / decisions 57 / 提案書 22
直前の完了フェーズ = **phase 55**（キーボードUIのウィンドウ改善・`decisions_archive/55_keyboard_ui_window.md`）
last_commit_location: `claude/screen-grid-cursor-tool-2cd348`（phase 56 起票 `c58a817`。以降の未コミット = 暫定 40 §6 の検証環境の追記・本ファイル・handoff.md）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 56 起票済・task_01（画面・座標の検証スパイク）未着手。ユーザーが VirtualBox のゲストを仮想モニタ 2 台（縦並び）にするため一時シャットダウン中。**
mode: implementing

## last_action
ts: 2026-10-12T18:00:00
who: main
summary: |
  実施: ユーザー要望（画面の枠でカーソル移動・クリック）から暫定 40（`instructions/history/40_screen_grid_cursor.md`）を起票し v0.6 でユーザー確定、phase 56 を起票（phase.md・current.md・decisions.md）してコミット `c58a817`。
  レビュー: 起票時 deep-reviewer（修正要 16 件 → v0.2 反映）/ Codex 敵対的（needs-attention 5 件 → v0.4 全件採用・DPI の前提訂正〔pyautogui が import 時に SetProcessDPIAware〕）/ phase.md 整合 reviewer（重大なし・軽微 2 件反映）。
  ユーザー判断: 追加ダイアログの新規の行にも「枠を使う」/ 枠だけでもフック開始・再開可 / 最上段の Esc は素通し・BackSpace は suppress / 検証環境 = VirtualBox ゲストに仮想モニタ 2 台縦並び（2 枚目を主の上 = 負の y）・100%・拡大率の混在は検証せず受容（暫定 40 §6 に追記）。
result_files:
  - instructions/history/40_screen_grid_cursor.md（新規）
  - instructions/phase/56_screen_grid_cursor/phase.md（新規）
  - instructions/phase/current.md / .claude_data/state/decisions.md
verified:
  compile: not_run（文書のみ）
  tests: not_run（文書のみ）
  review: 暫定 40 = deep-reviewer + codex-adversarial 反映済 / phase.md = reviewer 整合確認済

## next_action
- ユーザーが仮想モニタ 2 台（Windows の表示設定で 2 枚目を主モニタの上）にして戻ったら、モニタ数と配置（2 枚目が主の上か）をユーザーに確認する
- `/task_new` で `instructions/phase/56_screen_grid_cursor/tasks/task_01_display_coordinate_spike.md` を起票（暫定 40 §6 の 0〜5 と末尾の抜き差し・連打。本番の起動経路 = `main.py` と同じ import 順・Tk 初期化後で測る）
- task_01 の実測スクリプト（scratchpad に置く検証用 probe・製品コードではない）を用意し、ユーザーの実機で実行・目視してもらう。既定案（DPI の状態は今のまま）で座標が一致しなければ止めてユーザーへ §6 の (a)〜(c) を確認
- task_01 完了後に task_02（`grid` の domain と JSON 全経路）を codex-implementer へ

## blockers
- ユーザーの検証環境の準備待ち（仮想モニタ 2 台）

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
