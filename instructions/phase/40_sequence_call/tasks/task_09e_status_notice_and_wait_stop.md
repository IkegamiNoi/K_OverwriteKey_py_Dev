# task_09e_status_notice_and_wait_stop

## 目的

暫定 29 v0.7 §4.7 に合わせて task_09c・09d の実装を直す: **警告のダイアログを廃止**してステータスバーの通知にする / 戻す・先頭へは 2 回押し /
**待機中に止めたら待機を終えた扱いで次の送る行へ進める**（単発・連続実行とも）。application・presentation の修正とテスト。

> 注意: 仕様書の `f5` は例示のキー。実装・テストは実際のキーを使う。

## 対象範囲

### application（`keyseq/application/sequence_runner/input_acceptance.py` ほか）

1. **確認の廃止**: `confirm_discard` の注入・`confirmation_active`・確認前後の状態の照合を削除する。代わりに「一時停止中のものを捨てて、捨てたキーを通知する」口
   （例: `discard_paused(keys=None) -> tuple[str, ...]`。捨てたら `notify_message` で「一時停止中の実行を破棄しました（<キーの一覧>）」）を用意する。
   - 他のトリガーの連続実行の開始: 一時停止中のものがあれば全部捨てて（通知して）開始する（確認しない）。
2. **戻す / 先頭への 2 回押し**（`_prepare_control_target` 付近）: 対象が一時停止中の連続実行・単発の呼び出しなら、
   - 1 回目: 何も変えず（既存の「保留中の対象の拒否」と同じ扱い）、「一時停止中の <キー> を破棄します。もう一度押すと実行します」と通知し、控え
     （戻す / 先頭へのトリガーのキー・対象のキー・一時停止中のものの集合〔キーと世代〕・処理中の有無・単発の保留の集合）を runner に持つ。
   - 続けて同じトリガーの押下で、控えと今の状態が同じなら対象だけを捨ててから実行する。
   - 他のトリガーの押下（`handle_key` にそのキー以外が来た）・状態の変化で控えを捨てる。時間の制限は設けない。
3. **待機中に止めたとき**（§4.7「待機中に止めたとき」）: 位置を待機の次へ進めて先行処理（`settle_after_normal`）し、「次に実行」を送る行に合わせる。戻す履歴は既存の規則（状態が変われば 1 段）。
   - 連続実行: **一時停止**（`pause_run_to_end`）・**停止**（`stop_run_to_end`。今は `_run_to_end_wait_position` = 待機の行へ戻している）・捨てる。
     一時停止ではそのステップを待機の次で確定し（1 段）、再開はその位置から通常の間隔の後に新しいステップとして続ける。
   - 単発: 待機の保留の取り消し（`cancel_pending_wait(s)` → `sequence_history.cancel_pending_steps`。他の連続実行の開始・停止操作・キーマップの切替の経路）。
     待機の保留（`file_line` も `call` も None の `PendingStep`）だけが対象。file_line・呼び出しの保留の取り消しは既存どおり。
   - 対象外: 位置変更・シーケンスの編集・構成セットの読込等（既存どおり）/ 呼び出しの文脈の中の待機（呼び出しは打ち切りで呼び出しの行）。
   - 先行処理にはトリガーの actions が要るため、`sequence_history.py`（actions を持たない）ではなく runner 側で行う形でよい。

### presentation

4. `keyseq/presentation/app.py`: `_confirm_paused_discard`（ダイアログ・最前面）と `confirm_discard` の配線を削除する。
5. `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`: 切替・アクティブの削除は、確認せずに 1 の口で捨てて（通知して）進める。
   削除は既存の確認（askyesno）だけで、「はい」の後に捨てて削除する。`confirmation_active` による切替キーの無視は削除する。連続実行の実行中の拒否は既存どおり。

### テスト

6. task_09c・09d で追加したダイアログ・確認・照合のテストを v0.7 に合わせて直す / 削除する。少なくとも:
   連続実行の開始・キーマップの切替で一時停止中のものが捨てられ通知が出る（ダイアログを呼ばない）/ 削除は既存の確認だけ /
   戻す・先頭へ: 1 回目は通知だけで何も変わらない・続けて 2 回目で対象だけ捨てて実行・間に他の押下があれば 1 回目に戻る・状態が変われば 1 回目に戻る /
   連続実行: 待機中の一時停止で位置が待機の次の送る行（先行処理後・例: `[text い, wait, counter_inc n, text あ]` なら「あ」の行）・再開で「あ」から /
   待機中の停止・捨てるでも同じ位置・1 段 / 単発: 待機中に停止操作・他の連続実行の開始で位置が待機の次の送る行・1 段 /
   既存テスト `test_cancelled_wait_callbacks_are_stale_and_keep_wait_position`（tests/test_sequence_runner.py）等「待機の行に残る」前提のものは v0.7 に合わせて期待を変える。

## 読むファイル

- `instructions/history/29_sequence_call.md` **§4.7**・§4.6・§8-4b
- `keyseq/application/sequence_runner/input_acceptance.py`（全体）/ `sequence_runner.py`（`cancel_pending_wait(s)`・`_queue_single_wait`・`_resume_single_wait`・`pause/resume/stop_run_to_end`・`_run_to_end_step` と待機の途中状態）
- `keyseq/application/sequence_history.py`（`cancel_pending_steps`・`apply_control`）/ `keyseq/application/sequence_steps.py`（`settle_after_normal`）
- `keyseq/presentation/app.py`（`_confirm_paused_discard`・runner の生成）/ `keymap_panel_controller.py`（切替・削除）
- `tests/test_sequence_runner.py`・`tests/test_sequence_runner_call.py`・`tests/test_sequence_runner_file_line.py`・`tests/test_app_state_keymap_switch.py`・`tests_ui/test_task06_keymap_management_ui.py`・`tests_ui/test_sequence_control_review_fixes.py`

## 含まない

- 処理中は他を無視・単発の呼び出しの一時停止・待機明けの扱い（task_09c のまま変えない）/ 正本（task_10）
