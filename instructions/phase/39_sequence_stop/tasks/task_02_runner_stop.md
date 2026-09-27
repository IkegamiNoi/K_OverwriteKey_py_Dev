# task_02_runner_stop

## 目的

連続実行で停止を働かせる（暫定 28 §4.1）。task_01 の `advance` / `settle_after_normal` の `stop_ends_run` を runner から渡し、停止で連続実行を終える。
単発実行は既定値（`stop_ends_run=False`）のまま読み飛ばしになるので変更しない（§4.2）。
**application（`keyseq/application/sequence_runner/`）とテストのみ・停止を含まないシーケンスの挙動は不変**。

## 対象範囲

### `keyseq/application/sequence_runner/sequence_runner.py`

- 読み飛ばしの印 `self._run_to_end_sent: bool`（その連続実行で通常アクションを送ったか）を持つ。
  - `_start_run_to_end` で False にする。**一時停止・再開では変えない**（同じ連続実行）。
  - 通常アクション（hotkey / text / mouse_click）の `perform_action` が False 以外で終わったら True。file_line は完了が成功したとき True（`file_line_wait.py` 側・下記）。エラーで終わったものは変えない。
- `_perform_run_to_end_step` の `advance(...)` に `stop_ends_run=self._run_to_end_sent` を渡す。`outcome.stopped` のときは既存の「通常アクションが無い」経路と同じく
  `commit_step` を 1 回して `stop_run_to_end()`（`_run_to_end_wait_position` は None なので位置を戻さない・二重に積まない）。位置は `advance` が返した停止の次で保存済みであること。
- `_finish_run_to_end_normal_action`: 印を True にしてから（呼び出し元で先に立ててもよい）`settle_after_normal(..., stop_ends_run=True)` を渡す。
  `settled.stopped` なら、控えた保留（`deferred_counters`）を**その場で反映**し（`apply_deferred_counters`・差分を deltas に足す）、保留を空にして保存し、呼び出し元に**停止**を返す。
  戻り値を `(deltas, position, stopped)` に広げ、呼び出し元は `stop = position == 0 or stopped` で終える（間隔を置かない）。既存の「位置 0 なら保留を反映して停止」はそのまま。

### `keyseq/application/sequence_runner/file_line_wait.py`

- 連続実行の file_line の完了（成功）で印を True にしてから `_finish_run_to_end_normal_action` を呼ぶ。戻り値の変更に合わせて停止を判定する（`stop = not result or position == 0 or stopped`）。

### テスト（`tests/test_sequence_runner.py` または新規 `tests/test_sequence_runner_stop.py`・既存の FakeScheduler の書き方に合わせる）

1. `[A, stop, B]` の連続実行: A の後に間隔を置かずに終了（予約なし）・位置 2 → 再び押すと B を実行して末尾で終了
2. `[A, counter_inc, stop, B]`: A の後に終了・カウンターがその場で +1・位置 3・戻す履歴 1 段に counter の差分が含まれ、戻すで打ち消せる
3. `[A, stop]`: 位置 0・周回空で終了
4. 読み飛ばし: 位置を停止の行にして開始 → 停止を読み飛ばして次の通常アクションを実行 / `[A, stop, stop]` の位置 1 から開始 → 何も送らず末尾で終了（位置 0）
5. 一時停止 → 再開で印が保たれる: `[A, wait, stop, B]` で A → 待機中に一時停止 → 再開 → 待機の次の停止で終了（読み飛ばさない）
6. 待機の続きで停止: `[A, wait, stop, B]` で待機後に終了・位置 3
7. ループ内の停止: `[loop_start×3, A, stop, loop_end]` で 1 周ごとに終了し、次の連続実行で周回が進む
8. 単発: `[A, stop, B]` を 2 回押すと A、B（停止を読み飛ばす）
9. file_line を読込中の完了（成功）でも印が立つ: `[file_line, stop, B]` の連続実行 → file_line の完了後に停止で終了（偽の begin / poll・`tests/test_sequence_runner_file_line.py` の書き方）
10. 停止を含まない既存の連続実行テストが無変更で通る

## 読むファイル

- `instructions/history/28_sequence_stop_and_call.md` §4.1・§4.2（`:44-70` 付近）
- `keyseq/application/sequence_runner/sequence_runner.py:260-450`（連続実行）・`keyseq/application/sequence_runner/file_line_wait.py:100-172`（連続実行の file_line の完了）
- `keyseq/application/sequence_steps.py` の `advance` / `settle_after_normal` / `apply_deferred_counters` のシグネチャ
- `tests/test_sequence_runner.py:1-80`（FakeScheduler・make_runner）/ `tests/test_sequence_runner_file_line.py:1-80`

## 含まない

- 単発実行の変更（既定値で読み飛ばし）/ 編集ダイアログ・一覧（task_03）/ 正本・codebase_map（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加テスト・`tests.test_sequence_runner`・`tests.test_sequence_runner_file_line` が全 pass
- `unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 印の境界〔開始で消す・一時停止で保つ・file_line の完了〕/ 停止で間隔を置かない / 保留の反映と戻す履歴 1 段 / `stop_run_to_end` で位置を戻さない / 停止を含まない既存挙動の不変 / 先取りなし）。
- 実機目視: task_03 でまとめて実施。
