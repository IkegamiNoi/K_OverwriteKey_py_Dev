# 提案書 17: phase 40（呼び出し）後のリファクタ

> 起票: 2026-10-01 `/refactor_check`（phase 40）。PHASE_BASE = `89896e6`。**挙動不変**（メッセージ・保存内容は変えない）。ユーザー承認前に実施しない。
> 計測: verifier（M1〜M6）。判定の根拠は各項目に記載。

## 判定の要約

| 記号 | 結果 |
|---|---|
| M1 | **該当**: `application/sequence_runner/sequence_runner.py` 618 行（483 → +135） |
| M2 | 非該当（80 行超は `sequence_steps.advance` 103 行・`action_dialog.__init__` 138 行だが、いずれも phase 40 前から 80 行超〔`advance` は 87 行〕＝既存） |
| M3 | **該当**: 「file_line の読込の仕組みが未設定」の判定と通知が 4 箇所（`sequence_runner.py:261` / `file_line_wait.py:87` / `call_wait.py:178` / `call_run_to_end.py:165`） |
| M4 | **該当**: `StepResume(` の全項目の再構築 2 → 5 箇所（`sequence_runner.py:131,194,551` / `sequence_steps.py:85,262`） |
| M5 | 非該当（0 件） |
| M6 | **該当**: 上限 10000 が `sequence_steps.py:224,227,318` で直値、`call_context.py:19-21` で別定数（同値・同文言） |

別タスク化候補（本書に含めない・`current.md` へ追記）: 単発 / 連続実行 × 通常 / 呼び出しの file_line の開始・poll の 4 組の並行構造（`file_line_wait.py` / `call_wait.py` / `call_run_to_end.py`）。
照合（世代 / トークン / 失敗時の 1 つ前の許容）が経路ごとに違い、統合のリスクが効果を上回るため。

---

## 項目 0: 安全網の確認

- 対象: `sequence_steps.py` / `call_context.py` / `sequence_runner/` パッケージ。
- 既存テスト: `tests/test_sequence_steps.py` / `test_call_context.py`（上限 10,000 の境界・送信前後の通算〔task_10a〕）/ `test_sequence_runner.py` / `test_sequence_runner_call.py` /
  `test_sequence_runner_file_line.py` / `test_sequence_runner_stop.py`（待機・一時停止・停止の行）。
- 確認すること: 「file_line の読込の仕組みが未設定」の通知を 4 経路すべてで確かめるテストがあるか（`begin_file_line=None` で runner を作る）。無ければ**先に特性テストを追加**（項目 3 の安全網）。
- 完了条件: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準 tests 1009 OK・tests_ui 634 OK）。

## 項目 1: 上限 10,000 の定数の一本化と StepResume の継続生成（M6・M4）

- 対象: `application/sequence_steps.py:224,227,318`・`application/call_context.py:19-21`・`application/sequence_runner/sequence_runner.py:131,551`
- 問題: 同じ上限と文言が 2 モジュールに別々にある（M6）。`StepResume` の「前の resume に先行処理の結果を足した続き」を全項目の位置引数で 2 箇所再構築している（M4。項目追加のたびに直す）。
- 変更:

```python
# sequence_steps.py（定義側）
MAX_PROCESSED_SYSTEM_ACTIONS = 10000
PROCESSED_LIMIT_MESSAGE = "制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）"
# 直値 10000 と文言をこの 2 つへ置換。call_context.py は import して自前の定義を削除

def continue_resume(resume: StepResume, settled: SettleOutcome) -> StepResume:
    """先行処理（待機をまたぐ）の結果を足した続きの StepResume。"""
    return StepResume(resume.initial_position, settled.wrapped, settled.processed,
                      resume.counter_deltas + settled.counter_deltas, settled.deferred_counters)
# sequence_runner.py:131 / :551 をこの関数の呼び出しへ（:551 は outcome.counter_deltas を使うため、引数の形が合うかを確認し合わなければ :131 のみ）
```

- 完了条件: 項目 0 のコマンドが全 pass。`grep -n "10000" keyseq/application/` が定数定義と文言の 1 箇所だけ。
- リスクと戻し方: 文言の 1 字違いで通知が変わる → 定数は既存の文字列をそのまま移す。戻しはこのコミットの revert。
- 依存: 項目 0。

## 項目 2: `sequence_runner.py` から待機の処理を mixin へ切り出す（M1）

- 対象: `sequence_runner.py:127-204`（`_queue_single_wait` / `_resume_single_wait` / `_finish_single_normal_action` の待機部分）と `:547-618`（`_queue_run_to_end_wait` / `_continue_run_to_end_wait` / `_settle_after_stopped_sequence`）
- 問題: 618 行・phase 40 で +135（M1）。v0.8 の「送った後の待ち」の処理が本体に混在し、修正依頼で「sequence_runner の待機の部分」と修飾が要る。
- 変更: 新規 `application/sequence_runner/send_wait.py` に `SendWaitMixin`（送った後の待機の予約・明け・止めた後 / 停止の後の先行処理）を作り、上記メソッドを移す（本体は呼ぶだけ）。
  `wait_stop.py`（止めたときの「終えた扱い」）とは責務を分ける。配置は既存の mixin（`file_line_wait.py` 等）と同じパッケージ直下（Private）。`__init__` の再輸出は変えない。
  目標: `sequence_runner.py` 500 行前後。

```python
class SequenceRunner(InputAcceptanceMixin, WaitStopMixin, SendWaitMixin, FileLineWaitMixin, ...):
```

- 完了条件: 項目 0 のコマンドが全 pass。移したメソッドの中身は無変更（`git diff --stat` で移動のみ・`git diff -M` で確認）。
- リスクと戻し方: mixin の MRO で同名メソッドの解決順が変わる → 同名が無いことを `grep` で確認してから移す。戻しは revert。
- 依存: 項目 0（項目 1 と独立。同時に `sequence_runner.py` を触るため項目 1 の後に行う）。

## 項目 3: 「file_line の読込の仕組みが未設定」の判定を 1 つに（M3）

- 対象: `sequence_runner.py:261-262` / `file_line_wait.py:87-88` / `call_wait.py:178-181` / `call_run_to_end.py:165-168`
- 問題: 同じ条件 `self._begin_file_line is None or self._poll_file_line is None` と同じ文言が 4 箇所にコピーされている（M3）。
- 変更: `file_line_wait.py` に定数と判定を置き、4 箇所はそれを使う（通知の仕方・その後の処理は各経路のまま）。

```python
FILE_LINE_UNAVAILABLE_MESSAGE = "file_line の読込の仕組みが未設定です"

class FileLineWaitMixin:
    def _file_line_unavailable(self) -> bool:
        return self._begin_file_line is None or self._poll_file_line is None
```

- 完了条件: 項目 0 のコマンドが全 pass（項目 0 で追加した 4 経路の特性テストを含む）。`grep -rn "未設定です" keyseq/application/sequence_runner/` が定数定義の 1 箇所だけ。
- リスクと戻し方: 呼び出しの連鎖の付加（`call_wait` は `+ _call_chain_suffix(step)`）を落とすと文言が変わる → 連鎖の付加は各経路に残す。戻しは revert。
- 依存: 項目 0。
