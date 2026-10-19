# task_03d_no_repeat

## 目的

task_02 / task_03 で作った状態機械（v0.3 = リピートあり）を、暫定 46 v0.4（ユーザー確定 2026-10-20）に合わせる。

- **リピートなし**: 押し続けている間の押下は捨てる（`input_router.handle` を呼ばない・何も実行しない）（§2・§3.2「保留の確定」）
- **片方の離し**: 「押した」から「片方の離しの時間」（OS のリピートの待ち時間 − 100 ms）より前に確定した単独の保留は、2 回組の片方 =「離した」とする（§3.2・§3.3・§9 #3 の案 A）
- 覚えるのはフックへの戻り値だけ（§3.2 注 2）

**application 限定**（`make_only_keys.py` とそのテスト）。domain・presentation・infrastructure・JSON スキーマは変えない。task_03c のデバッグ出力の仕組みは残す。

## 対象範囲（application 限定）

### `keyseq/application/make_only_keys.py`

- `_KeyState` に「押した」の時刻（例: `pressed_at: float`）を足す
  - 「押した」（押していない状態の押下）と、「古い押下」の「離した」→「押した」で更新する
- `has_actions`・`_remember_press` の actions の記録をやめる（戻り値 `accept` だけを覚える）
- `_confirm_pending`（保留の確定）を次の 3 つに分ける。戻り値で「離した」になったかを呼び出し側へ返す
  1. 「古い押下」の印がある → 今と同じ（「離した」→「押した」・route を返す）
  2. 印が無く、`pending_at - pressed_at < 片方の離しの時間` → **「離した」**: `KeyStateManager` へ合成の `up`（今の「離した」と同じ `_release_state(SyntheticKeyEvent("up", ...))`）・`pressed = False`・`released_at = pending_at`・`released_accept = accept`。route は返さない
  3. それ以外 → 捨てる（route を返さない・押したまま）
- 片方の離しの時間 = `self._get_repeat_delay_ms() / 1000 - 0.1`（秒）。下限は設けない（`keyboard_repeat_timing` の待ち時間は 250 ms 以上）
- `_handle_down` の「押している・保留あり・t − p > 16 ms」: 確定で「離した」（上の 2）になったら、**この押下を「押していない」の行で扱い直す**（`released_at + PAIR_WINDOW_S` の判定から。t − p > 16 ms なので通常は「押した」）。それ以外は今どおり新しい保留
- `_expire` も上の 3 分岐に従う（2 のときは `_on_routes` を呼ばない）
- trace の文言: 確定の種類に `half-pair-release`（2）・`discarded-hold`（3）を出す（`repeat` は出なくなる）

### `tests/test_make_only_keys.py`

v0.3 のリピートを前提にした既存テストを v0.4 に合わせて直し、§6 #1 の v0.4 の項目を足す。

- 直す: `test_hold_repeats_three_times_then_releases`（→ リピート 0 回・`handle` は「押した」の 1 回だけ）/ `test_passthrough_with_actions_routes_repeats`（→ 押し続けても `handle` は 1 回・押している間は素通し）/ `test_late_timer_is_confirmed_by_the_next_press_then_new_pending_is_created`（→ 古くない保留は捨ててから新しい保留・actions が増えない）/ `test_trace_reports_press_release_and_repeat_transitions`（repeat の行が無くなる）/ `test_stale_repress_remembers_new_accept_and_actions_state`（actions の記録が無くなる）
- 足す:
  - 片方の取りこぼし後の押し直し（0 ms 押下 → 45 ms に 1 回だけ → 120 ms 押下 → 165 / 176 ms に 2 回組）→ 「押した」2 回・「離した」2 回・`handle` は 2 回
  - 境目（待ち時間 500 ms）: 「押した」から 399 ms の単独の押下 → 「離した」/ 401 ms → 捨てて押したまま / 待ち時間 250 ms に差し替えると 149 ms → 「離した」・151 ms → 捨てる
  - タイマーが遅れて、確定が「離した」になった押下（「押した」から 100 ms で保留 → 20 ms 後に次の押下）→ 次の押下は「押した」として `handle` へ渡る
  - 押し続けた後に片方だけ届く（押下 → 500 ms → 33 ms ごと × 3 → 22 ms → 1 回だけ）→ 捨てて押したまま / その後 900 ms 静かにして押下 → 16 ms 後に「離した」→「押した」

### `tests/test_make_only_keys_integration.py`

- `test_hold_repeats_replacement_then_release_clears_pressed_state` を「押し続けても置換先は 1 回だけ・離した後に押下状態に残らない」へ直す（§6 #2）

### 設計メモ / 制約

- ロックの中で Tk を呼ばない・世代つきの予約・停止要求の間は素通し・実の `up` の扱いは v0.3 のまま（変えない）
- 「片方の離し」の判定は時刻で行う（タイマーが満了した時刻ではなく `pending_at` と `pressed_at` を比べる。§3.1 の「判定は時刻で行う」）

## 読むファイル

1. `instructions/history/46_make_only_keys.md` の §2・§3.2・§3.3・§6 #1〜#2
2. `keyseq/application/make_only_keys.py`（全体）
3. `tests/test_make_only_keys.py`（全体）
4. `tests/test_make_only_keys_integration.py:100-150`

## 含まない

- キーボードUI の色（task_03e）
- 正本反映・暫定 46 の凍結（task_04）
- 送信の見直し・リピートの復活（idea_53）
- `hook_controller.py`・`app.py` の変更（呼び出し口は今のまま）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_make_only_keys tests.test_make_only_keys_integration` が全 pass（上の「直す」「足す」の項目を含む）
- 既存テストが全 pass（`unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`）
- `keyseq/application/make_only_keys.py` が keyboard・tkinter を import しない

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- 実機目視は task_03e の後にまとめて行う（§6 #6）
