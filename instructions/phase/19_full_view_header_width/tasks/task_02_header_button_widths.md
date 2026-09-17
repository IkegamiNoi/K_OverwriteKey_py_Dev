# task_02_header_button_widths

## 目的

暫定仕様 17（v0.3）§3-3・§3-4 を実装する。①**フル表示のヘッダで文言が切り替わるボタン 4 つ**（停止キー取得 / トグルキー取得 / フック開始 / 通常トリガー切替）の
`width` を、取りうる文言の最大幅で固定する（起動時・フォント変更時。**省略表示のボタンは固定しない** §2-5）
②文言を中立な定数モジュールへ 1 か所にまとめる ③キーボード選択のドロップダウンを `width=12`（フル・省略の両方）にする。
**presentation 限定**。ヘッダ幅のウィンドウ最小幅への組込みは task_03。スキーマ不変。

## 対象範囲（presentation 8 ファイル + tests_ui 1 新規）

### `keyseq/presentation/hook_button_texts.py`（新規・定数のみ）

- `CAPTURE_IDLE_TEXT = "キー入力で取得"` / `CAPTURE_ACTIVE_TEXT = "取得中…（Escで停止）"` / `CAPTURE_TEXTS = (IDLE, ACTIVE)`
- `HOOK_START_TEXT = "開始（フックON）"` / `HOOK_STOP_TEXT = "停止（フックOFF）"` / `HOOK_TOGGLE_TEXTS`
- `TRIGGER_DISABLE_TEXT = "通常トリガー無効化"` / `TRIGGER_ENABLE_TEXT = "通常トリガー有効化"` / `TRIGGER_TOGGLE_TEXTS`
- `KEYBOARD_LAYOUT_COMBO_WIDTH = 12`
- import は持たない（views / controllers の双方から import してよい中立モジュール。暫定仕様17 §3-3）。

### `keyseq/presentation/controllers/button_width.py`（新規）

- `apply_fixed_button_width(button: ttk.Button, texts: Sequence[str]) -> None`: TButton スタイルのフォント
  （`tkfont.Font(root=button, font=ttk.Style(button).lookup("TButton", "font"))`。取得できなければ `TkDefaultFont`）で各文言と `"0"` を `measure` し、
  `button_width_rules.fixed_button_width_chars` の結果を `button.configure(width=...)` で当てる。文言の仮切替はしない。

### `keyseq/presentation/controllers/key_capture.py`

- `start` / `stop` の文言を `CAPTURE_ACTIVE_TEXT` / `CAPTURE_IDLE_TEXT` に置換。
- 新規 `apply_fixed_button_width() -> None`: `_capture_btn` があれば `apply_fixed_button_width(self._capture_btn, CAPTURE_TEXTS)`。
- `register_widgets` の最後で `apply_fixed_button_width()` を呼ぶ。

### `keyseq/presentation/controllers/hook_controller.py`

- `sync_hook_toggle_buttons` / `sync_trigger_toggle_buttons` の文言を定数へ置換（分岐・状態は不変）。
- `register_hook_buttons(hook_btn, trigger_btn, *, fixed_width: bool = False)`: 組と一緒にフラグを保持する（既存の `_hook_button_pairs` を使う箇所の反復は壊さない形で。
  例: 固定対象の組を別リスト `_fixed_width_button_pairs` に追加）。`fixed_width=True` なら登録時に幅を当てる。
- 新規 `apply_fixed_button_widths() -> None`: 固定対象の組だけ、フック開始に `HOOK_TOGGLE_TEXTS`、通常トリガー切替に `TRIGGER_TOGGLE_TEXTS` で幅を当てる。

### `keyseq/presentation/app.py`

- 新規 `_apply_fixed_button_widths() -> None`: `self.hook.apply_fixed_button_widths()` / `self.stop_key_capture.apply_fixed_button_width()` / `self.toggle_key_capture.apply_fixed_button_width()`。
- `_apply_font_delta`: `apply_global_theme(...)` の直後、**`self.pane_layout.on_font_changed()` より前**に `self._apply_fixed_button_widths()` を呼ぶ（省略表示中も呼ぶ）。

### Views

- `views/full_view/hook_frame.py`: 4 ボタンの初期文言を定数参照に。`register_hook_buttons(..., fixed_width=True)`。
- `views/compact_view/hook_frame.py`: 2 ボタンの初期文言を定数参照に。`register_hook_buttons` は **`fixed_width` を渡さない**（固定しない）。
- `views/full_view/display_frame.py` / `views/compact_view/display_frame.py`: Combobox の `width=KEYBOARD_LAYOUT_COMBO_WIDTH`。

### `tests_ui/test_header_button_widths.py`（新規）

