# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-06T10:00:00
phase: **なし**（phase 45 は 2026-10-05 完了・`instructions/phase/45_call_step_and_view`・暫定 31 v0.6 凍結）。次採番 = phase 46 / 暫定 32 / decisions 46 / 提案書 20。
直前の完了フェーズ = **phase 45**（呼び出しのステップ実行と呼び出し先の表示・`decisions_archive/45_call_step_and_view.md`）/ phase 44 / phase 43。
last_commit_location: `claude/sequential-trigger-cancellation-priority-8eebac`（phase 45 完了。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 45 完了（提案書 19 も task_12_refactor で実施済み）。次フェーズはユーザー判断待ち。**
mode: idle

## last_action
ts: 2026-10-06T10:00:00
who: main
summary: |
  task_06 の実機目視 OK → task_07（正本反映: features.md §4.2.3・4.2.5・4.2.6・4.2.8・4.2.9 全面改訂・4.2.10・4.6 呼び出し先の表示枠 / data_schema.md §5.4・§5.11.6 / codebase_map.md）。
  完了判定前レビュー: deep-reviewer 修正要 / codex 敵対的 needs-attention → 転記の誤りを修正、M1〜M4 はユーザー判断（M1 一時停止で書き戻して積む＝実装のまま / M2 実行中の単発の呼び出しは呼び出し先の変更で取り消し / M3 受容 / M4 一時停止中の呼び出し先は捨てて進める）。
  task_07a（M2・M4・codex-delegating）→ reviewer 採用。暫定 31 凍結・decisions_archive/45・索引・current.md。/refactor_check = 推奨 → 提案書 19 → ユーザー判断で task_12_refactor として実施（sequence_runner.py 649 → 377 行・run_to_end.py 新設・apply_control 104 → 39 行・reviewer 採用・件数不変）。
result_files:
  - instructions/common/spec_detail/{features,data_schema}.md・instructions/common/codebase_map.md
  - keyseq/application/{call_context.py,sequence_runner/{sequence_runner,input_acceptance,call_wait,call_run_to_end}.py}・tests/test_sequence_runner_call.py
  - instructions/history/31（凍結）・decisions_archive/45・instructions/modified_proposal/19_refactor_call_step_and_view.md
verified:
  compile: clean
  tests: 1292 OK（skipped 7）
  tests_ui: 824 OK
  smoke: pass
  review: task_07 = deep-reviewer + codex-adversarial（指摘は修正・ユーザー判断済み）/ task_07a = reviewer 採用

## next_action
- ユーザー判断: 次フェーズ（候補は current.md「次フェーズ候補」）。
- main へのマージはユーザー。

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる（複数の verifier や reviewer の UI テストと並行させない。フック・ダイアログの取り合いで止まる）。verifier には **`taskkill` で python.exe を一括終了しない**よう必ず書く（2026-10-04 に全 python が落ちた事故）。
  tests_ui は 260〜730 秒。タイムアウトは 1800 秒・出力はファイルへリダイレクト。
- **【phase 45】呼び出しの種類は JSON `all: true` = 一括 / 無し = ステップ（既定）**（`domain/sequence_control.is_step_call` / `is_all_call`）。
  **v0.6 = 参照による連動**: 写し・呼び出し文脈の常駐は無い。押下（連続実行はステップ）ごとに各トリガー自身の状態から `CallContext` を組み立て（`call_context.start_linked_call`）、終わりに書き戻す（`sequence_runner/linked_call.py`）。
  参照中の印 = `AppState.call_refs_for`・連鎖 = `application/call_chain.chain_from`・履歴は押下の番号つきで各トリガーへ（`sequence_history.commit_press`・戻すは同じ番号の一番上の段をまとめて）。表示 = `SequenceRunner.call_view_summary_for(key)` を選んでいるトリガーで問い合わせ（通知は引数なし）。
  Codex は python を実行できず修正の往復が増えやすい → 修正依頼には verifier の失敗（テスト名・assert・行）をそのまま渡し、実装かテストかを条項つきで判断させる。
- **tk.PanedWindow の注意**: `panes()` は Tcl_Obj を返すので `str()` に揃えて比べる / `paneconfigure` の後は `update_idletasks()` してから `sash_place`（後の再配置で位置が戻る）/ テストで境界線をドラッグするときは押下の後に `update()`。
- **【phase 43・44 の成果は正本が正】一覧の操作 = `features.md` §4.6「一覧の操作」・§4.1・§4.3 / 子ファイル保存ダイアログ = §4.6「子ファイル保存ダイアログ」**（暫定 30 は凍結）。
- **【phase 40 の成果は正本が正】呼び出し = `features.md` §4.2.9 / 入力の受け付けと一時停止 = §4.2.10 / 待機 = §4.2.5 / 停止 = §4.2.8**。runner の mixin 構成は `codebase_map.md`「出力シーケンスの制御アクション」節。
  **テストで「戻す履歴が 1 段」を確かめるときは状態が変わるシーケンスにする**（状態が変わらなければ commit_step は積まない＝仕様どおり）。
- トリガー一覧へのアクセスは `domain/keymap_triggers.py` の口だけ（presentation に `"triggers"` 直値を書くと静的検査で落ちる）。
- **Codex のプラグインのレビュー系コマンドは推論レベルを渡せない**（`--model` のみ）。`CLAUDE_PLUGIN_ROOT` 未設定時は companion を絶対パスで呼ぶ。
- それ以前の完了フェーズの要点は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜30）の条項を実装の根拠に引かない。
