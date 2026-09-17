# task_05d_window_width_resize_save

## 目的

task_05c の実機目視を受けた暫定仕様 16 **v0.5**（ユーザー確定 2026-09-17）を実装する。
①**ウィンドウ幅は変わるたびに 500ms 間引いて保存**し、終了時の保存とドラッグ時の同時書き込みを廃止（§2-13・§3-8「保存の契機」・§5-16）
②**ユーザーが幅を変えたら自動決定幅を無効化**（自動決定幅へ手で戻した幅も保存する）
③**`write_startup` の失敗ダイアログ中はフックを止める**（正本 `key_input.md` §7.2 への適合。既存呼び出し元も同じ扱いになる）。
**presentation 限定**。domain / application / infrastructure・JSON スキーマは変更しない（キー `full_view_window_width` の意味も不変）。

## 対象範囲（presentation 3 ファイル + tests_ui 2〜3 ファイル）

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

1. **定数** `WINDOW_WIDTH_SAVE_DELAY_MS = 500`（このモジュールに 1 か所。`pane_width_rules.py` へ置いてもよい）。
2. **監視**: `install()` で `self.app.bind("<Configure>", self._on_window_configure, add="+")`。
   `_on_window_configure(event)`: `event.widget is not self.app` なら return。`event.width` が前回扱った幅（属性 `_last_window_width: int | None`）と
   同じなら return。異なれば記録し、予約済み（属性 `_width_save_id: str | None`）を `after_cancel` して `after(WINDOW_WIDTH_SAVE_DELAY_MS, self._save_window_width)` で予約し直す。
3. **予約の実行** `_save_window_width() -> None`（§3-8 の 3.）: `_width_save_id = None` にしてから、
   `not self._is_ready()` / `app.wm_state() != "normal"` / `app._compact_mode` のいずれかなら **何もせず** return（自動決定幅も触らない）。
   `width = app.winfo_width()`。`width == self._auto_window_width` なら return。
   異なれば `self._auto_window_width = None`（無効化）。`app._startup_settings.get(WINDOW_WIDTH_KEY) == width` なら return。
   それ以外は `app.startup_io.write_startup({WINDOW_WIDTH_KEY: width})`（戻り値は見ない）。
   App が破棄済みで `tk.TclError` になる場合は何もしない（破棄後の実行の防御）。
4. **予約の取消** `cancel_window_width_save() -> None`: 予約中なら `after_cancel` して `None` に戻す。
5. **ドラッグ保存からウィンドウ幅を外す**: `_on_desired_changed` の `write_startup` 引数は `{PANE_WIDTHS_KEY: {...}}` のみ（v0.4 の同時書き込みを削除）。
6. **削除**: `window_width_to_save()` / `save_window_width_on_close()`、および不要になった `re` import。
7. 自動決定幅の記録（`apply_initial_widths` 直後は常に / `apply_layout` で geometry を変えたときだけ）は**変えない**。
8. 250 行を超える場合は同フォルダへ責務単位で分割してよい（親フォルダ方式・`__init__.py` の公開面を維持）。分割したら報告する。

### `keyseq/presentation/app.py`

- `on_close`: `width = self.pane_layout.window_width_to_save()` を削除し、`confirm_save_if_dirty` 通過直後に
  `self.pane_layout.cancel_window_width_save()` を呼ぶ。`try` 内の `save_window_width_on_close(width)` を削除。
  `begin_shutdown` → キーボードウィンドウ破棄 → `stop_hook` → `finally: destroy` の順序は維持。

### `keyseq/presentation/controllers/config_io/startup_io.py`

- `write_startup` の `except` 節: `self._app.hook.suspend_hook_for_dialog()` → `try: messagebox.showerror(...)` →
  `finally: self._app.hook.resume_hook_after_dialog()` → `return False`。成功経路・戻り値・`_startup_settings` の扱いは変えない。

### `tests_ui/test_pane_window_width_persistence.py`（v0.5 へ書き換え）

v0.4 の終了時保存・ドラッグ同時書き込みのテスト（`_close` 系の保存アサーション・`test_drag_includes_manual_window_width_in_one_write` 等）は
v0.5 の条項に合わせて置き換える（仕様変更に伴う置換であり、弱化ではない）。起動時の復元（§5-15）・780 基準・間引き（§5-17）のテストは**変えない**。
予約は `after` を待たずに `_save_window_width()` を直接呼んで検査する（実時間待ちに依存しない）。

1. **予約**: `_on_window_configure` に幅の違う `event.widget is app` のイベントを 3 回 → `after` の予約が最後の 1 件だけ残る（`after_cancel` 2 回）/
   高さだけ違う（幅同じ）→ 予約しない / `event.widget` が子ウィジェット → 予約しない。
2. **保存**: 縁で幅を変える → `_save_window_width()` → `write_startup({"full_view_window_width": 幅})` 1 回。
   保存値と同じ / 自動決定幅と同じ / `wm_state` を `"zoomed"`・`"iconic"` に patch / 省略表示中 / 初回適用前（`desired = None`）→ 呼ばれない。
