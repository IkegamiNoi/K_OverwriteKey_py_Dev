# task_02_step_call_single

## 目的

ステップの呼び出しの**土台（段の印）と単発の実行**を実装する（暫定 31 v0.4 §4.1・§4.2・§4.4・§10-2・§10-3・§10-5〔単発〕・§10-6〔単発〕）。
**application（`call_context.py`・`sequence_runner/{call_wait,input_acceptance}.py`）中心。presentation・JSON・連続実行の停止の行（task_03）は変えない。一括の呼び出しの挙動は変えない。**

## 対象範囲

### `keyseq/application/call_context.py`

- `CallFrame` に **`step: bool = False`**（その段がステップとして動くか）を足す
- 段を積むとき（文脈の開始・入れ子の `_push_frame` 相当）に、**`step = 呼び出しの行が is_step_call かつ 下の段（呼び出し元なら True とみなす）も step`** で決める（§4.1: 一括の中のステップの行は一括）。
  判定は task_01 の `domain/sequence_control.is_step_call` を使う
- 呼び出し先の 1 ステップ（`call_step`）の結果から、**最上段がステップの段かを呼び出し側が判定できる**ようにする（例 `CallStep` に `top_is_step: bool` を足す / `CallContext` に `top_is_step()` を足す。どちらかに統一）
- 入れ子の呼び出しの行・空の呼び出し先は現行どおり同じ `call_step` の中で通過する（押下を消費しない = §4.2）。system の上限 10,000 は `call_step` の 1 回ごとに数える現行のまま

### `keyseq/application/sequence_runner/call_wait.py`（単発の呼び出し）

- 呼び出し先の通常アクションを送り終えて文脈の中の先行処理をした後（現行は次を予約する箇所）、**最上段がステップの段なら次を予約せず「押下の合間」に入る** = 単発の呼び出しの一時停止と同じ状態にする
  （`pending.call_paused = True`・世代を進める・予約を取り消す・`update_status`。`_pause_single_call` の処理を共有する）
- 段を降ろして呼び出し元へ戻る（`done`）・エラー・打ち切りは現行どおり（呼び出しの成功は同じ押下の中で呼び出し元の先行処理）
- **ステップの段の再開は間隔を置かない**（`_resume_single_call` の `top_interval` の遅延は、最上段がステップの段なら 0）。呼び出し先の待機は、再開した押下の頭で `call_step` が返す `wait` を待つ（現行の文脈の待機と同じ）

### `keyseq/application/sequence_runner/input_acceptance.py`（押下の受け付け）

- 押下の合間（`call_paused` かつ最上段がステップの段）にそのトリガーを押したら、**`_resume_single_call`（= 1 ステップ進めて、送った後にまた合間へ）**。区別は不要（再開 = 次の 1 ステップ）
- **1 ステップの処理中**（`_active_key()` がそのキーで、保留中の単発の呼び出しが**ステップの文脈 = 最初の段がステップの段**。入れ子の一括の実行中を含む・暫定 31 §4.2）に同じトリガーを押したら**無視**する（現行の「一時停止にする」を、ステップの文脈のときだけ無視へ）。
  一括の文脈（最初の段が一括）のときは現行どおり一時停止（2026-10-04 メイン修正: 当初「最上段がステップ」と書いたが、入れ子の一括の実行中を含めるため「最初の段」に訂正）
- 他のトリガー・捨てる契機・戻す / 先頭への 2 回押し・同時に持てる数は、単発の呼び出しの一時停止の現行の扱いのまま（押下の合間は `call_paused` なので自動で従う）
- 戻す履歴・直前のトリガー: 現行どおり呼び出し全体で 1 段（`PendingStep.snapshot` を持ち越す）。押下の合間には積まない

### テスト（追加・修正まで）

- `tests/`（`test_sequence_runner.py` / 呼び出しのテストに倣う。偽のタイマーで進める）:
  - 呼び出し元 `[call step f5, X]`・f5 `[A, B]`: 1 押下目 = A を送って合間（`call_paused`）/ 2 押下目 = B を送り、呼び出しが成功して呼び出し元の先行処理（次に実行 = X）/ 3 押下目 = X
  - 合間に他の単発トリガーが動き、文脈が残る / 合間に他のトリガーの連続実行を開始すると捨てられ、位置は呼び出しの行
  - 入れ子 `f5 = [call step f7, B]`・`f7 = [C]`: 1 押下目で C まで進む（入れ子の呼び出しの行は押下を消費しない）/ 空の呼び出し先は同じ押下で通過
  - 一括の中のステップの行（f5 が一括で、中に `call step f7`）は一括として 1 押下で丸ごと実行
  - 呼び出し先の待機 `f5 = [A, wait 100, B]`: 2 押下目の頭で 100ms 待ってから B を送る。再開に間隔を置かない
  - 処理中（待機中）に同じキーを押しても無視（一時停止しない）。一括の呼び出しの処理中は現行どおり一時停止
  - 戻す履歴が呼び出し全体で 1 段・合間には積まない
  - 呼び出し先の停止の行は単発では読み飛ばす
  - 一括の呼び出しの既存のテストがすべて変わらず通る

### 設計メモ / 制約

- 押下の合間の状態を新設しない（`call_paused` を使う = 暫定 31 §4.2）
- 連続実行のステップ（停止の行・「送った」の文脈の印・停止の後の分岐）は task_03。本タスクで連続実行の経路に段の印が届いても、挙動は一括のまま
- `call_wait.py` は 307 行。増えて 300 行を大きく超える・関数 30 行を超えるなら、ステップの判定を小さな関数に分ける

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4
- 正本 `features.md` §4.2.9・§4.2.10
- `keyseq/application/call_context.py`（全体）
- `keyseq/application/sequence_runner/call_wait.py`（全体）・`input_acceptance.py`（全体）
- `keyseq/application/app_state.py:15-45`（`PendingStep`）
- `keyseq/domain/sequence_control.py` の `is_step_call`
- 手本のテスト: 単発の呼び出しの既存のテスト（`grep -rln "call_paused\|_start_single_call" tests`）

## 含まない

- 連続実行のステップ（task_03）/ 表示の要約・通知（task_04）/ 枠（task_05・06）/ 正本反映（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。task_03 の完了後に task_02・03 をまとめて統合確認（`deep-reviewer` + `codex-reviewer`）。
- **実機目視（task_03 とまとめて実施）**: 単発でステップの呼び出しを押すたびに呼び出し先が 1 行ずつ進む・合間に他のトリガーが動く・最後の押下で呼び出し元の次へ進む。
