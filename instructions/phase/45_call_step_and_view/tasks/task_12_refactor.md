# task_12_refactor

## 目的

phase 45 の `/refactor_check` が「推奨」と判定した提案書 19（`instructions/modified_proposal/19_refactor_call_step_and_view.md`）の項目 1・2 を実施する（2026-10-06 ユーザー判断・phase 45 末の追加タスク）。
**application 限定・挙動不変**（正本・JSON・presentation・エラーメッセージを変えない）。

## 対象範囲（application 限定・挙動不変）

### 項目 1: 連続実行の進行を mixin へ（M1）

- `keyseq/application/sequence_runner/sequence_runner.py` の `_start_run_to_end` / `pause_run_to_end` / `resume_run_to_end` / `stop_run_to_end` / `on_runtime_reset` / `_run_to_end_step` /
  `_schedule_run_to_end_step` / `_perform_run_to_end_step` / `_finish_run_to_end_normal_action` を、新設の `keyseq/application/sequence_runner/run_to_end.py`（`RunToEndMixin`）へ移し、`SequenceRunner` の基底に足す
- 呼び出しの連続実行（`call_run_to_end.py` の `CallRunToEndMixin`）とは分けたまま。公開メソッド名・シグネチャは変えない。MRO で同名メソッドの上書き関係が変わらないこと
- 完了の目安: `sequence_runner.py` が 400 行程度・`run_to_end.py` が 300 行未満

### 項目 2: `apply_control` の分割（M2）

- `keyseq/application/sequence_history.py` の `apply_control` を、提案書の `_back_origin` / `_control_group` / `_restore_press_group` の 3 関数へ切り出し、本体は対象の検査と呼び分けだけにする（40 行以下）
- `state.lock` の取り方の範囲を変えない（`prepare_targets` はロックの外・2 回目の読み直しはロックの中）

### テスト

- テストは原則変えない。patch 先がモジュール名を直接指していて移動で壊れるものだけ追随する（変えたら一覧と理由を報告）

## 読むファイル

- `instructions/modified_proposal/19_refactor_call_step_and_view.md`（全体）
- `keyseq/application/sequence_runner/sequence_runner.py`（全体）・`keyseq/application/sequence_runner/send_wait.py:1-40`（mixin の書き方の手本）
- `keyseq/application/sequence_history.py:180-300`
- `keyseq/application/sequence_runner/__init__.py`

## 含まない

- 提案書の範囲外のリファクタ（`call_run_to_end.py`・`call_context.py` の行数・`trigger.get("actions", [])` の慣用など）
- 正本の変更（挙動不変のため不要）。`codebase_map.md` の追記はメインが行う

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（件数が直前〔tests 1292 / tests_ui 824〕と同じ）
- `wc -l` で目安の行数・`apply_control` が 40 行以下

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視: なし（挙動不変）
