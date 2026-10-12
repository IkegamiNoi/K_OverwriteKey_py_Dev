# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-12T11:00:00
phase: instructions/phase/55_keyboard_ui_window（暫定 39 v0.6・ユーザー確定済 / decisions 55）。次採番 = phase 56 / 暫定 40 / decisions 56 / 提案書 22
直前の完了フェーズ = **phase 54**（テンキーの区別・`decisions_archive/54_numpad_key_distinction.md`）
last_commit_location: `claude/keyboard-input-priority-999558`（task_04・04b まで。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 55 task_05（正本反映・暫定 39 凍結・decisions_archive/55）済み。追加タスク task_05a（保留比率の minsize）→ task_06_refactor（提案書 21）進行中。**
mode: implementing

## last_action
ts: 2026-10-12T07:00:00
who: main
summary: |
  task_03（キーボードUIを常に手前 + ダイアログ表示中の一時解除）: 所有関係は probe で None（前提成立）。codex-implementer・reviewer 採用。表示欄の行追加で tests_ui の `test_compact_sequence_view` の固定高さ 820 が不足 → 860 へ（メイン・原因を実測で切り分け）。
  初回目視で「ダイアログがキーボードUIに覆われる」NG → 原因 = topmost を外すと非 topmost の最上位へ来る（probe 確認）→ 暫定 39 v0.5・task_03b（infrastructure `place_window_below` = SetWindowPos でダイアログ直下へ）。
  verifier: tests 1550 / tests_ui 953 / smoke pass。reviewer 採用。ユーザー実機目視 OK。
result_files:
  - keyseq/infrastructure/input_gateway.py（foreground_own_window・place_window_below）/ keyseq/presentation/app.py・ui_vars.py・controllers/layout_controller.py・views/*/display_frame.py
  - tests/test_input_gateway_repeat.py / tests_ui/test_app_ui_flows.py・test_compact_sequence_view.py
  - instructions/history/39_keyboard_ui_window.md（v0.5）/ instructions/phase/55_keyboard_ui_window/（phase.md・tasks/task_03・03b）
verified:
  compile: clean
  tests: 1550 OK（skipped 7）
  tests_ui: 953 OK
  smoke: pass
  review: task_03・03b reviewer 採用・ユーザー実機目視 OK

## next_action
- task_05（正本反映）: 暫定 39 v0.6 §8 の昇格（features.md §4.6 に「キーボード表示のウィンドウ」新設〔deep 統合レビュー指摘 5 の書く事項〕・モーダルダイアログの作法の残存リスク追記・codebase_map :306 / :593 / :604 / 前面判定の節・新規モジュール）・暫定 39 凍結・phase.md の目的 / 主入力の記述更新・decisions_archive/55・decisions.md 索引・current.md 完了記載・/refactor_check（verifier でメトリクス）・完了判定前 deep-reviewer + codex-adversarial-reviewer

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
