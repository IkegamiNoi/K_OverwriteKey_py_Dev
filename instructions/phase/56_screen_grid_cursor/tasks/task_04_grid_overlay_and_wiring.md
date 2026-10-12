# task_04_grid_overlay_and_wiring

## 目的

task_03 の `ScreenGridSession` を実際の画面とつなぐ: モニタの列挙・カーソル移動 / クリックの実体、枠の窓（重ね表示）、`app.py` での生成と `InputRouter` への注入、表示の同期、`GridKeyAction` の UI スレッドでの実行（暫定 40 §4.1・§4.5・§7・task_01「結果」の確定 1〜4）。
**infrastructure（`win32_window.py`・`input_gateway.py`）+ presentation（新規の枠の窓とコントローラ・`app.py`・`layout_controller.py`・`hook_controller.py` の最小の追加）。domain・application は不変。スキーマ不変。実装後にユーザーの実機目視。**

## 対象範囲

### `keyseq/infrastructure/win32_window.py`（既存の `_user32` / `_guarded` / `_ERROR_MESSAGES` の流儀に合わせる）

- `list_monitor_rects() -> list[tuple[tuple[int, int, int, int], bool]]`: `EnumDisplayMonitors` + `GetMonitorInfoW` の `rcMonitor`（作業領域ではない）と主かどうか（`dwFlags & MONITORINFOF_PRIMARY`）を列挙順で返す。失敗・非 Windows なら空リスト
- `make_click_through_overlay(widget_id: int) -> bool`: Tk のラッパーの HWND（`GetParent(widget_id)`）へ `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` を足す（`GetWindowLongPtrW` / `SetWindowLongPtrW`・`GWL_EXSTYLE`）。失敗・非 Windows なら False
- 定数・`_ERROR_MESSAGES` へのキーの追加

### `keyseq/infrastructure/input_gateway.py`（`InputGateway` にメソッドを追加。既存のメソッドは変えない）

- `cursor_position() -> tuple[int, int]`（`pyautogui.position()`）
- `move_cursor(x, y) -> None` / `click_at(x, y, button) -> None`（`button` = `"left"` / `"right"`）: FAILSAFE を一時的に外して戻す（既存の `_send_mouse_button` と同じ形）・**`_pause=False`** を付ける（既定の `PAUSE` は約 100ms UI を止める・task_01）。`click_at` は `moveTo` → `click`

### 新規 `keyseq/presentation/screen_grid/`（Private パッケージ・tkinter はここだけ）

- `grid_overlay_window.py` `GridOverlayWindow`
  - 最初に表示するときに作る（遅延生成）: `tk.Toplevel(root)` → `withdraw` → `overrideredirect(True)` → `-topmost` → 背景と Canvas を透過色（固定値。例 `#ff00fe`）にして `-transparentcolor` → `update_idletasks()` → `win32_window.make_click_through_overlay(winfo_id())`（task_01 の確定 4 の順）
  - `show(view: GridView)`: `view.visible` かつ `view.monitor` があれば、`geometry(f"{w}x{h}+{left}+{top}")`（負の座標可）→ 描き直し → 未表示なら `deiconify`。それ以外は `hide()`
  - `hide()`: `withdraw`。`destroy()`: 窓を壊す（アプリ終了時）
  - 描画（§7・配色等は固定値・設定にしない）: 今の段の枠の線とキー（枠の中央・枠が小さければ文字を省く・文字の大きさは枠の大きさに合わせて数段階）/ 選んだ枠の強調（太い線または色）/ 段 ≥1 では今の領域の外を暗くする（`stipple="gray50"` の塗り等・透過色と重ならない色）。座標は `view` の画面座標からモニタの左上を引いて Canvas 座標へ
- `screen_grid_controller.py` `ScreenGridController(app)`
  - `ScreenGridSession` を作る。注入: `list_monitors` = `win32_window.list_monitor_rects()` を `MonitorInfo(monitor_identifier(*rect), rect, primary)` へ変換 / `cursor_position` / `move_cursor` / `click` = `app.input_gateway` の上記メソッド / `on_view_changed` = 窓の `show(session.view())`
  - `snapshot()`: `session.snapshot()`（フックのスレッドから呼ばれる。Tk に触れない）
  - `sync()`: 表示の条件 = `app.hook.hook_active` ∧ `app.hook.custom_input_enabled` ∧ `app.hook.hook_suspend_count == 0`、対象 = `app.keymap_service.get_active_keymap(app.data)` の `id` と `grid`。`session.sync(...)` の後に窓を `show(session.view())`
  - `handle(action)`: `session.handle(action)`。カーソル移動・クリック・列挙の例外は握りつぶさず `logging` で記録し、`app._set_flash_message("枠の操作に失敗しました: …")` で知らせる（フックを止めない）
  - `shutdown()`: 窓を壊す
- `__init__.py`: `ScreenGridController` を公開

### 既存ファイルへの最小の追加

