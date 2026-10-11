# task_01_foreground_check

## 目的

暫定 37 の実装一式（§3 前面判定・§4 `_fire` での停止・§6 置き場）とテスト。実装後にユーザーの実機目視（§8 の 9〜11）。

## 対象範囲

### infrastructure `keyseq/infrastructure/input_gateway.py`
- モジュール関数 `is_own_process_foreground() -> bool`（`keyboard_repeat_timing` と同じくモジュール関数）
  - `sys.platform != "win32"` なら偽
  - `@cache` の専用関数で `ctypes.WinDLL("user32")` のインスタンスを作り、`GetForegroundWindow`（`argtypes = []`・`restype = wintypes.HWND`）と
    `GetWindowThreadProcessId`（`argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]`・`restype = wintypes.DWORD`）を設定する（手本 `keyseq/presentation/modal.py:15-21`。**共有の `ctypes.windll.user32` の属性は書き換えない**）
  - 前面の窓が NULL（None / 0）→ **真**（止める・暫定 37 §2-6）
  - プロセス ID を取り、0 なら偽。自プロセス（`os.getpid()`）と一致すれば真・違えば偽
  - 例外は吸収して偽。**例外のログは初回だけ**（モジュール内のフラグ。`_logger` があれば使い、無ければ `logging.getLogger(__name__)`）

### application `keyseq/application/key_repeat.py`
- `KeyRepeater.__init__` に任意のキーワード引数 `is_blocked: Callable[[], bool] | None = None` を足す（既定 None = 判定しない）
- `_fire` で、世代・抑止の確認の**後**、`_send` の**前**に `is_blocked` を呼び、真なら `self.stop()` して return（送らない・再予約しない・再開しない）
  - `is_blocked` の例外は吸収して「ブロックしない」（送り直しを続ける）。ログは初回だけ
- **`start` / `resume_after_text` では呼ばない**（暫定 37 §2-5・§4.1）

### presentation `keyseq/presentation/app.py`
- `KeyRepeater(...)` の生成（:126-130）で `is_blocked=is_own_process_foreground` を渡す（import を追加）

### テスト
- `tests/test_key_repeat.py`: 偽の `after` と偽の `is_blocked` で
  - 真なら 1 回目の発火で送らずに止まる（`has_target` が偽・予約が残らない）。押す・start 自体は従来どおり（§8-1）
  - リピート中に真になると次の発火で止まり、偽に戻しても以後の発火（古い予約）で送らない（§8-2）
  - `resume_after_text` の後、真なら 1 回目の発火で止まる（§8-3）
  - `is_blocked` が例外 / 未注入なら従来どおり送り続ける（§8-4）
  - `start` で `is_blocked` が呼ばれないこと
- `tests/test_input_gateway_repeat.py`: `is_own_process_foreground` を、専用の user32 を偽物に差し替えて（`@cache` の関数を patch するか `cache_clear`）
  自プロセス → 真 / 他プロセス → 偽 / 前面 NULL → 真 / プロセス ID 0 → 偽 / 例外 → 偽（2 回目の例外でログが増えない）/ Windows 以外 → 偽（§8-5）
- `tests_ui/test_key_hold_presentation.py`: `app.key_repeater._is_blocked is input_gateway.is_own_process_foreground`（§8-6）。
  既存の抑止のテストで発火（`_fire`）を通るものがあれば、`is_blocked` を偽に差し替えて実環境の前面に依存させない（§8-7。`start` だけを見るテストは影響しない）
- テストは実入力を送らない・実の Win32 を呼ばない

## 読むファイル

- `instructions/history/37_repeat_stop_on_own_foreground.md`（全体）
- `keyseq/application/key_repeat.py`（全体）・`keyseq/infrastructure/input_gateway.py`（:1-95）・`keyseq/presentation/modal.py`（:1-31）・`keyseq/presentation/app.py`（:60-140）
- `tests/test_key_repeat.py`・`tests/test_input_gateway_repeat.py`・`tests_ui/test_key_hold_presentation.py`

## 含まない

- ダイアログを出す側の変更・phase 52 の抑止（`begin_suppress` / `end_suppress`）の変更・`HeldInputs` / `ActionExecutor` の変更・正本の改訂（task_03）

## 確認

- 上記テスト + 既存テスト（tests / tests_ui / smoke。実行は verifier）・reviewer（5 観点）・ユーザーの実機目視（暫定 37 §8 の 9〜11）
