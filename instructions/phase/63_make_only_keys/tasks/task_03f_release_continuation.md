# task_03f_release_continuation

## 目的

task_03d で v0.4 に合わせた状態機械を、暫定 46 v0.5（ユーザー確定 2026-10-20）に合わせる。

- **離した直後の押下は押し続けの続き**: 続きの対象の「離した」から、16 ms を超え「離しの直後の時間」（60 ms）以内に届いた押下は、押し直しではなく押し続けの続きとみなす（§2・§3.2 の表・注 5・§3.3）
  - 続きの対象の「離した」は 2 つ: 長押しの途中の 2 回組（「押した」から「片方の離しの時間」以上たってからの 2 回組）と、案 A の片方
  - 続きでは押している状態へ戻し、`input_router.handle` を呼ばない。覚えた決定は元のまま、**「押した」の時刻は続きの時刻に置き直す**
- 長押しの途中のフックの詰まりによる「離した」の取り違えから、リピートのように置換先が出続ける連鎖を止める（§1「実機目視の NG の計測（v0.5 の根拠）」）

**application 限定**（`make_only_keys.py` とそのテスト）。domain・presentation・infrastructure・JSON スキーマは変えない。task_03c のデバッグ出力の仕組みは残す。

## 対象範囲（application 限定）

### `keyseq/application/make_only_keys.py`

- 定数 `CONTINUATION_WINDOW_S = 0.060`（離しの直後の時間・§3.3）を足す
- `_KeyState` に「この「離した」は続きの対象か」（例: `released_continuable: bool = False`）を足す
- 「離した」を記録する 2 か所で値を決める
  - 2 回組の「離した」（`_handle_down` の「押している・保留あり・t − p ≤ 16 ms」）: `released_continuable = now - state.pressed_at >= 片方の離しの時間`（長押しの途中の 2 回組だけ True）
  - 案 A の「離した」（`_confirm_pending` の `half-pair-release`）: `released_continuable = True`
- `_handle_down` の「押していない」の分岐を 3 つにする（§3.2 の表の順）
  1. `released_at` があり `now <= released_at + PAIR_WINDOW_S` → 今と同じ（2 回組の続きとして捨てる）
  2. `released_at` があり `released_continuable` で `now <= released_at + CONTINUATION_WINDOW_S` → **続き**: `pressed = True`・`pressed_at = now`・`released_at = None`・`released_continuable = False`（覚えた決定 `accept` は触らない）。そのうえで「押している・保留なし」と同じく `_start_pending` で保留にし、`self._result(state.accept, scan_code=..., now=...)` を返す。`self._route` は呼ばない。押下状態（`_release_state`）は戻さない（§3.2 注 5）
  3. それ以外 → 今と同じ「押した」
- 遅れた保留の確定で案 A の「離した」になって `_handle_down` を扱い直す経路（今の再帰呼び出し）は、上の 2 が先に当たれば続きになる（追加の分岐は要らない）
- 実の `up`（`handle` の `up` の分岐）では `released_at = None`・`released_continuable = False` にする（§3.2 注 5「`up` の後は「離した」の時刻を持たない」）
- 片方の離しの時間の計算（`self._get_repeat_delay_ms() / 1000 - 0.1`）は `_confirm_pending` と同じ式を使う。2 か所で使うなら小さな private メソッドにまとめてよい
- trace: 続きのときに `continuation since_release_ms=...` を出す。2 回組の「離した」の行に `continuable=True/False` を足す

### `tests/test_make_only_keys.py`

§6 #1 の v0.5 の項目を足す（既存のテストは期待値を変えない。変わるものがあれば理由を完了報告に書く）。

- 実機の連鎖の再現: 押下 → 500 ms → 33 ms ごとに押下 × 6 → 15 ms 後に押下（取り違えの 2 回組）→ 続けて 30 ms ごとに押下 × 6 → 22 ms → 押下 → 13 ms → 押下 → `route`（`handle`）の呼び出しは最初の「押した」の 1 回だけ・最後に押していない状態
- 案 A の後の続き: 押下 → 100 ms で単独の押下 → 30 ms 後に押下（タイマーより先・遅れた確定で案 A の「離した」→ 続き）→ `route` は 1 回だけ
- 境目: 長押しの途中の 2 回組の「離した」から 60 ms ちょうどの押下 → 続き / 61 ms → 「押した」/ 16 ms ちょうど → 捨てる（v0.4 のまま）
- 短い押下の 2 回組の後には続きにならない（連打）: 押下を 0 / 100 / 200 ms・2 回組を 50 / 63・150 / 163・250 / 263 ms → `route` は 3 回（100 / 200 ms は 2 回組から 37 ms でも「押した」）
- 長押しの後の連打: 0 ms 押下 → 33 ms ごとのリピート（500 ms から）→ 1050 / 1063 ms に 2 回組 → 1100 ms 押下 → 1150 / 1163 ms → 1200 ms 押下 → 1250 / 1263 ms → 1300 ms 押下 → 1350 / 1363 ms → `route` は 0 / 1200 / 1300 ms の 3 回（1100 ms は続き）・最後に押していない状態
- 2 回組が「片方の離しの時間」をまたぐ: 0 ms 押下 → 390 / 420 ms に押下 → 509 ms 押下 → `route` は 0 / 509 ms の 2 回
- 続きの後の本物の 2 回組の 80 ms 後の押下は「押した」
- 続きでは覚えた決定（抑止）を返す / 停止要求の間は続きの押下も素通し
- 実の `up` の後は、60 ms 以内の押下でも「押した」

### `tests/test_make_only_keys_integration.py`

- `input_router` を通して、上の「実機の連鎖の再現」の時刻列で直接置換の置換先が 1 回だけ送られることを 1 件足す（§6 #2）

### 設計メモ / 制約

- 時刻は全て `self._clock()` の値で比べる（タイマーの満了時刻を使わない・§3.1）
- ロックの中で Tk を呼ばない・世代つきの予約・停止要求の間は素通しは v0.4 のまま（変えない）
- 続きで `_release_state` に合成の `down` を渡して押下状態を戻すことはしない（§3.2 注 5）

## 読むファイル

1. `instructions/history/46_make_only_keys.md` の §2「リピートなし」・§3.2（表・注 5）・§3.3・§6 #1
2. `keyseq/application/make_only_keys.py`（全体）
3. `tests/test_make_only_keys.py:1-75`（手本: 時計・スケジューラの差し替え）と `:127-260`（手本: 時刻列のテスト）
4. `tests/test_make_only_keys_integration.py`（全体）

## 含まない

- キーボードUI の色の変更（実機目視の後に判断・必要なら別タスク）
- IME の切り替えの調査（ユーザーの報告待ち・暫定 46 §9 #7）
- 正本反映・暫定 46 の凍結（task_04）
- 送信の見直し・リピートの復活（idea_53）
- `hook_controller.py`・`app.py`・domain の変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_make_only_keys tests.test_make_only_keys_integration` が全 pass（上の「足す」の項目を含む）
- 既存テストが全 pass（`unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`）
- `keyseq/application/make_only_keys.py` が keyboard・tkinter を import しない

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- 実機目視は本タスクの後にユーザーが行う（§6 #6・デバッグ出力つき）
