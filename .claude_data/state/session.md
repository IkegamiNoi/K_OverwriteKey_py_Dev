# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-06T22:00:00
phase: なし（**phase 47 完了** 2026-10-06）。次採番 = phase 48 / 暫定 33 / decisions 48 / 提案書 20。
直前の完了フェーズ = **phase 47**（アクションの追加・編集ダイアログの整理・`decisions_archive/47_action_dialog_layout_cleanup.md`）。
last_commit_location: `claude/jikki-mokushi-ok-5df544`（phase 47 完了まで。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 47 完了。次フェーズはユーザー判断待ち。**
mode: idle

## last_action
ts: 2026-10-06T22:00:00
who: main
summary: |
  task_01 実機目視 OK → 完了。task_02 起票・features.md §4.6 / codebase_map.md 追記。
  完了判定前 deep-reviewer 修正要（軽微）/ codex 敵対的 needs-attention → ユーザー承認で 指摘1 = 正本の文言を値・記録・プリセットまわりに絞る / 指摘2 = task_01a（記録中の hotkey 再選択で文言が戻る後退・codex-implementer・reviewer 採用）。
  refactor_check 不要。decisions_archive/47・decisions.md 索引・current.md 完了記載。
result_files:
  - keyseq/presentation/dialogs/action_dialog.py / tests_ui/test_action_dialog_control.py
  - instructions/common/{spec_detail/features.md,codebase_map.md} / instructions/phase/{current.md,47_action_dialog_layout_cleanup/}
  - .claude_data/state/{decisions.md,decisions_archive/47_action_dialog_layout_cleanup.md}
verified:
  compile: clean
  tests: 1308 OK（skipped 7）
  tests_ui: 840 OK
  smoke: pass
  review: task_01a = reviewer 採用 / フェーズ完了 = deep-reviewer + codex 敵対的（指摘対応済み）

## next_action
- 次フェーズはユーザー判断（着手時は `/phase_start`）。候補 = idea_37（カウンター条件分岐）/ idea_39（表示中のトリガーを戻す・先頭への対象に）ほか backlog。

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しない**よう必ず書く。tests_ui は 150〜730 秒。
- **素の `python` を Bash で呼ばない**（ストア版スタブでハングする。必ず `..\..\..\.venv\Scripts\python.exe`）。
- **【phase 47】`ActionDialog` の表示切替は `_sync_capture_ui` → `_sync_type_visibility` / `_sync_hotkey_controls` / `_sync_mouse_visibility`**。
  `_rebuild_preset_buttons` は `__init__` の途中（preset_edit_btn 作成前）で呼ばれるため、そこから `_sync_capture_ui` を呼ばない。
  `winfo_ismapped()` のテストは `update()` で表示を待つ（`update_idletasks()` では初回が False）。
- **【戻す・先頭へ】対象 = `target` があればそれ・無ければ直前のトリガー**（正本 `features.md` §4.2.6）。表示中のトリガーを対象にする案は idea_39。
- トリガー一覧へのアクセスは `domain/keymap_triggers.py` の口だけ（presentation に `"triggers"` 直値を書くと静的検査で落ちる）。
- **Codex のプラグインのレビュー系コマンドは推論レベルを渡せない**。`CLAUDE_PLUGIN_ROOT` 未設定時は companion を絶対パスで呼ぶ。
- それ以前の完了フェーズの要点は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜32）の条項を実装の根拠に引かない。