- `keyseq/presentation/app.py`: `self.screen_grid = ScreenGridController(self)` を `InputRouter` の生成より前（または `get_grid_snapshot=lambda: self.screen_grid.snapshot()` が生成後に解決される形）で作り、`InputRouter(..., get_grid_snapshot=...)` を渡す。アプリ終了の処理（既存の終了経路）で `self.screen_grid.shutdown()`
- `keyseq/presentation/controllers/layout_controller.py:158` `refresh_keyboard_window`: **先頭（キーボード表示の窓が無くて return する前）で `self._app.screen_grid.sync()` を呼ぶ**（表示の同期は 1 か所・§4.1。`screen_grid` 属性が無い場合〔起動途中〕は何もしない）。既存の処理は変えない
- `keyseq/presentation/controllers/hook_controller.py` `_execute_reserved_action`: `GridKeyAction` なら、`hook_active ∧ custom_input_enabled` のときだけ `self._app.screen_grid.handle(action)` を呼んで return（`action_executor` へ渡さない）

### テスト

- `tests/` に追加: `InputGateway.move_cursor` / `click_at` が pyautogui を `_pause=False` で呼び、FAILSAFE を戻すこと（pyautogui を mock）/ `cursor_position`
- `tests/` に追加: `win32_window.list_monitor_rects` と `make_click_through_overlay` が非 Windows または Win32 の失敗で空 / False を返し例外を出さないこと（`_user32` を mock・既存の win32_window のテストがあればその書き方に合わせる）
- `tests_ui/` に新規 `test_screen_grid_overlay.py`: 偽の monitors / cursor / click を注入した `ScreenGridController`（または App 上で `input_gateway`・`list_monitor_rects` を mock）で、枠 ON の keymap がアクティブ ∧ フック動作中で `sync` すると窓が表示され、フック停止・一時停止・枠 OFF の keymap への切替で隠れる / `GridKeyAction` の実行で `move_cursor` / `click` が呼ばれる / 停止中の `GridKeyAction` は無視される / モニタ 0 個でも例外にならず窓は隠れたまま
- 既存の tests_ui が窓の生成で壊れないこと（遅延生成なので、枠 ON の keymap が無いテストでは窓を作らない）

### 設計メモ / 制約

- presentation から ctypes を直接呼ばない（Win32 は `win32_window.py`・phase 55 の方針）。pyautogui は `input_gateway.py` だけ（Mac 対応の予定のため既存のマウス操作と同じ経路・task_01 のユーザー判断）
- **自アプリの窓が前面のとき `tk.Toplevel` の作成で前面を取られる**（task_01 の発見）。遅延生成なので通常は別アプリが前面のときに作られるが、自アプリが前面で作られた場合の挙動は実機目視で確かめる（対策は実機の結果を見てから・本タスクで先回りしない）
- `sync` は UI スレッドだけで呼ぶ。`snapshot` は Tk に触れない
- ファイルは 300 行以内を目安に分ける

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §4.1・§4.5・§7
- `instructions/phase/56_screen_grid_cursor/tasks/task_01_display_coordinate_spike.md`「結果」節（確定 1〜4）
- `keyseq/application/screen_grid_session.py`（全体・使う API）
- `keyseq/infrastructure/win32_window.py`（全体・編集対象）
- `keyseq/infrastructure/input_gateway.py:1-20`・`:191-200`・`:325-375`
- `keyseq/presentation/app.py:125-200`（生成順と InputRouter）と終了処理（`grep -n "def _on_close\|destroy\|begin_shutdown" keyseq/presentation/app.py` で該当箇所だけ）
- `keyseq/presentation/controllers/layout_controller.py:150-175`・`keyseq/presentation/controllers/hook_controller.py:300-320`
- `keyseq/presentation/hover_tooltip.py:40-55`（枠なし・最前面の窓の前例）
- テストの手本: `tests_ui/` の App を使う既存テスト 1 本の冒頭 60 行（例 `tests_ui/test_app_ui_flows.py` の setUp）

## 含まない

- ダイアログの「枠を使う」・`grid` の作成（task_05）/ 編集の窓（task_06）
- 自アプリが前面のときの前面の取り戻し等の対策（実機の結果を見てから判断）
- 正本への反映・`codebase_map.md`（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストのモジュールが pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `discover -s tests_ui`（1 本ずつ）/ `-m tests.smoke_app` が全 pass
- **ユーザーの実機目視**（JSON の keymap に `"grid": {"enabled": true}` を手で足して起動。手順はメインが用意する）:
  枠 ON の keymap をアクティブにしてフック開始で枠が出る（カーソルのある画面・3×4）/ キーで強調とカーソル移動 / Space で 3×3 / Esc・BackSpace で戻る / Enter で左・Shift+Enter で右クリックして最上段へ / Tab で別の画面（負の y の画面を含む）/
  フック停止・一時停止・別の keymap への切替・ダイアログ表示で消える / 枠の表示中に前面のアプリのフォーカスが移らない・クリックが素通りする / 最上段の Esc はアプリへ届き BackSpace は届かない / ctrl+c 等は効く
- フック動作中のクリック所要時間を一度ログで確かめる（task_01 の注記）

## 完了条件

- 上記確認 pass・**reviewer 採用**・ユーザーの実機目視で問題なし
