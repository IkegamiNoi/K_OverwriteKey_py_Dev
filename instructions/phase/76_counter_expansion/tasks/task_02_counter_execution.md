# task_02_counter_execution

## 目的

カウンターの実行を暫定 58 §4 に合わせる。①実行時の開始値を `AppState` に持たせ、**実効値**（値が入っていればその値・無ければ開始値・それも無ければ 0）を 1 か所で求める
②カウンターの行は `amount` を足す・リセットは開始値へ ③保留の内容を `(op, name, amount)` にして全経路で同じ型と同じ反映の関数を使う ④無視された押下の巻き戻しで、その押下で初めて値が入った名前を消す。
**application 限定**（`presentation/app.py` の file_line 用 `get_counter` 1 行を除く）。domain・保存形式・表示・UI は変えない。

## 対象範囲（application 限定）

### 新規 `keyseq/application/counter_values.py`

- `class CounterValues(dict[str, int])`: カウンターの値（キーがある = 値が入った）に**開始値**を添えたもの。
  - 属性 `starts: dict[str, int]`（既定 `{}`）。
  - `value(name: str) -> int`: `self[name]` があればそれ / 無ければ `self.starts.get(name, 0)`（実効値）。
  - `set_starts(starts: Mapping[str, int]) -> None`: `starts` を写しで差し替える（`self` の値は変えない・§4.1「値が入った名前は変えない」）。
- モジュール関数 `counter_value(counters: Mapping[str, int], name: str) -> int`: `counters` が `CounterValues` なら `value(name)`、ただの dict なら `counters.get(name, 0)`（既存テストの dict をそのまま受ける）。
  **カウンターを読む・動かす経路はすべてこの関数（または `CounterValues.value`）を通す**。`counters.get(name, 0)` の直読みを application に残さない。
- `counter_start(counters, name) -> int`: `CounterValues` なら `starts.get(name, 0)`・dict なら 0（リセットの行き先）。

### `keyseq/application/app_state.py`

- `counters` の既定を `CounterValues()` にする。`counters` を別の dict で置き換えている箇所があれば `CounterValues` を保つ（置き換えずに中身を操作する）。
- `set_counter_starts(starts: Mapping[str, int]) -> None` を足す（lock の中で `counters.set_starts`）。呼び出し（構成セットの読込等での同期）は task_05。
- 保留 `deferred_counters` / `keymap_deferred_counters` の要素の型を `tuple[str, str, int | None]`（op, name, amount。リセットは `None`）にする。

### `keyseq/application/sequence_steps.py`

- `_counter`: 起点を `counter_value(counters, name)` にする。
  - `counter_inc`: `amount = counter_amount(action)`（`domain.sequence_control`・task_01）。`None` なら実行時エラー（新しい文言キー `application.sequence_steps.counter_amount_invalid`「増やす量が正しくありません」/ 英語 "The amount is not valid."）。
    値 = 実効値 + amount、差分 `(name, amount)` を積む（**amount 0 でも値は入り、差分 0 は積まない**＝リセットの差分 0 と同じ扱い）。
  - `counter_reset`: 値 = `counter_start(counters, name)`、差分 = 開始値 − 反映前の実効値（0 なら積まない・現行どおり）。
- `apply_deferred_counters`: 要素 `(op, name, amount)` を受け、控えた `amount` で反映する（行を読み直さない）。
- 先行処理（`advance` / `settle_after_normal` ほか保留を作る箇所）: 控える内容を `(op, name, amount)` にする。**`amount` が不正（`counter_amount` が `None`）な `counter_inc` の行は控えず、その行で止まり、次のステップの開始時にエラー**（ループの回数不正・待機の `ms` 不正と同じ扱い・暫定 58 §4.2）。
- `format_system_error_notification`: `counter_inc` は値の欄に増やす量を足す（新しいキー `application.sequence_steps.counter_with_amount` = 日本語 `カウンター={counter} 増やす量={amount}` / 英語 `Counter: {counter}, Amount: {amount}`。`amount` が無ければ従来の `counter` のキー）。

### 保留の型の追従（`(op, name)` → `(op, name, amount)`）

`sequence_history.py`（snapshot・比較）/ `call_context.py` / `sequence_runner/linked_call.py`・`call_wait.py`・`call_run_to_end.py`・`run_to_end.py`・`send_wait.py`・`wait_stop.py`・`sequence_runner.py` のうち、保留の組を作る・比べる・写す・反映する箇所をすべて 3 要素にする。
反映は必ず `apply_deferred_counters` を使う（別の反映を書かない）。`grep -rn "deferred" keyseq/application` で漏れを確かめる。

### 無視された押下の巻き戻し（`sequence_runner/linked_call.py` の `_rollback_linked_press`）