`tests_ui/test_pane_window_width_persistence.py:12-50` の型（クラス単位で `ConfigService.load_startup`〔`{}`〕/ `StartupIo.write_startup` / `ConfigService.save_startup` を patch・
`theme._BASE_FONT_SIZES` の退避と復元・破棄前に `app.pane_layout.cancel_window_width_save()`）。各テストの後始末でフォントを 0 に戻し、変えた文言を元に戻す。

1. **フル表示の 4 ボタン**（`full_view.hook_frame` の `stop_key_capture_btn` / `toggle_key_capture_btn` / `hook_toggle_btn` / `trigger_toggle_btn`）: フォント −3 / 0 / ＋3 それぞれで、
   対応する文言の組の各文言を `configure(text=...)` → `update_idletasks()` しても `winfo_reqwidth()` が同じで、
   かつ同じ文言を `width` 指定なしの一時 `ttk.Button`（同じ親・破棄する）で測った要求幅以上（§5-4）。
2. **フォント変更で幅が当て直される**: フォント ＋3 にした後の `cget("width")` が、その時点のフォントで `fixed_button_width_chars` を計算した値と一致（標準の値と異なることは要求しない）。
3. **省略表示のボタンは固定しない**: `compact_view.hook_frame.hook_toggle_btn` / `trigger_toggle_btn` の `cget("width")` が未指定（`0` または空）（§2-5）。
4. **ドロップダウン**: `full_view.display_frame.keyboard_layout_combo` と `compact_view.display_frame.compact_keyboard_layout_combo` の `cget("width")` が 12（§5-6）。
5. **取得の実経路**: `stop_key_capture.start()` → ボタンの文言が `CAPTURE_ACTIVE_TEXT`・要求幅が開始前と同じ → `stop(cancel=True)` で `CAPTURE_IDLE_TEXT`（フックの停止カウンタが元に戻ること）。

### 設計メモ / 制約

- `dialogs/trigger_dialog.py` / `keymap_edit_dialog.py` の同じ文言は**変更しない**（ヘッダ外・本フェーズ対象外）。
- ボタンの `sticky` / `grid` / `pack` の配置は変えない。
- 既存テストのアサーションは変えない。`apply_global_theme` の呼び出し順は変えない。

## 読むファイル

- 編集対象（全体）: `keyseq/presentation/controllers/key_capture.py` / `views/full_view/hook_frame.py` / `views/compact_view/hook_frame.py` /
  `views/full_view/display_frame.py` / `views/compact_view/display_frame.py`
- `keyseq/presentation/controllers/hook_controller.py:1-30,60-86`
- `keyseq/presentation/app.py:270-283`（`_apply_font_delta`）/ `keyseq/presentation/theme.py:91-110`（TButton のフォント）
- `keyseq/presentation/button_width_rules.py`（task_01）
- 仕様: `instructions/history/17_full_view_header_width.md` §2-5・§3-3・§3-4・§5-4・§5-6
- 手本: `tests_ui/test_pane_window_width_persistence.py:1-50`

## 含まない

- ヘッダの測定・ウィンドウ最小幅への組込み・既存テストの期待値見直し（**task_03**）
- 起動時の保存値更新（**task_04**）/ 正本反映（**task_06**）
- ダイアログ内の取得ボタン / 省略表示のボタン幅の固定（§2-5・§6）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq tests_ui` が clean。
2. `-m unittest tests_ui.test_header_button_widths -v` が全 pass。
3. `-m unittest tests_ui.test_hook_controller_teardown tests_ui.test_startup_font_characterization -v` が pass（無変更）。
4. `-m unittest discover -s tests` が 450 OK（skip 7）/ `-m unittest discover -s tests_ui` が全 OK（件数を報告）/ `-m tests.smoke_app` が SMOKE OK / `git status --short config` が空。
   **pane 系 tests_ui（`test_full_view_panes` 等）が落ちた場合**は、ボタン幅固定でヘッダ・ウィンドウの要求幅が変わったことが原因かを切り分けて報告する（期待値の見直しは task_03 の範囲。本タスクでは直さず報告）。
5. `rg -n "from keyseq.presentation.controllers" keyseq/presentation/views` が 0 件（views → controllers の import を作らない）。
6. `rg -n "\"キー入力で取得\"|\"取得中…（Escで停止）\"|\"開始（フックON）\"|\"停止（フックOFF）\"|\"通常トリガー無効化\"|\"通常トリガー有効化\"" keyseq/presentation` が
   `hook_button_texts.py` と `dialogs/` の 2 ファイルだけ。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は task_05 でまとめて実施。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（presentation 9 ファイル + tests_ui 1 新規）。
- `verifier`: compileall clean / 新規 5 OK / teardown・font 特性 14 OK / `tests` 450 OK（skip 7）/ `tests_ui` 418 OK（pane 系も全 OK・期待値変更なし）/ smoke OK / config mtime 不変 / views→controllers import 0 件 / 文言直値は定数モジュール + dialogs 2 ファイルのみ。
- `reviewer` = 完了可（指摘なし）。
