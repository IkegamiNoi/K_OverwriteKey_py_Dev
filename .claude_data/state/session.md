# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-12T04:00:00
phase: instructions/phase/55_keyboard_ui_window（暫定 39 v0.4・ユーザー確定済 / decisions 55）。次採番 = phase 56 / 暫定 40 / decisions 56 / 提案書 21
直前の完了フェーズ = **phase 54**（テンキーの区別・`decisions_archive/54_numpad_key_distinction.md`）
last_commit_location: `claude/keyboard-input-priority-999558`（task_02・02b まで。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 55（キーボードUIのウィンドウ改善）task_01・02・02b 完了・task_03（キーボードUIを常に手前 + ダイアログ表示中の一時解除）着手。タスクの連続実行は許可済み（実機目視・スペックフラグでは止まる）。**
mode: implementing

## last_action
ts: 2026-10-12T04:00:00
who: main
summary: |
  task_02（縦横比固定）初回の実機目視で「縮めると大きく・広げると小さく」NG → 原因 = ドラッグ中に止まった間の補正を Windows のサイズ変更ループが上書きし基準がずれる。
  ユーザー確定で暫定 39 v0.4（マウスのボタンが押されている間は補正しない）→ task_02b（infrastructure `is_mouse_button_down`・App 注入・`_settle_size` 延期）。Codex が消した BOM 2 件（input_gateway.py / app.py）をメインで復元。
  verifier: tests 1542 / tests_ui 949 / smoke pass。reviewer 採用。ユーザー実機目視 OK。Codex 敵対的レビュー（v0.4）2 件はユーザー判断で受容（他アプリのドラッグ中は補正が延びる / Alt+Space のキーボードでのサイズ変更は保証外）として §5 に明記。
result_files:
  - keyseq/presentation/keyboard_window_size.py（新規）/ keyboard_window.py / controllers/layout_controller.py / app.py / keyseq/infrastructure/input_gateway.py
  - tests/test_keyboard_window_size.py（新規）/ tests/test_input_gateway_repeat.py / tests_ui/test_app_ui_flows.py
  - instructions/history/39_keyboard_ui_window.md（v0.4）/ instructions/phase/55_keyboard_ui_window/（phase.md・tasks/task_02b）
verified:
  compile: clean
  tests: 1542 OK（skipped 7）
  tests_ui: 949 OK
  smoke: pass
  review: task_02・02b reviewer 採用・ユーザー実機目視 OK

## next_action
- task_03（「キーボードUIを常に手前」+ ダイアログ表示中の一時解除・暫定 39 §4）のタスク定義を起票 → 着手時に所有関係（`GetWindow(hwnd, GW_OWNER)`）を実測（成り立たなければ止めてユーザー確認）→ codex-implementer → verifier + reviewer → ユーザー実機目視（§6 の 5・7）
- 前面の窓の判定は `infrastructure/input_gateway.py` の前面窓 API（`_foreground_process_api`）の再利用・App で注入（task_02b の `is_mouse_button_down` と同じ経路）

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
