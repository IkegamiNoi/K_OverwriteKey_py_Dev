# task_02_key_repeater

## 目的

暫定 36 §4・§6 の application 部分: リピートのタイマー `KeyRepeater` と、`HeldInputs` / `ActionExecutor` との連携。
App の配線（`after` / 間隔の取得 / 知らせの口の注入）・知らせの前の停止と表示中の抑止の**呼び出し**・ダイアログは task_03（本タスクは口まで）。JSON 不変。

## 対象範囲

### 新規 `keyseq/application/key_repeat.py` の `KeyRepeater`（対象は高々 1 つ・UI スレッドで使う）
- 注入: `after(ms, callback) -> id` / `after_cancel(id)`（どちらか `None` ならリピートしない）・`get_timing() -> (待ち ms, 間隔 ms)`・送り直し `send(key)`（keydown 1 回）・失敗時の後始末 `on_failure(identity, key, action, exc)`
- 状態: 今の対象（identity・キー名・action）・予約 id・世代番号・抑止の数（入れ子）
- `start(identity, key, action)`: 抑止中なら何もしない（断った開始は復活させない）。今の対象を止めてから、`get_timing()` を読み、待ちで予約する（§4.2・§4.5）
- `stop()`: 予約を取り消し対象を空にし、世代を進める。`is_target(identity) -> bool`
- 発火: 世代・対象が合わなければ送らずに終える（古い予約）。抑止中なら止めて終える。`send(key)` が成功したら間隔で次を予約（遅れの追いつきはしない）。例外なら `stop()` してから `on_failure(...)`（§4.7）
- text の前後: `pause_for_text() -> 控え`（今の対象を控えて `stop()`）/ `resume_after_text(控え)`（控えがあり抑止中でなければ `start` し直す）（§4.4）
- 抑止: `begin_suppress()`（数を増やし、今のリピートを止める）/ `end_suppress()`（数を減らす。0 になっても再開しない）（§4.8・§2-8）

### `keyseq/application/held_inputs.py` の `HeldInputs`
- 任意の注入 `repeater: KeyRepeater | None`（無ければ従来どおり・リピートしない）
- **止める場所の規定（§4.3）**: キーボードのキー K の押す・離すの送信を**始める前に**、`repeater.is_target(K の identity)` なら `stop()`。
  対象: `press_key`（`_press` の前）・`release_key`・`_release_records`（キーごとに送る前）・`suspend_keyboard`（下記）
- `press_key(owner, key, *, repeat_action: dict | None = None)`: 送信（と補償）が成功し `repeat_action` があれば `repeater.start(identity, key, repeat_action)`
- `suspend_keyboard`: 送る前に `repeater.pause_for_text()` で控える（控えを内部に持つ）。`resume_keyboard`: 押し直しは `repeat_action` なしで行い（切替に数えない）、**すべての押し直しが成功したら**、控えのキーがまだ集合にあれば `resume_after_text(控え)`。例外で抜ける場合・送信失敗で `resume` が呼ばれない場合は再開しない（控えは捨てる）（§4.4）
- `stop_repeat_for_keys(keys: Iterable[str])`: 送るキーのどれかの identity が対象なら `stop()`（hotkey・直接置換の前・§2-9）
- 送り直しの送信 `send` と失敗の後始末は `HeldInputs` が `KeyRepeater` に渡す: `send` = send_guard の中で `input_gateway.press_key(key)`（記録は変えない・`_notify` しない）/
  失敗 = そのキーの離す（`release_key` と同じく成功なら外す・失敗なら残す）をしてから、注入された `on_repeat_error(action, message)`（任意・task_03 で配線）を呼ぶ
- タイマーの状態を `HeldInput` の記録に入れない（表示の更新を起こさない）

### `keyseq/application/action_executor.py`
- `_execute_key_hold`: キーボードの押すで `is_repeat_enabled(action)`（task_01 の domain）なら `repeat_action=action` を渡す
- `_execute_hotkey`・`_send_mapped_key`: 送る前に `held_inputs.stop_repeat_for_keys(送るキーの列)`（hotkey は正規化後の文字列を `+` と `,` で分けた各キー）
- `ActionExecutor` の既定の `HeldInputs(input_gateway)`（repeater なし）は変えない

### テスト（偽の gateway・偽の after〔予約を記録して手で発火〕）
- 暫定 36 §8 の 1〜7 のうち application で確かめられるもの: 開始・待ち→間隔の送り直し・離す行で止まり以後送らない / `repeat_action` なしはリピートしない /
  phase 51 の自動で離す（`release_owner` / `release_all` / `release_keyboard`）で止まる / 離す送信の失敗・押すと補償の離すの失敗で止まる /
  text の前後（`suspend` → `resume` で元の対象だけ待ちから・他のキーは再開しない・失敗で再開しない）/ 切替（別キーの有効な押すで切り替わる・`repeat_action` なしの押す・マウス・対象を含まない hotkey では切り替わらない・同じキーを `repeat_action` なしで押すと止まる）/
  対象を含む hotkey・直接置換の前に止まる / 送り直しの例外で止まり・離し・`on_repeat_error` が呼ばれ・実行は止めない / 古い予約は送らない / after が無ければリピートしない / 送り直しで `on_change` が呼ばれない /
  抑止中は開始・再開・発火しない・入れ子・解除しても再開しない
- 既存テスト（phase 51 の held_inputs・action_executor の key_hold）が変わらず通ること

## 読むファイル

- `instructions/history/36_key_hold_auto_repeat.md` §4・§6
- `keyseq/application/held_inputs.py`（全体）・`keyseq/application/action_executor.py`（`__init__`・`_execute_key_hold`・`_execute_hotkey`・`_validate_hotkey`・`_send_mapped_key`・`_write_text`）
- `keyseq/domain/key_hold.py`（task_01 の `is_repeat_enabled`）
- `tests/test_held_inputs.py`・`tests/test_action_executor_key_hold.py`

## 含まない

- App の配線・知らせの前の停止 / 表示中の抑止の呼び出し・ダイアログ（task_03）・正本の改訂（task_05）

## 確認

- 上記テスト（実行は verifier）・reviewer（5 観点）
