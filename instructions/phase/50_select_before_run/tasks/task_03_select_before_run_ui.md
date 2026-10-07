# task_03_select_before_run_ui

## 目的

暫定 34 §5・§7 の presentation 側を実装する: フック欄の全体のチェック（フル = 操作可・省略 = 表示のみ）・出力シーケンス欄のトリガーごとのチェック・runner への注入（選ばれている有効な行のキー・全体の設定）。
**presentation 限定（判定は task_02 で実装済み・保存は task_01 で実装済み）。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/ui_vars.py`

- `select_before_run_var`（全体・BooleanVar・初期値は `master.data` の `select_before_run`）と `sequence_select_before_run_var`（トリガーごと・BooleanVar・初期値 False）を足す（`hook_keys_individual_var` / `run_to_end_var` と同じ流儀）

### フック欄（全体）

- `views/full_view/hook_frame.py`: 「このキーマップセットで個別指定する」の**次の行**にチェックボックス「選んでから実行」（`select_before_run_var`・command = App の新しい小さなメソッド）
- `views/compact_view/hook_frame.py`: 同じ位置に同じ文言のチェックボックスを `state="disabled"` で表示のみ（個別指定チェックと同じ作法・同じ変数）
- `presentation/app.py`:
  - 新メソッド（例 `toggle_select_before_run`）: `self.data["select_before_run"] = bool(var.get())` → 構成セットを未保存（`self.dirty_tracker.set_dirty(True)`・`toggle_hook_keys_individual` と同じ扱い）
  - `_sync_control_vars_from_data`（:517-）に `select_before_run_var.set(self.data.get("select_before_run") is True)` を足す（読込・新規作成・例を復元・Import で同期される経路）
  - `SequenceRunner(...)` の生成（:220 付近）に注入: `get_selected_trigger_key` = 一覧で選んでいる行が有効な行ならそのキー（`normalize_key_name` 済み）・そうでなければ None（`trigger_panel.selected_trigger_key()` と `selected_trigger_is_effective()` を使う）/ `is_select_before_run_enabled` = `self.data.get("select_before_run") is True`
  - app.py は 661 行。増分は最小にする（新メソッドは数行）

### 出力シーケンス欄（トリガーごと）

- `views/full_view/sequence_box.py`: 「連続実行」のチェック（:69-75）の**直下**（「間隔(ms)」の行の上）にチェックボックス「選んでから実行」（`sequence_select_before_run_var`）
- 同期と書き戻し（「連続実行」と同じ扱い）:
  - 選択の切替で選んでいるトリガーの `select_before_run` を var へ（未選択なら False）
  - 操作で選んでいるトリガーの `select_before_run` を更新し、値が変わればそのシーケンスを未保存（`mark_sequence_dirty`）
  - グレーの行・未選択時の扱いは「連続実行」のチェックと同じ
- **`trigger_panel_controller.py`（637 行）は増やさない**: 同期・書き戻しは `sync_run_to_end_ui` / `update_run_to_end`（:377-, :511-）と同じ流れに 1〜2 行で乗せるか、`controllers/trigger_panel/` に小さな補助へ切り出す（640 行以下を保つ）
- ボタン列の幅が変わる場合でもフル表示の最小幅の計測（`pane_measure.py`）はチェックボックスを含めて測る（既存の作法のまま）

### テスト（tests_ui/）

- 新規 `tests_ui/test_select_before_run_ui.py`（App を作るので `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法で実 `config/` を隔離・`setUpClass` で共有）:
  ①全体のチェックの操作で `data["select_before_run"]` が変わり構成セットが未保存になる ②省略表示の全体のチェックは disabled で同じ値を表示
  ③`_sync_control_vars_from_data` の経路（データの差し替え）で全体のチェックが同期 ④トリガーの選択の切替でトリガーごとのチェックが同期・操作でトリガーの値が変わりシーケンスが未保存
  ⑤配線: 全体 ON で選ばれていないトリガーの押下（`sequence_runner.handle_key`）→ 一覧で選ばれ・実行されず・一時メッセージ「<key> を選びました（もう一度押すと実行します）」→ もう一度で実行
  ⑥配線: `repeat=True` の押下（`ActionExecutor.execute_router_action(TriggerAction(key, True))`）が runner まで届き無視される
  ⑦グレーの重複行を選んでいるときの押下は選ぶだけ（有効な行へ移る）

## 読むファイル

- `instructions/history/34_select_before_run.md` の §5・§7
- `keyseq/presentation/ui_vars.py`・`views/full_view/hook_frame.py`・`views/compact_view/hook_frame.py`（全体）・`views/full_view/sequence_box.py:60-90`
- `keyseq/presentation/app.py:205-245, 510-530, 590-615`・`controllers/trigger_panel/trigger_panel_controller.py:100-145, 370-405, 505-525`
- テストの手本: `tests_ui/test_keymap_set_history_flow.py:17-34`・`run_to_end` の UI を扱う既存テスト（`grep -rln "run_to_end_var" tests_ui`）

## 含まない

- 判定・保存の変更（task_02 / task_01 で完了）・正本の改訂（task_05）
- 省略表示のシーケンス欄へのトリガーごとのチェック（出さない・§2-6）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加したテストを含めて tests・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない
- `trigger_panel_controller.py` が 640 行以下

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（ユーザー）: 本タスクで実施（チェックの置き場・全体 / 個別の ON・OFF・選ぶだけの案内・2 回目の実行・長押し・待機中の選択・省略表示の表示・保存して再読込）
