# task_01d_shift_skip_with_modifiers

## 目的

正本 `key_input.md`「キー置換の送信の Shift」の送り方どおり、Ctrl / Alt / Windows キーのどれかが押されているときは Shift を足さない。

## 対象範囲

### `keyseq/infrastructure/win32_window.py`

- `is_ctrl_alt_win_down() -> bool` を `is_shift_down` と同じ形で追加する（`VK_CONTROL = 0x11` / `VK_MENU = 0x12` / `VK_LWIN = 0x5B` / `VK_RWIN = 0x5C`・`_guarded` の種類 `"modifier_keys"`。`_ERROR_MESSAGES` の文言は英語にする）。
- `is_shift_down` の docstring の `physical` を削る（注入された Shift も含むため）。

### `keyseq/infrastructure/input_gateway.py`

- `send_mapped_key` の条件に `and not win32_window.is_ctrl_alt_win_down()` を足す。

### テスト

- `tests/test_input_gateway_send.py`: Ctrl 等が押されていれば Shift を足さないケースを追加。既存の Shift を足すケースは `is_ctrl_alt_win_down` を `False` に patch する。
- `tests/test_action_executor_key_hold.py:68` 付近の無関係な空行（task_01c で混入）を消す。

## 含まない

- 記録・表示・hotkey・key_hold の変更

## 確認

verifier で compile / tests / smoke。

## 完了条件

上記 pass・reviewer 採用。
