# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-06T18:00:00
phase: なし（アクティブなフェーズ無し）。次採番 = phase 47 / 暫定 33 / decisions 47 / 提案書 20。
直前の完了フェーズ = **phase 46**（戻す・先頭への対象トリガー指定・`decisions_archive/46_back_rewind_target.md`）。
last_commit_location: `claude/physical-device-verification-d3c460`（phase 46 完了まで。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 46 完了（2026-10-06・正本反映・暫定 32 凍結・refactor_check 不要）。次フェーズはユーザー判断待ち。**
mode: completed

## last_action
ts: 2026-10-06T18:00:00
who: main
summary: |
  task_03: ユーザー実機目視 OK で完了。task_04: 暫定 32 を正本（features.md §4.1・§4.2.6・§4.2.10・§4.6 / data_schema.md §5.11.6 / codebase_map.md）へ昇格・凍結。
  完了判定前レビュー: deep-reviewer 完了可（低 L1〜L8・L3/L4/L7 は正本の文言修正・他は保留）/ codex 敵対的 needs-attention 1 件
  （2 回押しの破棄で直前のトリガーが指定先になる）→ ユーザー判断で受容し §4.2.6 に明記。表示中のトリガーを対象にする案は idea_39 に起票（ユーザー提案）。
  /refactor_check = 不要（M4 境界は current.md「別タスク化候補」へ 1 行）。decisions_archive/46 作成・decisions.md 索引・current.md 完了記載。
result_files:
  - instructions/common/{spec_detail/features.md,spec_detail/data_schema.md,codebase_map.md}
  - instructions/history/32_back_rewind_target.md
  - instructions/backlog/{idea_39_back_rewind_visible_trigger.md,INDEX.md}
  - instructions/phase/{current.md,46_back_rewind_target/phase.md,46_back_rewind_target/tasks/task_04_canonical_reflection.md}
  - .claude_data/state/{decisions.md,decisions_archive/46_back_rewind_target.md}
verified:
  compile: clean（task_03 時点・task_04 は文書のみ）
  tests: 1308 OK（skipped 7）
  tests_ui: 829 OK
  smoke: pass
  review: deep-reviewer 完了可 / codex 敵対的 1 件（受容）

## next_action
- 次フェーズをユーザーに確認する（候補: idea_39 表示中のトリガーを戻す・先頭への対象にする / idea_37 カウンター条件分岐）。着手時は `/phase_start`。

## blockers
- なし（次フェーズはユーザー判断待ち）

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しない**よう必ず書く。tests_ui は 150〜730 秒。
- **素の `python` を Bash で呼ばない**（ストア版スタブでハングする。必ず `..\..\..\.venv\Scripts\python.exe`）。
- **【戻す・先頭へ】対象 = `target` があればそれ・無ければ直前のトリガー**（正本 `features.md` §4.2.6）。`target` の判定は `domain/sequence_control.control_target` の 1 か所。
  idea_39 に着手するなら、対象の決定は `application/sequence_history.apply_control`・押下で選択が移るのは `sequence_runner/run_to_end.py:38` 等。
- **【phase 45 の成果は正本が正】** 呼び出し・参照中の印・まとめて戻すは `features.md` §4.2.6・§4.2.9・§4.2.10。runner の mixin 構成は `codebase_map.md`「出力シーケンスの制御アクション」節。
- トリガー一覧へのアクセスは `domain/keymap_triggers.py` の口だけ（presentation に `"triggers"` 直値を書くと静的検査で落ちる）。
- **Codex のプラグインのレビュー系コマンドは推論レベルを渡せない**。`CLAUDE_PLUGIN_ROOT` 未設定時は companion を絶対パスで呼ぶ。
- それ以前の完了フェーズの要点は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜32）の条項を実装の根拠に引かない。
