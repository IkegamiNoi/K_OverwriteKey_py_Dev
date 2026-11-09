# task_01c_mapped_key_shift

## 目的

正本 `key_input.md`「キー置換の送信の Shift」を実装する。キーマップの送信先が Shift の要る文字なら Shift 付きで送る。

## 対象範囲

### `keyseq/infrastructure/input_gateway.py`

- `send_mapped_key(key: str) -> None` を追加する。`resolve_send(key)` の結果の `kind` が `"keyboard"` で、Shift が要り、かつ Shift が押されていないときだけ、`keyboard.press("shift")` → `press_send` → `release_send` → `keyboard.release("shift")`。Shift の離しは `finally`。それ以外は `press_send` → `release_send`。
- 判定 `_needs_shift(key)`: `keyboard._os_keyboard.map_name(keyboard.normalize_name(key))` の先頭の要素 `(scan_code, modifiers)` について `tuple(modifiers) == ("shift",)`。先に `keyboard.key_to_scan_codes(key)` が呼ばれて表が初期化済みの前提でよい（`resolve_send` が先に呼ぶ）。例外は `False`。
- Shift の押下状態は `win32_window.is_shift_down()` を使う（`input_gateway.py` からの import は同じ infrastructure 層）。

### `keyseq/application/action_executor.py`

- `_send_mapped_key` の `press_key` / `release_key` の 2 行を `self.input_gateway.send_mapped_key(key)` の 1 行にする。guard・`stop_repeat_for_keys`・例外処理は変えない。

### テスト

- `tests/` に gateway のテストを追加（`keyboard` と `is_shift_down` を patch。既存の gateway のテストファイルがあればそこへ）: Shift が要る・押されていない → press shift, press, release, release shift の順 / 既に押されている → Shift を足さない / 要らない文字 / `kind` が keyboard 以外 / キー送信の例外でも Shift を離す / 判定の例外は要らない扱い。
- `_send_mapped_key` の経路を偽の gateway で検証しているテストを `tests/` `tests_ui/` から grep し（`press_key` を持つ偽物・`SendKeyAction`・`_send_mapped_key`）、`send_mapped_key` を呼ぶ形へ合わせる。偽物の `send_mapped_key` は press_key → release_key を呼ぶ形でよい。

## 読むファイル

- `instructions/common/spec_detail/key_input.md` の該当項
- `keyseq/infrastructure/input_gateway.py:224-248,323-355`
- `keyseq/application/action_executor.py:326-335`

## 含まない

- hotkey・key_hold・キーリピート・`held_inputs.py` の変更
- 記録・表示の変更

## 確認

verifier で compile / tests / tests_ui / smoke。

## 完了条件

上記 pass・reviewer 採用。実機目視は task_02。
