# task_02_pass_symbols_and_redraw

## 目的

選んでいるレイアウトの上書きの表（task_01 の `KeyboardLayout.key_symbol_map`）を、記号の表示を使う全箇所へ渡す。あわせて、レイアウトが変わる操作でトリガー一覧と出力シーケンス一覧を描き直す（暫定 64 §4・§5・§6）。
**presentation 限定**。domain・application・infrastructure は変えない。JSON・保存するキー名・送信・逆引き（`tk_keys.py:73`）は変えない。`key_symbols` の無いレイアウト（内蔵の US TKL を含む）では表示を変えない。

## 対象範囲（presentation 限定）

### 表の取り方（共通）

- 表は `self._app.layout.get_current_keyboard_layout().key_symbol_map`（`layout_controller.py:220`）から取る。`app.layout` が無い・例外のとき（tests の fake の app など）は `None` を渡す（今の表示）。取り方は 1 か所の小さな補助（例: `trigger_panel_controller` のメソッド）にまとめ、各所で書き写さない。

### `keyseq/presentation/controllers/action_list_rendering.py`

- `build_action_rows`・`format_next_action_summary` にキーワード引数 `key_symbols: Mapping[str, str] | None = None` を足し、`format_action_list_item(..., key_symbols=key_symbols)` に渡す（`:39`・`:63`）。

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `refresh_triggers`（`:217`）: `format_trigger_list_item(i, t, key_symbols=...)`。
- `refresh_actions`（`:299`）: `build_action_rows(..., key_symbols=...)`（詳細表示の一覧と簡易表示の欄で同じ行を共有・`:334-335`）。
- 「次に実行」の要約（`:506` `format_next_action_summary`）: `key_symbols=...`。

### `keyseq/presentation/controllers/call_view_controller.py`

- `_render_rows`（`:224`）: `build_action_rows(..., key_symbols=...)`。表は `self.app.trigger_panel` の補助から取る（`resolve_call` と同じ取り方）。

### `keyseq/presentation/keyboard_window.py`

- キー置換の枠（`:478`）: `self._layout.key_display_name(display) or display_key_name(display, self._layout.key_symbol_map)`。英字の大文字は今と同じくどちらも引かない（`:476`）。

### `keyseq/presentation/controllers/layout_controller.py`

- 一覧を描き直す補助（例 `_refresh_lists_after_layout_change`）を足す: `self._app.trigger_panel.refresh_triggers()` と `refresh_actions()` を呼ぶ（`trigger_panel` が無ければ何もしない）。`refresh_triggers` は中でキーボードUIも描き直す（`trigger_panel_controller.py:249`）。
- 呼ぶ場所（§6）:
  - `on_keyboard_layout_selected`（`:333`）: `reload_keyboard_layouts()` の後・`persist_keyboard_layout_selection()` の前。
  - `add_external_keyboard_layout`（`:341`）: `reload_keyboard_layouts()`（`:362`）の後。
  - `delete_keyboard_layout`（`:366`）: 最後の `reload_keyboard_layouts()`（`:408`）の後。
  - `set_keyboard_layout_selection`（`:310`）: `refresh_keyboard_window()` の後・`persist` の判定の前（削除で選んでいたレイアウトを外した後に保存が失敗・取り消しで抜けても揃うように）。
- `_refresh_active_layout`・`sync_keyboard_layout_controls`・`reload_keyboard_layouts` には入れない（構成の読込・起動・フックキーの個別設定の切替の経路は今のまま）。
- 出力シーケンス一覧の選択は `refresh_actions()` の既定のまま（「次に実行」へ戻る・§6 の受容）。選択を保つ仕組みは作らない。

### テスト（追加。期待値を変える既存のテストは無い見込み。変えた場合は報告）

- `tests_ui/test_action_list_rendering.py`: `build_action_rows`・`format_next_action_summary` に表を渡すと key_hold の行が上書き・渡さないと今のまま。
- `tests_ui/test_keyboard_key_text.py`（または `test_keyboard_window_left_right.py` の枠の文字のテストがある方）: キー置換の枠で `key_display_names` → `key_symbols` → `KEY_SYMBOLS` の順・英字の大文字は引かない・`key_symbols` の無いレイアウトは今のまま。
- `tests/test_layout_controller_registration.py`（または `test_layout_controller_scan_code.py`）: 4 か所（選択・追加・削除・`set_keyboard_layout_selection`〔`persist=True` で保存が失敗する場合を含む〕）で一覧の描き直しが呼ばれる / `reload_keyboard_layouts`・`sync_keyboard_layout_controls` 単独では呼ばれない（fake の `trigger_panel` で呼び出しを数える）。
- トリガー一覧・呼び出し先の表示枠に表が届くこと（`tests_ui/test_app_ui_flows.py` か `test_key_hold_presentation.py` の手本に倣う。`App` を作るなら import 直後に `fix_language("ja")`）。

## 読むファイル

- 暫定 64: `instructions/history/64_layout_key_symbols.md` §4〜§6
- 編集対象（全体）: `keyseq/presentation/controllers/action_list_rendering.py`
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:190-345`・`:480-520`
- `keyseq/presentation/controllers/call_view_controller.py:215-240`
- `keyseq/presentation/keyboard_window.py:460-490`
- `keyseq/presentation/controllers/layout_controller.py:200-410`
- task_01 で足した API: `keyseq/presentation/keyboard_layouts.py:22-45`（`key_symbol_map`）・`keyseq/domain/key_symbols.py:45-58`
- テストの手本: `tests_ui/test_action_list_rendering.py`・`tests_ui/test_keyboard_key_text.py`・`tests/test_layout_controller_registration.py`（各ファイルの既存のテストの書き方だけ）

## 含まない

- ステータスバーの警告の下敷き・追加のときの文言・見本 jis.json / us_tkl.json（task_03）
- 統合確認と実機目視（task_04）・正本の更新（task_05）
- domain・`keyboard_layouts.py` の読込の変更（task_01 で済み）
- 出力シーケンス一覧の選択を保つ仕組み・フックキーの個別設定の切替の経路での描き直し（§6 の受容）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（既知の負荷依存の窓の大きさのテストは切り分けて報告）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は無し（task_04 でまとめて実施）。
