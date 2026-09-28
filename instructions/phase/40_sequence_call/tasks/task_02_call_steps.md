# task_02_call_steps

## 目的

ステップの進め方（`advance` / `settle_after_normal`）で呼び出しの行を「押下を消費するアクション」として止める（暫定 29 §4.1）。
あわせて、呼び出し文脈の中で使うための「無限ループの始まりでエラー」の分岐を足す（§4.2・§4.4）。**application（`sequence_steps.py`）とテストのみ・既定値で既存の挙動は不変**。

## 対象範囲

### `keyseq/application/sequence_steps.py`

- `advance`: 呼び出しの行（`action_type == system` かつ `system_op == OP_CALL`）に達したら、**通常アクションと同じ位置・同じ形**で
  `StepOutcome(normal_index=その行, position=その行, ...)` を返す（上限 10,000 の判定・`processed` の加算より前。通常アクションが返る箇所と同じ扱い）。
  単発の先頭への回り込み・開始位置で終える規則は通常アクションと同じになること。
- `settle_after_normal`: 呼び出しの行で止まる（処理しない）。現状も未知の op で止まるが、`OP_CALL` を明示して止める。
- `advance(..., in_call: bool = False)` / `settle_after_normal(..., in_call: bool = False)` を追加（キーワード専用・既定 False）:
  - `advance` で `in_call` が True のとき、**無限のループの始まり**（`loop_start` で `infinite` が真）に達したら実行時エラー「呼び出し先に無限ループがあります」（位置はその行）。
  - `settle_after_normal` で `in_call` が True のとき、無限のループの始まりでは止まる（処理しない。次の `advance` でエラーになる）。
  - False のときは従来どおり。
- `_system_step` は変更しない（呼び出しの行は `_system_step` に到達しない）。

### テスト（`tests/test_sequence_steps.py`）

1. `advance`: `[counter_inc, call, A]` 位置 0 → counter を処理し `normal_index=1`（呼び出しの行）/ `processed` に呼び出しを数えない
2. 単発 `wrap_once=True`: `[A, call]` の位置 1 から → `normal_index=1` / `[call]` だけのシーケンスで位置 0 → `normal_index=0`
3. `settle_after_normal`: `[A, loop_start×2, call, loop_end]` の位置 1 から → ループの始まりを処理して呼び出しの行（位置 2）で止まる
4. `in_call=True`: `[loop_start(infinite), A, loop_end]` 位置 0 → エラー「呼び出し先に無限ループがあります」/ `in_call=False` では従来どおり周回を積んで A
5. `settle_after_normal(in_call=True)`: 無限のループの始まりの手前で止まる / `in_call=False` では従来どおり処理する
6. 呼び出しを含まない既存テストが無変更で通る

## 読むファイル

- `instructions/history/29_sequence_call.md` §4.1・§4.4
- `keyseq/application/sequence_steps.py`（全体・編集対象）
- `keyseq/domain/sequence_control.py:1-40`（`OP_CALL`・`system_op`・`action_type`）
- `tests/test_sequence_steps.py:1-60`（書き方の手本）

## 含まない

- runner での呼び出しの実行（task_03〜05。それまでは呼び出しの行に達すると既存の `perform_action` へ渡り送信エラーになる＝UI からはまだ作れないので受容）
- 呼び出し文脈（task_03）/ UI（task_06〜08）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_steps -v` が全 pass・`unittest discover -s tests` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 呼び出しの行が通常アクションと同じ位置で返る / 上限の数え方 / 既定値で従来どおり / 無限ループの分岐 / 先取りなし）。
