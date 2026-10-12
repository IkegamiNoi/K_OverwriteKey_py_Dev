# 提案書 21: phase 55（キーボードUIのウィンドウ改善）後のリファクタ

> 状態: **実施済**（2026-10-12・phase 55 task_06_refactor。`infrastructure/win32_window.py` 新設・`_user32` / `_log_once` / `_guarded` の共通補助・SWP_* / `_KEY_DOWN` の定数化・テスト 18 件を `tests/test_win32_window.py` へ移動）。

## 判定の要約

範囲 `git diff f8a3b8a..HEAD -- keyseq/`（8 ファイル・+453 / -60）。メトリクスは verifier の実測、M3・M6 はメインで裏取り。

- **M3 該当**（根拠は ②。① は参考）: `infrastructure/input_gateway.py` の Win32 問い合わせが同型で 4 個になった。
  ①専用 user32 の関数を作る `@cache` 小関数（`_foreground_process_api` に加え `_place_window_below_api` / `_mouse_button_api`。送信系の 1 個を含め 4 個）
  ②「例外を吸収し初回だけ `_logger.exception` → 専用フラグ → 偽 / None」の try/except（`is_own_process_foreground` に加え `foreground_own_window` / `place_window_below` / `is_mouse_button_down`）。新規 3 個は既存のコピー
- M6: `place_window_below` のフラグ `0x0001 | 0x0002 | 0x0010` は `_KEYEVENTF_*` と同値だが意味が別（SWP_*）→ 非該当。ただし項目 1 で名前を付ける
- M1（600 行超は `app.py` 726 行 +5 のみ）・M2（80 行超の新規関数なし）・M4・M5（0 件）: 非該当
- 参考（非該当・2 個止まり）: `keyboard_window.py` の「マウスのボタンが押されていれば置き直す」（`_settle_size` / `_apply_pending_ratio`）・表示欄 2 つの同一 Checkbutton
- 関連する既知: `current.md` 別タスク化候補「`input_gateway.py` の責務の並び」（phase 54）。項目 1 はその一部（Win32 の窓・マウスの問い合わせ）を先に切り出す

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_input_gateway_repeat.py`（前面判定・`foreground_own_window`・`place_window_below`・`is_mouse_button_down`）/ `tests_ui/test_app_ui_flows.py`（`test_keyboard_window_*`）
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: Win32 の窓・マウスの問い合わせを専用モジュールへ切り出し、同型を 1 つにまとめる（M3）

- 対象: `input_gateway.py` の `_foreground_process_api`・`is_own_process_foreground`・`foreground_own_window`・`_place_window_below_api`・`place_window_below`・`_mouse_button_api`・`is_mouse_button_down`（:85-200 付近）と各 `_*_logged` フラグ
- 変更: 新規 `infrastructure/win32_window.py`（窓とマウスの状態の問い合わせ）へ移し、共通の 2 つの補助で同型を解消する
  ```python
  # 変更前（4 回繰り返し）
  def is_mouse_button_down() -> bool:
      global _mouse_button_error_logged
      if sys.platform != "win32":
          return False
      try:
          ...
      except Exception:
          if not _mouse_button_error_logged:
              _logger.exception("...")
              _mouse_button_error_logged = True
          return False
  # 変更後（例）
  def _guarded(name: str, default, call):   # 非 Windows → default / 例外は name ごとに初回だけ記録して default
      ...
  def is_mouse_button_down() -> bool:
      return _guarded("mouse_button", False, lambda: any(_user32("GetAsyncKeyState", (c_int,), c_short)(vk) & _KEY_DOWN for vk in (VK_LBUTTON, VK_RBUTTON)))   # argtypes は tuple（`@cache` の引数はハッシュ可能に）
  ```
  `_user32(name, argtypes: tuple, restype)` は `@cache` で専用 user32 の関数を返す（argtypes は tuple・list はハッシュできない）。`SWP_NOSIZE` / `SWP_NOMOVE` / `SWP_NOACTIVATE`・`_KEY_DOWN = 0x8000` を名前付き定数にする。
  `input_gateway.py` からの再輸出はしない（恒久互換レイヤー禁止）。`app.py` の import 先を新モジュールへ変え、テストは移動先を参照する
- 完了条件: `codebase_map.md` の phase 53・phase 55 の項の `input_gateway.py` への言及を新モジュールへ更新・`grep -c "_logger.exception" keyseq/infrastructure/win32_window.py` が 1・`grep -n "0x0001 | 0x0002 | 0x0010" keyseq` が 0 件・項目 0 が全 pass
- リスクと戻し方: 既定値は関数ごとに分かれる（`is_own_process_foreground` は前面なし → True・例外 → False / 他は False・None）。共通補助の既定値 1 つへ潰さず、前面なしの扱いは各関数に残す。phase 53 のキーリピートの前面判定（`is_own_process_foreground`）も移るため、`key_repeat` の注入（`app.py:132`）を取りこぼすとリピートが止まらなくなる → `tests/test_input_gateway_repeat.py` の前面判定テストと `tests/test_key_repeat*.py` で確認。戻しはファイル移動の取り消し
- 依存: 項目 0

## 対象外（別タスク化候補へ）

- `keyboard_window.py` のボタン判定 → 置き直しの 2 個・表示欄の Checkbutton 2 個（3 個目が出たら再判定）
- `input_gateway.py` の送信系の責務の並び（phase 54 の候補のまま）
