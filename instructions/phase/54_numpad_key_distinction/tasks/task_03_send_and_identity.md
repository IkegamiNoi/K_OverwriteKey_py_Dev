# task_03_send_and_identity

## 目的

暫定 38（v0.5）§5 の送信と同じキーの判定。テンキーの名前（`keyseq/domain/numpad_keys.py` の表）を、そのスキャンコードと拡張フラグで `SendInput` のスキャンコード入力として送る（NumLock に従う＝物理キーと同じ・task_01 の probe で確認済み）。

## 対象範囲（`keyseq/infrastructure/input_gateway.py` のみ）

- テンキーの送信の関数（モジュール内・例 `_send_numpad_event(scan, extended, key_up)`）: `SendInput` に `INPUT_KEYBOARD`・`wVk=0`・`wScan=scan`・`dwFlags = KEYEVENTF_SCANCODE (0x0008) | (KEYEVENTF_EXTENDEDKEY if extended) | (KEYEVENTF_KEYUP if key_up)` の 1 件を渡す。
  - 構造体（`KEYBDINPUT` / `MOUSEINPUT` / union / `INPUT`）と `SendInput` の `argtypes` を明示する。**共有の `ctypes.windll.user32` の属性は書き換えない**（phase 53 の `_foreground_process_api` と同じく `@cache` + `ctypes.WinDLL("user32", use_last_error=True)` の専用インスタンス）
  - 戻り値が 1 でなければ `OSError(ctypes.get_last_error())` を投げる（送信の例外は既存の扱い〔phase 51・52〕に乗る）
  - 既存の `_send_extended_event` と同じく、`keyboard._listener.is_replaying` を立てて keyboard の押下記録に載せない（`_listener` が無ければそのまま送る）
- `press_key` / `release_key`: **最初に** `numpad_key_spec(key)` を見て、表の名前ならテンキーの送信で送る（keyboard・拡張キー表には渡さない）。それ以外は従来どおり
- `send_hotkey`: 順に押して逆順に離す分岐の条件を「拡張キー**または表の名前**を含むか」に広げる（表の名前を含む hotkey は `keyboard.send` に渡さない）
- `key_identity`: **最初に** `numpad_key_spec(key)` を見て、表の名前なら `(scan_code, extended)` を返す。それ以外は従来どおり（記号の名前 `+` / `*` / `-` は従来どおり keyboard の先頭のスキャンコード〔テンキー側〕＝暫定 38 §2-8）
- 拡張キー表 `_EXTENDED_KEYS` と既存の送信経路は変えない

### テスト（`tests/test_input_gateway_send.py`）
- 表の名前の `press_key` / `release_key` がテンキーの送信の関数（patch してよい）に `(scan, extended, key_up)` で渡り、`keyboard.press` / `release` / `send` と `_send_extended_event` を呼ばない（`num 1` → 79 / False・`num enter` → 28 / True・`num divide` → 53 / True・大文字 / 前後空白）
- `send_hotkey("ctrl+num 1")` が ctrl → num 1 の順に押し、逆順に離す（`keyboard.send` を呼ばない）。`send_hotkey("ctrl+a")` は従来どおり `keyboard.send`
- `key_identity("num 1") == (79, False)`・`key_identity("num enter") == (28, True)`・`key_identity("end") == (79, True)`・`key_identity("1")` は keyboard の先頭（patch した `key_to_scan_codes` で 2）で `num 1` と別
- テンキーの送信の関数: `SendInput` を偽物に差し替えて、渡した `INPUT` の `wScan` / `dwFlags`・戻り値 0 で `OSError`・`is_replaying` を立てて戻す（§8-6）
- 実の Win32 を呼ばない

## 読むファイル

- `instructions/history/38_numpad_key_distinction.md` §5・§8-6
- `keyseq/infrastructure/input_gateway.py`（全体）・`keyseq/domain/numpad_keys.py`
- `tests/test_input_gateway_send.py`

## 含まない

- 記録（task_04）・入力の名前（task_02 で完了）・正本の改訂（task_06）・application 側の変更（送信はすべて `InputGateway` を通るため不要）

## 確認

- 上記テスト + 既存テスト（実行は verifier）・reviewer（5 観点）
