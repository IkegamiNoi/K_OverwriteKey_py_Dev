# task_07e_completion_review_fixes

## 目的

phase 37 のフェーズ完了判定前レビュー（deep-reviewer / codex-adversarial〔Sol medium〕）のコード指摘と、暫定仕様 26 v0.6 §2-27 を反映する。
- **M-1**: 連続実行の待機中に「追加」すると、ダイアログを開く前に読んだ位置を書き戻し、§2-22（位置は待機の行）に反する（`trigger_panel_controller.py` の `add_action`）。
- **§2-27（M-2）**: 連続実行が末尾に達して停止するとき、保留中のカウンター操作をその場で反映し、その最後のステップの差分として戻す履歴に入れる。
- **Codex Medium**: 連続実行の `after` 予約に世代番号が無く、停止後に残った古い予約が新しい連続実行を進め得る → 単発の待機と同じく世代番号で守る。
- **L-1**: `format_system_error_notification` が生の `op` で比較しており、手編集の大文字の op（`"WAIT"` 等）で値が通知に出ない → `system_op()` で比較する。
- **L-4**: トリガーの改名で、位置を新しいキーへ移した後に `cancel_pending_wait(old)` を呼ぶため、待機中のステップが履歴に積まれないことがある → 取り消し（と記録）を先に行ってから付け替える。
- **L-6**: テストの穴（「保留 → 待機 → 取り消し → 戻す」で保留と n が戻る / M-1 の経路）。

**application + presentation の最小修正とテスト**。

## 対象範囲

### `keyseq/presentation/controllers/trigger_panel_controller.py`

- `add_action`: 実行位置（`self._app._indices.get(key)`）の読み取りを `dialog.wait_window()` の**後**へ移す。
- `rename_trigger`: 古いキーの待機の取り消し（`cancel_pending_wait(old)`）を、位置・周回・保留・履歴を新しいキーへ付け替える**前**に行う。

### `keyseq/application/sequence_runner.py`（と必要なら `sequence_steps.py` / `sequence_history.py`）

- §2-27: 連続実行で、通常アクション後の先行処理の結果が末尾（位置 0）で停止するとき、保留中のカウンター操作をその場で反映し（カウンターを更新し差分に加え）、
  保留を空にしてから、そのステップを履歴に積んで停止する。待機の途中での停止（M2）・エラー停止・一時停止では反映しない。
- Codex Medium: 連続実行の開始ごとに世代番号を採番し、`after` で予約するコールバックに世代を渡す。実行時に世代と `run_to_end_key` が現在と一致しなければ何もしない。
  `stop_run_to_end` で世代を進める。
- L-1: `format_system_error_notification` の op の比較を `system_op(action)` で行う。
- 行数は 360 行未満（増えるなら補助関数を `sequence_history.py` / `sequence_steps.py` 側へ）。

### テスト

- `tests/test_sequence_runner.py`（追記）: §2-27（`[A, カウンター+1]` の連続実行が終わると n=1・保留なし・戻すで n=0）/ 待機途中の停止・エラー停止・一時停止では反映しない /
  世代番号（停止後に古い予約を手動で発火しても新しい連続実行が進まない）/ L-1（`"WAIT"` の不正ミリ秒で通知に値が出る）/
  L-6（単発で保留あり → 待機 → 取り消し → 戻す で位置・保留・n が戻る）。
- `tests_ui/test_sequence_control_review_fixes.py`（追記）: M-1（連続実行の待機中にダイアログを開く = stop_hook が位置を待機の行に戻す状況を偽装し、追加後も位置が待機の行を基準に補正される）/
  L-4（待機中のトリガーを改名すると取り消しが先に行われ、履歴が新しいキーに付く）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §2-22・§2-27・§7・§8.1（仕様）
- `keyseq/application/sequence_runner.py`（編集対象・全体）/ `keyseq/application/sequence_steps.py`（`format_system_error_notification`・保留の反映部分）/ `keyseq/application/sequence_history.py`
- `keyseq/presentation/controllers/trigger_panel_controller.py` の `add_action` / `rename_trigger`（`rg -n` で位置を特定し範囲指定）
- 既存テスト: `tests/test_sequence_runner.py` / `tests_ui/test_sequence_control_review_fixes.py`

## 含まない

- file_line の非同期読込（idea_38・次フェーズ）/ 仕様書・正本・codebase_map（task_08）/ 大きさのリファクタ（`/refactor_check` で判定）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、`..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視は不要（挙動の修正は境界の経路のみ。ユーザー判断で追加可）。