- 押下の文脈（`CallContext`・`call_context.py:54` 付近）に、押下の開始時点で `counters` にあった名前の集合を持たせる（新しいフィールド・押下の文脈を作る所で記録）。
- `_rollback_linked_press` は、差分を引いた後に、**その集合に無い名前のキーを `counters` から消す**（その押下で初めて値が入った名前を未使用に戻す・差分 0 のリセットで入った名前を含む）。ユーザー操作の戻す（`sequence_history.undo_counter_deltas`）は変えない。

### `keyseq/presentation/app.py`

- file_line 用 `get_counter=lambda name: self.state.counters.get(name, 0)`（216 行付近）を `counter_value(self.state.counters, name)` に変える（この 1 か所だけ）。

### 文言（`keyseq/shared/i18n/locales/ja.json`・`en.json` の両方）

- 上の 2 キー（`counter_amount_invalid`・`counter_with_amount`）を足す。

### テスト（追加・修正。**テストの実行はしない**）

- `tests/test_counter_values.py`（新規）: `value`（値あり・開始値・0）/ `set_starts` が値を変えない / `counter_value` が dict と `CounterValues` の両方を受ける。
- `tests/test_sequence_steps.py`: amount 3 / −2 / 0 / 不正（エラーで止まる・先行処理で控えず次のステップでエラー）/ 開始値のある未使用の名前に足す・リセットで開始値へ・差分 / 保留に amount が入り控えた値で反映される（負の amount が 1 回だけ）。
- `tests/test_sequence_history.py`: 戻すで amount の差分・リセットの差分が打ち消される。
- `tests/test_sequence_runner*.py`・`tests/test_sequence_runner_call.py`・`tests/test_call_context.py`: **経路ごとに未使用の名前が開始値から動く**（単発・連続実行・呼び出し先のステップ / 一括・連続実行の停止の行・待機の続き）。
  無視された押下の巻き戻しの後、その押下で初めて入った名前が未使用に戻り、続けて `set_counter_starts` で開始値を変えると追従する（加算・差分 0 のリセットの両方・`test_sequence_runner_call.py:2463-2479` 付近の手本）。
- 保留の組を 2 要素で書いている既存テストは 3 要素に直す。
- file_line の一時停止からの読み直しで開始値が使われること（`get_counter` 経由・既存の file_line のテストの手本に合わせる）。

## 設計メモ / 制約

- 主入力 = 暫定 58 §4（§4.1・§4.2・§4.3）・§7.2〜§7.5。
- **`CounterValues` を dict の派生にする理由** = カウンターを受ける既存の関数の引数（`counters: dict[str, int]`）とテストの dict をそのまま通し、経路ごとに開始値の引数を足さずに済ませるため。**`__missing__` で暗黙に開始値を返す実装にはしない**（`get` を通らず、読む箇所が見えなくなる）。読む箇所は `counter_value` を明示的に呼ぶ。
- `undo_counter_deltas` の `counters[name] -= delta` はキーがある前提のまま（差分を積んだ名前は必ず値が入っている）。
- domain は `AppState` / `CounterValues` を読まない（表示の書式は task_04 で実効値を引数で受ける）。
- 呼び出し先の表示枠の写し（`call_view.py`）・一覧の表示・ダイアログ・構成セットからの開始値の同期は**変えない**（task_04・task_05）。
- 編集は apply_patch で行い、Python のスクリプトでファイルを書き換えない。互換の工夫・テストの期待値の推測を足さない。

## 読むファイル

- `instructions/history/58_counter_expansion.md` §4・§7（主入力）
- `keyseq/application/sequence_steps.py`（全体・編集対象）
- `keyseq/application/app_state.py`（全体）
- `keyseq/application/sequence_history.py`（全体）
- `keyseq/application/call_context.py`（全体）
- `keyseq/application/sequence_runner/linked_call.py`（全体）
- `keyseq/application/sequence_runner/` の `call_wait.py`・`call_run_to_end.py`・`run_to_end.py`・`send_wait.py`・`wait_stop.py`・`sequence_runner.py` は `grep -n "deferred\|counters"` の該当箇所だけ
- `keyseq/domain/sequence_control.py` の `counter_amount`（task_01 で追加済）
- 手本のテスト: `tests/test_sequence_steps.py` のカウンターのテスト・`tests/test_sequence_runner_call.py:2440-2490`

## 含まない

- `counter_text` の実行・種別（task_03）
- 一覧・簡易表示・呼び出し先の表示枠の `(=値)` と書式（task_04）
- 編集ダイアログ・開始値の確定・構成セットを置き換える経路からの `set_counter_starts` の呼び出し（task_05）
- 正本 `spec_detail/` の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_counter_values tests.test_sequence_steps tests.test_sequence_history tests.test_call_context` と `tests.test_sequence_runner*`（`discover -s tests -p "test_sequence_runner*.py"`）全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass
- `grep -rn "counters.get(" keyseq/application keyseq/presentation/app.py` が 0 件（実効値を通らない読み方が残っていない）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（task_06 でまとめて実施）。
