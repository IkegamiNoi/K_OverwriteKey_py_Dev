# task_05a_settle_after_stop

## 目的

停止で連続実行を終えた後も先行処理をする（暫定 28 v0.6 §4.1-1・ユーザー判断 2026-09-28）。「次に実行」が次に実際に実行される行を指し、ループの最終周の後の空振りを無くす。
**application（`sequence_runner/sequence_runner.py`）とテストのみ**。

## 対象範囲

### `keyseq/application/sequence_runner/sequence_runner.py`

- 停止で終える 2 経路（`advance` の `outcome.stopped` / `_finish_run_to_end_normal_action` の `settled.stopped`）の両方で、終える前に**停止の次の位置から先行処理**を行う:
  - 位置が 0（停止が最後の行・末尾に達した）でなければ `settle_after_normal(actions, 位置, 周回, counters, allow_wrap=False, processed=<停止までの処理数>, stop_ends_run=False)`（停止の行は通過）。
  - 先行処理の結果の位置・周回を保存する。控えた保留（`deferred_counters`）は、**先行処理で末尾に達して位置 0 になった場合はその場で反映**（差分を deltas に足す）、それ以外は保留として保存する（次の押下で反映）。
  - 停止の手前の保留をその場で反映する既存の処理（task_02）は変えない（停止の手前の反映 → 停止の後の先行処理の順）。
  - 共通の非公開メソッドにまとめ、2 経路で重複させない。`commit_step` はそのステップで 1 回のまま（先行処理の差分も同じステップに含める）。
- 単発実行・停止を含まないシーケンスは変えない。

### テスト（`tests/test_sequence_runner_stop.py`）

1. `[A, stop, counter_inc, B]` の連続実行: A の後に終了・位置 3（B）・カウンターは未反映で保留に控える → 次の押下で +1 を反映して B
2. 3 周ループ `[loop_start×3, A, stop, loop_end]`: 3 周目の A の後に終了・位置 0（ループを抜けて末尾）→ 次の押下で先頭から 1 周目の A（空振りなし）。1・2 周目の後は位置が A（ループの始まりの次）
3. `[A, counter_inc, stop, counter_inc]`: A の後に終了・停止の手前の +1 はその場で反映・停止の後の +1 は末尾に達するのでその場で反映（計 +2）・位置 0・戻すで +2 とも戻る
4. `[A, stop, stop, B]` の停止で終えた後: 先行処理で 2 つ目の停止を通過して位置 3（B）
5. 待機の続きで停止に達した場合（`advance` の経路）も同じく先行処理される
6. 既存の test_01〜12 のうち期待値が変わるもの（停止の後にループ / カウンター / 停止の行が続くもの）だけを新しい仕様に合わせて直し、直した理由をテスト内のコメントに 1 行書く

## 読むファイル

- `instructions/history/28_sequence_stop_and_call.md` §4.1（v0.6）
- `keyseq/application/sequence_runner/sequence_runner.py:365-455`
- `keyseq/application/sequence_steps.py` の `settle_after_normal` / `apply_deferred_counters` のシグネチャ
- `tests/test_sequence_runner_stop.py`（全体・編集対象）

## 含まない

- 単発実行 / sequence_steps.py の変更 / 正本（メインが task_05 後半で行う）

## 確認

- `unittest tests.test_sequence_runner_stop tests.test_sequence_runner tests.test_sequence_runner_file_line` / `discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 2 経路の共通化・反映の順序・末尾で位置 0 のときの反映・戻す履歴 1 段・停止を含まない挙動の不変・既存テストの期待値変更の妥当性）。
- 実機目視: 不要（テストで担保。ループ最終周の空振り解消は完了報告で伝える）。
