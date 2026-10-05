# task_11b_integration_spec_decisions

## 目的

task_08〜11 の統合確認で仕様判断が要った 4 点（ユーザー確定 2026-10-05）を実装する（暫定 31 v0.6 §4.5.8）。
**application（runner の問い合わせの口・M4・L1・L2）+ presentation（M3 の受付拒否 = 出力シーケンス欄の操作の入口だけ）。JSON は変えない。** task_11a の後に着手する。

## 対象範囲

### M3: 実行中の連続実行の連鎖は外から動かさない（§4.5.8 の 1 項目）

- application: `SequenceRunner.is_running_chain_callee(key: str) -> bool`（連続実行が**実行中**〔一時停止していない〕で、key がその連鎖の呼び出し先の段〔連続実行のキー自身は除く〕なら真）
- presentation: 出力シーケンス欄でダイアログを経ずに状態を変える入口（`trigger_panel_controller.py` の `on_action_list_mouse_release`〔クリックで次に実行の位置を変える〕・`on_action_list_move`〔ドラッグ移動〕・`move_action`〔上へ / 下へ〕・`paste_actions`・`duplicate_action`）で、
  選んでいるトリガーが上の真なら何もせず一時メッセージ「連続実行中は呼び出し先を変更できません（一時停止してから操作してください）」を出す（既存の一時メッセージの口 `_set_flash_message` 等）。一時停止中は今のまま受け付ける（再開は変更後の状態から）
- 呼び出し元（連続実行のキー自身）の位置の変更は今の規則のまま

### M4: 一時停止中の連続実行のトリガーが呼び出し先として末尾に達したら終える（§4.5.8 の 2 項目）

- 完了の伝播（`linked_call.py`）で、末尾に達したトリガー U が**一時停止中の連続実行のキー**なら、その連続実行を終える（停止扱い・通知は終えるときの既存の扱い）

### L1: 伝播で一時停止中の呼び出し元を進めるとき待機・停止の行で止める（§4.5.8 の 3 項目）

- `linked_call.py:72-76` の `wait_mode="skip"` を、一時停止中の呼び出し元を位置だけ進める場合は**待機の行・停止の行の手前で止める**形へ（その行を `▶` が指す）。再開時に通常どおり処理する。伝播で末尾に達して連続実行を終える場合だけ今の §4.2.8 の扱い

### L2: まとめて戻す対象の検査（§4.5.8 の 4 項目）

- `sequence_history.apply_control`（戻す）: まとめて戻すトリガーのどれかが単発の待機中・処理中なら「対象のトリガーが待機中のため操作できません」で何もしない / 一時停止中なら対象と同じく 2 回押しの対象（`prepare_target` を各トリガーに適用）
- 印のある対象で最上段の履歴が空なら、対象自身の履歴を起点にする

### テスト（追加まで）

- M3: 連続実行の実行中に呼び出し先を選んでクリック・ドラッグ・上へ・貼り付け・複製 → 変わらずメッセージ / 一時停止中は変わり再開は新しい位置から / 呼び出し元自身のクリックは今のまま（application の口の単体 + tests_ui で入口 1〜2 件）
- M4: U を連続実行で a の後に一時停止 → X で U を末尾まで → U の連続実行が終わっている（再開で全部を流し直さない）
- L1: X = `[call A, wait 500, B]`・X の連続実行が A の中で一時停止 → 別の押下で A を末尾まで → X の `▶` は wait・再開で待ってから B / `[call A, 停止, B]` は停止の行で止まり再開で停止の扱い
- L2: まとめて戻す相手が待機中ならメッセージで何もしない / 一時停止中なら 2 回押し / 最上段の履歴が空なら対象自身の段を戻す

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.5.3・§4.5.5・§4.5.8
- `keyseq/application/sequence_runner/linked_call.py`（全体）・`sequence_runner.py:60-130`・`:340-420`（連続実行の停止・一時停止）・`keyseq/application/sequence_history.py:195-270`
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:530-620`・`action_edit.py:110-160`・`:280-320`

## 含まない

- 呼び出し元自身の位置変更の規則の変更 / ダイアログを経る変更（フック停止で連続実行が止まるため対象外）
- L4・L6・L7（/refactor_check・task_07）/ 省略表示の枠（task_06）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクの後にまとめて実施）**: task_05a の枠・呼び出しの連動（§10-12〜16）・M3 のメッセージ。

## 追記（2026-10-05・task_11a からの持ち越し）

- **§4.2.10 のずれ**: task_11a で `_start_run_to_end` 冒頭の `cancel_pending_waits()`（連続実行の開始で単発の待機の保留を取り消す）が 1 手目の結果ごとの呼び出しへ移され、**1 手目が呼び出しの行のときは取り消さない**形になった
  （`test_run_to_end_back_and_rewind_use_two_press_discard_for_only_target` の退行を避けるため。HEAD〔task_11〕では冒頭の取り消しで同テストが通っていたので、退行の真因は別にある）。
  真因（戻す / 先頭へだけの連続実行トリガー f2 の 2 回押しの実行で、一時停止中の単発の呼び出し f5 が取り消される経路）を特定し、
  **連続実行の開始では単発の待機の保留だけを取り消し、一時停止中の単発の呼び出しは §4.2.10 の「全部捨てて通知」/「戻す・先頭へだけのトリガーは捨てない」の規則で扱う**形に直す。1 手目が呼び出しの行でも単発の待機は取り消すこと（テスト追加）
