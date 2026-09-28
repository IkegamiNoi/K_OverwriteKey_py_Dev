# task_09b_integration_review_fixes

## 目的

task_09 の統合レビュー（deep-reviewer / Codex 標準）で採用した指摘を直す（暫定 29 v0.5・判断は decisions.md「task_09 統合レビュー」）。**application・presentation の小修正とテスト**。

> 注意: 仕様書の `f5` は例示のキー。実装・テストは実際のキーを使う。

## 対象範囲

1. **M1**（`keyseq/application/sequence_steps.py` `format_system_error_notification`）: `call` の値の欄を `call 呼び出し先=<target を trim した値>`（空・非文字列なら `call 呼び出し先=(なし)`）にする。
2. **M2**（`keyseq/application/sequence_runner/call_run_to_end.py`）: エラー通知・送信失敗・file_line の失敗の**後**の照合は、世代・キー・トークン・文脈の同一性だけで行い、**一時停止を条件に含めない**
   （一時停止中でもエラーとして `_fail_run_to_end_call` → 停止）。成功の後の照合は従来どおり一時停止を含めてよい。
   あわせて `call_context.py` の `_advance_call` で、**最初の段を積むのに失敗したら `started` を False へ戻す**（再度呼ばれても成功扱いの `done` を返さない）。
3. **M3**（`keyseq/application/call_context.py`）: `call_step` / `finish_call_action` の 1 回の呼び出しの中で、`advance` / `settle_after_normal` が処理した system の数（`processed`）を**入れ子をまたいで通して**数え、
   10,000 を超えたら `CallStep(kind="error", message="制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）", chain=...)`。
4. **L1**（`call_context.py`）: 循環のエラーの文言から経路を外し「呼び出しが循環します（<キー>）」にする（連鎖は通知の ` / 呼び出し: …` で出るので二重にしない）。編集時の文言（`call_graph.edit_call_violation`）は経路つきのまま。
5. **L7**（`keyseq/presentation/dialogs/action_control_fields.py`）: 参照先なしの項目を選んだまま OK したとき、`call_check` があれば先に `call_check(その target)` を呼び、文言が返ればそれを出す（自分自身なら「自分自身は呼び出せません」）。無ければ従来の「呼び出し先のトリガーがありません（<キー>）」。
6. **L2**（`tests_ui/test_action_list_rendering.py`）: `test_delay_heading_mentions_call_usage` を中身に合う名前（見出しが「間隔(ms)」のまま）に変える。
7. **M4 テスト補完**（`tests/test_sequence_runner_call.py`・`tests/test_call_context.py`・`tests/test_sequence_steps.py`・tests_ui）:
   - M1: 呼び出しのエラー通知の値の欄に `呼び出し先=<キー>` が入る
   - M2: 連続実行で (a) 最初の呼び出し先のエラーの通知中に一時停止 → 停止して呼び出し元は進まない・履歴を誤って積まない・再開しても成功扱いにならない / (b) 送信失敗の通知中に一時停止 → 停止・再送しない
   - M3: 呼び出し先 `[loop_start count=20000, call <空のトリガー>, loop_end]` → 上限のエラー（UI を固めない）
   - 単発: 呼び出し中のトリガーを戻す / 先頭への対象にすると拒否メッセージ / 他のトリガーの連続実行の開始で打ち切り（呼び出し先の差分を含む 1 段）/ `reset_indices` で履歴なし / 呼び出し元の位置変更（`reset_loop_frames`）で打ち切り
   - 連続実行: 呼び出し元を消す（トリガー一覧から外す）→ 次のステップで履歴を積まずに停止
   - 通知の表示中の停止操作: 単発・連続とも、偽の notify_error の中で停止操作をしても履歴は 1 段だけ
   - 呼び出し先の周回・履歴が変わらない / 空の呼び出し先でも停止の読み飛ばしの「送った」に数える / 連鎖の書式 `呼び出し: <キー> > <キー>` / 呼び出し先が戻す・先頭へ + 他の行 → 「単独で登録してください」のエラー
   - L1・L7 の文言

## 読むファイル

- `instructions/history/29_sequence_call.md` §4.2・§4.5（v0.5）
- `keyseq/application/sequence_steps.py:25-50` / `keyseq/application/call_context.py`（全体）/ `keyseq/application/sequence_runner/call_run_to_end.py`（全体）/ `call_wait.py:230-250`
- `keyseq/presentation/dialogs/action_control_fields.py:255-295`
- `tests/test_sequence_runner_call.py`・`tests/test_call_context.py`（全体・編集対象）/ `tests_ui/test_action_list_rendering.py:260-275`・`tests_ui/test_action_dialog_control.py:180-230`

## 含まない

- L3・L4・L6（参考）/ L5 の共通化（`/refactor_check`）/ 正本（task_10）

## 確認

- `compileall` clean / 変更・追加したテスト / `discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass
- M2 のテストは、修正前のコード（一時停止を照合に含める）では落ちることを確認する（`git stash` を使わず、該当の条件を一時的に戻して実行 → 元に戻す）

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: M2 の照合の条件と started の戻し / M3 の数え方が入れ子をまたぐ / 既存の挙動の不変 / テストが指摘の場面を再現している）。
