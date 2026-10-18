# task_03c_make_only_trace

## 目的

task_03 の実機目視で次の 2 つの不具合が出たので、原因を実測するための時刻つきのデバッグ出力を足す（2026-10-19）。

- リピートの途中で IME が切り替わる
- 離してもリピートがすぐ終わらない

デバッグ設定 `debug_jis_special_key_events` が真のときだけ出す（既存のデバッグ出力と同じ設定・既定は偽）。
**挙動は変えない**（出力だけ）。application・presentation 限定。

## 対象範囲

### `keyseq/application/make_only_keys.py`

- コンストラクタに任意の引数 `trace: Callable[[str], None] | None = None` を足す（既定 `None` = 何もしない）
- 次の時点で `trace(f"...")` を呼ぶ。各行に `t={now:.4f}`・走査コード・世代を含める
  - 押した: `accept`・`has_actions`
  - 離した直後の捨て
  - 保留にした: 古い押下の印
  - 離した: 保留からの経過 ms
  - 遅れた満了で確定: 経過 ms
  - 保留の確定: 種類（リピート / 古い押下の押し直し / 何もしない）・`route` の `accept` と actions の数
  - 満了処理: 呼ばれた時刻・早すぎて待ち直した / 世代違い・保留違いで捨てた
  - `up`
  - 停止要求中で素通しにした
- `trace` の呼び出しはロックの中でよい（`print` 相当の軽い処理だけを渡す）

### `keyseq/presentation/app.py`

- `MakeOnlyKeyFilter(...)` に `trace=self._make_only_trace` を渡す
- `_make_only_trace(line)`: `self.data.get("debug_jis_special_key_events")` が真なら `print("[make-only] " + line, flush=True)`

### `keyseq/presentation/controllers/hook_controller.py`

`on_input_event` で、デバッグ設定が真のときだけ、**すべてのイベント**について 1 行出す。

- 内容:
  - 入口の `time.perf_counter()`（4 桁）
  - `event_type` / `scan_code` / `name`
  - 押下だけのキーかどうか
  - 戻り値 `accept`
  - actions の数
  - 処理にかかった ms（入口から return まで）
  - `get_send_guard_count()` の値（`self._app._get_send_guard_count()`）
- 形式: `print(f"[hook] t=... type=... scan=... name=... make_only=... accept=... actions=... guard=... dur_ms=...", flush=True)`

`_execute_make_only_action` と `_execute_reserved_action` の実行時（UI スレッド）にも、デバッグ設定が真なら次を 1 行出す。

- `[ui] t=...`
- action の種類
- 世代の比較結果（捨てたか）

### テスト

- `tests/test_make_only_keys.py`: `trace` を渡すと各遷移で呼ばれる（押した・離した・リピートの 3 つ程度）/ 渡さなくても動く
- 既存テストは変えない（`trace` 既定 `None`）

## 読むファイル

1. `keyseq/application/make_only_keys.py`（全体）
2. `keyseq/presentation/controllers/hook_controller.py:290-345`
3. `keyseq/presentation/app.py`（`MakeOnlyKeyFilter(` を組み立てている所）

## 含まない

- 挙動の修正（計測の結果を見てから決める）
- 正本反映

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_make_only_keys tests.test_make_only_keys_integration` が全 pass
- 既存テストが全 pass（`unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`）

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- そのうえで、ユーザーにデバッグ設定を有効にして実機で操作してもらい、出力を受け取る
