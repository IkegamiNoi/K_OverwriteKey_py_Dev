# task_02_execution_core

## 目的

暫定仕様 26 の実行モデルの中核を作る（§4・§5・§6・§10）。
- §4.1: **ステップ**（system は押下を消費しない / 末尾で位置 0・周回を空に / 単発は先頭へ 1 度だけ回り開始位置で終える /
  1 ステップの system 処理が 10,000 を超えたらエラー）
- §4.2・§4.3・§4.4: トリガーごとの**周回スタック**・アプリ全体の**カウンター**、ステップ開始時の整合（張り直し）、生存期間
- §5.2・§5.3: ループの動作と実行時エラー / §6: カウンター +1・0 に / §10: 実行時エラーの通知と停止

**application 中心**。presentation は「位置の変更・編集・削除時に周回を張り直す呼び出し」と「エラー通知の配線」の最小限だけ。
domain は task_01 の `keyseq/domain/sequence_control.py` を使うだけで変更しない。

## 対象範囲（application 中心・presentation は配線の最小限）

### `keyseq/application/sequence_steps.py`（新規）

ステップの進め方を UI・タイマーから独立した関数群として置く（runner の肥大を避ける）。
- `LoopFrame`（dataclass）: `start: int`（始まりの添字）/ `iteration: int`（何周目・1 始まり）。
- `StepOutcome`（dataclass）: 次の通常アクションの添字（無ければ None）/ 保存する位置 / 新しい周回スタック /
  エラー（添字 + メッセージ。無ければ None）/ 末尾に達したか 等、runner が判断に要るもの。
- `advance(actions, position, frames, counters, *, wrap_once: bool) -> StepOutcome`:
  `position` から system アクションを順に処理し、最初の通常アクション（system 以外の行。file_line を含む）の手前で止まる。
  - 開始時に §4.3 の整合を検査: `analyze_loops` で対応崩れが無く、`frames` の始まりの列が `enclosing_loop_starts(position)` と
    一致しなければ、囲むループを周回 1 で張り直す（対応崩れがあれば張り直さない）。
  - `loop_start`: 対応崩れ・深さ超過（`unmatched` / `too_deep`）・回数不正（無限でなく `int(count)` 不能または 1 未満）はエラー。
    正常なら `LoopFrame(start, 1)` を積んで次の行へ。
  - `loop_end`: 対応崩れはエラー。対の始まりの回数を読み、周回 < 回数（または無限）なら周回 +1 して始まりの次へ、
    そうでなければフレームを降ろして終わりの次へ（回数不正はエラー）。
  - `counter_inc` / `counter_reset`: `counters`（呼び出し側の dict を直接更新）の名前（trim のみ・大文字小文字区別）を +1 / 0。名前が空はエラー。
  - `wait` / `back` / `rewind`: **本タスクでは何もせず次へ進む**（task_03 / task_04 で置き換える暫定。コードにその旨のコメントを残す）。
  - op が空・未定義: エラー。
  - 末尾（len）に達したら位置 0・フレームを空にする。`wrap_once=True`（単発）なら 1 度だけ先頭から続け、開始位置に達したら
    その行を処理せず終える（位置は開始位置のまま）。`wrap_once=False`（連続）は末尾に達した時点で終える。
  - 処理した system アクションが 10,000 を超えたらエラー（その行で止まる）。
  - エラー時は位置をエラーの行に置き、フレームはその時点のまま返す。
- `after_normal_action(actions, index, frames) -> (position, frames)`: 通常アクションの実行後の位置（index+1・len なら 0 と空フレーム）。
- エラーメッセージは日本語で、何が不正か分かるもの（例: 「ループの終わりに対応する始まりがありません」「ループの回数が不正です（1 以上の整数）」
  「ループの入れ子が 9 段を超えています」「カウンター名が空です」「system の操作が不正です。操作: <op>」「制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）」）。

### `keyseq/application/app_state.py`

- 周回スタックを実行位置と同じ単位で持つ: `loop_frames` / `keymap_loop_frames`（trigger_set_id → key → list[LoopFrame]）と
  `loop_frames_for(trigger_set_id)`（`indices_for` と同じ規則）。
- カウンター `counters: dict[str, int]`（アプリ全体・保存しない）。
- `reset_indices` / `forget_trigger_set` / `rekey_trigger_set` で周回スタックも同様に消す・付け替える。**カウンターは消さない**（§4.4）。

### `keyseq/application/sequence_runner.py`

- `_run_single_action` と `_run_to_end_step` を `sequence_steps` の `advance` / `after_normal_action` で書き換える。
  - 単発: `advance(wrap_once=True)` → 通常アクションがあれば `perform_action` → 成功なら `after_normal_action`、`False` ならその行に留まる（現行どおり）。
    通常アクションが無ければ（system だけで末尾へ）位置と周回を保存して終える。
  - 連続: 1 ステップ = `advance(wrap_once=False)` → 通常アクションを実行 → 間隔 `run_to_end_delay_ms` で次のステップ。末尾で位置 0・停止（現行どおり）。
  - エラー: 位置・周回を保存し、エラー通知を呼び、連続実行なら停止（§10）。
