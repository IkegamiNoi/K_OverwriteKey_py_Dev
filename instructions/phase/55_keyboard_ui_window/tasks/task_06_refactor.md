# task_06_refactor

## 目的

[提案書 21](../../../modified_proposal/21_refactor_keyboard_ui_window.md) 項目 1 の実施（ユーザー判断 2026-10-12）。`infrastructure/input_gateway.py` の Win32 の窓・マウスの問い合わせ 4 関数を
新規 `infrastructure/win32_window.py` へ移し、「例外を吸収し初回だけ記録して既定値を返す」同型 4 個（M3）と専用 user32 の関数生成を共通の補助 2 つにまとめる。
**挙動不変**（戻り値・既定値・ログの回数）。infrastructure + presentation の import 先 + テストの参照先・codebase_map。domain / application 不変・スキーマ不変。

## 対象範囲

### 新規 `keyseq/infrastructure/win32_window.py`（窓とマウスの状態の問い合わせ）

- 移すもの（`input_gateway.py` から削除し、ここに置く。**`input_gateway.py` から再輸出しない**）:
  `is_own_process_foreground` / `foreground_own_window` / `place_window_below` / `is_mouse_button_down` と、それぞれの `_*_error_logged` フラグ・`_foreground_process_api` / `_place_window_below_api` / `_mouse_button_api`・`VK_LBUTTON` / `VK_RBUTTON`
- 共通の補助:
  - `_user32(name: str, argtypes: tuple, restype)`（`@cache`。`ctypes.WinDLL("user32")` の専用インスタンスから関数を取り argtypes / restype を設定して返す。argtypes は tuple）
  - 初回だけ記録する補助（例: `_log_once(key: str, message: str)` が key ごとに 1 回だけ `_logger.exception(message)`。フラグはモジュール内の set で持つ）
- 既定値は関数ごとに保つ: `is_own_process_foreground` = 非 Windows False / 前面なし **True** / 他プロセス False / 例外 False・`foreground_own_window` = None 系・`place_window_below` = False 系・`is_mouse_button_down` = False 系（既存のテストが期待する値をそのまま満たすこと）
- 名前付き定数: `SWP_NOSIZE = 0x0001` / `SWP_NOMOVE = 0x0002` / `SWP_NOACTIVATE = 0x0010` / `_KEY_DOWN = 0x8000`
- ログのメッセージ文言は既存のものを保つ
- logger は `logging.getLogger(__name__)`（モジュール名が変わることは受容）

### `keyseq/infrastructure/input_gateway.py`

- 上記を削除。残る送信・リピート設定・名前の検査等は変えない（未使用になった import〔`os` 等〕があれば削除）

### `keyseq/presentation/app.py`

- 4 関数の import 先を `keyseq.infrastructure.win32_window` へ変える（注入の行は変えない）。**BOM・改行コードを変えない**

### テスト

- `tests/test_input_gateway_repeat.py` の前面判定・`foreground_own_window`・`place_window_below`・`is_mouse_button_down` のテストクラスを新規 `tests/test_win32_window.py` へ移し、参照先・差し替え先（`cache_clear` するキャッシュ・ログのフラグのリセット）を新モジュールに合わせる。**期待値は変えない**
  （ログのフラグを直接リセットしていた箇所は、新しい「初回だけ」の状態をリセットする方法に置き換える）
- `tests_ui/test_key_hold_presentation.py:88` の `input_gateway.is_own_process_foreground` を新モジュールの参照へ

### 文書

- `instructions/common/codebase_map.md`: phase 53 の項（:770 付近「前面判定: `infrastructure/input_gateway.py` の…」）と phase 55 の項（Win32 の 3 関数）の参照先を `infrastructure/win32_window.py` へ。ファイル一覧（infrastructure の節）に `win32_window.py` を 1 行追加

## 読むファイル

- `instructions/modified_proposal/21_refactor_keyboard_ui_window.md`
- `keyseq/infrastructure/input_gateway.py`（1-60 行の import・定数と、85-200 行付近の対象関数）
- `keyseq/presentation/app.py:76-82`
- `tests/test_input_gateway_repeat.py`（96 行以降・移す対象）
- `tests_ui/test_key_hold_presentation.py:80-95`
- `instructions/common/codebase_map.md`（infrastructure のファイル一覧・phase 53 / 55 の項）

## 含まない

- `input_gateway.py` の送信系の責務の整理（別タスク化候補のまま）
- `keyboard_window.py` / 表示欄の同型 2 個（別タスク化候補）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（移したテストの件数が減っていない）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `grep -rn "is_own_process_foreground\|foreground_own_window\|place_window_below\|is_mouse_button_down" keyseq/infrastructure/input_gateway.py` が 0 件 / `grep -n "0x0001 | 0x0002 | 0x0010" -r keyseq` が 0 件 / `grep -c "_logger.exception" keyseq/infrastructure/win32_window.py` が 1

## 完了条件

- 上記確認 pass・**reviewer 採用**。挙動不変のため実機目視は任意（キーリピートの前面停止・キーボードUIの前面化とリサイズが従来どおり）。
