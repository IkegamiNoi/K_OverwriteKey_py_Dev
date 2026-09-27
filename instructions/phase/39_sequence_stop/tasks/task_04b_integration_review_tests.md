# task_04b_integration_review_tests

## 目的

task_04 の統合レビュー（deep-reviewer）で採用したテスト不足を補う（M1・M2）と、mixin のコメント漏れ（L2）を直す。**挙動変更なし**（テスト + コメント 1 行）。

## 対象範囲

- `tests/test_sequence_runner_stop.py` に追加:
  - **M1**: 同じ runner で `[A, 停止, 停止, B]` の連続実行 → 1 回目の押下で A を送って終了（位置 2）→ 2 回目の押下は位置 2 の停止を**読み飛ばして** B を送る（開始で印が消えること。`_start_run_to_end` の印のリセットを消すと落ちる）。
  - **M2**: `[待機, 停止, A]` の連続実行で、待機中に一時停止 → 再開 → 停止を読み飛ばして A を送る（印が立っていないまま一時停止をまたいでも立たない）。
  - 可能なら private 属性ではなく送信結果と位置で確かめる。
- `keyseq/application/sequence_runner/file_line_wait.py` の mixin 冒頭の「使う runner の属性」コメントに `_run_to_end_sent` を追加する（L2）。

## 読むファイル

- `tests/test_sequence_runner_stop.py`（全体）
- `keyseq/application/sequence_runner/file_line_wait.py:1-25`

## 含まない

- 実装の変更 / L3〜L5（保留）/ 正本（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_runner_stop -v` が全 pass・`unittest discover -s tests` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: テストが指摘の場面を実際に再現しているか・実装を変えていないか）。
