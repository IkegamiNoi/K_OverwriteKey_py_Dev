# task_08_refactor_sequence_runner

## 目的

提案書 [16](../../../modified_proposal/16_refactor_file_line_async_read.md) の項目 1〜3 を実施する（phase 38 の `/refactor_check` = 推奨・ユーザー承認 2026-09-27）。
**挙動不変**・application 限定（`sequence_runner.py` と `sequence_steps.py` への純関数 1 つ）・テストは変更しない。

## 対象範囲

- **項目 1**: `sequence_runner.py` の連続実行の次ステップ予約 3 箇所（`generation = self._run_to_end_generation` → `self.state.run_to_end_after_id = self._after(delay, lambda: self._run_to_end_step(generation=generation, key=key))`）を
  `_schedule_run_to_end_step(self, key: str, delay: int) -> None` へ集約する（`_run_to_end_step(schedule_only=True)` 内の予約も含む）。世代は予約直前に取る（現行と同じ）。
- **項目 2**: `_perform_run_to_end_step`（94 行）の file_line 分岐（begin → 札・トークン・resume / snapshot / wait_position の設定 → 確認タイマー）を
  `_begin_run_to_end_file_line(...)` へ切り出す。`StepResume(initial_position, outcome.wrapped, outcome.processed, outcome.counter_deltas)` の 2 箇所（単発 `_queue_single_file_line` と連続）を
  `keyseq/application/sequence_steps.py` の純関数 `resume_for_pending(outcome: StepOutcome, initial_position: int) -> StepResume` に寄せる。開始位置の計算は呼び出し元に残し、引数で渡す。
  `_perform_run_to_end_step` は 80 行以下（目安 60 行）。
- **項目 3（条件付き）**: 項目 1・2 の後に `sequence_runner.py` が **550 行以上**なら、親フォルダ方式で `keyseq/application/sequence_runner/` パッケージにして
  `sequence_runner.py`（本体）+ `file_line_wait.py`（file_line の読込中の処理のメソッドを持つ mixin `FileLineWaitMixin`）へ分け、
  `sequence_runner/__init__.py` で `SequenceRunner` と `FILE_LINE_POLL_INTERVAL_MS` を再輸出する。mixin の冒頭に、使う runner の属性・メソッドを列挙するコメントを置く。
  **550 行未満なら項目 3 は行わない**（完了報告で行数を示す）。
- テストは変更しない（`from keyseq.application.sequence_runner import SequenceRunner, FILE_LINE_POLL_INTERVAL_MS` と private 属性の参照がそのまま動くこと）。

## 読むファイル

- `instructions/modified_proposal/16_refactor_file_line_async_read.md`（全体）
- `keyseq/application/sequence_runner.py`（全体・編集対象）
- `keyseq/application/sequence_steps.py:15-80`（`StepResume` / `StepOutcome`）
- `.claude/rules/file_organization_rules.md`（項目 3 を行う場合のみ）

## 含まない

- 挙動・エラーメッセージの変更 / テストの変更 / 単発側の予約・照合の共通化（提案書に無い）/ `codebase_map.md` の更新（メインが行う）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `unittest discover -s tests`（882 OK・skipped 7）/ `-s tests_ui`（615 OK）/ `-m tests.smoke_app` が**件数不変**で全 pass
- `grep -c "_run_to_end_step(generation=" <runner 本体>` が 1 / `grep -c "StepResume(" <runner 本体と mixin>` が 0 / `_perform_run_to_end_step` が 80 行以下
- `git diff --stat` にテストファイルが無い

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 挙動不変〔予約の世代・開始位置・札の片付けの順序〕/ 提案書どおり / 項目 3 の判断が行数どおり / テスト無変更）。
- 実機目視: 不要（挙動不変・テストで担保）。
