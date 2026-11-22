# task_04_counter_display

## 目的

出力シーケンスの一覧・簡易表示の要約・呼び出し先の表示枠で、カウンターの行を暫定 58 §5.3 の書式にし、`(=値)` を**実効値**（未使用の名前は開始値）にする。
**domain の書式（`sequence_control.py`・`config.py`）・application の表示用の値（`counter_values.py`・`call_view.py`）・presentation の呼び出し箇所に限定**。実行・保存・ダイアログは変えない。
domain は `AppState` / `CounterValues` を読まず、実効値と開始値を**引数で受け取る**（§5.3・依存方向）。

## 対象範囲

### `keyseq/application/counter_values.py`

- `counter_display_values(counters: Mapping[str, int]) -> dict[str, int]`: 表示用の実効値の写し。`CounterValues` なら `{**counters.starts, **counters}`（値が入った名前は値・それ以外は開始値）、ただの dict ならその写し。
- `counter_starts_of(counters: Mapping[str, int]) -> dict[str, int]`: 開始値の写し（`CounterValues` なら `dict(counters.starts)`・dict なら `{}`）。

### `keyseq/domain/sequence_control.py`

- `format_control_value(..., counter_starts: Mapping[str, Any] | None = None)` を足し、内側の書式関数へ渡す。表示は §5.3:
  - `counter_inc`: `counter_amount(action)` が整数なら `[count{amount:+d}] n (=v)`（`[count+1]`・`[count+3]`・`[count-2]`・`[count+0]`）/ `None`（不正）なら `[count?] n (=v)`。
  - `counter_reset`: `[count={開始値}] n (=v)`（開始値 = `counter_starts.get(n, 0)`・`counter_starts` が `None` なら 0。既存の `[count=0]` は開始値 0 の場合と一致）。
  - 新しい種類 `counter_text`: `[counter_text] n (=v)`（`ACTION_TYPE_COUNTER_TEXT`・`format_control_value` の種類の分岐に足す）。
  - `(=v)` は従来どおり `counters.get(n, 0)`（呼ぶ側が実効値の写しを渡す）。file_line の書式は変えない。

### `keyseq/domain/config.py`

- `format_action_list_item(..., counter_starts=None)` を足して `format_control_value` へ渡す。`is_control_action` の種類に `ACTION_TYPE_COUNTER_TEXT` を足す（一覧の行頭は他の制御と同じく `format_control_value` の印をそのまま使う）。

### `keyseq/application/call_view.py`

- `CallViewSummary` に `counter_starts: Mapping[str, int]` を足す。`build_call_view_summary` は `counters` を `counter_display_values(counters)`、`counter_starts` を `counter_starts_of(counters)` の読み取り専用の写し（`MappingProxyType`）にする。

### `keyseq/presentation/controllers/action_list_rendering.py`

- `build_action_rows` / `format_next_action_summary` に `counter_starts: Mapping[str, int] | None = None` を足して `format_action_list_item` へ渡す。
- `format_next_action_summary` の制御の種類の列挙（59 行）に `"counter_text"` を足す。

### 呼び出し箇所（presentation）

- `controllers/trigger_panel/trigger_panel_controller.py:294-299`・`:500-505`: `counters=counter_display_values(self._app.state.counters)`・`counter_starts=counter_starts_of(self._app.state.counters)` を渡す。
- `controllers/call_view_controller.py:224-229`: `counter_starts=summary.counter_starts` を足す。
- 他に `build_action_rows` / `format_next_action_summary` / `format_action_list_item` に `counters=` を渡している箇所があれば同じく直す（`grep -rn "counters=" keyseq/presentation`）。

### テスト（追加・修正。**テストの実行はしない**）

- `tests/test_sequence_control.py`: `[count+1]`（キー無し）・`[count+3]`・`[count-2]`・`[count+0]`・`[count?]`（`"abc"`）/ リセットの `[count=10]`（開始値あり）・`[count=0]`（`counter_starts` 無し）/ `[counter_text] n (=5)`。
- `tests/test_counter_values.py`: `counter_display_values`（値あり・開始値だけ・dict）・`counter_starts_of`。
- `tests/test_call_view.py`: 要約の `counters` が実効値（未使用の名前が開始値）・`counter_starts` が写しで、元を変えても要約が変わらない。
- `tests_ui/test_action_list_rendering.py`（既存の作り方に合わせる。tests_ui の追加は最小限）または `tests/` 側の該当テスト: `build_action_rows` が開始値を `(=値)` とリセットの `=` に出す・要約が `counter_text` を一覧と同じ書式にする。
- 既存の `[count+1]` / `[count=0]` の期待値のテストはそのまま通ること（変えない）。

## 設計メモ / 制約

- 主入力 = 暫定 58 §5.3・§4.1（表示も実効値）。
- 実効値の式（値 → 開始値 → 0）は application の `counter_values.py` に置く（task_02 の `counter_value` と同じモジュール）。domain は渡された写しを読むだけ。
- **描き直しの契機**（開始値の確定・構成セットの置き換えの後に一覧と呼び出し先の表示枠を描き直す）は、開始値を変える側の task_05 で既存の描き直しを呼ぶ。本タスクでは足さない。
- 編集は apply_patch で行い、Python のスクリプトでファイルを書き換えない。互換の工夫・テストの期待値の推測を足さない。既存のテストの途中に新しいテストを差し込まない。

## 読むファイル

- `instructions/history/58_counter_expansion.md` §5.3（主入力）
- `keyseq/domain/sequence_control.py:180-275`（`format_control_value` 以下）
- `keyseq/domain/config.py:486-520`（`format_action_list_item`）
- `keyseq/application/counter_values.py`（全体）・`keyseq/application/call_view.py`（全体）
- `keyseq/presentation/controllers/action_list_rendering.py:24-70`
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:288-300,498-506`・`controllers/call_view_controller.py:218-230`
- 手本のテスト: `tests/test_sequence_control.py` の書式のテスト・`tests/test_call_view.py`

## 含まない

- 編集ダイアログ・開始値の確定・`set_counter_starts` の呼び出し・描き直しの契機・文言・ヘルプ（task_05）
- 正本 `spec_detail/` の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_control tests.test_counter_values tests.test_call_view tests.test_domain_config` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass
- tests_ui を足した・直した場合はそのモジュールだけ（例 `-m unittest tests_ui.test_action_list_rendering`）を 1 本ずつ流す

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（task_06 でまとめて実施）。
