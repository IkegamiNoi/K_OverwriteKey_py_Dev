# task_03b_place_below_dialog

## 目的

task_03 の実機目視で、キーボードUIだけ手前の状態でダイアログを開くと、ダイアログが一度前に出た後キーボードUIに覆われた。
Windows は topmost を外した窓を非 topmost の最上位へ置くため。**一時解除で外した直後に、キーボードUIを前面のダイアログの直下へ置く**（暫定 39 v0.5 §4「ダイアログ表示中の一時解除」）。
**infrastructure に 1 関数追加・presentation（app.py の注入 / layout_controller.py）。domain / application 不変・スキーマ不変。**

### 実測（2026-10-12・メイン probe）

素の Tk で topmost の Toplevel の `-topmost` を 0 にした直後もダイアログ（transient）より上のまま。`SetWindowPos(kb, dlg, 0,0,0,0, SWP_NOSIZE|SWP_NOMOVE|SWP_NOACTIVATE)` でダイアログの下になる。

## 対象範囲

### `keyseq/infrastructure/input_gateway.py`

- `place_window_below(hwnd: int, above_hwnd: int) -> bool` を `foreground_own_window` の近くに追加:
  非 Windows → False。専用 user32（`@cache` の小関数・argtypes `[HWND, HWND, c_int, c_int, c_int, c_int, c_uint]`・restype `BOOL`）で
  `SetWindowPos(hwnd, above_hwnd, 0, 0, 0, 0, SWP_NOSIZE(0x0001) | SWP_NOMOVE(0x0002) | SWP_NOACTIVATE(0x0010))` を呼び、戻り値の真偽を返す。例外は吸収して False（初回だけログ・別フラグ）

### `keyseq/presentation/app.py`

- `place_window_below` を import し、`self.foreground_own_window = ...` の隣で `self.place_window_below = place_window_below` を注入

### `keyseq/presentation/controllers/layout_controller.py`

- `_watch_topmost_tick` で一時解除に**入った**とき（`is_dialog` が真になり `apply_keyboard_topmost()` を呼んだ直後）だけ、
  `getattr(self._app, "place_window_below", None)` が callable なら `(int(window.wm_frame(), 16), int(foreground))` で呼ぶ。例外は吸収
- 一時解除から戻るとき・それ以外の経路は変えない

### テスト

- `tests/test_input_gateway_repeat.py`: `place_window_below` の 3 ケース（API が真 → True・引数〔hwnd / above / フラグ 0x0013〕の確認 / API が偽 → False / 例外 → False・ログ 1 回）。非 Windows → False もあれば足す
- `tests_ui/test_app_ui_flows.py`: task_03 の監視テストに、一時解除に入る tick で `place_window_below` が（キーボードUIの HWND, ダイアログ役の HWND）で 1 回呼ばれ、戻る tick では呼ばれないことを加える（差し替えは後始末で戻す）

### 設計メモ / 制約

- `lower()`（最背面）は使わない
- 余計な整形変更・BOM / 改行コードの変更をしない（`input_gateway.py` / `app.py` は BOM 付き）

## 読むファイル

- `instructions/history/39_keyboard_ui_window.md` §4「ダイアログ表示中の一時解除」
- `keyseq/infrastructure/input_gateway.py:85-175`
- `keyseq/presentation/app.py:76-82`・`:226-234`
- `keyseq/presentation/controllers/layout_controller.py:60-150`
- `tests/test_input_gateway_repeat.py` の `foreground_own_window` のテスト（task_03 で追加した箇所）
- `tests_ui/test_app_ui_flows.py` の task_03 の監視テスト（`_watch_topmost_tick` を呼ぶもの）

## 含まない

- 正本・codebase_map の更新（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **ユーザーの実機目視**（暫定 39 §6 の 7: キーボードUIだけ手前でダイアログを開くとダイアログが上に出たまま操作でき、閉じると手前に戻る）で task_03 と合わせて完了とする。
