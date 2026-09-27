# task_03_single_step_file_line_pending

## 目的

**単発実行**で file_line に達したら、読込をワーカーで始め、そのステップを**読込中の保留**にする。50 ms ごとの確認タイマーで結果を受け取り、同じステップの続き（送信・先行処理）を行う
（暫定 27 §3.1-4〜5・§3.2・§3.3・§4・§5）。executor は file_line を「開始」と「問い合わせ（送信まで）」に分ける。
**application（executor・runner・app_state）+ presentation の最小配線（`app.py` の組み立てのみ）・スキーマ不変**。連続実行は task_04。

## 対象範囲（application + `presentation/app.py` の組み立てのみ）

### `keyseq/application/action_executor.py`

- コンストラクタに `file_line_loader: FileLineLoader | None = None` を追加する（task_02 の `keyseq/application/file_line_loader.py`）。
- `begin_file_line(self, action: dict) -> FileLineHandle | None`（`FileLineHandle` はこのモジュールの小さな dataclass。runner には不透明な札）:
  - 準備を UI スレッドで行う（§3.1-1）: `normalize_file_line_options` → カウンター名が空 / コールバック未設定のエラー（現行 `:95-100` と同じ文言・順）→
    loader 未設定なら `FileLineError("ファイル読込の仕組みが未設定です")` → `line_number = get_counter(counter)` → `resolved = resolve(path)` →
    `validate_file_line_request(resolved, line_number, encoding=..., out_of_range=...)` → `loader.request(resolved, encoding)`（「前回のファイル読込が終わっていません」はここで送出される）。
  - 例外はすべて現行 `:112-123` と同じ形の通知（`file_line 実行エラー（種類: file_line / 値: …）: {exc}` + ラベル）をして `None` を返す。文言の組み立ては共通の非公開関数へ切り出す。
  - 成功なら、要求・行番号・`out_of_range`・解決済みパス・元の action を持つ札を返す。**行番号は開始時点の値**（§3.1-4）。
- `poll_file_line(self, handle: FileLineHandle) -> bool | None`:
  - `loader.poll(handle.request)` が `pending` → `None`。
  - `error` → 上と同じ形で通知して `False`。
  - `done` → `pick_file_line(lines, line_number, out_of_range=..., path=resolved)` → 行があれば `_write_text(line)`（send guard は現行どおり）→ `True`。
    `pick_file_line` / `_write_text` の例外は通知して `False`。空の行・`empty` の範囲外は何も送らず `True`。
- `execute()` の file_line 分岐（同期実行）は**このタスクでは残す**（連続実行が task_04 まで使うため）。`_execute_file_line` に
  `# 暫定: 連続実行の非同期化（phase 38 task_04）で削除する` のコメントを付ける。中身は変えない。

### `keyseq/application/app_state.py`

- `PendingStep` に `file_line: object | None = None`（読込中の札。None なら従来の待機）を追加する。既存の生成箇所は変更不要な位置（末尾・既定値あり）に置く。

### `keyseq/application/sequence_runner.py`

- コンストラクタに `begin_file_line: Callable[[dict[str, Any]], object | None] | None = None` と `poll_file_line: Callable[[object], bool | None] | None = None` を追加。
  定数 `FILE_LINE_POLL_INTERVAL_MS = 50`。
- `_run_single_action` で、実行する通常アクションが file_line（`type` を trim・小文字化して `"file_line"`。domain の `ACTION_TYPE_FILE_LINE` を使う）かつ
  2 つのコールバックが設定済みなら、`perform_action` の代わりに:
  1. `handle = begin_file_line(action)`。`None` なら `perform_action` が False のときと同じ扱い（位置は file_line の行・`finally` の `commit_step` で 1 段）。
  2. それ以外は、位置を file_line の行（`outcome.normal_index`）にして保存し、`PendingStep(generation, after_id, position=その行,
     resume=StepResume(outcome の開始位置・wrapped・processed・counter_deltas), snapshot, file_line=handle)` を `pending_steps` に登録して、
     `after(FILE_LINE_POLL_INTERVAL_MS, 確認)` を予約する。待機と同じく `waiting = True`（`finally` で commit しない）。
     **`resume.initial_position` は `advance` が使った開始位置**（`StepOutcome` / 既存の `_queue_single_wait` がどの値で `StepResume` を作っているかに合わせる。
     既存の `outcome.resume` を流用できるならそれを使う）。
- 確認（新メソッド）: `(trigger_set_id, key, generation)` で保留を引き、無い / 世代違い / トリガー一覧が違う / トリガーが無いなら何もしない（予約もしない）。
  `poll_file_line(handle)` が `None` なら `after` を予約し直して `pending.after_id` を更新する。結果が出たら保留を外し:
  - `False`（エラー）: 位置は file_line の行のまま。`commit_step(snapshot, resume.counter_deltas)` を 1 回。
  - `True`（成功）: `_run_single_action` の通常アクション実行後と**同じ後処理**（`after_normal_action` → 開始位置での終了判定 → `settle_after_normal` → `_save_progress` →
    `commit_step` を 1 回）。後処理は `_run_single_action` と共有の非公開メソッドへ切り出し、**二重に書かない**。
  - どちらも最後に `select_trigger(key)`（`_run_single_action` の `finally` と同じ）。
- 取り消し（`cancel_pending_wait(s)`・`reset_loop_frames`・他トリガーの連続実行開始）は既存の `cancel_pending_steps` がそのまま効く（確認タイマーの `after_cancel`・1 段）。
  **既存の取り消し経路は変更しない**。同じトリガーの押下の無視（`:140`）・戻す / 先頭への拒否（`sequence_history.py:169`）も既存のまま効くこと。
