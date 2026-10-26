# task_03_hook_font_topmost

## 目的

ヘルプの窓とアプリの他部分のつなぎを足す: フィルターの入力欄のフォーカスでのフック停止（暫定 53 §4.4）・
フォントサイズ変更の通知（§4.5）・メインの「常に手前」の追従とキーボードUIの再同期（§4.1）・アプリの終了時にヘルプの窓を閉じる（§4.1）。
**presentation 限定（`help/` の窓と管理役・`app.py` の 3 か所・`LayoutController` に窓口 1 つ）。見張りの判定条件（`_watch_topmost_tick`）は変えない。
フックは `app.hook` の既存の窓口（`suspend_hook_for_dialog` / `resume_hook_after_dialog`）だけを使う。domain / application 不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/help/help_window.py`（task_02 の窓）

- フィルターの入力欄のフック停止（§4.4）:
  - 入力欄の `<FocusIn>` で、「止めている」の印が下りていれば `app.hook.suspend_hook_for_dialog()`（**引数なし**）を呼び、印を立てる。
  - 印が立っている間に、入力欄の `<FocusOut>`・入力欄の `<Destroy>`・窓の `<Destroy>` の**先に来た方**で `app.hook.resume_hook_after_dialog()` を**ちょうど 1 回**呼び、印を下ろす（`<Destroy>` は `event.widget` が自分自身のときだけ見る。`hook_controller.py:58-66` の書き方にならう）。
  - Alt+Tab のたびに FocusOut / FocusIn が来て停止・再開を繰り返すのは正しい挙動（印で 1 対 1 を守るだけ）。
  - 入力欄以外（Notebook・本文・見出し）にフォーカスがあるときはフックに触らない。窓を開いただけでは止めない（初期フォーカスは Notebook のまま）。
  - 窓はフックの窓口を管理役経由で受け取る（窓が `app` 全体に依存しすぎないよう、`suspend` / `resume` の 2 つの callable を渡す形が望ましい）。
- `on_font_changed()`（task_02 で用意）の中身を仕上げる: 名前付きフォントから派生させた独自フォント（見出しの太字等）を作り直し、表示を崩さない（開閉・フィルター・ハイライトの状態を保つ）。
- `apply_topmost(enabled: bool) -> None`: `-topmost` を設定（例外は吸収）。

### `keyseq/presentation/help/help_window_controller.py`

- 窓を作るとき・`open` で前面化するときに、`app.ui_vars.always_on_top_var` の値で窓の `-topmost` を設定する（§4.1）。
- `apply_topmost() -> None`: 開いていれば現在の `always_on_top_var` の値を窓へ当てる。
- `on_font_changed() -> None`: 開いていれば窓の `on_font_changed()` を呼ぶ。
- `close()` は既存（task_02）のものを使う。

### `keyseq/presentation/controllers/layout_controller.py`

- 窓口 `resync_keyboard_topmost() -> None` を足す（§4.1）: キーボードUIが開いていて `keyboard_always_on_top_var` が ON のときだけ、`_topmost_released = False` にし、`apply_keyboard_topmost()` と `_update_topmost_watch()` を呼ぶ（= 一時解除の状態を捨て、次の見張りの判定で手前の属性と重なり順〔前面の窓の下へ置く〕をやり直させる）。それ以外は何もしない。
- `_watch_topmost_tick`・`_update_topmost_watch`・`apply_keyboard_topmost` の判定条件は**変えない**。

### `keyseq/presentation/app.py`

- `_apply_always_on_top`: 既存の `self.attributes("-topmost", ...)` の後に、`self.help.apply_topmost()` → `self.layout.resync_keyboard_topmost()` を呼ぶ（それぞれ例外で止めない。既存の try の書き方にならう）。
- `_apply_font_delta`: 既存の `on_font_changed` 呼び出し群に `self.help.on_font_changed()` を足す。
- `on_close`: キーボードUIの窓を閉じる処理の隣（`self.hook.stop_hook()` より前）で `self.help.close()` を呼ぶ（例外で終了を妨げない）。`begin_shutdown` 後の再開は `start_hook` 側が既に止めるため、ヘルプの破棄で `resume_hook_after_dialog` が走ってもフックは再開しない（この前提をテストで確かめる）。

### `tests_ui/test_help_window.py`（task_02 のファイルに追加）または `tests_ui/test_help_window_integration.py`（新規）

- フック（§10-5）: `app.hook.suspend_hook_for_dialog` / `resume_hook_after_dialog` を spy（`patch.object(..., wraps=...)`）して確かめる
  - 窓を開いただけでは呼ばれない
  - 入力欄の FocusIn で suspend 1 回・FocusOut で resume 1 回（`get_hook_pause_count()` が 1 → 0）
  - FocusIn が 2 回続いても suspend は 1 回
  - 入力欄にフォーカスを持ったまま窓を破棄（× / `close()`）→ resume がちょうど 1 回・カウント 0
  - 本文・Notebook へのフォーカスでは呼ばれない
- フォント（§10-6）: `set_ui_font_delta(+2)` → 開いている窓の派生フォントの大きさが追従・開閉とフィルターの状態が保たれる（終了時に 0 へ戻す）
- 常に手前（§4.1・§10-4a）:
  - `always_on_top_var` ON で開くとヘルプの `-topmost` が 1・OFF なら 0。開いたまま切り替えると追従
  - キーボードUIを開き両方 ON・ヘルプを開いた状態で、メインを OFF にしたとき `resync_keyboard_topmost` が呼ばれ `_topmost_released` が False に戻り、その後 `_watch_topmost_tick` を 1 回進めた結果が見張りの規則どおりになる（**見張りの判定の前と後のそれぞれ**で `-topmost` を確かめる。前景の窓は `foreground_own_window` を patch してヘルプの窓の hwnd を返す）
  - `resync_keyboard_topmost` はキーボードUIが閉じている・`keyboard_always_on_top_var` OFF のとき何もしない
- 終了: `on_close` の流れ（`confirm_save_if_dirty` を True に patch・`destroy` 等は既存テストの作法にならい実際に App を壊さないよう patch）でヘルプの `close` が呼ばれ、入力欄にフォーカスがあってもフックが再開しない

### 設計メモ / 制約

- 停止の印は窓ごとに持つ（窓を作り直したら新しい印）。
- `suspend_hook_for_dialog(window)` の自動解除（window 引数）は使わない（入力欄のフォーカスに合わせるため、自前の印で 1 回だけ解除する）。
- 既存の tests_ui（特に `test_hook_controller_teardown`・キーボードUIの常に手前の既存テスト）を壊さない。

## 読むファイル

- `instructions/history/53_help_window.md` §4.1（74-86 行）・§4.4〜§4.5（112-126 行）
- task_02 の成果: `keyseq/presentation/help/help_window.py`・`help_window_controller.py`（編集対象）
- `keyseq/presentation/controllers/hook_controller.py` 48-84 行（停止と再開）・113-130 行（終了中の扱い）
- `keyseq/presentation/controllers/layout_controller.py` 90-175 行（常に手前と見張り）
- `keyseq/presentation/app.py` 468-482 行（`_apply_font_delta`）・613-619 行（`_apply_always_on_top`）・758-780 行（`on_close`）
- 手本: キーボードUIの常に手前の既存 tests_ui（`grep -l "_watch_topmost_tick" tests_ui` で探す。該当の数十行だけ）

## 含まない

- ダイアログの「?」（task_04）・ライセンスの窓の常に手前の追従（task_05）
- 本文の執筆（task_06）・正本反映（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加した tests_ui のモジュール単独 pass
- tests 全体 pass / tests_ui 全体（既知の負債 `test_compact_window` の 1 件を除き pass）/ smoke pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_08 でまとめて実施（Alt+Tab での停止・再開、キーボードUIとの重なり）