- 既存の `% len` による回り込みは `advance` の規則に置き換える（system が無いシーケンスでは従来と同じ動き〔1 押下 1 アクション・末尾の次は先頭〕になること）。
- コンストラクタにエラー通知のコールバック `notify_error: Callable[[dict, str], None] | None = None`（キーワード・既定 None）を追加。
- 公開メソッド `reset_loop_frames(key: str) -> None`: アクティブな trigger_set のそのキーの周回スタックを張り直す
  （今の位置を囲むループを周回 1 で。対応崩れなら空）。presentation から位置変更・編集時に呼ぶ。

### presentation（配線の最小限）

- `keyseq/presentation/app.py`: `SequenceRunner` に `notify_error=lambda action, msg: self.hook.show_action_error("", action, msg)` を渡す。
- `keyseq/presentation/controllers/trigger_panel_controller.py`:
  - `on_action_list_select`（位置を変えた後）・`add_action` / `edit_action` / `delete_action` / `move_action`（編集の後）で
    `self._app.sequence_runner.reset_loop_frames(key)` を呼ぶ（§4.3）。
  - `delete_trigger` で `_indices.pop` と同じ箇所で周回スタックも消す。`rename_trigger` でキーが変わるなら、実行位置の扱いに合わせて周回スタックも同様に扱う。

### テスト

- `tests/test_sequence_steps.py`（新規）: `advance` の単体テスト（ループ 1 回 / 3 回 / 無限の途中 / ネスト / 兄弟 /
  単発の回り込みと開始位置での終了〔system だけのシーケンス・`[back]` 相当で 2 度処理しない〕/ 連続の末尾停止 /
  カウンター +1・0 に・名前空・共有 / 対応崩れ・深さ 10・回数不正・未定義 op のエラーと位置 / 10,000 超のエラー /
  §4.3 の張り直し〔一致・不一致・対応崩れ〕/ system を含まないシーケンスで従来どおり）。
- `tests/test_sequence_runner.py`（追記）: 単発・連続で system を含むシーケンスが規定どおり進むこと / エラー時に `notify_error` が呼ばれ停止し位置が残ること /
  system を含まない既存ケースの挙動不変 / `reset_loop_frames`。
- `tests/test_app_state.py` があれば追記、無ければ `test_sequence_steps.py` 内で `AppState` の周回スタックの消去・付け替え（reset / forget / rekey）とカウンター不変を確認。

### 設計メモ / 制約

- `sequence_steps.py` は tkinter・presentation を import しない（`after` 等のタイマーは runner 側だけが持つ）。
- ループの対応・深さは `domain/sequence_control.py` の `analyze_loops` / `enclosing_loop_starts` を使い、再実装しない。
- 1 関数 30 行程度を目安に分割（op ごとの処理を小関数へ）。`sequence_runner.py` は 200 行程度に収める。
- 周回スタックの保存は位置と同じタイミング（`state.lock` の扱いも現行に合わせる）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §4・§5・§6・§10（仕様）
- `keyseq/domain/sequence_control.py`（使う関数: `analyze_loops` / `enclosing_loop_starts` / `system_op` / `action_type` / 定数）
- `keyseq/application/sequence_runner.py` / `keyseq/application/app_state.py`（編集対象・全体）
- `keyseq/presentation/app.py:196-212`（runner の組み立て）/ `:240-252`（`_indices`）
- `keyseq/presentation/controllers/trigger_panel_controller.py:416-480`（rename / delete_trigger）/ `:490-580`（アクションの追加〜選択）
- `tests/test_sequence_runner.py`（既存テストの手本・先頭 80 行程度）

## 含まない

- 待機の実装（`wait` は本タスクでは素通り）→ task_03
- 戻す・先頭へ・戻す履歴・直前のトリガー（`back` / `rewind` は素通り）→ task_04
- file_line の読込と送信（本タスクでは通常アクションとして `perform_action` へ渡すだけ。executor は現状どおり種別不正で止まる）→ task_05
- 編集ダイアログ・追加位置・移動規則 → task_06 / 一覧への周回・カウンター値の表示・色分け → task_07
- 正本・codebase_map の更新 → task_08

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` がエラー無し。
- 単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_steps tests.test_sequence_runner -v` が全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` と `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `grep` で `keyseq/application/sequence_steps.py` に `tkinter` / `keyseq.presentation` の import が無いこと。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_07 でまとめて実施（本タスク単独では一覧に周回が出ないため）。
- **実装モデルの試行**（phase.md）: 実装後に Codex のセッション記録でサブエージェントのモデル・推論レベルを確認し、完了報告に含める。
