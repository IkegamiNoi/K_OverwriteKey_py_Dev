# task_01_stop_domain_and_steps

## 目的

system の操作「停止」（`op: stop`）を domain に定義し、ステップの進め方（`advance` / `settle_after_normal`）で扱えるようにする（暫定 28 §3・§4）。
runner への組み込み（連続実行を終える・読み飛ばしの印・保留の反映）は task_02。
**domain（`sequence_control.py`）+ application（`sequence_steps.py`）とテストのみ・UI 非依存の純関数・既存の挙動（停止を含まないシーケンス）は不変**。

## 対象範囲

### `keyseq/domain/sequence_control.py`

- `OP_STOP: str = "stop"` を追加する。
- 表示: `format_control_value`（`_format_system_value`）で停止を `[stop]` にする。

### `keyseq/application/sequence_steps.py`

- `StepOutcome` に `stopped: bool = False`、`SettleOutcome` に `stopped: bool = False` を追加する（既存の生成箇所は変えない位置・既定値つき）。
- `advance(..., stop_ends_run: bool = False)` を追加（キーワード専用・既定 False = 従来どおり）。停止の行に達したら `processed` を 1 増やしてから（上限の判定は他の system と同じ位置で先に行う）:
  - `stop_ends_run` が False → 読み飛ばす（位置 + 1 で続ける）。単発実行・連続実行で「まだ通常アクションを送っていない」ときに runner が False を渡す。
  - True → **停止の次の位置で `StepOutcome(None, 次の位置, 周回, stopped=True, counter_deltas=…, wrapped=…, processed=…)` を返す**。
    次の位置が末尾（= `len(actions)`）なら位置 0・周回を空にする（末尾の規則）。
- `settle_after_normal(..., stop_ends_run: bool = False)` を追加。停止の行に達したら:
  - False → 読み飛ばして続ける（`processed` + 1。待機・戻す・先頭へ等で止まる既存の規則は変えない）。
  - True → 停止の次の位置（末尾なら 0・周回を空）で `SettleOutcome(..., stopped=True)` を返す。それまでに控えた `deferred_counters` はそのまま返す（反映は runner・task_02）。
  - 上限 10,000 に達して止まる既存の判定は、停止の行を調べる**前**に行う（達していれば停止を処理せず止まる＝暫定 §4.1-1 の境界）。
- `_system_step` で `OP_STOP` を「位置 + 1・エラーなし」にする（未知の op のエラーにしない。念のための経路）。
- 戻す・先頭への単独登録の検査（`advance` 内と `domain/sequence_editing.py` の `standalone_violation`）は**変えない**（停止は混ぜてよい）。

### テスト

- `tests/test_sequence_control.py`: `[stop]` の表示（ラベルなし / あり〔既存の `format_action_list_item` の規則〕）。
- `tests/test_sequence_steps.py`（既存の書き方に合わせる）:
  1. `advance(stop_ends_run=False)`: `[stop, A]` で A の手前まで読み飛ばす（normal_index=1）/ 単発 `wrap_once=True` で `[A, stop]` の位置 1 から → 末尾で回り込み A
  2. `advance(stop_ends_run=True)`: `[stop, A]` 位置 0 → `stopped=True`・位置 1 / `[A, stop]` 位置 1 → `stopped=True`・位置 0・周回空 / ループ内の停止で周回が保たれる
  3. `advance(stop_ends_run=True, resume=待機の続き)`: `[A, wait, stop, B]` の待機の続きで停止 → `stopped=True`・位置 3・counter_deltas を引き継ぐ
  4. `settle_after_normal(stop_ends_run=True)`: `[A, counter_inc, stop, B]` の位置 1 から → `stopped=True`・位置 3・deferred に counter_inc / 停止が最後の行 → 位置 0・周回空
  5. `settle_after_normal(stop_ends_run=False)`: 停止を通過して次の通常アクションの手前まで / 待機の手前では従来どおり止まる
  6. 上限: `processed=10000` で settle に入ると停止を処理しない（`stopped=False`・位置は停止の行）
  7. 停止を含まない既存テストが無変更で通る

## 読むファイル

- `instructions/history/28_sequence_stop_and_call.md` §3・§4（`:38-70` 付近）
- `keyseq/domain/sequence_control.py:1-40`・`:127-180`
- `keyseq/application/sequence_steps.py`（全体・編集対象）
- `tests/test_sequence_steps.py:1-60`（書き方の手本）/ `tests/test_sequence_control.py` の表示テスト部分

## 含まない

- runner での利用（`stop_ends_run` の渡し方・連続実行を終える・読み飛ばしの印・保留の反映・戻す履歴）（task_02）
- 編集ダイアログ・一覧の UI（task_03）/ 正本・codebase_map（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_steps tests.test_sequence_control -v` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存の失敗なし）

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 既定値で従来どおり / 停止の位置・末尾の規則・周回 / 上限の判定順 / 単独登録の制限を変えていない / 後続タスクの先取りなし）。
- 実機目視: task_03 でまとめて実施。
