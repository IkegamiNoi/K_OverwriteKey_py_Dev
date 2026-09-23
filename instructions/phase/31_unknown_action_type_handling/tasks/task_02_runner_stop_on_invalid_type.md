# task_02_runner_stop_on_invalid_type

## 目的

`SequenceRunner` が executor の戻り値（task_01 で追加）を受け、**種類が不正で「送らなかった」ときにシーケンスを止める**
（暫定仕様 24 §3.2 = 案 S）: run_to_end は停止 / 単発は index を進めない。
あわせて `App._perform_action` が executor の戻り値を返すようにする。

**application（`sequence_runner.py`）+ presentation は委譲 1 行（`app.py` の `_perform_action`）・domain / executor 不変・スキーマ不変**。

## 対象範囲（application 1 ファイル + presentation 1 行 + 既存テストファイルへ追記）

### `keyseq/application/sequence_runner.py`

1. `__init__` の `perform_action` の型を `Callable[[dict[str, Any]], bool | None]` にする。
2. **判定は `self._perform_action(...) is False` のときだけ「送らなかった」**とする（`None` 等を返す既存の呼び出し元〔テストの
   `performed.append` など〕は従来どおり「進める」扱い。`not result` で判定しない）。
3. `_run_single_action`（`:57-71`）: 戻り値が `False` なら **`self.state.indices[key]` を更新しない**。
   `reentry_guard` の解除と `_select_trigger(key)` は既存の `finally` のまま（変えない）。
4. `_run_to_end_step`（`:146-156`）: 戻り値が `False` なら **index を更新せず**（不正な行のまま）、`self.stop_run_to_end()` →
   `self._select_trigger(key)` して return する（次の予約を入れない）。`True` / `None` なら既存の処理（index を進める → 末尾なら停止 / 予約）のまま。
5. `stop_run_to_end` 自体は変えない（予約取り消し・`run_to_end_key = None`・`paused = False`・`update_status`。重複呼び出しは無害）。

### `keyseq/presentation/app.py`

6. `:495-496` の `_perform_action(self, action: dict)` を `-> bool` にし、`return self.action_executor.execute(action)` とする（1 行）。

### `tests/test_sequence_runner.py`（追記）

7. 既存の `FakeScheduler` / `make_runner` はそのまま使い、**本物の `ActionExecutor`**（`input_gateway` / コールバックは `Mock`・
   `tests/test_action_executor_type.py` の組み立てと同じ）を `perform_action=executor.execute` に結線する組み立てを 1 つ追加し、
   下記「確認」の 1〜5 を実装する。既存テストは変更しない。

### 設計メモ / 制約

- **hotkey 検証エラー・`x` / `y` 不正・送信例外の進み方は変えない**（executor はこれらで `True` を返す。runner は `False` のときだけ止める）。
- `handle_key` の run_to_end 中のトグル（`:33-43`）・`pause_run_to_end` / `resume_run_to_end` は変えない。
- 例外は使わない（戻り値で判定する）。`_perform_action` 以外の presentation は触らない。
- `sequence_runner.py` の先頭に BOM がある。**BOM と改行コードを保持**すること。

## 読むファイル

1. 主入力 `instructions/history/24_unknown_action_type_handling.md` §3.2 / §3.6 / §6-3・§6-4
2. `keyseq/application/sequence_runner.py`（編集対象・全体 156 行）
3. `keyseq/presentation/app.py:179-189`（runner の生成）/ `:495-496`（`_perform_action`・編集対象）
4. `keyseq/application/action_executor.py:50-81`（`execute` の戻り値・task_01 の成果。読むだけ）
5. `tests/test_sequence_runner.py`（追記先・全体 107 行）
6. `tests/test_action_executor_type.py` の `setUp`（executor の組み立ての手本）

## 含まない

- 正本 `data_schema.md` §5.11.1 / §5.11.5 の改訂・`codebase_map.md`・暫定 24 の凍結・decisions_archive/31・idea_35 のクローズ・
  `/refactor_check`・完了判定前レビュー（**task_03**）
- executor の変更（task_01 で完了）/ `hook_controller.py` の変更
- 通知の表示中の実行禁止・フック停止（暫定 24 §3.6 / §7 = スコープ外）
- `x` / `y` 不正時の進み方の変更（暫定 24 §7）

## 確認

- 追加する単体テスト（`tests/test_sequence_runner.py`・本物の `ActionExecutor` × `SequenceRunner`）:
  1. **run_to_end**: `[有効な text, 不正な種類(`"hotky"`), 有効な text]` を run_to_end で流すと、1 件目は送られ（`write_text` 1 回）、
     2 件目で停止 = `state.run_to_end_key is None`・`scheduler.queue == []`・`state.indices[key] == 1`（不正な行のまま）・
     3 件目は送られない（`write_text` は合計 1 回）・`on_action_error` 1 回。
  2. **単発**: 不正な種類 1 件のトリガーを 2 回押す → 送信 0 回・`state.indices.get(key, 0) == 0` のまま・`on_action_error` 2 回
     （`reentry_guard` が空に戻っていること）。`[有効, 不正]` で 2 回押すと 1 回目で index 1、2 回目で index 1 のまま。
  3. **通知中の再入**（暫定 24 §6-3）: run_to_end 中、`on_action_error` のダブルの中で同じキーの `handle_key` を 2 回呼ぶ
     （一時停止 → 再開）→ 送信は不正な行以降 0 回・最終的に `run_to_end_key is None`・`scheduler.queue == []`。
  4. **既存経路の進み方が不変**（§6-4）: hotkey 検証エラー（`validate_hotkey` が `("エラー", "")`）/ `mouse_click` の `x` 不正を含む
     run_to_end は**止まらず最後まで進む**（`on_action_error` / `on_runtime_error` は呼ばれ、後続の有効アクションは送られる）。
  5. **`None` を返す `perform_action`**（既存の `make_runner` の `performed.append`）では従来どおり進む（既存テストが pass し続けることで確認）。
- 実測（`verifier`・`.venv` python）:
  - `compileall -q keyseq main.py tests tests_ui` clean
  - `-m unittest discover -s tests` 全 pass（件数は追加分だけ増える）
  - `-m unittest discover -s tests_ui` 全 pass
  - `-m tests.smoke_app` pass
- `git diff -- keyseq` が `keyseq/application/sequence_runner.py` と `keyseq/presentation/app.py`（`_perform_action` の 2 行のみ）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は**任意**（手編集 JSON で `type` を壊したアクションを含むトリガーを run_to_end / 単発で実行し、通知が出てシーケンスが止まる・
  前面アプリへ何も入力されないことを確認する。ユーザー判断で task_03 前に実施してよい）。