3. **自動決定幅の無効化**: 起動時の幅 W0 → W0+220 で保存 → W0 へ戻して `_save_window_width()` → `write_startup({... : W0})`。
   `wm_state` を `"zoomed"` に patch した状態で幅を変えて実行 → 自動決定幅は変わらない（その後 W0 に戻すと書かれない）。
   画面幅 patch で切り詰めて起動 → 何もせず `_save_window_width()` → 呼ばれない（`ClampedWidthStartupTest` を v0.5 の形に置換）。
   フォントを上げて自動で広がった → `_save_window_width()` → 呼ばれない。
4. **ドラッグ**: 縁で幅を変えてからサッシュをドラッグ → `write_startup` の引数に `full_view_window_width` が**含まれない**。
5. **終了**: 幅を変えて予約がある状態で `on_close()`（`confirm_save_if_dirty` True・`destroy` / `stop_hook` / `write_startup` を patch）→
   `write_startup` は呼ばれない・予約は取り消される（`_width_save_id is None`）・`destroy` が最後。
   `confirm_save_if_dirty` False → 予約は残り `destroy` も呼ばれない。`stop_hook` が例外 → `destroy` は呼ばれる。

### `tests_ui/test_startup_font_characterization.py`（追記）

- 保存失敗時（既存 `test_write_startup_returns_false_and_preserves_startup_settings_on_save_failure` の型）:
  `showerror` 実行中に `hook.get_hook_pause_count() == 1`、戻った後は 0。`showerror` が例外を投げても 0 に戻る。成功時は停止要求が発生しない。

### 設計メモ / 制約

- **実 `config/config.json` を書かない**: `tests_ui` の他モジュールでも、幅を変えて `update()` するテストで予約が実行されうる。
  確認で `config` に差分が出たら、該当テストの後始末で `app.pane_layout.cancel_window_width_save()` を呼ぶ（アサーションは変えない）。
- `tests_ui/test_pane_widths_persistence.py` の準備で `_auto_window_width` を拡幅後の幅にしている処理（task_05c）は、v0.5 では不要だが**残してよい**（アサーション不変）。
- 判定は予約の**実行時**に行う（イベント時に `wm_state` を見ない。最大化への切り替え途中の値を拾わないため）。

## 読むファイル

- 編集対象（全体）: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` / `tests_ui/test_pane_window_width_persistence.py`
- `keyseq/presentation/app.py:336-392`（省略表示の切替）/ `:541-556`（`on_close`）
- `keyseq/presentation/controllers/config_io/startup_io.py:39-59`（`write_startup`）
- `keyseq/presentation/controllers/hook_controller.py:26-59`（`suspend_hook_for_dialog` / `resume_hook_after_dialog` / `get_hook_pause_count`）
- 仕様: `instructions/history/16_full_view_resizable_panes.md` の §3-8「保存する値」〜「自動で決めた幅は保存しない」・§5-16（`rg -n "§3-8|^16\. " ` で位置特定）
- 手本（範囲のみ）: `tests_ui/test_startup_font_characterization.py:82-106`

## 含まない

- ヘッダ幅（idea_21）/ 縦方向の最小サイズ（idea_22）/ ウィンドウの高さ・位置・最大化状態の保存（§6）
- 正本 `features.md` / `data_schema.md` / `key_input.md` / `codebase_map.md` の更新（**task_06**）
- 実機目視（本タスク完了後に **task_05 で再実施**: 幅変更 → 最大化 → 閉じる → 再起動 / 自動決定幅へ戻す / 省略表示の往復）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_pane_window_width_persistence tests_ui.test_startup_font_characterization -v` が全 pass（上記 1〜5 と追記分）。
3. `-m unittest tests_ui.test_full_view_panes tests_ui.test_pane_drag_and_window_min tests_ui.test_pane_widths_persistence -v` が 6 / 12 / 13 pass（無変更）。
4. `-m unittest discover -s tests` が 445 OK（skip 7・無変更）/ `-m unittest discover -s tests_ui` が全 OK（件数は 405 ± 置換分を報告）。
5. `-m tests.smoke_app` が SMOKE OK。`git status --short config` が空。
6. `rg -n "window_width_to_save|save_window_width_on_close" keyseq tests tests_ui` が 0 件。
7. `reviewer` が「判定は予約の実行時」「状態条件で書かないときは自動決定幅を無効化しない」「失敗ダイアログのフック停止が finally で解除」をコードで確認する。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_05 で再実施**（幅変更 → 最大化 → 閉じる → 再起動で変えた幅 / 自動決定幅へ戻す / 省略表示の往復で 270 が保存されない）。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（コントローラは分割なし・256 行）。
- `verifier` 1 回目: 全 pass（`tests` 445 OK skip 7 / `tests_ui` 413 OK / smoke OK / config 差分なし / 旧メソッド参照 0 件）。
  ただし `tests_ui` の stderr に破棄後の `after` 実行（`_save_window_width`）が出た（テストが `on_close` を経ずに `destroy`）。
- **メインで追加**（タスク定義外・数行）: App の `<Destroy>` で保存予約を取り消す `_on_window_destroy`（§3-8「破棄後に実行させない」の防御）。
- `verifier` 2 回目: 同件数で全 pass。stderr の残り 4 件は既存の `_clear_flash_message`（本タスクと無関係）で、`_save_window_width` 由来は 0 件（メインで実測）。
- `reviewer` = 完了可。`_on_window_destroy` は採用。軽微（任意）: 同追加の専用テストなし / 256 行（目安 250 をわずかに超過）→ 対応不要と判断。
