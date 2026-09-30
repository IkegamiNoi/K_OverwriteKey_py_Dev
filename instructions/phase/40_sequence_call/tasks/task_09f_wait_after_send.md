# task_09f_wait_after_send

## 目的

暫定 29 v0.8 **§4.8** に合わせて待機の扱いを直す: **待機は直前に送った行の後の待ち**。送った後の通常の先行処理で待機に達したら同じステップ（単発は同じ押下）の中で待ち、
明けたら次の送る行で止まる / 送る前に達した待機は読み飛ばす / 連続実行は待機の前に間隔を置かない / 止めた後・停止の行の後の先行処理では待機を読み飛ばす。
呼び出しの文脈の中の待機は対象外（従来どおり）。application の修正とテスト。

## 現状（実測 2026-10-01）

- `sequence_steps.py` `advance`: 送る前に達した待機で `wait_ms` を返して待つ（`:246-263`）。`settle_after_normal`: 待機で止まる（`:328` の op 判定で break）。
- 単発: `_run_single_action` が `advance` の待機で `_queue_single_wait` → 明けたら `_resume_single_wait` が**次の通常アクションまで送る**（`sequence_runner.py:127-163`）。
- 連続実行: 待機に入るとき位置を**待機の次**へ保存している（`sequence_runner.py:432`）→ 待機中にフォーカスが次の行へ移る（実機で確認した不具合）。待機の前に通常の間隔が入る。
- 止めたときの位置合わせ `wait_stop.py` `_settle_stopped_wait`・`_finish_run_to_end_wait`・`sequence_runner.py` `_settle_after_stopped_sequence` は `settle_after_normal` を共用。

## 対象範囲（application）

1. **先行処理の 2 つの形**（`settle_after_normal` に引数を足す等。形は任せる）:
   - 送った後の通常の先行処理: 待機に達したら**その行で待つ**ことを呼び出し側へ返す（位置 = 待機の行・ms・続きの位置 = 待機の次・周回・控えたカウンター操作・processed）。ms が不正なら既存どおりその行で止まる（次のステップの開始時にエラー）。
   - 止めた後・停止の行の後の先行処理: 待機を**読み飛ばす**（続く待機も。10,000 に数える。ms 不正の行では止まる）。
     対象: `_settle_stopped_wait`・`_finish_run_to_end_wait`（待機中に止めた・一時停止・捨てる）・`_settle_after_stopped_sequence`（停止の行で終える）。
   - `in_call=True`（呼び出しの文脈の中）は従来どおり待機で止まる（文脈の次のステップの `advance` が待つ）。
2. **`advance` の送る前の待機は読み飛ばす**（呼び出しの文脈の外のみ。ms 不正ならその場でエラー・10,000 に数える・回り込み後に開始位置で終える規則はそのまま）。
   呼び出しの文脈の中（`in_call=True`）は従来どおり待つ。
3. **単発**: 送った後の先行処理（通常アクション `_finish_single_normal_action`・file_line の完了・呼び出しの成功後）で待機に達したら、押下を終えずに待機の保留（`PendingStep`）を作り、
   位置（「次に実行」）は待機の行。明けたら**送らずに**待機の次から通常の先行処理を続け（また待機なら再び待つ）、終わったらステップを確定（戻す履歴 1 段・`commit_step`）して押下を終える。
   待機中は既存どおり止まっている間（同じトリガーの押下は無視・他のトリガーは動く・戻す / 先頭への対象なら「待機中」で拒否・取り消し契機も既存）。
   §4.7「単発の待機が明けたときに処理中のものがある場合」の分岐（`_resume_single_wait` の `_active_key()` 判定）は不要になる（常に送らずに終える）。
4. **連続実行**: 送った後の先行処理で待機に達したら、**間隔を置かず**に待機に入る（位置 = 待機の行を保存 → 待機中の「次に実行」は待機の行）。
   明けたら待機の次から通常の先行処理（停止の行の扱い `stop_ends_run` は既存どおり）を続け、また待機なら待つ。終えたら**間隔を足さず**に次のステップ。
   待機に達しなかったステップの後は通常の間隔。一時停止・停止・捨てるは 1 の読み飛ばしで次の送る行へ（v0.7 の既存の経路）、再開はその位置から通常の間隔の後。
5. 待機をまたいでも戻す履歴はステップ全体で 1 段・カウンター操作の保留は控えたまま次のステップの開始時に反映（既存）・10,000 はステップ全体で通算（既存）。

## テスト

6. 少なくとも（単発・連続実行とも。実際のキー名を使う）:
   - `[A, 待機, B]`: 単発 1 回目 = A を送り待機中の位置は待機の行・明けたら位置 B で何も送らない / 2 回目 = B。待機中の同じキーの押下は無視
   - 位置が待機の行から始まる（一覧で位置を変えた・`[待機, A]` の先頭）: 待たずに A を送る。`[カウンター+1, 待機, A]` の先頭からも待たない。ms 不正の待機は送る前でもエラー
   - `[A, 待機1, 待機2, B]`: 単発で A の後に 2 つ待って位置 B / 待機1の最中に停止操作・他の連続実行の開始・一時停止で位置 B（待機2を待たない）・戻す履歴 1 段
   - 末尾の回り込み: `[待機, A]` を単発で 2 回目以降押すと A の後に先頭の待機を待つ
   - 連続実行: 待機の前に間隔を置かない（after の遅延が待機の ms）・待機中の位置は待機の行・明けた後は間隔なしで次のステップ・`[A, 停止, 待機, B]` は A の後に待たずに終えて位置 B
   - 呼び出しの文脈の中の待機は従来どおり（既存テストが通る）
   - 既存テストのうち「待機の明けで次を送る」「送る前の待機で待つ」「連続実行の待機中の位置が次の行」前提のものは v0.8 に合わせて期待を変える

## 読むファイル

- `instructions/history/29_sequence_call.md` **§4.8**・§4.7「待機中に止めたとき」・§8-4c / 正本 `instructions/common/spec_detail/features.md` §4.2.1・§4.2.2・§4.2.5・§4.2.8（v0.8 で改める前の規定）
- `keyseq/application/sequence_steps.py`（`advance`・`settle_after_normal`）/ `keyseq/application/sequence_runner/sequence_runner.py`（単発の待機・`_finish_single_normal_action`・連続実行のステップと待機・`_settle_after_stopped_sequence`）
- `keyseq/application/sequence_runner/wait_stop.py`・`file_line_wait.py`・`call_wait.py`・`call_run_to_end.py`（先行処理の呼び出し箇所）/ `keyseq/application/call_context.py`（`in_call` の settle）
- `tests/test_sequence_runner.py`・`tests/test_sequence_steps.py`・`tests/test_sequence_runner_stop.py`・`tests/test_sequence_runner_call.py`・`tests/test_sequence_runner_file_line.py`

## 含まない

- 呼び出しの文脈の中の待機の扱い / presentation の変更（位置の表示は既存の `_save_progress` → 再描画の経路）/ 正本（task_10）
