# task_11a_integration_review_fixes

## 目的

task_08〜11 の統合確認（2026-10-05 deep-reviewer「修正して採用」・codex-reviewer P1/P2）の指摘のうち、**仕様の判断が要らない欠陥**を直す（暫定 31 v0.6 §4.5.1・§4.5.2・§4.5.3・§4.5.5）。
**application 限定。presentation・JSON は変えない。** 仕様判断が要る指摘（M3・M4・L1・L2）は本タスクに含めない。

## 対象範囲（application 限定）

### H1（高・codex P1 と同じ）一時停止中の単発の呼び出しの文脈を捨てると古い位置と印を書き戻す

- `sequence_runner.py` `_cancel_pending_steps`（:173-192）は一時停止中（`pending.call_paused`）の文脈にも `_commit_linked_call` を実行し、`linked_call._write_linked_progress` が古い段の位置で上書き・印を付け直す
- 修正: **一時停止中の文脈を捨てるときは、書き戻し・印の付け直し・履歴・`last_trigger` の更新をしない**（状態は一時停止の時点で書き戻し済み。連続実行の `stop_run_to_end` の一時停止中の分岐と同じ形）。処理中（一時停止していない）の取り消しは今のまま
- テスト: f1 = `[call all f5, next]`・f5 = `[a, b]` → f1 を押し a の後に f5 で一時停止 → f5 で b（f5 末尾・f1 は next へ・印なし）→ 捨てる（フック停止・別の連続実行の開始・2 回押しの各経路）→ f5 の位置 0・f1 は next・f1 の印なし・履歴が増えない・`last_trigger` が変わらない

### M1（中）単発の末尾の待機を取り消すと完了が伝わらない

- `wait_stop.py:15-43` の `_settle_stopped_wait` が末尾に回っても `_record_single_completion` を呼ばない。`sequence_history.cancel_pending_steps` は `commit_step` を直接呼び伝播を通らない
- 修正: 取り消し時の先行処理が末尾に回ったら完了として記録し、`_commit_step_and_publish` の伝播を通す（§4.5.3「誰が押したかによらない」）
- テスト: U = `[a, wait 1000]`・X = `[call U, B]`（X は U を参照中）→ U を押して待機中にフック停止 → U は先頭・X は B へ（送らない）・X の印なし

### M2（中・codex P2 と同じ）「待機中・読込中の呼び出し先を呼んでも押下を消費しない」が直接の参照先しか見ない

- `input_acceptance.py:175-182` は押したトリガーの `▶` の行が呼び出しのときだけ、印でたどった最上段だけを照合する。抜ける形: (a) `▶` が呼び出しの前の system 行（例 `[counter_inc n, call A]`）/ (b) X→A→U で A に印が無く A の `▶` が `call U`・U が単独で待機中
- 修正: 判定を**実際に段に入る時点**へ移す（`call_context._push_frame` で対象キーに自身の保留〔単発の待機・file_line の読込・保留中のステップ〕があれば、その押下を消費せず状態を変えずに終える）。押下の受付の判定はこの新しい判定に任せてよい（重複しない形に整理）
- 「押下を消費しない」= 位置・印・履歴・`last_trigger`・カウンターを変えない（system 行を先に処理していても、その押下の変化をすべて巻き戻すか、段に入る前に判定する）
- テスト: (a)・(b) の各形で押下が無視され状態が変わらない / 既存の直接の形のテストも通る

### L3（低）`_commit_linked_context` が `last_trigger` を無条件に上書きする

- `linked_call.py:106` を `commit_press` の「変化があるときだけ更新」に任せる

### L5（低）写しの方式の残り

- `sequence_runner.py:176` のコメント（「snapshot-based runs」）を実態に合わせる / `start_linked_call` の docstring（single press 限定の書き方）を直す
- `call_wait._add_call_deltas` の `pending.resume.counter_deltas` 累積と `app_state.rekey_trigger_set` が呼び出し元の段に計上する経路: 呼び出しでは使わないなら累積をやめ、二重計上を起こさないこと（テストで確認）
- `call_run_to_end._begin_run_to_end_call` の `_run_to_end_resume` / `_run_to_end_snapshot` が呼び出し中に不要なら外す（挙動不変）

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.5.1〜§4.5.5
- `keyseq/application/sequence_runner/{sequence_runner,linked_call,wait_stop,input_acceptance,call_wait,call_run_to_end}.py`（指摘の行の前後）
- `keyseq/application/call_context.py`（`_push_frame` 周辺）・`keyseq/application/sequence_history.py:140-200`・`keyseq/application/app_state.py:150-175`
- `tests/test_sequence_runner_call.py`・`tests/test_call_link_lifecycle.py`（手本）

## 含まない

- M3（連続実行中の呼び出し先の位置をユーザーが変えた場合）・M4（一時停止中の連続実行のトリガーが呼び出し先として完了した場合）・L1（一時停止中の呼び出し元を伝播で進めるときの待機・停止の行）・L2（まとめて戻す対象の検査）＝仕様判断待ち（task_11b で扱う）
- L4・L6・L7（構造・サイズ・検査範囲）＝ /refactor_check または task_07 の正本反映で扱う

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_11b の後にまとめて実施。
