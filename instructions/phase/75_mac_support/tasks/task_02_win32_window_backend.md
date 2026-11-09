# task_02_win32_window_backend

## 目的

暫定 57 §3.2・§3.3 の段階 ① の 2 番目。`win32_window.py` と `app_relaunch.py` を `os_backend/windows/` へ移動し、`WindowBackend` / `AppIdentity` と、`TkKeyTranslator` のうち VK 変換の 2 メソッドの裏へ入れる。

**レイヤ制約**: infrastructure・presentation の参照箇所・`main.py`・テスト。domain / application 不変・JSON スキーマ不変・Windows の動作不変。テストの件数を減らさない（基準 tests 1961 / tests_ui 1270）。

## 対象範囲

### `keyseq/infrastructure/os_backend/contracts.py` に追加

窓を受ける引数は `tkinter.Misc`。窓の識別子は不透明な値（`object`）で、等値比較と `place_window_below` の引数にだけ使う（§3.2「HWND の int を Protocol に出さない」）。

- `class WindowBackend(Protocol)`:
  - `is_own_process_foreground(self) -> bool`
  - `foreground_own_window(self) -> object | None`
  - `window_handle(self, window: tkinter.Misc) -> object`
  - `place_window_below(self, window: tkinter.Misc, above: object) -> bool`
  - `list_monitor_rects(self) -> list[tuple[tuple[int, int, int, int], bool]]`
  - `make_click_through_overlay(self, window: tkinter.Misc) -> bool`
  - `is_mouse_button_down(self) -> bool` / `is_shift_down(self) -> bool` / `is_ctrl_alt_win_down(self) -> bool`
- `class TkKeyTranslator(Protocol)`: `vk_to_scan_code(self, vk: int) -> int | None` / `vk_to_char(self, vk: int) -> str`（残りは task_04）
- `class AppIdentity(Protocol)`: `apply_process_identity(self, app_id: str) -> bool` / `relaunch(self, startup_cwd: str) -> OSError | None`（`app_data_root` は task_12）
- `OsBackend` に `window: WindowBackend` / `tk_keys: TkKeyTranslator` / `app: AppIdentity` を追加（`__all__` にも 3 つの Protocol を追加）

### 移動（旧パスに横流しを残さない）

- `keyseq/infrastructure/win32_window.py` → `os_backend/windows/win32_window.py`。`_guarded` の `sys.platform` の分岐と `import sys` を削除する（他のロジック・ログ文言は変えない）
- `keyseq/infrastructure/app_relaunch.py` → `os_backend/windows/app_relaunch.py`（中身は不変）

### `os_backend/windows/backend.py`

`WindowsWindowBackend` / `WindowsTkKeyTranslator` / `WindowsAppIdentity` を追加し、`create_backend` で組み立てる。モジュール属性経由で委譲する。

- `window_handle(window)` = `int(window.wm_frame(), 16)`
- `place_window_below(window, above)` = `win32_window.place_window_below(int(window.wm_frame(), 16), above)`
- `make_click_through_overlay(window)` = `win32_window.make_click_through_overlay(window.winfo_id())`
- `apply_process_identity` = `set_app_user_model_id`

### 呼び出し側（`win32_window` / `app_relaunch` の import をやめ、`from keyseq.infrastructure.os_backend import get_backend`）

