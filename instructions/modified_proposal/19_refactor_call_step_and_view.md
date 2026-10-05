# 提案書 19: phase 45（呼び出しのステップ実行と呼び出し先の表示）後のリファクタ

> 状態: **実施済**（2026-10-06・phase 45 task_12_refactor。`sequence_runner.py` 649 → 377 行・`run_to_end.py` 299 行・`apply_control` 104 → 39 行）。

## 判定の要約

範囲 `git diff 988c618..HEAD -- keyseq/`（26 ファイル・+1704 / -256）。メトリクスは verifier の実測（関数長は awk の概算）。

- **M1 該当**: `application/sequence_runner/sequence_runner.py` 649 行（+146）
- **M2 該当**: `application/sequence_history.py:193` `apply_control` 104 行（phase 44 時点 53 行・今回 +51 行の変更で 80 行超）
- M3: 非該当（`trigger.get("actions", []) if trigger else []` が 8 か所だが慣用の 1 行で、片方を直してももう片方を直す必要が無い）
- M4（コンストラクタ数の増減なし）・M5（0 件）・M6（数値の重複なし）: 非該当
- 参考（非該当）: `call_run_to_end.py` 497 行・`call_context.py` 462 行・`app.py` 640 行（+11）・`trigger_panel_controller.py` 633 行（+35）

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_sequence_runner.py`・`test_sequence_runner_call.py`・`test_sequence_runner_stop.py`・`test_sequence_runner_file_line.py`・`test_sequence_history.py`・`test_call_link_lifecycle.py`・`test_call_chain_run_to_end_integration.py`
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: 連続実行の進行を `sequence_runner.py` から mixin へ切り出す（M1）

- 対象: `sequence_runner.py:365-649`（`_start_run_to_end` / `pause_run_to_end` / `resume_run_to_end` / `stop_run_to_end` / `on_runtime_reset` / `_run_to_end_step` / `_schedule_run_to_end_step` / `_perform_run_to_end_step` / `_finish_run_to_end_normal_action`・約 285 行）
- 変更: 同フォルダに `run_to_end.py`（`RunToEndMixin`）を新設して移し、`SequenceRunner` の基底へ足す（既存の `call_wait.py` / `send_wait.py` 等と同じ mixin の形）。
  呼び出しの連続実行（`call_run_to_end.py` の `CallRunToEndMixin`）とは分けたまま。公開メソッド名は変えない（`App`・テストの呼び出し先を変えない）
  ```python
  # sequence_runner.py
  class SequenceRunner(CallViewMixin, InputAcceptanceMixin, WaitStopMixin, SendWaitMixin, FileLineWaitMixin,
                       RunToEndMixin, ...):
  ```
- 完了条件: `sequence_runner.py` が 400 行程度・`run_to_end.py` が 300 行未満・項目 0 が全 pass
- リスクと戻し方: mixin の解決順（MRO）で同名メソッドの上書き関係が変わらないこと（`grep -n "def _run_to_end_step\|def stop_run_to_end" keyseq/application/sequence_runner/*.py` で重複が無いことを確認）。
  テストの patch 先が `sequence_runner.sequence_runner.<名前>` を直接指していれば追随が要る。戻しは移動の取り消しのみ
- 依存: なし

## 項目 2: `apply_control` の分割（M2）

- 対象: `sequence_history.py:193-296`
- 変更: 次の 3 つの関数へ切り出し、`apply_control` は対象の検査と呼び分けだけにする（30〜40 行目安）
  - `_back_origin(state, target_id, target_key, find_trigger) -> str`（印のある対象は最上段・その履歴が空なら対象自身。`:219-227`）
  - `_control_group(state, target_id, op, restore_key, target_key) -> tuple[tuple[str, str], ...] | None`（同じ押下の番号の段が一番上のトリガーと、待機中・処理中の検査。`:228-251`。待機中なら None）
  - `_restore_press_group(state, target_id, histories, restore_key) -> bool`（同じ番号の段をまとめて戻す。`:258-284`）
- 完了条件: `apply_control` が 40 行以下・`tests/test_sequence_history.py` と項目 0 が全 pass
- リスクと戻し方: ロック（`state.lock`）の取り方の範囲を変えない（`prepare_targets` はロックの外で呼ぶ・2 回目の読み直しはロックの中）。戻しは関数の展開のみ
- 依存: なし
