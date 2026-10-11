# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-12T00:00:00
phase: instructions/phase/55_keyboard_ui_window（暫定 39 v0.3・ユーザー確定済 / decisions 55）。次採番 = phase 56 / 暫定 40 / decisions 56 / 提案書 21
直前の完了フェーズ = **phase 54**（テンキーの区別・`decisions_archive/54_numpad_key_distinction.md`）
last_commit_location: `claude/keyboard-input-priority-999558`（main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 55（キーボードUIのウィンドウ改善）task_01 完了・task_02（縦横比固定）着手。タスクの連続実行は許可済み（実機目視・スペックフラグでは止まる）。**
mode: implementing

## last_action
ts: 2026-10-12T00:00:00
who: main
summary: |
  phase 55 起票（暫定 39 v0.1 → deep-reviewer + Codex 敵対的レビュー反映 → ユーザー判断〔ダイアログ表示中は前面の窓の監視で一時解除 / 手を離して 150ms 後に補正 / 斜めは今の大きさに収まる最大の形・スナップ後の補正は受容〕→ v0.3 確定）。
  task_01（ステータス欄の削除・タイトル表示）完了: codex-implementer・reviewer 採用・tests 1529 / tests_ui 946 / smoke pass。
  task_02 のタスク定義を起票済み（未実装）。
result_files:
  - instructions/history/39_keyboard_ui_window.md / instructions/phase/55_keyboard_ui_window/（phase.md・tasks/task_01・task_02）/ instructions/phase/current.md
  - keyseq/presentation/keyboard_window.py / tests/test_keyboard_window_title.py（新規）/ tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: 1529 OK（skipped 7）
  tests_ui: 946 OK
  smoke: pass
  review: task_01 reviewer 採用

## next_action
- codex-implementer に `instructions/phase/55_keyboard_ui_window/tasks/task_02_aspect_ratio_resize.md` の実装を依頼 → verifier 実測 + reviewer → ユーザー実機目視（暫定 39 §6 の 1・2・8・10）
- その後 task_03（前面化・一時解除。着手時に所有関係を実測）のタスク定義を起票

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