- `main.py`: `get_backend().app.apply_process_identity(APP_USER_MODEL_ID)` / `get_backend().app.relaunch(startup_cwd)`
- `keyseq/infrastructure/input_gateway.py:341-342`: `get_backend().window.is_shift_down()` / `is_ctrl_alt_win_down()`
- `keyseq/presentation/app.py`: 104〜107 行の import をやめる。`__init__` 内で `window_backend = get_backend().window` を取り、179・290〜292・301 行で従来の関数の代わりに同じ名前のメソッドを渡す
- `keyseq/presentation/controllers/layout_controller.py:165-186`: `backend = get_backend().window` を使い、`main = backend.window_handle(self._app)` / `keyboard = backend.window_handle(window)`・`is_dialog = foreground not in (main, keyboard)`・`place_below(window, foreground)`。分岐と順序は変えない
- `keyseq/presentation/keyboard_window.py:622,651`: `get_backend().window.is_shift_down()` / `get_backend().tk_keys.vk_to_scan_code(vk)`
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:467,473`: `get_backend().tk_keys.…`
- `keyseq/presentation/screen_grid/grid_overlay_window.py:42`: `get_backend().window.make_click_through_overlay(window)`
- `keyseq/presentation/screen_grid/screen_grid_controller.py:38`: `get_backend().window.list_monitor_rects()`

### テスト

- `tests/test_os_backend_boundary.py`: 許可リストから `infrastructure/win32_window.py` の 2 項目を消す
- `tests/test_os_backend_contracts.py`: `WindowBackend` / `TkKeyTranslator` / `AppIdentity` と Windows 実装の一致を追加。`window_handle` / `place_window_below` / `make_click_through_overlay` の窓の変換のテストを追加
- `tests/test_win32_window.py` / `tests/test_win32_window_screen_grid.py`: import を `from keyseq.infrastructure.os_backend.windows import win32_window` にし、`win32_window.sys` の patch を除去する。`test_non_windows_*` の 5 件は「`ctypes.WinDLL` が使えない環境（`side_effect=OSError` または `create=True` で None）では既定値を返す」検証へ置き換える（削除しない）
- `tests/test_app_relaunch.py`: 新パスへ
- `tests/test_no_japanese_ui_literals.py:30`: 許可リストのパスを新パスへ
- `tests/test_input_gateway_send.py`（`input_gateway.win32_window` の patch 9 か所）/ `tests_ui/test_keyboard_window_scan_code.py` / `tests_ui/test_screen_grid_overlay.py` / `tests_ui/test_task06_keymap_management_ui.py`: 各モジュールの `get_backend` を、該当属性に Mock を持つオブジェクト（`SimpleNamespace(window=…, tk_keys=…)`）を返す patch へ置き換える
- `tests_ui/test_key_hold_presentation.py:92`: `get_backend().window.is_own_process_foreground` と比較する（束縛メソッドなので `assertIs` ではなく `assertEqual`）
- `tests_ui/test_app_ui_flows.py:2449` / `tests_ui/test_help_window.py:575`: `place_window_below` の第 1 引数の期待値を窓オブジェクトへ
- 他に旧パスや `set_app_user_model_id` を参照するテストがあれば同様に直す（`git grep` で確認）

### `instructions/common/codebase_map.md`

36・37・7・9・135・818・831・989 行付近のパスと呼び方を新しいものへ直す。

### 設計メモ / 制約

- 既存ファイルの編集は apply_patch（Python で編集しない）。`inspect` / 互換の `getattr` を足さない
- 新規コードのコメント・文字列は英語

## 読むファイル

- `instructions/history/57_mac_support.md` §3.1〜§3.3
- `keyseq/infrastructure/os_backend/`（task_01 の実装）
- `keyseq/infrastructure/win32_window.py`・`app_relaunch.py`
- 呼び出し側は上に挙げた行の周辺のみ
- `tests/test_os_backend_contracts.py`・`tests/test_input_gateway_send.py:90-155`

## 含まない

- `input_gateway` の分解（task_03）
- `modal.py` と `tk_keys.py` の切替・`TkKeyTranslator` の残り・`action_dialog.py`（task_04）
- `app_data_root`（task_12）・`spec_detail/` の更新（task_14）

## 確認

`..\..\..\.venv\Scripts\python.exe` で（verifier）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`: 失敗 0・1961 件以上・skip 7
- `-m unittest discover -s tests_ui`: 失敗 0・1270 件以上
- `-m tests.smoke_app` が pass
- `git grep -n "infrastructure import win32_window\|infrastructure\.win32_window\|infrastructure\.app_relaunch"` が keyseq / tests / tests_ui / main.py で 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は段階 ① の完了時にまとめて行う（キーボードUIの常に手前・カーソルグリッド・言語の再起動）。
