# task_05_run_to_end_call

## 目的

**連続実行**で呼び出しの行に達したら、呼び出し文脈（task_03）を runner の連続実行の途中状態に持ち、文脈のステップを予約しながら最後まで進める（暫定 29 §4.3・§4.5・§4.6 の連続実行列）。
一時停止では文脈を保持して再開で続きから、停止操作・位置変更・構成セットの読込では文脈を片付ける。**application（`sequence_runner/`）とテストのみ**。

## 対象範囲

### `keyseq/application/sequence_runner/call_run_to_end.py`（新規・mixin `CallRunToEndMixin`）

`SequenceRunner` が継承する（冒頭に使う runner の属性・メソッドの列挙コメント）。runner に次の状態を持つ（`SequenceRunner.__init__` で初期化）:
`_run_to_end_call`（文脈 or None）/ `_run_to_end_call_token: int` / `_run_to_end_call_file_line`（文脈の中の file_line の札 or None）。

- `_begin_run_to_end_call(key, actions, index, outcome, snapshot, initial_position)`: 呼び出しの行の `target` で `start_call` を作り、既存の待機・file_line と同じく
  `_run_to_end_resume = resume_for_pending(outcome, initial_position)` / `_run_to_end_snapshot = snapshot` / `_run_to_end_wait_position = index`（停止操作で位置を呼び出しの行に置き 1 段積む＝既存の `stop_run_to_end`）/
  文脈を保持・トークンを 1 進め、位置を呼び出しの行で保存して、`run_to_end_after_id = after(0, 進める)`（最初のステップは間隔を置かない）。
- `_advance_run_to_end_call(generation, key, token)`（予約から）:
  1. 連続実行の世代・キー・トークンが違う / 一時停止中 / 文脈が無い → 何もしない。**呼び出し元の照合**: 今のトリガー一覧 ID が文脈と違う・呼び出し元が無い →
     文脈を片付け、`_run_to_end_resume` / `_snapshot` / `_wait_position` を None にして `stop_run_to_end()`（履歴を積まない）。
  2. `call_step` → 差分を `_run_to_end_resume` へ積み増す（`dataclasses.replace`）。
  3. `kind`: `action`（通常）→ `perform_action` → **戻った後に世代・キー・トークンを照合し直す** → False はエラー終了 / それ以外は `finish_call_action` → `next` で `after(interval_ms, 進める)` / `done` で完了。
     `action`（file_line）→ begin（未設定・None はエラー終了）→ 札を保持して `after(FILE_LINE_POLL_INTERVAL_MS, 確認)`。確認: 照合 → poll → 戻った後に再照合 → None 再予約 / True は `finish_call_action` へ / False はエラー終了。
     `wait` → `after(wait_ms, 進める)`。`error` → 呼び出しの行の action で通知（メッセージの後ろに ` / ` + `chain_text`）→ 再照合 → エラー終了。`done` → 完了。
     予約はすべて `run_to_end_after_id` に入れる（一時停止・停止で止まるように）。
- **完了**: 文脈を片付け（トークンを進める）、`_run_to_end_sent = True`、`_run_to_end_resume` / `_wait_position` を None にしてから `_finish_run_to_end_normal_action(key, 呼び出し元の actions, 呼び出しの行, resume)`
  → `(deltas, position, stopped)` → `commit_step(snapshot, deltas)` を 1 回 → `position == 0 or stopped` なら `stop_run_to_end()`、そうでなければ呼び出し元の間隔で `_schedule_run_to_end_step`。`_run_to_end_snapshot = None`・`select_trigger(key)`。
- **エラー終了**: 文脈を片付け、`_run_to_end_wait_position = None` にしてから `commit_step(snapshot, resume.counter_deltas)` を 1 回（状態が変わっていれば）→ `stop_run_to_end()`（位置は呼び出しの行のまま）。
- `_discard_run_to_end_call()`: 文脈・札を捨ててトークンを進める。

### `keyseq/application/sequence_runner/sequence_runner.py`

