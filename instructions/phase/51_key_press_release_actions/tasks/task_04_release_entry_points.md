# task_04_release_entry_points

## 目的

押したままのキーを、暫定 35 §5 の契機（application の入口）で自動で離し、runner から持ち主（押したトリガー = 最上段のキー）を送信へ渡す（§4.3・§5・§8）。
**application 限定**（`sequence_runner/`・`app_state.py`・`action_executor.py` の小さな追加）。presentation の配線（`app.py` で HeldInputs を runner へ渡す・reset_listeners への登録・フック停止 / キーマップ一時停止 / アプリ終了での解放）は task_05。JSON 不変。

## 対象範囲（application 限定）

### 持ち主の受け渡し（§4.3・§8）
- `HeldInputs` に「今の持ち主」を持たせる（例: `owner_scope(owner)` のコンテキスト / `current_owner` 属性）。runner は**送信の直前に**最上段のキーをそこへ置き、送信の後で戻す（単発 `_run_single_action`・連続実行・呼び出し〔ステップ / 一括・連続実行の呼び出し〕・file_line の送信〔`_poll_file_line`〕のすべて）
  - 最上段 = 押したトリガー（連続実行なら連続実行のキー・呼び出しなら呼び出しを始めたキー）。呼び出し先の行で押したものも最上段が持ち主（§4.3）
- `ActionExecutor.execute` / `poll_file_line` は owner 引数が None なら `HeldInputs` の今の持ち主を使う（runner の `perform_action` の呼び出し形〔action 1 つ〕は変えない＝既存テストの偽の perform_action を壊さない）
- `ActionExecutor.execute` の**未知の種類**の経路も、知らせる前に持ち主の分を離す（`_report_held_error` を通す・§4.5「実行を終えるエラー」）

### runner への注入
- `SequenceRunner(..., held_inputs: HeldInputs | None = None)`（省略可・省略時は離す処理をしない＝既存テストの組み立てを壊さない）。runner 内の解放は `held_inputs.release_owner(key)`。戻り値の例外の一覧は、知らせる口（`_notify_error` 等の既存の口）でまとめて 1 回知らせる（空なら何もしない）

### 離す入口（§5 の表。実体の関数を特定し、そこで離す）
| 契機 | 置き場（目安・実体はコードで特定） | 範囲 |
|---|---|---|
| 連続実行が終わる（停止操作・末尾・エラー・トリガーの消失・他の連続実行の開始による破棄） | `run_to_end.py` の `stop_run_to_end`（呼ばれる直前の連続実行のキーを控えて離す） | そのキー |
| **停止の行の区切り（4.2.8）では離さない**（§2-10） | 区切りで連続実行を終える経路が `stop_run_to_end` を通るなら、区切りの経路だけ離さない印を付ける | — |
| 連続実行の一時停止 | `pause_run_to_end` | そのキー |
| 単発の呼び出しの一時停止 | `input_acceptance.py` の `_pause_single_call` | そのキー |
| 一時停止中のものを捨てる | `discard_paused` | 捨てた各キー |
| 単発の待機の取り消し | `_cancel_pending_steps`（`sequence_runner.py:195` と `wait_stop.py:36` の**どちらが実体か特定**）・`cancel_pending_wait(key)` | 取り消した各キー |
| 先頭へ（rewind）。**戻す（back）では離さない** | runner の `_control`（op が rewind で対象 T が決まり実際に先頭へ移したとき） | T |
| シーケンスの編集・一覧で位置を変えた | `reset_loop_frames(key)` | そのキー |
| トリガーの削除・キー変更・有効な行の交代 | presentation から呼ばれる `cancel_pending_wait(key)`（`effective_row_transition.clear_trigger_state`・`trigger_row_edit.py:120`）で離す（待機が無くても離す） | そのキー（キー変更は旧キー） |
| 最上段の末尾に達した | 単発: `advance` の結果が末尾に達した（`reached_end` / 同じ押下の中で先頭へ回った `wrapped`）とき、**先頭の行を送る前**に離す。連続実行の末尾は `stop_run_to_end` で離れる | そのキー |
| 連動で末尾に達した呼び出し元 | `linked_call.py` の `_propagate_linked_completion` で末尾まで進んだ各呼び出し元 | その各キー |
| **呼び出し先の末尾（呼び出しの完了）では離さない**（§2-6） | — | — |
| 実行を終える実行時エラー | runner の `_report_error`（知らせる**前**に離す）・連続実行のエラー停止（`stop_run_to_end` より前に知らせる経路があれば、知らせる前に離す）・`_fail_single_call` | そのキー（最上段） |
| 状態を消す契機（構成セットの読込等・キーマップの切替 / 削除） | `AppState.reset_indices` の `reset_listeners`（runner の `on_runtime_reset` 等）で**すべて**離す。登録自体は app 側（task_05）でもよいが、runner の `on_runtime_reset` で離すならここで行う | すべて |

- 末尾の時点の規則: 単発で末尾の制御行から同じ押下の中で先頭へ回り先頭の `key_hold` 押すを送る場合でも、**押すより先に**離す。末尾の後の待機で押下が待機明けまで続く場合は、末尾に達した時点で離す（§5）
- 離さない契機（停止の行の区切り・戻す・単発の押下の合間・呼び出し先の末尾）で離していないことをテストで固定する

### テスト（偽の gateway / 偽の HeldInputs で記録・実際の入力は送らない）
- 新規 `tests/test_sequence_runner_key_hold.py`: 上の表の各契機で該当キーが離れる / 離れない（区切り・戻す・押下の合間・呼び出し先の末尾）・持ち主が最上段（呼び出し先の行で押しても最上段のキー）・末尾で先頭へ回るときの順（離す → 押す）・連動の末尾・`_report_error` で知らせる前に離す・held_inputs を渡さないとき従来どおり
- 既存テストは held_inputs を渡さないので変えない（変える必要があれば理由をコメントに残す）

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §4.3・§5・§8
- `keyseq/application/held_inputs.py`・`keyseq/application/action_executor.py`（task_03）
- `keyseq/application/sequence_runner/`（`sequence_runner.py`・`run_to_end.py`・`input_acceptance.py`・`call_wait.py`・`call_run_to_end.py`・`linked_call.py`・`wait_stop.py`・`send_wait.py`・`file_line_wait.py`）
- `keyseq/application/sequence_steps.py:180-350`（`advance` の末尾・`wrapped`・停止の行）・`keyseq/application/app_state.py:40-70`
- `keyseq/presentation/controllers/trigger_panel/effective_row_transition.py:10-18`・`trigger_row_edit.py:110-125`（呼び出し元の確認のみ・編集しない）
- `tests/test_sequence_runner.py:40-70`（runner の組み立て）

## 含まない

- presentation の変更（`app.py` の配線・reset_listeners への登録を app 側で行う場合・フック停止 / キーマップ一時停止 / アプリ終了での解放・ダイアログ・表示）（task_05）
- 正本の改訂（task_07）

## 確認

- 上記テストの追加（実行は verifier: compileall・tests・tests_ui・smoke）
- held_inputs を渡さない既存の経路が完全に従来どおりであること
- reviewer（5 観点）
