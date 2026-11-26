# task_03a_test_reinforcement

## 目的

task_03 の統合レビュー（deep-reviewer 低 5 件）のうちユーザーが採用した ①③⑤ に対応し、テストの検出力を補強する（暫定 62 §7-4・§5・§7-5a）。
**テストのみ・本体（keyseq/）は変えない**。

## 対象範囲（テスト限定）

### `tests/test_scroll_invert_setting.py`（既存の末尾に追加・⑤は既存テストの書き換え）

- ⑤ `test_does_not_touch_configuration_dirty_state` を、fake の self に `dirty_tracker=Mock()` と `state=Mock()` を持たせ、`set_scroll_invert` の後にどちらにも呼び出し（`mock_calls`）が無いことを assert する形に書き換える（意図の明示）。`_fake_app` に任意の引数を足してよい。
- ① 保存 → 再読込の往復: 一時フォルダ（`tempfile.TemporaryDirectory`）に置いた startup の JSON へ、本物の `StartupIo.write_startup` で `{"scroll_invert": {"vertical": True, "horizontal": False}}` を書き、`keyseq.presentation.startup_settings.load_startup_settings` で読み直して `coerce_scroll_invert` が `ScrollInvert(vertical=True)` になることを確かめる。
  - `StartupIo` に渡す fake の app は `_startup_settings`（例 `{"ui_language": "ja"}`）・`paths.preferred_startup_path()`（一時ファイルのパスを返す）・`config_service`（本物の `keyseq.application.config_service.ConfigService` か、`save_startup` / `load_startup` が JSON を読み書きする最小の fake）・`hook`（`Mock()`）を持つ。`load_startup_settings` の引数は `startup_settings.py:4` のシグネチャに合わせる。
  - 続けて、他の設定の保存（`write_startup({"ui_font_delta_pt": 1})`）の後も読み直した `scroll_invert` が残ることを確かめる。

### `tests_ui/test_scroll_invert_menu.py`（既存の末尾に追加）

- ③-a メニューの項目を実際に押す: `_settings_menu()` から「スクロールの向き」のサブメニューを取り、`write_startup` を `return_value=True` で patch した状態で、保存済みを両方 False・変数を False にしてから `scroll_menu.invoke(0)` → `self.app.update()`（macOS では `menu_commands` の待ち行列を `after(0)` で回すため）→ `write_startup` が `{"scroll_invert": {"vertical": True, "horizontal": False}}` で 1 回呼ばれ、`action_executor._get_scroll_invert()` が `ScrollInvert(vertical=True)` になる。テストの最後に `_startup_settings` と 2 つの変数を元に戻す。
- ③-b フォント変更での作り直し: 縦の変数を True にした状態で、`write_startup` を patch して `self.app.set_ui_font_delta(1)` → 作り直したメニューの「スクロールの向き」の 1 項目目の `variable` が `ui_vars.scroll_invert_vertical_var` のままで値が True。最後に `set_ui_font_delta(0)` で戻し、変数を False に戻す。

### 設計メモ / 制約

- 既存テストの途中に新しいテストを差し込まない（⑤の書き換えを除く）。
- tests_ui の `invoke` は Windows では即時に、macOS では待ち行列経由で実行される。`update()` を挟めばどちらでも同じ assert になる。
- 本物の書き込みは一時フォルダにだけ行う（worktree の `config/config.json` を書かない）。

## 読むファイル

- `tests/test_scroll_invert_setting.py`（全体）・`tests_ui/test_scroll_invert_menu.py`（全体）
- `keyseq/presentation/controllers/config_io/startup_io.py:43-67`（`write_startup`）・`keyseq/presentation/startup_settings.py`（全体）
- `keyseq/application/config_service/__init__.py:120-140`（`load_startup` / `save_startup`）
- `keyseq/presentation/app.py:565-586`（`_apply_font_delta`・`set_ui_font_delta`）

## 含まない

- 本体（keyseq/）の変更
- ②（失敗のつながり）は受容・④（正本昇格の注意）は task_04

## 確認

- `../../../.venv/bin/python -m compileall -q tests tests_ui` が clean
- `../../../.venv/bin/python -m unittest tests.test_scroll_invert_setting -v` が pass
- `../../../.venv/bin/python -m unittest tests_ui.test_scroll_invert_menu -v` が pass（単独）
- `../../../.venv/bin/python -m unittest discover -s tests` が全 pass
- worktree の `config/config.json` がテストで書き換わっていない（実行前後の `git status`・ファイルの更新時刻）
- 差分が上記 2 テストファイルに限られる

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は不要（task_03 で完了済み）。
