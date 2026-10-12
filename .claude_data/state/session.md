# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-12T13:00:00
phase: なし（phase 55 は 2026-10-12 完了）。次採番 = phase 56 / 暫定 40 / decisions 56 / 提案書 22。次フェーズはユーザー判断
直前の完了フェーズ = **phase 55**（キーボードUIのウィンドウ改善・`decisions_archive/55_keyboard_ui_window.md`）。その前 = phase 54（テンキーの区別）/ phase 53（アプリの窓が前面のときはキーリピートしない）
last_commit_location: `claude/keyboard-input-priority-999558`（phase 55 完了まで。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 55 完了。アクティブなフェーズなし・次フェーズはユーザー判断待ち。main へのマージはユーザー。**
mode: completed

## last_action
ts: 2026-10-12T13:00:00
who: main
summary: |
  phase 55 完了（暫定 39 v0.6 凍結・正本 `features.md` §4.6「キーボード表示のウィンドウ」）。ステータス欄を削除しタイトルへ / 「キーボードUIを常に手前」〔保存しない・ダイアログ前面 or grab 中は一時解除しダイアログ直下へ〕/ 縦横比固定〔手を離して 150ms 後・マウスのボタンが離れた後〕。
  実機目視で 2 回 NG（リサイズの基準ずれ → ボタン判定 / ダイアログが覆われる → 直下へ置く）を修正。統合・完了判定前レビューの指摘は task_04b・05a で修正・一部受容。
  /refactor_check 推奨（M3）→ 提案書 21 をユーザー判断で task_06_refactor として実施（`infrastructure/win32_window.py`）。
result_files:
  - keyseq/infrastructure/win32_window.py（新規）/ input_gateway.py / keyseq/presentation/keyboard_window.py・keyboard_window_size.py（新規）・controllers/layout_controller.py・app.py・ui_vars.py・views/*/display_frame.py
  - tests/test_win32_window.py・test_keyboard_window_size.py・test_keyboard_window_title.py（新規）/ tests_ui/test_app_ui_flows.py ほか
  - instructions/history/39（凍結）/ instructions/phase/55_keyboard_ui_window/ / spec_detail/features.md / codebase_map.md / decisions_archive/55 / modified_proposal/21（実施済）
verified:
  compile: clean
  tests: 1550 OK（skipped 7）
  tests_ui: 959 OK
  smoke: pass
  review: 各タスク reviewer 採用 / 統合 deep + codex / 完了判定前 deep + codex-adversarial の指摘は反映・受容を decisions_archive/55 に記録

## next_action
- 次フェーズはユーザー判断（着手時は `/phase_start`）。main へのマージはユーザーが行う
- 別タスク化候補に keyboard_window の同型 2 個（current.md「キーボード表示（phase 55 由来）」）を追記済み

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**（phase 54 でも新規テストの期待値・Mock の戻り値の誤りが 2 件）。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- キー入力の要点: 押下中の集合 = `application/held_inputs.py` / リピート = `application/key_repeat.py`（`is_blocked` = 前面判定・発火時だけ）/ 送信・同じキー・名前の検査 = `infrastructure/input_gateway.py` / テンキーの名前 = `domain/numpad_keys.py`（入力）・`presentation/tk_keys.py`（記録）。正本は `key_input.md` §7.7・§7.8・`features.md` §4.2.12
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜38）の条項を実装の根拠に引かない。
