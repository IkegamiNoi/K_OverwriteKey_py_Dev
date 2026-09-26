# task_03_wait

## 目的

暫定仕様 26 §7（待機）を実装する。task_02 で「素通り」にしてある `wait` を置き換える。
- 連続実行: 待機の行を処理したら `ms` 後に続き（間隔 `run_to_end_delay_ms` は足さない）。一時停止で残りの待機は捨て、再開は通常の間隔の後に待機の次から。
- 単発実行: `after()` で待ち（UI スレッドを塞がない）、待ち終わったら同じステップの続き。待機中は**保留中ステップ**として同じトリガーの押下を無視
  （§2-17・他のトリガーは動く）。続きは**世代番号**で守り、取り消し後に呼ばれても何もしない。
- 取り消し契機（§7）: フック停止 / キーマップの切替 / 対象トリガーの位置変更・編集・削除 / runtime 状態を消す契機（構成セットの読込等）/
  他のトリガーの連続実行の開始。取り消し時、位置は**待機の行に残る**。
- 10,000 の上限は待機をまたいで通算（§4.1）。`ms` が変換不能・1 未満は実行時エラー。

**application 中心**。presentation は取り消しの呼び出しの配線だけ。domain は変更しない。
戻す履歴への記録（§7「取り消し時に履歴へ 1 段積む」）は task_04 で行う（本タスクでは履歴を持たない）。

## 対象範囲（application 中心・presentation は配線のみ）

### `keyseq/application/sequence_steps.py`

- ステップの途中状態 `StepResume`（dataclass）: 押下の開始位置 / 先頭へ回ったか / 処理した system の数。
- `advance(..., resume: StepResume | None = None)`: `resume` があればその状態から続ける（開始位置での終了判定・10,000 の通算に使う）。
- `wait` に到達したら:
  - `ms` を `int()` で判定。変換不能・1 未満はエラー（「待機時間が不正です（1 以上の整数・ミリ秒）」）。
  - 正常なら `StepOutcome` に `wait_ms` と、続きの開始位置（待機の次の行）・その時点の `StepResume` を入れて返す。
    **保存する位置（`position`）は待機の行**（単発の取り消し時に待機の行に残すため）。周回スタックはその時点のもの。
  - 待機の次が末尾（len）でも、続きの側で通常の末尾処理（位置 0・周回を空・単発の回り込み）になるようにする。
- `back` / `rewind` は task_02 のまま素通り（task_04）。

### `keyseq/application/app_state.py`

- 単発の保留中ステップ `pending_steps: dict[tuple[str, str], PendingStep]`（(trigger_set_id, key) → 世代番号・`after` の ID・続きの位置・`StepResume`）と、
  世代番号の採番用カウンタ。
- `reset_indices` / `forget_trigger_set` / `rekey_trigger_set` で保留中ステップも消す（消えた保留の続きは世代番号の不一致で何もしない）。

### `keyseq/application/sequence_runner.py`

- 単発:
  - `handle_key` で、そのキーに保留中ステップがあれば何もしない（同じトリガーの押下を無視）。
  - `advance` が `wait_ms` を返したら、位置（待機の行）と周回を保存し、保留中ステップを登録して `after(wait_ms, 続き)` を予約。`reentry_guard` は解除してよい
    （保留中ステップが再入を防ぐ）。
  - 続き: 保留中ステップが残っていて世代番号とトリガー一覧 ID が一致するときだけ、続きの位置から `advance(resume=...)` → 通常アクションの実行
    （task_02 と同じ後処理）。一致しなければ何もしない。完了・エラーで保留を消す。続きの中でまた待機に当たれば再び保留にする。
- 連続:
  - `advance` が `wait_ms` を返したら、**位置は待機の次**を保存し（一時停止・再開で待機の次から続けるため）、`after(wait_ms, _run_to_end_step)` を予約。
    `StepResume` は runner が次のステップの開始まで持ち、10,000 を通算する（通常アクションを実行したらリセット）。
  - 一時停止・停止は現行どおり `run_to_end_after_id` を取り消す（残りの待機は捨てる）。
