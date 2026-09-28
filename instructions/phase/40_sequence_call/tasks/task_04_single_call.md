# task_04_single_call

## 目的

**単発実行**で呼び出しの行に達したら、呼び出し文脈（task_03）を作って呼び出し元のステップを保留にし、文脈のステップを予約しながら最後まで進める（暫定 29 §4.3・§4.5・§4.6 の単発列）。
**application（`sequence_runner/`・`app_state.py`）とテストのみ**。連続実行は task_05（それまでは連続実行で呼び出しの行に達すると従来どおり送信エラー＝UI からはまだ作れないので受容）。

## 対象範囲

### `keyseq/application/app_state.py`

- `PendingStep` に `call: object | None = None`（呼び出し文脈）と `call_file_line: object | None = None`（文脈の中の file_line の札）を追加（末尾・既定値つき）。

### `keyseq/application/sequence_runner/call_wait.py`（新規・mixin `CallWaitMixin`）

`SequenceRunner` が継承する（`FileLineWaitMixin` と同じ形。冒頭に使う runner の属性・メソッドを列挙するコメント）。単発の呼び出しの処理をここに置く:

- `_start_single_call(key, actions, outcome, snapshot, initial_position)`: 呼び出しの行（`outcome.normal_index`）の `target` で `start_call(トリガー一覧 ID, key, target, find)` を作る
  （`find` = 今のアクティブなトリガー一覧で正規化済みキーからトリガーを引く関数。runner の `_find_trigger` を使う）。
  位置を呼び出しの行で保存し、`PendingStep(世代, None, 呼び出しの行, resume_for_pending(outcome, initial_position), snapshot, call=ctx)` を登録して、
  **`after(0, 進める)`** を予約する（最初のステップは間隔を置かない）。
- `_advance_single_call(trigger_set_id, key, generation)`（予約から呼ばれる）:
  1. 保留が無い / 世代違い / 文脈が無い → 何もしない。**呼び出し元の照合**（§4.2）: 今のトリガー一覧 ID が文脈と違う・呼び出し元のトリガーが無い → 保留を外して何もしない（履歴を積まない）。
  2. `step = call_step(ctx, counters)`。`step.counter_deltas` を保留の `resume` の差分へ**積み増す**（`dataclasses.replace`）。
  3. `kind`:
     - `action`（hotkey / text / mouse_click）: `perform_action(step.action)` → **戻った後に保留の同一性（同じ PendingStep・同じ世代）を照合し直し**、変わっていれば何もしない（§4.5 の再照合）。
       False なら呼び出し元のエラー（下）。それ以外は `finish_call_action` → 差分を積み増し → `next` なら `after(interval_ms, 進める)` / `done` なら完了（下）。
     - `action`（file_line）: begin / poll が未設定なら「file_line の読込の仕組みが未設定です」のエラー。`begin_file_line` が None → 呼び出し元のエラー（通知は executor 済み）。
       札を `pending.call_file_line` に置き、`after(FILE_LINE_POLL_INTERVAL_MS, 確認)`。確認: 同一性の照合 → `poll_file_line` が None なら再予約 / 戻った後に再照合 /
       True → `finish_call_action` へ（上と同じ）/ False → 呼び出し元のエラー。
     - `wait`: `after(wait_ms, 進める)`。
     - `error`: 呼び出しの行の action で通知（`_report_error` と同じ経路。メッセージの後ろに ` / ` + `chain_text(step.chain)`）→ 戻った後に再照合 → 呼び出し元のエラー。
     - `done`: 完了（下）。
  4. 予約のたびに `pending.after_id` を更新する（取り消しで止まるように）。
- **完了**: 保留を外し、`_finish_single_normal_action(key, 呼び出し元の actions, 呼び出しの行, resume)` で位置を進めて先行処理 → `commit_step(snapshot, 差分)` を 1 回 → `select_trigger(key)`。
  呼び出し元の actions は `_find_trigger(key)` で引き直す（照合済み）。
- **呼び出し元のエラー**: 保留を外し、位置は呼び出しの行のまま `commit_step(snapshot, resume.counter_deltas)` を 1 回（状態が変わっていれば 1 段）→ `select_trigger(key)`。
- 取り消し（既存の `cancel_pending_steps` 等）は変更しない（`after_id` の取り消しと差分つきの 1 段がそのまま効く）。

### `keyseq/application/sequence_runner/sequence_runner.py`

- `SequenceRunner` に `CallWaitMixin` を加える。
- `_run_single_action`: 実行する行が呼び出し（`action_type == system` かつ `system_op == OP_CALL`）なら `_start_single_call(...)` を呼んで `waiting = True`（file_line と同じ位置・同じ開始位置の計算）。

### テスト（`tests/test_sequence_runner_call.py`・新規。FakeScheduler と偽の perform / begin / poll・トリガーの辞書）

1. 単発 1 押下で `f1=[call f5, X]`・`f5=[A, B]` → A、（f5 の間隔）後に B → 完了で呼び出し元の位置は X（1）・f5 の位置は変わらない / 最初の A は `after(0)` で予約される
2. 呼び出し中の同じトリガーの押下は無視・他のトリガーは動く・戻す / 先頭への対象なら拒否
3. 呼び出し先の待機・入れ子の呼び出し・停止の読み飛ばし・file_line（偽の begin / poll）
4. エラー（参照先なし・循環・深さ・無限ループ）で通知に `呼び出し: …` が付き、位置は呼び出しの行・カウンターの差分があれば履歴 1 段・なければ積まない
5. 呼び出し先の `[counter_inc, A]` → 完了後の履歴 1 段に +1 が含まれ、戻すで打ち消せる / 途中で `cancel_pending_wait` → 位置は呼び出しの行・+1 を含む 1 段
6. 通知の再照合: 偽の perform の中で `cancel_pending_wait` を呼んでから False / True を返す → 戻った後に状態を変えず、履歴は 1 段だけ
7. 呼び出し元の照合: 呼び出し中にトリガー一覧 ID を変える / 呼び出し元を消す → 次の進めで保留を外し、履歴を積まない
8. 呼び出し中に呼び出し先のシーケンスを書き換えても、開始時点の内容で最後まで
9. 呼び出しを含まない既存の単発テストが無変更で通る

## 読むファイル

- `instructions/history/29_sequence_call.md` §4.2〜§4.6
- `keyseq/application/call_context.py`（公開 API）/ `keyseq/domain/call_graph.py`（`call_target`）
- `keyseq/application/sequence_runner/sequence_runner.py`（全体・編集対象）/ `file_line_wait.py:1-100`（単発の file_line の保留・再照合の手本）
- `keyseq/application/app_state.py:1-40` / `keyseq/application/sequence_history.py:100-145`
- `tests/test_sequence_runner_file_line.py:1-80`（FakeScheduler と偽の begin / poll の書き方）

## 含まない

- 連続実行（task_05）/ UI（task_06〜08）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `unittest tests.test_sequence_runner_call tests.test_sequence_runner tests.test_sequence_runner_file_line tests.test_sequence_runner_stop -v` / `discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 戻す履歴〔状態が変わったときだけ 1 段・差分の積み増し・二重に積まない〕/ 再照合 / 呼び出し元の照合 / after_id の更新と取り消し / 既存の単発の不変 / 先取りなし）。
