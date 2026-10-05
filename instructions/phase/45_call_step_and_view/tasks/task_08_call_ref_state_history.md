# task_08_call_ref_state_history

## 目的

参照による連動（暫定 31 v0.6 §4.5）の土台として、**トリガーごとの「参照中」の印**と、**押下の番号つきの戻す履歴・まとめて戻す**を application の状態層に入れる（§4.5.1・§4.5.5）。
**application の状態・履歴に限定（`app_state.py`・`sequence_history.py`・新規 `call_chain.py`）。runner の実行経路（call_context / sequence_runner 配下）は変えない（task_09・10）。印が無い限り既存の挙動は 1 つも変わらないこと。**

## 対象範囲（application の状態層・追加のみ）

### `keyseq/application/app_state.py`

- 参照中の印: `keymap_call_refs: dict[str, set[str]]`（トリガー一覧 id → 印のあるキーの集合）と `call_refs_for(trigger_set_id) -> set[str]`（`indices_for` 等と同じ形。id が空なら一覧なしの `call_refs: set[str]`）
- 押下の番号: `press_counter: int = 0` と `next_press_id() -> int`（呼び出し側がロックを持つ前提で単調増加）
- 印の後始末を既存の後始末と同じ所に足す: `reset_indices`（全消去）/ `forget_trigger`（その key の印を外す。編集・位置の変更・削除・交代はここを通る）/ `rekey_trigger`（印を新しいキーへ移す）/ `forget_trigger_set` / `rekey_trigger_set`

### `keyseq/application/sequence_history.py`

- `HistoryEntry` に `press_id: int = 0` と `call_ref: bool = False`（その段の前の印）を足す。`StepSnapshot` に `call_ref: bool = False` を足し、`snapshot_for` が印を写す
- `push_history(...)` に `press_id` と今の印を渡せるようにし、**印の変化も「状態が変わった」に数える**（位置・周回・保留・差分がすべて同じでも印が変われば積む）
- `commit_step(state, snapshot, deltas, press_id=None)`: `press_id` が None なら `state.next_press_id()` で新しく振る（既存の呼び出しはそのままで 1 押下 1 番号になる）
- 新規 `commit_press(state, snapshots: Sequence[StepSnapshot], deltas_by_key: Mapping[str, Sequence[CounterDelta]], *, pressed_key: str) -> bool`:
  1 押下で状態が変わった**各トリガーの履歴に同じ番号で 1 段ずつ**積む（変わらないトリガーには積まない）。1 段でも積めば `last_trigger = (id, pressed_key)`
- `apply_control` の戻す（`back`）を §4.5.5 に合わせる:
  1. 起点 = 対象 T に印があれば `call_chain.chain_top(...)`（下記）、無ければ T
  2. 起点の履歴の一番上の段の番号 N を取る（履歴が無ければ今と同じく何もしない）
  3. **同じトリガー一覧の中で、履歴の一番上の段の番号が N のトリガーをすべて**、位置・周回・保留・印を段の状態へ戻し、その段のカウンターの差分を打ち消す
  - 印の無い既存の使い方では、起点 = T・番号 N の段は T だけなので、今の結果と同じになること
  - 待機中（`pending_steps` に対象がある）のメッセージ・対象なしの判定は今のまま
- `apply_control` の先頭へ（`rewind`）: 今の処理に加えて**対象の印を外す**（参照先の状態はそのまま）

### 新規 `keyseq/application/call_chain.py`（状態を読むだけの関数）

- `chain_from(state, trigger_set_id, key, find_trigger) -> tuple[str, ...]`: key から印をたどった連鎖（key を含む・最上段まで）。たどり方 = 印のあるトリガーの今の位置の行が呼び出し（`sequence_control.OP_CALL`）なら `call_graph.call_target` の先（`find_trigger` で有効な行があるもの）へ進む。印があっても位置の行が呼び出しでない・参照先が無い・同じキーが 2 度出る・深さ `MAX_CALL_DEPTH` を超えるならそこで止める（例外にしない）
- `chain_top(...)` = `chain_from(...)[-1]`
- ロックの扱いは `snapshot_for` と同じ（読む間だけ `state.lock`）

### テスト（追加まで。既存のテストは変えない）

- 新規 `tests/test_call_chain.py`: 印なし → 自分だけ / 印あり 2 段・3 段 / 位置の行が呼び出しでない・参照先なし・循環・深さ超過で止まる
- `tests/test_sequence_history.py` に追加: 印の変化だけで積む / `commit_press` が変わったトリガーだけに同じ番号で積む / 戻すで同じ番号の一番上の段をまとめて戻し差分を打ち消す（§10-15d の X・A・U の形を状態だけで組む）/
  後から別の押下で一番上が変わったトリガーは戻さない（§10-15 の X・Y 交互）/ 印のある対象の戻すは最上段を起点にする / 先頭へで印が外れ参照先はそのまま / 印なしの既存の戻す・先頭への結果が同じ
- `tests/test_app_state.py`（無ければ新規）: 印の後始末（reset / forget / rekey / forget_trigger_set / rekey_trigger_set）

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.5.1・§4.5.5
- `keyseq/application/app_state.py`（全体）・`keyseq/application/sequence_history.py`（全体）
- `keyseq/domain/call_graph.py:1-40`（`call_target`）・`keyseq/domain/sequence_control.py:1-60`（`OP_CALL`・`MAX_CALL_DEPTH`・`system_op`）
- `tests/test_sequence_history.py`（書き方の手本）

## 含まない

- 印を立てる・押下で最上段を進める・完了で呼び出し元を進める（task_09）/ 連続実行・停止の行・「送った」・一時停止の合流（task_10）
- 停止操作・キーマップ切替で印を残す扱い、要約の問い合わせと表示（task_11）
- `call_context.py`・`sequence_runner/` 配下・presentation の変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass（**既存のテストを 1 件も変えずに**）・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（挙動不変の土台。task_09〜11 の後にまとめて実施）。
