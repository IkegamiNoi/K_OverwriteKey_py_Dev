# task_04_run_to_end_file_line

## 目的

**連続実行**でも file_line を読込中の保留にする（暫定 27 §3.4・§5）。読込中は次のステップを予約しない。一時停止では結果を捨て、再開時に file_line の行から読み直す
（同じ 1 ステップ・戻す履歴 1 段）。停止・エラー・上限超過でも戻す履歴は 1 段。
あわせて、task_03 で暫定で残した**同期経路を削除**し、同期前提のテストを書き換える（暫定 27 §3.1-5）。
**application（runner・executor）とテストのみ・presentation 不変・スキーマ不変**。

## 対象範囲（application 限定: `sequence_runner.py` / `action_executor.py` とテスト）

### `keyseq/application/sequence_runner.py`（連続実行）

`_perform_run_to_end_step`（現 `:385` 付近）で、実行する通常アクションが file_line（task_03 と同じ判定）なら `perform_action` の代わりに:

1. `handle = begin_file_line(action)`。`None` なら `perform_action` が False のときと同じ（`commit_step` 1 回 → 停止。位置は file_line の行）。
2. それ以外は、**待機と同じ持ち越しの仕組み**で読込中にする:
   - 位置を file_line の行で保存する。
   - `self._run_to_end_resume = StepResume(このステップの開始位置, outcome.wrapped, outcome.processed, outcome.counter_deltas)` / `self._run_to_end_snapshot = snapshot` /
     `self._run_to_end_wait_position = file_line の行`（停止時に既存の `stop_run_to_end` がこの行へ位置を置き、`resume.counter_deltas` で 1 段積む）。
     開始位置は待機の続きならその `resume.initial_position`、そうでなければ advance に渡した位置（task_03 の単発と同じ考え方）。
   - 札を `self._run_to_end_file_line` に持ち、**読込トークン** `self._run_to_end_file_line_token`（int）を 1 進める。
   - `self.state.run_to_end_after_id = after(FILE_LINE_POLL_INTERVAL_MS, 確認(token, generation, key))`。**次のステップの予約はしない**。
3. 確認（新メソッド）: 連続実行の世代・キー・トークンが今と一致しない / 一時停止中 / 札が無い なら何もしない（予約もしない）。
   `poll_file_line(handle)` が `None` なら同じ確認を予約し直す（`run_to_end_after_id` を更新）。結果が出たら札・トークンを片付け、`_run_to_end_resume` / `_run_to_end_wait_position` を None にしてから:
   - `True`: 現行の「通常アクション実行後」の後処理（`after_normal_action` → `settle_after_normal` → 位置 0 なら保留の反映 → `_save_progress`）→ `commit_step` を 1 回 →
     位置 0 なら停止、そうでなければ `delay` 後に次のステップ。**この後処理は `_perform_run_to_end_step` の既存部分と共有の非公開メソッドへ切り出し、二重に書かない**。
   - `False`: `commit_step(snapshot, resume.counter_deltas)` を 1 回 → 停止（`_run_to_end_wait_position` を先に None にしてあるので `stop_run_to_end` は積まない）。
   - どちらも `_run_to_end_snapshot = None`・`select_trigger(key)`（現行の末尾と同じ）。
4. **一時停止**（`pause_run_to_end`）: 既存どおり `run_to_end_after_id` を取り消す（確認タイマーも止まる）。加えて札を捨ててトークンを進める。
   `_run_to_end_resume` / `_run_to_end_snapshot` / `_run_to_end_wait_position` は**保持**する（再開後の advance が file_line の行から同じステップとして続く）。
   再開（`resume_run_to_end`）は既存どおり通常の間隔の後に `_run_to_end_step` → `_perform_run_to_end_step`（`resume=self._run_to_end_resume`）→ file_line で再び `begin`（§6.1 の待ち合わせは loader 側で起きる）。
5. **停止**（`stop_run_to_end`）・`_start_run_to_end`・`reset_loop_frames`（連続実行中のキー）: 札を捨ててトークンを進める（既存の片付けに 1〜2 行足す）。
   停止時の 1 段・位置は既存の `_run_to_end_wait_position` の仕組みのまま。

### 同期経路の削除（暫定 §3.1-5）

- `keyseq/application/action_executor.py`: `_execute_file_line`（task_03 で「暫定」コメントを付けたもの）を削除する。`execute()` に file_line が来たら
  `_on_action_error(action, _file_line_error_message(action, FileLineError("file_line は読込の経路（begin_file_line / poll_file_line）で実行します")))` 相当を通知して `False`
  （プログラムの誤りの防御。runner は通常ここへ渡さない）。`read_file_line` の import が不要になれば外す。
