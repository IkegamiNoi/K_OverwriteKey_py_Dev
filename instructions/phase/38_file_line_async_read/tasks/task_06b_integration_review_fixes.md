# task_06b_integration_review_fixes

## 目的

task_06 の統合レビュー（deep-reviewer / Codex 標準）で採用した指摘を直す（暫定 27 v0.7 §3.4・§6.1・§6.2・判断は decisions.md「task_06 統合レビュー」）。
**application（`sequence_runner.py` / `file_line_loader.py` / `app_state.py` の 1 行）とテストのみ・presentation 不変・スキーマ不変**。

## 対象範囲

### H1: 連続実行の読込中の位置変更・編集で固まる（`keyseq/application/sequence_runner.py`）

- `reset_loop_frames` で、`key` が連続実行中のキーで**読込中**（札あり・一時停止でない）なら: `run_to_end_after_id` を `after_cancel` で止めて None にし、札を捨て、
  `_run_to_end_step(schedule_only=True)` で通常の間隔の後に新しい位置から続ける予約を入れる（暫定 §3.4。待機中に位置を変えたときの既存挙動と同じ結果）。
  一時停止中（札は既に無い）なら予約しない（再開で新しい位置から続く）。既存の `_run_to_end_resume` 等の片付けはそのまま。
- テスト: 読込中に `reset_loop_frames` → 古い確認は何もしない・`delay` の予約が 1 件入る → それを実行すると新しい位置のアクションが実行される / 一時停止中の reset では予約されない。

### M2: 連続実行の完了時の確認（`keyseq/application/sequence_runner.py`）

- 読込開始時のトリガー一覧 id（`_get_trigger_set_id()`）を札と一緒に持つ。
- `_poll_run_to_end_file_line` で `poll_file_line` を呼ぶ**前に**、トリガーが無い / 今のトリガー一覧 id が開始時と違うなら、`poll` を呼ばず（送らず）、
  `_run_to_end_resume` / `_run_to_end_snapshot` / `_run_to_end_wait_position` を None にして札を捨て、`stop_run_to_end()`（**履歴は積まない**。一覧が変わっているため）。
- テスト: 読込中にトリガーを消す / トリガー一覧 id を変える → 確認で poll されず停止・送信なし・履歴なし。

### M1: 待ち合わせ中の要求の上限判定の順序（`keyseq/application/file_line_loader.py`）

- `poll` の「待ち合わせ中（`job is None`）」分岐で、**起動より先に**上限を判定する。経過が上限以上なら起動せず上限超過の `error`（印は付けない）。
- テスト: 1 本目が上限の直前に終わり、2 本目（待ち合わせ中）の最初の確認が上限以上 → `error`・起動関数は呼ばれない・同じキーの次の `request` は即エラーにならず起動できる。

### L1: `os.stat` の ValueError（`keyseq/application/file_line_loader.py`）

- `_run_job` の `stat` の例外捕捉を `except (OSError, ValueError):` にする（読込側 `load` の従来の文言「ファイルを読み込めません」になる）。
- テスト: `stat` が ValueError → `load` の例外がそのまま結果（task_02 の確認 3 と同じ形）。

### M3: 受け入れ条件 3・4 のテストの補完（テストのみ）

- `tests/test_sequence_runner_file_line.py`:
  - 単発の読込中に `state.reset_indices()` → 残った確認コールバックを実行しても poll されない・保留が無い
  - 単発の読込中に別トリガーの連続実行を開始 → 保留が消え 1 段・確認は何もしない
  - 連続実行: 一時停止 → 停止で 1 段（位置は file_line の行）/ 一時停止 → 再開 → エラー（poll False）で 1 段・停止

### L5 の一部（`keyseq/application/app_state.py`）

- `reset_listeners` を `field(default_factory=list, compare=False, repr=False)` にする（1 行）。

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §3.4・§6.1・§6.2（v0.7 の追記部分）
- `keyseq/application/sequence_runner.py:70-95`・`:300-360`・`:420-570`（reset / 連続実行の開始・一時停止・停止・file_line）
- `keyseq/application/file_line_loader.py:100-215`（poll / _run_job）
- `keyseq/application/app_state.py:30-40`
- `tests/test_sequence_runner_file_line.py`（全体・編集対象）/ `tests/test_file_line_loader.py`（全体・編集対象）

## 含まない

- L2（execute の防御文言）・L3・L4・runner の分割（`/refactor_check`）・正本 / codebase_map（task_07）・実機目視（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_runner_file_line tests.test_file_line_loader tests.test_sequence_runner tests.test_action_executor_file_line -v` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: H1 で予約が 1 件だけ・一時停止中は予約しない / M2 で送らず履歴を積まない / M1 で起動しない・印なし / 既存の待機・連続実行の挙動が不変 / 後続タスクの先取りなし）。
- 実機目視: task_05 と合わせて実施。
