# task_07a_completion_review_fixes

## 目的

フェーズ完了判定前レビュー（Codex 敵対的）の High 2 件を直す（暫定 27 v0.8 §3.4・判断は decisions.md「task_07 完了判定前レビュー」）。
**application（`sequence_runner.py`）+ presentation（`app.py` の登録 1 行）とテストのみ・スキーマ不変**。

## 対象範囲

### 1. 構成セットの読込等で連続実行を常に停止（`sequence_runner.py` / `app.py`）

- `SequenceRunner` に公開メソッド `on_runtime_reset(self) -> None` を追加する: 連続実行中（`state.run_to_end_key` が None でない）なら、
  札を捨て（`_discard_run_to_end_file_line`）、`_run_to_end_resume` / `_run_to_end_snapshot` / `_run_to_end_wait_position` を None にしてから `stop_run_to_end()`。
  （`reset_indices` が実行位置・履歴を先に消しているので、停止で位置を戻さない・履歴を積まない）。連続実行中でなければ何もしない。
- `presentation/app.py`: runner の生成後に `self.state.reset_listeners.append(self.sequence_runner.on_runtime_reset)` を 1 回登録（既存の `clear_cache` の登録の後）。
- 待機中・通常の連続実行も同じく止まる（既存挙動の変更・ユーザー判断）。

### 2. 完了の結果を受け取った後の再照合（`sequence_runner.py`）

- `_poll_run_to_end_file_line` で `poll_file_line(handle)` が `None` 以外を返した直後に、呼ぶ前と同じ照合（連続実行の世代・キー・読込トークン・札が同じ `handle`）をもう一度行い、
  変わっていれば**何もせずに戻る**（通知は executor 側で済んでいる。履歴・位置・予約を触らない）。
- 単発側（`_poll_single_file_line`）は既に呼出し後に保留を照合しているので変更しない。

### テスト（`tests/test_sequence_runner_file_line.py`）

1. 連続実行の読込中に `state.reset_indices()`（runner の `on_runtime_reset` を reset_listeners に登録した状態）→ 連続実行が止まる・poll されない・履歴なし・予約なし
2. 待機（system wait）中の連続実行で `reset_indices()` → 止まる（予約済みの待機の続きを実行しても何も実行されない）
3. 通常の連続実行（間隔の予約中）で `reset_indices()` → 止まる
4. 偽の poll の中で `stop_run_to_end()` を呼んでから False を返す → 戻った後に履歴が二重に積まれない・停止のまま
5. 偽の poll の中で `stop_run_to_end()` → 別トリガーの連続実行を開始してから False を返す → 新しい連続実行が止められず、その状態（resume 等）が消されない

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §3.4（v0.8 追記部分）
- `keyseq/application/sequence_runner.py:70-110`・`:300-380`・`:510-600`
- `keyseq/presentation/app.py:150-160`・`:200-220`
- `tests/test_sequence_runner_file_line.py`（全体・編集対象）

## 含まない

- 通常アクション（hotkey 等）のエラー通知中の同種の再照合（既存経路・phase 38 の範囲外）
- 正本・codebase_map の更新（task_07 後半）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 停止で履歴・位置を触らない / 登録 1 回 / 再照合で古い結果が状態を変えない / 既存経路の不変 / 先取りなし）。
- 実機目視: 不要（テストで担保）。ただし構成セットの読込で連続実行が止まる点は完了報告でユーザーへ伝える。
