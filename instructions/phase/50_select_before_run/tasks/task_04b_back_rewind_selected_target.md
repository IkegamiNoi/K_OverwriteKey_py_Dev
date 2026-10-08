# task_04b_back_rewind_selected_target

## 目的

実機目視の指摘（2026-10-08）で暫定 34 を v0.6 に改訂した（ユーザー確定 2026-10-09）。そのうち application の 2 点を実装する（暫定 34 §2-14・§3a・§10 の 9a〜9c）。

1. **対象指定（`target`）の無い戻す・先頭への対象 = 押した時点で一覧に選ばれているトリガー**（確認して実行の ON / OFF によらない）。使えないとき（有効な行が選ばれていない / 押したトリガー自身 / 戻す・先頭へだけのトリガー / 選択の注入口が無い）は従来どおり直前のトリガー
2. **戻す・先頭へだけのトリガーを押しても、そのトリガー自身は一覧で選ばない**（`target` の有無によらない）。実際に戻した / 先頭へ移したときだけ対象を選ぶ（既存）。確認の 1 回目・待機中の拒否・処理中の無視・戻す段が無い・対象が無いときは押す前の選択のまま

## 対象範囲

- `keyseq/application/sequence_runner/sequence_runner.py`: `_control`（:289-）で `target_key` が None のとき、選択の注入口（`_get_selected_trigger_key`・task_02 で注入済み）から押した時点の選択を取り、使える場合は対象にする。
  単発の実行の `finally`（:384 付近）で押したキーを選ぶ処理を、**押したトリガーが戻す・先頭へだけのトリガーなら行わない**（対象を選ぶ :385-386 は残す）。
  連続実行のトリガーで戻す・先頭へだけのもの（単発の扱い・`input_acceptance.py` の :189-192 付近）が同じ経路を通るか確認し、通らないなら同じ規則にする
- `keyseq/application/sequence_history.py` の `apply_control`: 対象の決め方を変える場合は、選択の候補を引数で受ける（例: `selected_key: str | None = None`・省略時は従来どおり直前のトリガー）。直前のトリガーの記録の規則は変えない
- 「戻す・先頭へだけ」の判定は既存の `_is_standalone_control`（`input_acceptance.py:217-226`）を使う（同じ判定を複製しない）
- テスト追加・修正（`tests/`）: §10 の 9a・9b・9c。手本は `tests/test_sequence_runner_select_before_run.py`（選択の注入）と既存の戻す・先頭へのテスト（`grep -l "rewind\|OP_BACK" tests/`）。
  特に 9c: 選択を更新するコールバック付き（select で注入口の戻り値が変わる）で、一時停止中の X を選び直前のトリガーが Y のとき戻すを 2 回押す → 1 回目は select が呼ばれず（または X のまま）、2 回目で X が戻り Y は変わらない
- 既存テストで「戻す・先頭へのトリガー自身が選ばれる」ことを前提にしているものは、§3a に照らして期待値を直す（**直した件数と理由を報告**）

## 対象外

- presentation（task_04c）・JSON・正本の改訂（task_05）
- 直前のトリガー（`last_trigger`）の廃止・記録の変更
- 選択の注入口が無い（注入なし）ときの 1. の変更（直前のトリガーのまま）。**2. は注入の有無によらず常に適用する**

## 読むファイル

- `instructions/history/34_select_before_run.md` の §2-14・§3a・§7・§10
- `instructions/common/spec_detail/features.md` §4.2.6（対象・判定の順序・選択）
- `keyseq/application/sequence_runner/sequence_runner.py:280-300, 300-390`・`input_acceptance.py:100-230`・`sequence_history.py:190-240`

## 確認

- tests 全体 pass（verifier が `.venv` で実行）
- 機能の注入なしの既存テストで、対象の決め方（直前のトリガー）が変わらない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: task_04c の後にまとめて実施