- `keyseq/application/sequence_runner.py`: コールバック（`begin_file_line` / `poll_file_line`）が未設定のまま file_line に達したら、`perform_action` へ回さず
  **実行時エラー**「file_line の読込の仕組みが未設定です」を `_report_error` で通知し、エラーと同じ扱い（単発 = 位置は file_line の行・1 段 / 連続 = 停止）。
- `keyseq/application/file_line_reader.py` の `read_file_line` は**残す**（暫定 §8-10 の既存テストの対象。削除は `/refactor_check` で判断）。

### テスト

- `tests/test_action_executor_file_line.py`: `execute()` の同期経路を前提にした既存テスト（成功・空行・エラー・カウンター名・コールバック未設定）を
  `begin_file_line` / `poll_file_line` の形へ書き換える（task_03 で追加した同等のテストと重複するものは統合してよい。観点を落とさない）。
  `execute()` に file_line を渡すと通知して False・送信しないテストを 1 件追加。
- `tests/test_sequence_runner.py:133` の `test_other_trigger_file_line_reads_current_counter_before_deferred_step` を、偽の begin / poll（begin 時点の `state.counters` を記録）で書き換える（観点は同じ）。
- `tests/test_sequence_runner_file_line.py` に連続実行のテストを追加（FakeScheduler・偽の begin / poll）:
  1. 読込中は次のステップが予約されない（予約は確認タイマーだけ）→ True で完了後に `run_to_end_delay_ms` で次のステップ / 位置 0 で停止
  2. poll が None の間は 50 ms で予約し直す
  3. False → 停止・位置は file_line の行・戻す履歴 1 段（`[counter_inc, file_line]` の counter_deltas を含む）・二重に積まれない
  4. 一時停止 → 確認タイマーが消える・古い確認コールバックを直接呼んでも poll されない → 再開（間隔の後）で begin がもう一度呼ばれ、完了後も戻す履歴は 1 段（読み直しを含めて 1 ステップ）
  5. 読込中に停止 → 位置は file_line の行・1 段・古い確認コールバックは何もしない
  6. begin が None → 停止・1 段
  7. コールバック未設定で file_line → エラー通知（単発・連続とも）・perform_action は呼ばれない

### 設計メモ / 制約

- 連続実行の世代番号は一時停止で進まない（`pause_run_to_end`）ため、**読込トークン**で古い確認を捨てる（暫定 §3.2）。確認は世代・キー・トークンのすべてを見る。
- 既存の待機（`wait`）の連続実行の挙動を変えない（`_run_to_end_resume` の意味は「同じステップの続き」のまま）。
- runner が 500 行を超えても分割しない（`/refactor_check` で判断）。ただし新しい後処理は既存と共有し、重複させない。

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §3.1-5・§3.4（`:59-66`・`:92-100` 付近）
- `keyseq/application/sequence_runner.py`（全体・編集対象。task_03 の単発の実装が手本）
- `keyseq/application/action_executor.py:100-200`（`_execute_file_line` / `begin_file_line` / `poll_file_line` / 文言の共通関数）
- `keyseq/application/sequence_history.py:115-145`（`commit_step` / `cancel_pending_steps`）
- `tests/test_sequence_runner_file_line.py`（全体・編集対象）/ `tests/test_action_executor_file_line.py`（全体・編集対象）/ `tests/test_sequence_runner.py:120-150`

## 含まない

- `clear_cache` の呼び出し（構成セットの読込等）・実機目視（task_05）
- `read_file_line` の削除・runner の分割（`/refactor_check`・task_07）
- codebase_map / 正本の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_action_executor_file_line tests.test_sequence_runner tests.test_sequence_runner_file_line tests.test_file_line_reader tests.test_file_line_loader -v` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
- `grep -n "_execute_file_line\|read_file_line" keyseq` で production コードからの `read_file_line` 呼び出しが無い（定義のみ）

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 戻す履歴 1 段〔エラー時の commit と stop の二重なし・一時停止をまたいで 1 ステップ〕/ 読込トークンで一時停止後の古い結果を捨てる /
  読込中に次を予約しない / 既存の待機の連続実行が不変 / 後処理の共有 / 同期経路の削除とテストの観点の維持 / 後続タスクの先取りなし）。
- 実機目視: task_05 でまとめて実施。
