# 提案書 16: phase 38（file_line の非同期読込）後の sequence_runner の整理

> 起票: 2026-09-27（phase 38 の `/refactor_check` = 推奨）。**挙動不変**。ユーザー承認前に実施しない。
> PHASE_BASE = `2086904`（phase 37 の最終コミット）。対象は phase 38 で変更した `keyseq/application/sequence_runner.py` のみ。

## 判定の根拠（メトリクス）

| 記号 | 測定値 | 該当 |
|---|---|---|
| M1 | `sequence_runner.py` 359 → 605 行（+246） | 該当 |
| M2 | `_perform_run_to_end_step` 94 行（phase 38 で file_line の分岐を追加） | 該当 |
| M3 | 「`run_to_end_after_id = self._after(delay, lambda: self._run_to_end_step(generation=…, key=key))`」の予約ブロックが `:414`（schedule_only）・`:506`・`:602` の 3 箇所 | 該当 |
| M4 | `StepResume(initial, wrapped, processed, counter_deltas)` の全フィールド組み立てが 1 → 3 箇所（`:145`・`:471`・`sequence_steps.py:221`） | 該当 |
| M5 / M6 | なし | — |

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_sequence_runner.py`・`tests/test_sequence_runner_file_line.py`（29 件）・`tests/test_sequence_steps.py`・`tests_ui` の連続実行系。
- 完了条件: 実施前に `unittest discover -s tests`（882 OK・skipped 7）/ `-s tests_ui`（615 OK）/ `tests.smoke_app` を記録し、実施後に件数不変・全 pass。
  テストは**変更しない**（private メソッドの参照〔`runner._run_to_end_resume` 等〕が壊れる移動はしない）。

## 項目 1: 連続実行の次ステップ予約を 1 メソッドへ（M3）

- 対象: `sequence_runner.py:414`・`:506`・`:602`
- 変更: `_schedule_run_to_end_step(self, key: str, delay: int) -> None`（`generation = self._run_to_end_generation` を取り、`run_to_end_after_id` に予約）を追加し 3 箇所を置き換える。
  ```python
  # 前（3 箇所）
  generation = self._run_to_end_generation
  self.state.run_to_end_after_id = self._after(delay, lambda: self._run_to_end_step(generation=generation, key=key))
  # 後
  self._schedule_run_to_end_step(key, delay)
  ```
- 完了条件: 項目 0 のコマンドが件数不変で全 pass。`grep -c "_run_to_end_step(generation=" keyseq/application/sequence_runner.py` が 1（新メソッド内のみ）。
- リスクと戻し方: 予約の世代を取るタイミングがずれると古い予約が進む → 取るのは予約直前（現行と同じ）。1 コミットで戻せる。

## 項目 2: `_perform_run_to_end_step` の file_line 分岐を切り出す（M2・M4）

- 対象: `sequence_runner.py:421-514`（file_line の分岐 `:455-490` 付近）・`:139-150`
- 変更:
  - 連続実行の file_line 開始（begin → 札・トークン・resume / snapshot / wait_position の設定 → 確認タイマー）を `_begin_run_to_end_file_line(key, action, index, outcome, snapshot, advance_position)` へ移す。
  - `StepResume` を outcome から組み立てる 2 箇所（`:145`・`:471`）を、`sequence_steps.py` の純関数 `resume_for_pending(outcome, initial_position) -> StepResume` に寄せる
    （`sequence_steps.py:221` の既存の組み立ては advance 内部のため対象外）。
  - `_perform_run_to_end_step` は 60 行以下を目安にする。
- 完了条件: 項目 0 のコマンドが件数不変で全 pass。`_perform_run_to_end_step` が 80 行以下。`grep -c "StepResume(" keyseq/application/sequence_runner.py` が 0。
- リスクと戻し方: 開始位置（`previous_resume.initial_position` / advance に渡した位置）の取り違え → 引数でそのまま渡し、計算を移さない。1 コミットで戻せる。
- 依存: 項目 1 の後（予約を新メソッドで呼ぶため）。

## 項目 3: file_line の読込中の処理をファイル分割（M1）

- 対象: `sequence_runner.py` の file_line 関連メソッド（`_queue_single_file_line` / `_poll_single_file_line` / `_discard_run_to_end_file_line` / 項目 2 の `_begin_run_to_end_file_line` / `_poll_run_to_end_file_line`・計約 150 行）
- 変更: 親フォルダ方式（`.claude/rules/file_organization_rules.md`）で `keyseq/application/sequence_runner/` パッケージにし、
  `sequence_runner.py`（本体）+ `file_line_wait.py`（上記メソッドを持つ mixin `FileLineWaitMixin`・runner 専用＝Private）へ分ける。
  `sequence_runner/__init__.py` で `SequenceRunner` と `FILE_LINE_POLL_INTERVAL_MS` を再輸出する（公開面の定義・互換レイヤーではない）。
- 完了条件: 項目 0 のコマンドが件数不変で全 pass。`sequence_runner/sequence_runner.py` が 500 行未満。
  `from keyseq.application.sequence_runner import SequenceRunner, FILE_LINE_POLL_INTERVAL_MS` が従来どおり動く（テスト・`app.py` の import を変えない）。`codebase_map.md` の該当行を更新。
- リスクと戻し方: mixin と本体の属性の暗黙の依存が読みにくくなる → mixin の冒頭に使う属性・メソッドを列挙するコメントを置く。
  効果（行数）に対し構造変更が大きいので、**項目 1・2 だけで 550 行を切るなら項目 3 は見送ってよい**。
- 依存: 項目 1・2 の後。

## 実施タイミング（ユーザー選択）

(a) phase 38 末の追加タスク（`task_08_refactor`）/ (b) 次フェーズ前の独立ミニ計画。