- `SequenceRunner` に `CallRunToEndMixin` を加える。
- `_perform_run_to_end_step`: 実行する行が呼び出しなら `_begin_run_to_end_call(...)` を呼んで戻る（file_line と同じ位置・同じ開始位置の計算）。
- **再開**（`resume_run_to_end` → `_run_to_end_step(schedule_only=True)`）: 文脈が残っていれば、呼び出し元の間隔ではなく**最上段の呼び出し先の間隔**（`top_interval`）の後に `_advance_run_to_end_call` を予約する（呼び出しの行から新しい呼び出しを始め直さない）。
- **一時停止**（`pause_run_to_end`）: 既存どおり予約を止め、文脈は**保持**する。文脈の中の file_line の札は捨て、トークンを進める（再開で `call_step` が file_line の行から読み直す）。文脈の中の待機は残りを捨てる（予約を止めるだけで、再開は待機の次から）。
- **停止**（`stop_run_to_end`）・`_start_run_to_end`・`on_runtime_reset`: `_discard_run_to_end_call()` を加える（停止の位置と 1 段は既存の `_run_to_end_wait_position` の仕組みのまま）。
- **位置変更・編集**（`reset_loop_frames`）: 連続実行中のキーで**呼び出し中**（文脈あり・一時停止でない）なら、file_line の読込中と同じく予約を止めて文脈を捨て、通常の間隔の後に新しい位置から続ける（既存の `reschedule_run_to_end` の条件に呼び出し中を加える）。

### テスト（`tests/test_sequence_runner_call.py` に追加・連続実行のトリガー）

1. `f1(連続)=[call f5, X]`・`f5=[A, B]`（間隔 9）・f1 の間隔 7 → A（after 0）→ 9 後 B → 完了 → 7 後 X → 末尾で停止 / f5 の位置は不変 / 履歴
2. 一時停止 → 再開: A の後で一時停止 → 予約が消える → 再開で f5 の間隔の後に B（A を二度送らない）/ 文脈の中の待機中に一時停止 → 再開で待機の次から
3. 停止操作（`stop_run_to_end`）: 位置は呼び出しの行・呼び出し先のカウンター差分を含む 1 段・古い予約は何もしない
4. エラー（参照先なし・無限ループ）: 通知に `呼び出し: …`・位置は呼び出しの行・停止・状態が変わっていなければ履歴なし
5. 位置変更（`reset_loop_frames`）中の呼び出し: 文脈を捨て、呼び出し元の間隔の後に新しい位置から続行
6. `on_runtime_reset`: 停止・履歴なし
7. 通知の再照合: 偽の perform の中で `stop_run_to_end` → 戻った後に状態を変えず、履歴は 1 段だけ
8. 停止の読み飛ばし: `[call f5, stop, Y]` の連続実行 → 呼び出しの成功で印が立ち、停止で終える
9. 文脈の中の file_line（偽の begin / poll）と、読込中の一時停止 → 再開で読み直す
10. 呼び出しを含まない既存の連続実行テストが無変更で通る

## 読むファイル

- `instructions/history/29_sequence_call.md` §4.3・§4.5・§4.6
- `keyseq/application/call_context.py`（公開 API）
- `keyseq/application/sequence_runner/sequence_runner.py`（全体・編集対象）/ `call_wait.py`（単発の手本）/ `file_line_wait.py:77-173`（連続実行の file_line の手本）
- `tests/test_sequence_runner_call.py`（全体・編集対象）

## 含まない

- UI（task_06〜08）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `unittest tests.test_sequence_runner_call tests.test_sequence_runner tests.test_sequence_runner_file_line tests.test_sequence_runner_stop -v` / `discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 再開で続きから〔新しい呼び出しを始めない〕/ 戻す履歴〔1 段・二重なし・停止操作で呼び出し先の差分を含む〕/ 照合と再照合 / 予約が run_to_end_after_id に入る / 位置変更で続行 / 既存の連続実行の不変 / 先取りなし）。
