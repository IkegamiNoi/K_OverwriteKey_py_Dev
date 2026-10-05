# task_02_apply_control_target

## 目的

戻す・先頭への実行時に、行の `target`（task_01 の `control_target`）で対象を決める（暫定 32 §4）。
`target` が無ければ従来どおり直前のトリガー、あれば同じトリガー一覧の指定先、空・見つからない・自分自身なら「戻す対象のトリガーがありません」。
判定の順序（待機 / 一時停止の検査と 2 回押しの破棄が先・戻す段が無ければ戻さず選択も移さない）と直前のトリガー不変は現行の仕組みのまま満たし、テストで固定する。
**application 限定。domain は task_01 の関数を使うだけ・presentation は変えない・スキーマ不変。**

## 対象範囲（application 限定）

### `keyseq/application/sequence_history.py`

- `apply_control` にキーワード専用引数 `target_key: str | None = None` を足す（`control_target` の結果をそのまま受ける）
  - `None` → 現行どおり `state.last_trigger`（既存の判定 :199-202 は不変）
  - `None` 以外 → `target = (source[0], target_key)`。`target_key == ""`・`target_key == source[1]`・`find_trigger(target_key) is None` なら `(None, NO_TARGET_MESSAGE)`
  - 以降（`_back_origin`・`_control_group`・`prepare_targets`・`_restore_press_group`・rewind）は**変えない**
  - docstring を「`target_key` があればそれ・無ければ直前のトリガー」に直す
- `state.last_trigger` を書かない（現行どおり）

### `keyseq/application/sequence_steps.py`

- `advance` の `on_control` の型を `Callable[[str, str | None], None] | None` にし、:285-286 で `on_control(op, control_target(action))` と呼ぶ（`keyseq.domain.sequence_control.control_target` を import）

### `keyseq/application/sequence_runner/sequence_runner.py` / `run_to_end.py`

- `_control(self, key, op)` を `_control(self, key, op, target_key=None)` にし、`apply_control(..., target_key=target_key)` へ渡す（`sequence_runner.py:284-292`）
- 2 つの `on_control` クロージャ（`sequence_runner.py:318-320`・`run_to_end.py:196-198`）を `def on_control(op: str, target_key: str | None) -> None:` にし `self._control(key, op, target_key)` を呼ぶ

### テスト

- `tests/test_sequence_history.py`（既存クラス `SequenceHistoryControlTest` へ追加）:
  - `target_key` ありの back / rewind が `last_trigger` と違うトリガーに効く（選択キー・位置・履歴）・`last_trigger` が変わらない
  - `target_key` の `""` / 自分自身 / 見つからない → `(None, NO_TARGET_MESSAGE)`・状態を変えない
  - `target_key` ありで `last_trigger` が `None` でも動く
  - `target_key` ありの戻すで、参照中の印がある指定先は連鎖の最上段を起点にする（既存の `test_back_from_marked_target_uses_chain_top_as_origin` の形を流用）
  - `target_key` ありで指定先が待機中 → `PENDING_TARGET_MESSAGE`
- `tests/test_sequence_steps.py`（:419-425 付近の `on_control` のテスト）: 呼び出し引数が `(op, target_key)` になったことに合わせて直し、`target` ありの行で正規化後のキーが渡ることを追加
- `tests/test_sequence_runner.py`（既存の 2 回押しのテストの形を流用）:
  - 指定ありの戻すのトリガー B（`target: "T"`）と T・別のトリガー X を置き、X を押して直前のトリガー = X の状態で B を押すと T が戻る（X は変わらない）
  - **受け入れ条件 10**: 履歴の無い T（連続実行・先頭に file_line）を開始し、読込中に一時停止 → B を 1 回押すと「一時停止中の t を破棄します。もう一度押すと実行します」の通知・状態不変 → 2 回目で一時停止中の実行を破棄し、戻す段が無いので位置は先頭のまま・`_control` の戻り値（選択キー）は `None`。
    file_line の読込中の一時停止の作り方が既存テストで難しければ、待機（`wait`）の一時停止など**履歴が空のまま一時停止中になる**別の作り方でよい（その旨をテストのコメントに 1 行）
  - 2 回押しの控えの対象が T（`_pending_control_discard` を直接見ず、通知の文言のキーで確認する）

### 設計メモ / 制約

- `input_acceptance.py` は**変更しない見込み**（控えは対象の identity で持つため T で満たされる）。変更が必要と判断したら実装を止めて理由を報告する
- 「戻す対象のトリガーがありません」以外の新しい文言は作らない
- `call_context.py:253` の `on_control=None`（呼び出し先の中）はそのまま（呼び出し先の戻す / 先頭へは既に実行時エラー）

## 読むファイル

- `instructions/history/32_back_rewind_target.md` §2（判定の順序）・§4
- `keyseq/application/sequence_history.py:180-310`（編集対象）
- `keyseq/application/sequence_steps.py:190-200`・`:270-295`（編集対象の付近）
- `keyseq/application/sequence_runner/sequence_runner.py:280-330`・`keyseq/application/sequence_runner/run_to_end.py:190-210`
- `keyseq/application/sequence_runner/input_acceptance.py:127-151`（2 回押しの仕組み・読むだけ）
- `keyseq/domain/sequence_control.py` の `control_target`（task_01 で追加済み）
- `tests/test_sequence_history.py:105-400`・`tests/test_sequence_steps.py:405-430`・`tests/test_sequence_runner.py` の「もう一度押すと実行します」を検索した付近（手本）

## 含まない

- 編集ダイアログ・OK 時の検査の配線・キー変更の書き換えの配線・表示の解決（task_03）
- domain の変更（task_01 で完了）
- 案 B（空の履歴で破棄したときに選択を移す・後送り）
- 正本 `spec_detail/`・`codebase_map.md` の更新（task_04）

## 確認

- 追加 / 修正した単体テストが pass: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_history tests.test_sequence_steps tests.test_sequence_runner tests.test_sequence_runner_call`
- 既存テスト全 pass: `-m compileall -q keyseq tests` / `-m unittest discover -s tests` / `-m unittest discover -s tests_ui` / `-m tests.smoke_app`（verifier が実行）
- `target` の無い戻す / 先頭への既存テストが無修正で通る

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施。
