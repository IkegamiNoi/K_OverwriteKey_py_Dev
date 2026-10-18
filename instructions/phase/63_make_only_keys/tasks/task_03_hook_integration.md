# task_03_hook_integration

## 目的

task_02 の状態機械（`MakeOnlyKeyFilter`）を、フックの入口に組み込む（暫定 46 §3.1・§3.2 注 4）。

- タイマーのワーカー・時計・世代つきの予約・フックの開始 / 停止での消去も入れる
- 範囲: application（タイマーのワーカー・新規）と presentation（`hook_controller.py`・`app.py`）
- `input_router` / `key_state_manager` / `make_only_keys.py`（task_02）は変えない

## 対象範囲

### `keyseq/application/delayed_calls.py`（新規）

`class DelayedCallWorker`: 1 本のデーモンのスレッドで、`schedule(delay_s: float, callback)` を受けて、時刻が来たら順に呼ぶ。

- 中身は優先度つきのキューと `threading.Condition`
- `schedule` は**呼び出し元のスレッドで callback を同期実行しない**（`MakeOnlyKeyFilter` はロックの中で `schedule` を呼ぶため）
- callback の例外は `logging` に残して続ける
- スレッドは最初の `schedule` で遅延起動してよい
- `stop()`: 待ちを捨ててスレッドを終える（アプリの終了で呼ぶ）
- tkinter・keyboard を import しない

### `keyseq/presentation/app.py`

- `input_router` を作った後に、`self.make_only_keys = MakeOnlyKeyFilter(...)` を組み立てる。引数:
  - `route=self.input_router.handle`
  - `release_state=self.key_state_manager.handle_event`
  - `clock=time.perf_counter`
  - `schedule=self.delayed_calls.schedule`（`self.delayed_calls = DelayedCallWorker()`）
  - `get_hook_pause_count=lambda: self.hook.get_hook_pause_count()`
  - `get_repeat_delay_ms=lambda: keyboard_repeat_timing()[0]`
  - `on_routes=lambda routes, generation: self.hook.schedule_make_only_routes(routes, generation)`
  - `self.hook` は後で作られるので、遅延評価の lambda で渡す
- アプリの終了処理（`on_close` 系の、フックを止める所の近く）で `self.delayed_calls.stop()` を呼ぶ（例外は握って続ける）

### `keyseq/presentation/controllers/hook_controller.py`

- `on_input_event(event)`（:289-）:
  - デバッグ出力（今の 2 行）は生のイベントのまま、先に行う
  - 次に `result = self._app.make_only_keys.handle(event)`
    - `None` でなければ、`result.routes` の actions を世代つきで予約し（下）、`return result.accept`
    - `None` なら今と同じ経路（`input_router.handle` → actions を `after(0)` → `return route.accept`）
- 世代つきの予約（新規の private メソッド）: route の actions ごとに `after(0, ...)` で予約する
  - 実行時（UI スレッド）に `generation != self._app.make_only_keys.generation` なら捨てる
  - それ以外は今の `_execute_reserved_action(action, route.shadowed)`
- `schedule_make_only_routes(routes, generation)`（公開・タイマーのスレッドから呼ばれる）: 上の予約を呼ぶ
  - `after` が例外（アプリの終了後の `RuntimeError` / `TclError` 等）なら `logging` に残して捨てる
- `start_hook`（:138）と `stop_hook`（:166）: `self._app.key_state_manager.clear()` の直後に `self._app.make_only_keys.clear()` を呼ぶ

### テスト

- `tests/test_delayed_calls.py`（新規）
  - 遅延の順に呼ばれる
  - `schedule` の呼び出し元で同期実行しない（呼び出し元がロックを持っていてもデッドロックしない）
  - callback の例外で止まらない
  - `stop` で終わる
- `hook_controller` の結合（`tests_ui` の既存の手本に合わせる。`tests_ui/test_hook_controller_reserved_actions.py` が近い）
  - 241 のイベントが `make_only_keys.handle` を通り、`result.accept` が返る / actions が予約される
  - 241 以外は今の経路
  - 古い世代の予約は実行時に捨てられる
  - `start_hook` / `stop_hook` で `make_only_keys.clear` が呼ばれる
- `input_router` + `MakeOnlyKeyFilter` + `KeyStateManager` の結合（暫定 46 §6 #2・`tests/` で可）
  - レイアウトに `muhenkan`（`scan_code` 123・`extra_scan_codes` [241]）
  - 直接置換の元キー `muhenkan` → 置換先 `a`
  - 1 回押して離す（時計とタイマーを差し替え）と `SendKeyAction` が 1 回だけ
  - 押し続けるとリピートで繰り返す
  - 離した後に `key_state_manager.is_pressed("muhenkan")` が偽

### 設計メモ / 制約

- task_02 の申し送り: `schedule` の実装は callback を同期で呼ばない（非再入のロックの中で呼ばれるため）
- `after` を呼ぶのはロックの外（`MakeOnlyKeyFilter` は `on_routes` をロックの外で呼ぶ・フックのスレッドの経路も `handle` から戻った後に予約する）
- 241 / 242 以外のキーの経路・戻り値を変えない

## 読むファイル

1. `instructions/history/46_make_only_keys.md` §3.1・§3.2
2. `keyseq/application/make_only_keys.py`（task_02・公開面だけ）
3. `keyseq/presentation/controllers/hook_controller.py`（:120-175・:285-315）
4. `keyseq/presentation/app.py`（:75-90 の import・:130-260 の組み立て・終了処理の `on_close` 付近）
5. `tests_ui/test_hook_controller_reserved_actions.py`（手本）
6. `tests/test_make_only_keys.py`（時計とタイマーの差し替えの手本）

## 含まない

- `make_only_keys.py`・`input_router.py`・`key_state_manager.py` の変更
- 正本反映（task_04）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`
- **実機目視（ユーザー・JIS 外付けキーボード・jis.json）**（暫定 46 §6 #5）
  1. キーボードUI で無変換を BackSpace に置き換える。1 回押すと 1 文字消える / 押し続けると続けて消える / 離すと止まる
  2. 変換を別のキー（例: Enter）に置き換えて押す。IME が切り替わらない / 1 回だけ入る
  3. 無変換を押したまま Shift を押し、無変換を離す。余計な出力が出ない

## 完了条件

- 上記の確認（自動テスト）が pass し、**reviewer が採用**していること
- 実機目視は本タスクで行う（ユーザー）
