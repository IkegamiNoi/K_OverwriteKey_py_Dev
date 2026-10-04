# task_03_step_call_run_to_end

## 目的

連続実行でのステップの呼び出しを実装する。呼び出し先の**停止の行で連続実行を止め**、続きがあれば**連続実行の一時停止**、呼び出しが終わる形なら**連続実行を終える**（暫定 31 v0.4 §4.3・§4.4・§10-4・§10-4a・§10-5・§10-6）。
**application（`call_context.py`・`sequence_steps.py`・`sequence_runner/{call_run_to_end,sequence_runner}.py`）。presentation・JSON は変えない。一括の呼び出しの挙動・呼び出し元の `_run_to_end_sent` は変えない。**

## 対象範囲

### `keyseq/application/call_context.py`

- `CallContext` に**文脈ごとの「送った」の印** `sent: bool = False` を足す。**ステップの段で呼び出し先の通常アクション（file_line を含む・入れ子を含む）を送ったら立てる**（`finish_call_action` 等の送った後の処理の中）。
  文脈の開始時・再開時に下ろさない。文脈が無くなれば消える（文脈ごと捨てられる）
- `call_step` / 文脈の中の先行処理に「停止の行を効かせるか」を渡せるようにする（現行は `stop_ends_run=False` 固定 = `:168,216,260` 付近）:
  **最上段がステップの段 かつ 呼び出し側が連続実行 かつ `ctx.sent`** のときだけ停止の行を効かせる。それ以外は現行どおり読み飛ばす（単発・一括・まだ送っていない）
- 停止の行に達したときの結果を `CallStep` の新しい種類（例 `kind="stopped"`）で返す。返す前に **§4.2.8 の停止の後の先行処理**をする:
  待機を読み飛ばし、カウンター操作は保留に控える。最上段の末尾に達したら段を降ろしてその段の保留を反映する（降ろした先の段の続きの先行処理も同じ規則）。
  **呼び出し元まで段を降ろしきったら**「呼び出しは成功して止まった」ことが分かるようにする（例 `CallStep.kind="stopped"` + `call_done: bool`）

### `keyseq/application/sequence_steps.py`

- 停止の後の先行処理を文脈の中で使えるようにする必要があれば、既存の `settle_after_normal` / `advance` の停止の扱い（`:186-187`・`:333-345`）に最小の引数を足す（呼び出し元の連続実行の停止の行の挙動は変えない）

### `keyseq/application/sequence_runner/call_run_to_end.py`（連続実行の呼び出し）

- 連続実行の文脈で `call_step` に「連続実行である」ことを渡す
- `kind="stopped"` を受けたら:
  1. **文脈が残る**（`call_done` が偽）→ **連続実行の一時停止にする**（`pause_run_to_end` と同じ状態: `run_to_end_paused = True`・予約を取り消す・文脈 `_run_to_end_call` を保持・`update_status`）。
     再開は現行の `resume_run_to_end` で最上段の続きから（停止の次）。破棄の通知・2 回押しは一時停止の規定のまま
  2. **文脈が無くなった**（`call_done` が真）→ 現行の呼び出しの成功（`_complete_run_to_end_call`）と同じく呼び出し元の先行処理をし、**呼び出し元の停止の行と同じく連続実行を終える**（`stop_run_to_end`・間隔を置かない・一時停止にしない）。履歴は呼び出しの成功として 1 段
- **呼び出し元の `_run_to_end_sent` は従来どおり呼び出しの成功時だけ立てる**（`:307`）。文脈の `sent` は呼び出し元へ伝えない

### テスト（追加・修正まで）

- `tests/test_sequence_runner_call.py`（連続実行の呼び出しのテストに倣う。偽のタイマー）:
  - 呼び出し元 `[call step f5, X]`・f5 `[A, 停止, B]` を連続実行: A を送った後、停止の行で**一時停止**（`run_to_end_paused`・文脈あり・呼び出し先の位置は B）。再開すると B → 呼び出し成功 → X と続く
  - f5 `[停止, A]`（まだ送っていない）: 停止を読み飛ばして A を送り、最後まで続く
  - f5 `[A, 停止]`（停止の後に呼び出しが終わる）: A の後に**連続実行を終える**（一時停止にならない・次に実行は X・履歴 1 段）
  - f5 `[A, 停止, wait 100, B]`: 停止の後の先行処理で待機を読み飛ばし、位置は B
  - 入れ子 `f5 = [call step f7, C]`・`f7 = [A, 停止, B]`: f7 の停止で一時停止し、再開で B → C と続く
  - 一括の呼び出し（`step` なし）の呼び出し先の停止の行は従来どおり読み飛ばす
  - **互換（§10-4a）**: 一括の呼び出しで A を送った後に一時停止 → 呼び出し元の位置を停止の行へ変えて再開しても、従来どおり停止を読み飛ばす（`_run_to_end_sent` が変わらない）
  - 一時停止 → 再開で、一括・ステップとも呼び出し先の続きから動く（§10-6）
  - 単発のステップでは呼び出し先の停止の行を読み飛ばす（task_02 の挙動が変わらない）
  - 単発のステップの呼び出し先の **file_line** の完了後も押下の合間に入る（task_02 の reviewer の参考指摘）

### 設計メモ / 制約

- 一時停止・終了の状態は既存のもの（`run_to_end_paused`・`stop_run_to_end`）を使い、新しい状態を作らない（暫定 31 §4.3）
- `call_context.py`・`call_run_to_end.py` が 300 行を大きく超える・関数 30 行を超えるなら、停止の後の先行処理を小さな関数に分ける

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.3・§4.4
- 正本 `features.md` §4.2.2・§4.2.8・§4.2.9
- `keyseq/application/call_context.py`（全体）
- `keyseq/application/sequence_steps.py:170-200`・`:320-360`
- `keyseq/application/sequence_runner/call_run_to_end.py`（全体）・`sequence_runner.py:280-340`・`:410-470`
- 手本のテスト: `tests/test_sequence_runner_call.py`（連続実行の呼び出し・停止のテスト）

## 含まない

- 表示の要約・通知（task_04）/ 枠（task_05・06）/ 正本反映（task_07）
- 単発のステップの挙動の変更（task_02 のまま）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。続けて task_02・03 の統合確認（`deep-reviewer` + `codex-reviewer`）。
- **実機目視（task_02 とまとめて本タスクで実施）**: ①単発でステップの呼び出しを押すたびに呼び出し先が 1 行ずつ進み、合間に他のトリガーが動き、最後の押下で呼び出し元の次へ ②連続実行でステップの呼び出し先の停止の行で一時停止し、もう一度押すと続きから動く ③停止の後に呼び出し先が終わる形では連続実行が終わる ④一括の呼び出しの動きが今までと同じ。