- コールバックが未設定なら従来どおり `perform_action`（テスト・移行の都合。task_04 で扱いを決める）。

### `keyseq/presentation/app.py`（組み立てのみ）

- `self.file_line_loader = FileLineLoader()` を作り `ActionExecutor(file_line_loader=...)` へ渡す。
- `SequenceRunner(begin_file_line=self.action_executor.begin_file_line, poll_file_line=self.action_executor.poll_file_line)` を渡す。
- それ以外の変更をしない（`clear_cache` の配線は task_05）。

### テスト

- `tests/test_action_executor_file_line.py`: 既存テストは残す（同期経路が task_04 まで残るため）。`begin_file_line` / `poll_file_line` のテストを追加:
  実ファイル + `FileLineLoader(start_worker=貯めて手で実行)` で、開始 → `None`（pending）→ ワーカー実行 → `True` で 1 回送信 / 空の行・empty で送らず True /
  無いファイル・範囲外で通知して False（文言の形は既存テストと同じ）/ カウンター名が空・コールバック未設定・loader 未設定で `begin` が None と通知 /
  **開始後にカウンターを変えても開始時点の行が送られる** / 上限超過の印付きで `begin` が None と「前回のファイル読込が終わっていません」の通知。
- `tests/test_sequence_runner.py`（または新規 `tests/test_sequence_runner_file_line.py`。既存ファイルが 600 行を超えるなら新規）: FakeScheduler と偽の begin / poll で:
  1. 単発で file_line → 保留・位置は file_line の行・50 ms の予約 / 読込中の同じトリガーの押下は無視 / 他のトリガーは動く
  2. poll が None の間は 50 ms で予約し直す → True で完了・位置が進み、続く counter の行が先行処理で保留に控えられる（`[file_line, counter_inc, A]` 等）
  3. False で位置は file_line の行・`[counter_inc, file_line]` で戻す履歴が 1 段（counter_deltas を含む）・二重に積まれない
  4. 読込中に `cancel_pending_wait` / `cancel_pending_waits` / `reset_loop_frames` → 予約が消え、poll は呼ばれない・戻す履歴 1 段 / 取り消し後の古い確認コールバックを直接呼んでも何もしない（世代）
  5. 戻す・先頭への対象が読込中なら「対象のトリガーが待機中のため操作できません」
  6. begin が None → 保留にならず 1 段（位置は file_line の行）
  7. 待機（system wait）の後に file_line がある 1 ステップで、待機 → 読込 → 完了まで戻す履歴が 1 段
- 既存の `test_other_trigger_file_line_reads_current_counter_before_deferred_step`（`:133`）はコールバック未設定の経路でそのまま通ること。

### 設計メモ / 制約

- runner は file_line の中身（パス・行番号・loader）を知らない。知るのは「開始 → 札 / 問い合わせ → 未了・成功・失敗」だけ。
- 世代番号は既存の `state.pending_step_generation` を使う（暫定 §3.2 の「読込トークン」= 保留の世代）。
- 確認タイマーは `after` だけで作る（スレッドから Tk を呼ばない。ワーカーは loader の中で完結）。
- `sequence_runner.py` が大きく膨らむ場合（目安 +80 行超）は、確認と後処理を非公開メソッドへまとめる。別モジュール化は `/refactor_check` で判断する（このタスクでは行わない）。

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §3.1〜§3.3・§4・§5（`:53-105` 付近）
- `keyseq/application/sequence_runner.py`（全体・編集対象）
- `keyseq/application/action_executor.py:1-135`（編集対象の file_line まわり）
- `keyseq/application/app_state.py:1-40`（`PendingStep`）
- `keyseq/application/sequence_history.py:115-175`（`commit_step` / `cancel_pending_steps` / 戻す・先頭への拒否）
- `keyseq/application/sequence_steps.py:15-80`（`StepResume` / `StepOutcome`）・`:163-289`（`advance` / `after_normal_action` / `settle_after_normal` のシグネチャ）
- `keyseq/application/file_line_loader.py`（公開 API のみ）・`keyseq/application/file_line_reader.py`（`validate_file_line_request` / `pick_file_line`）
- `keyseq/presentation/app.py:115-140`・`:200-220`（executor・runner の組み立て）
- `tests/test_sequence_runner.py:1-80`・`:133-150`（FakeScheduler と既存の file_line テスト）/ `tests/test_action_executor_file_line.py`（全体）

## 含まない

- 連続実行の読込・一時停止・停止（task_04）、同期経路（`execute()` の file_line 分岐・コールバック未設定時の `perform_action`）の削除判断（task_04）
- `clear_cache` の呼び出し（構成セットの読込等）・実機目視（task_05）
- codebase_map / 正本の更新（task_07）
- 読込中の表示（暫定 §9 スコープ外）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_action_executor_file_line tests.test_sequence_runner tests.test_file_line_loader -v`（新規ファイルを作ったらそれも）が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 戻す履歴が 1 段〔commit の二重・漏れなし〕/ 成功時の後処理が `_run_single_action` と共有されているか / 世代で古い確認を捨てるか /
  取り消し経路を変えていないか / 行番号が開始時点か / 文言が既存と同じ形か / runner が loader を知らないか / 後続タスクの先取りなし）。
- 実機目視: task_05 でまとめて実施。