- 取り消しの公開メソッド:
  - `cancel_pending_wait(key: str) -> None`（アクティブなトリガー一覧のそのキー）/ `cancel_pending_waits() -> None`（すべて）。
    `after_cancel` で予約を取り消し、保留を消す。位置は保存済みの待機の行のまま。
  - `reset_loop_frames(key)` の中で `cancel_pending_wait(key)` も行う（位置変更・編集の呼び出し元は task_02 で配線済み）。
  - `_start_run_to_end` の開始時に `cancel_pending_waits()`（他のトリガーの連続実行の開始）。

### presentation（配線のみ）

- `keyseq/presentation/controllers/hook_controller.py`: `stop_hook` で `stop_run_to_end()` と並べて `cancel_pending_waits()` を呼ぶ
  （UI 編集中の一時停止は `suspend_hook_for_dialog` → `stop_hook` を通るので同時に満たす）。
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`: `activate_keymap_by_id` でアクティブが変わったとき（`changed`）に `cancel_pending_waits()`。
- `keyseq/presentation/controllers/trigger_panel_controller.py`: `delete_trigger` で周回スタックを消す箇所に `cancel_pending_wait(key)` を足す。

### テスト

- `tests/test_sequence_steps.py`（追記）: `wait` の到達（位置 = 待機の行・続きの位置・`wait_ms`）/ `ms` 不正のエラー / 待機の次が末尾 /
  `resume` による開始位置での終了と 10,000 の通算。
- `tests/test_sequence_runner.py`（追記・`after` は偽のタイマーで手動発火）: 単発の待機 → 続きで通常アクション / 待機中の同じキーの押下を無視・別キーは実行 /
  取り消し（`cancel_pending_wait(s)`・`reset_loop_frames`・`reset_indices`）後に続きが発火しても何もしない・位置は待機の行 /
  トリガー一覧 ID が変わった後の続きは何もしない / 連続の待機（間隔を足さない・位置は待機の次）/ 一時停止で待機を捨て再開で続きから /
  他トリガーの連続実行の開始で単発の保留が取り消される / 待機を含まないシーケンスの挙動不変。

### 設計メモ / 制約

- `time.sleep` 等の同期待ちを使わない（すべて `after`）。
- 保留中ステップは (trigger_set_id, key) 単位。続きは予約時のトリガー一覧 ID を保持し、現在の ID と違えば何もしない。
- キーマップ一時停止（`toggle_custom_input_enabled` の無効化）は §7 の取り消し契機に含まれないので、本タスクでは配線しない。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §4.1・§7（仕様）
- `keyseq/application/sequence_steps.py` / `keyseq/application/sequence_runner.py` / `keyseq/application/app_state.py`（編集対象・全体）
- `keyseq/presentation/controllers/hook_controller.py:158-170`（`stop_hook`）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:407-440`（`activate_keymap_by_id`）
- `keyseq/presentation/controllers/trigger_panel_controller.py` の `delete_trigger`（`rg -n "def delete_trigger"` で位置を特定し範囲指定で読む）
- `tests/test_sequence_runner.py` / `tests/test_sequence_steps.py`（既存テストの書き方・偽のタイマーの手本）

## 含まない

- 戻す・先頭へ・戻す履歴（取り消し時の履歴記録を含む）・「対象が単発の待機中なら戻さない」→ task_04
- file_line → task_05 / 編集 UI → task_06 / 一覧の表示 → task_07 / 正本反映 → task_08

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` がエラー無し。
- 単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_steps tests.test_sequence_runner -v` が全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `grep -rn "time.sleep" keyseq/application/sequence_steps.py keyseq/application/sequence_runner.py` がヒットしないこと。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_07 でまとめて実施。
