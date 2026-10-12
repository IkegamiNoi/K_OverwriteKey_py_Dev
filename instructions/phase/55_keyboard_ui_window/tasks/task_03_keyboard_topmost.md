# task_03_keyboard_topmost

## 目的

メインの表示欄に「キーボードUIを常に手前」を加え、アプリのダイアログが前面にある間はキーボードUIの「手前」を一時的に外す（暫定 39 §2-2・§4・§6 の 3〜7・11）。
**infrastructure に 1 関数追加・presentation（ui_vars / 表示欄 2 つ / app.py の注入 / layout_controller.py）。domain / application 不変・スキーマ不変（保存しない）。**

### 前提の実測（2026-10-12・メイン）

素の Tk で `tk.Tk()` の子 `tk.Toplevel` の枠（`wm_frame()`）の `GetWindow(hwnd, GW_OWNER)` は None（`-topmost` 付与後も None）。
キーボードUIはメインの所有窓ではない → 両方手前で「アクティブな方が上」の前提は成立（最終確認は実機目視 §6 の 5）。

## 対象範囲

### `keyseq/infrastructure/input_gateway.py`

- `foreground_own_window() -> int | None` を `is_own_process_foreground` の近くに追加: 前面の窓（`GetForegroundWindow`）が自プロセスならその HWND（int）、それ以外・前面なし・非 Windows・例外は None。
  `_foreground_process_api()` を再利用する。例外のログは初回だけ（別フラグ・既存の作法どおり）。`is_own_process_foreground` は変えない

### `keyseq/presentation/app.py`

- `foreground_own_window` を import し、`self.is_mouse_button_down = ...` の隣で `self.foreground_own_window = foreground_own_window` を注入する

### `keyseq/presentation/ui_vars.py`

- `self.keyboard_always_on_top_var = tk.BooleanVar(master=master, value=False)`（`always_on_top_var` の隣）。保存・読込の対象にしない

### 表示欄 `views/full_view/display_frame.py`・`views/compact_view/display_frame.py`

- 「キーボードUI」ボタンの行の下（row 3・column 0・`columnspan=2`・`sticky="w"`・`pady=(10, 0)`）に
  `ttk.Checkbutton(self, text="キーボードUIを常に手前", variable=app.ui_vars.keyboard_always_on_top_var, command=app.layout.on_keyboard_topmost_changed)`

### `keyseq/presentation/controllers/layout_controller.py`

- 状態: `_topmost_watch_job = None` / `_topmost_released = False`（一時解除中）
- `on_keyboard_topmost_changed()`: `_topmost_released = False` にして `apply_keyboard_topmost()`、続けて `_update_topmost_watch()`
- `apply_keyboard_topmost()`: キーボードUIが開いていれば `-topmost` を実効値（チェック ∧ ¬`_topmost_released`）にする。閉じていれば何もしない。例外（TclError 等）は吸収
- `open_keyboard_window()`: 既存窓の再表示・新規作成の**両経路の最後**で `apply_keyboard_topmost()` と `_update_topmost_watch()` を呼ぶ（メニュー「キーボードUIを開く」も同じ関数）
- `_update_topmost_watch()`: チェック ON かつキーボードUIが開いていれば監視を開始（未開始なら `self._app.after(200, self._watch_topmost_tick)`）。条件外なら予約を取り消し、`_topmost_released = False`
- `_watch_topmost_tick()`: 予約を消す。条件外なら止める（`_topmost_released = False`）。
  前面の窓 = `getattr(self._app, "foreground_own_window", None)` を呼んだ結果。ダイアログが前面 = 結果が None でなく、メイン（`int(self._app.wm_frame(), 16)`）でもキーボードUI（`int(window.wm_frame(), 16)`）でもない。
  `_topmost_released` と違えば更新して `apply_keyboard_topmost()`（状態が変わったときだけ当てる）。最後に 200ms 後へ置き直す。例外は吸収して置き直す
- `on_keyboard_window_closed()`: 監視の予約を取り消し `_topmost_released = False`
- 監視の間隔 200ms は定数（モジュール定数 `_TOPMOST_WATCH_MS = 200`）

### テスト

- `tests/test_input_gateway_repeat.py`: `foreground_own_window` の 4 ケース（自プロセス → HWND / 他プロセス → None / 前面なし → None / 例外 → None・ログ 1 回）。既存 `OwnProcessForegroundTests` の差し替え手法にならう
- `tests_ui/test_app_ui_flows.py`（既存のキーボードUIテストの近く・後始末で変数を False に戻し窓を閉じる）:
  - フル / 省略の表示欄の両方にチェックがあり、同じ変数を指す
  - 開いた状態でチェック ON → キーボードUIの `attributes("-topmost")` が真・OFF → 偽
  - 閉じた状態で ON → 開くと真
  - 監視: `foreground_own_window` を「メイン・キーボードUI以外の HWND を返す」差し替えにして `_watch_topmost_tick()` を呼ぶと偽、メインの HWND を返す差し替えで呼ぶと真に戻る
  - チェック OFF / 窓を閉じると監視の予約が None になる

### 設計メモ / 制約

- メインの「常に手前」（`app._apply_always_on_top`）は変えない
- presentation から ctypes を呼ばない（判定は App が注入した関数のみ）
- ダイアログ側（`modal.py` の `grab_modal` / messagebox / ファイル選択）は変えない
- 余計な整形変更・BOM / 改行コードの変更をしない

## 読むファイル

- `instructions/history/39_keyboard_ui_window.md` §2-2・§4
- `keyseq/infrastructure/input_gateway.py:85-150`（前面窓 API・`is_own_process_foreground`・`is_mouse_button_down`）
- `keyseq/presentation/app.py:76-81`・`:226-232`・`:543-549`（注入箇所・`_apply_always_on_top`）
- `keyseq/presentation/ui_vars.py`（全体）
- `keyseq/presentation/views/full_view/display_frame.py`・`views/compact_view/display_frame.py`（全体・各 40 行程度）
- `keyseq/presentation/controllers/layout_controller.py:1-80`（編集対象の範囲）
- `tests/test_input_gateway_repeat.py:96-210`（手本）
- `tests_ui/test_app_ui_flows.py:2324-2400`（既存のキーボードUIテスト）

## 含まない

- 前面化の保存（スコープ外）
- 正本・codebase_map の更新（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（新規 4 ケース以上）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（既存の窓サイズのテスト〔`test_full_view_min_height.py`・省略表示の最小の高さ〕を含む = §6 の 11）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **本タスクでユーザーの実機目視を行う**（暫定 39 §6 の 3〜7・11）: 表示欄の 2 か所のチェックの連動 / ON で手前に残る・閉じた状態で ON → 開くと手前・OFF で解除 /
  両方手前でアクティブな方が上 / 再起動で OFF / キーボードUIだけ手前で独自ダイアログ・messagebox・ファイル選択が上に出て操作でき閉じると戻る（キーボードUIからの割当エラーも）/ 表示欄の行追加で省略表示・フル表示の見た目が崩れない。
