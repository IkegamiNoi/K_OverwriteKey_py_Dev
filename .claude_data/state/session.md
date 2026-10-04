# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-04T23:00:00
phase: **phase 45**（`instructions/phase/45_call_step_and_view`・呼び出しのステップ実行と呼び出し先の表示・暫定仕様先行モード・主入力 = 暫定 31 v0.5〔ユーザー確定済〕）。次採番 = phase 46 / 暫定 32 / decisions 46 / 提案書 19。
直前の完了フェーズ = **phase 44**（子ファイル保存ダイアログの高さと列幅・`decisions_archive/44_child_save_dialog_layout.md`）/ **phase 43**（一覧のドラッグ移動・範囲選択・複製・`decisions_archive/43_list_reorder_range_copy.md`）。
last_commit_location: `claude/keymap-spec-review-d08fed`（066c680 = phase 45 task_05）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 45 task_01〜05 実装完了（task_05 は実機目視待ち）。次は task_06（省略表示の枠）→ task_07（正本反映・フェーズ完了）。**
mode: in_progress（ユーザーがタスクの連続実行を許可。スペックフラグ・フォールバック・実機目視では止まる）

## last_action
ts: 2026-10-04T23:00:00
who: main
summary: |
  phase 45 を暫定 31 で起票し task_01〜05 を実装。実機目視中のユーザー判断で v0.5（ステップを標準・一括は JSON `all: true` / 表示 `[call all]`・チェックボックス「一括で実行」）。
  task_02・03 の統合確認（deep 採用 / codex P2）→ task_03a（入れ子の一括の後の区切り・送った印の持ち越し）。task_04 = 要約 CallViewSummary と runner の通知の口（call_view_notice.py）。
  task_05 = フル表示の枠（出力シーケンスの一覧の下・tk.PanedWindow・読み取り専用・config.json の call_view_heights）。メインで「保存した高さが開き直しで反映されない」（paneconfigure の再配置が sash_place を戻す）を修正。
result_files:
  - keyseq/application/{call_context,call_view}.py・application/sequence_runner/{call_wait,call_run_to_end,input_acceptance,send_wait,file_line_wait,wait_stop,call_view_notice}.py
  - keyseq/domain/sequence_control.py（is_step_call / is_all_call・表示名）・presentation/dialogs/action_control_fields.py
  - keyseq/presentation/{call_view_heights.py,controllers/call_view_controller.py,views/full_view/{call_view_frame,sequence_box}.py,app.py}
verified:
  compile: clean
  tests: 1191 OK（skipped 7）
  tests_ui: 803 OK（261 秒）
  smoke: pass
  review: task_01〜05 すべて reviewer 採用（task_03a・04・05 は修正要を経て採用）

## next_action
- task_05 の実機目視の結果を受け取る（①枠が開き ▶ が進み終わると閉じる ②連続実行の停止の行で開く ③境界線の高さが開き直し・再起動後も保たれる ④枠のクリックで何も起きない ⑤`[call all]` だけでは開かない）。
- task_06 を `/task_new` で起票・実装: 省略表示の枠（トリガー一覧の下・境界線・表示の切替で同じ文脈〔CallViewController.last_summary〕・高さは call_view_heights の compact）。暫定 31 §5.1・§5.2。
- task_07: 暫定 31 §12 の正本昇格（features §4.2.8〜4.2.10・§4.6 / data_schema §5.4・§5.11.6 / codebase_map）・暫定 31 の凍結・decisions_archive/45・current.md・/refactor_check。完了判定前に deep-reviewer + Codex 敵対的レビュー。
  deep-reviewer M1（文脈の「送った」に入れ子の呼び出しの成功を数えない＝実装のまま）を正本に明記する。

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる（複数の verifier や reviewer の UI テストと並行させない。フック・ダイアログの取り合いで止まる）。verifier には **`taskkill` で python.exe を一括終了しない**よう必ず書く（2026-10-04 に全 python が落ちた事故）。
  tests_ui は 260〜730 秒。タイムアウトは 1800 秒・出力はファイルへリダイレクト。
- **【phase 45】呼び出しの種類は JSON `all: true` = 一括 / 無し = ステップ（既定）**（`domain/sequence_control.is_step_call` / `is_all_call`）。段の印 `CallFrame.step`・文脈の `first_step`（`is_step_context`）・文脈の「送った」`ctx.sent`（停止の行の判定）・段の `frame.sent`（区切りの判定。区切りを返す時に最上段がステップなら下ろす = `call_context._clear_step_frame_sent`）。
  ステップの押下の合間 = 単発の呼び出しの一時停止（`call_paused`）。呼び出し先の停止の行 = 連続実行の一時停止（呼び出しが終わる形なら終える）。
  表示の要約 = `application/call_view.py`・通知 = runner の `call_view_notice.py`（止まった順・最後に止まった文脈・カウンターは `_commit_step_and_publish` で再通知）。UI = `controllers/call_view_controller.py`。
- **tk.PanedWindow の注意**: `panes()` は Tcl_Obj を返すので `str()` に揃えて比べる / `paneconfigure` の後は `update_idletasks()` してから `sash_place`（後の再配置で位置が戻る）/ テストで境界線をドラッグするときは押下の後に `update()`。
- **【phase 43・44 の成果は正本が正】一覧の操作 = `features.md` §4.6「一覧の操作」・§4.1・§4.3 / 子ファイル保存ダイアログ = §4.6「子ファイル保存ダイアログ」**（暫定 30 は凍結）。
- **【phase 40 の成果は正本が正】呼び出し = `features.md` §4.2.9 / 入力の受け付けと一時停止 = §4.2.10 / 待機 = §4.2.5 / 停止 = §4.2.8**。runner の mixin 構成は `codebase_map.md`「出力シーケンスの制御アクション」節。
  **テストで「戻す履歴が 1 段」を確かめるときは状態が変わるシーケンスにする**（状態が変わらなければ commit_step は積まない＝仕様どおり）。
- トリガー一覧へのアクセスは `domain/keymap_triggers.py` の口だけ（presentation に `"triggers"` 直値を書くと静的検査で落ちる）。
- **Codex のプラグインのレビュー系コマンドは推論レベルを渡せない**（`--model` のみ）。`CLAUDE_PLUGIN_ROOT` 未設定時は companion を絶対パスで呼ぶ。
- それ以前の完了フェーズの要点は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜30）の条項を実装の根拠に引かない。
