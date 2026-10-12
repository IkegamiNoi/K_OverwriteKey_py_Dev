# task_05_grid_checkbox_in_dialogs

## 目的

キーマップの編集ダイアログと、追加のまとめて設定のダイアログ（新規の行だけ）に「枠を使う」チェックを足し、OK で keymap の `grid` を作る / `enabled` を切り替える（暫定 40 §8.1・§2-1・§2-10・§3「OFF に戻しても消さない」）。
**presentation（ダイアログ 2 つ・`keymap_panel_controller.py`・`keymap_add_flow.py`）+ domain に既定の grid を作る純関数 1 つ。application・infrastructure 不変。スキーマ不変（task_02 の `grid` を使う）。**

## 対象範囲

### domain `keyseq/domain/screen_grid/`

- `new_enabled_grid() -> dict`: `{"enabled": True, "monitors": {}, "sub": sub_layout_to_json(default_sub_layout())}`（§8.1「組み込みの既定の形で `grid` を作る」）。`__init__.py` の `__all__` へ追加

### `keyseq/presentation/dialogs/keymap_edit_dialog.py` `KeymapEditDialog`

- 引数 `initial_grid_enabled: bool = False` を追加。ラベルの行の下に `ttk.Checkbutton`「枠を使う」（`BooleanVar`）を足す（hint・ボタンの行は 1 行ずつ下へ）
- `_ok` の `result` に `"grid_enabled": bool` を足す（既存の `key` / `label` は変えない）
- 「枠を編集…」ボタンは足さない（task_06）

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- 編集ダイアログの呼び出し（:382 付近）で `initial_grid_enabled` = 対象 keymap の `grid` が dict で `enabled` が真か、を渡す
- `apply_keymap_edit` に `new_grid_enabled: bool | None = None` を追加（None = 変えない。既存の呼び出し元はそのまま動く）。今の値と違えば:
  - `grid` が dict でない（無い）かつ ON → `keymap["grid"] = new_enabled_grid()`
  - `grid` が dict → `grid["enabled"] = 値`（**OFF にしても `grid` を消さない**・形を保つ）
  - `changed = True`（既存の流れで一覧の更新・`refresh_triggers`・`mark_keymap_dirty`・知らせが走る）
- 呼び出し元から `result.get("grid_enabled")` を渡す

### `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py` `KeymapSwitchBatchDialog`

- 引数 `grid_option_rows: Collection[int] = ()` を追加（チェックを出す行の番号）。その行にだけラベルの行の下へ「枠を使う」チェック（既定 OFF）を足す。行が 1 つのとき（`single_row`）も同じ
- `_ok` の `values` の、チェックのある行の dict にだけ `"grid_enabled": bool` を足す（他の行は今のまま）

### `keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`

- `_run_batch` で、`kind == "新規"` のときだけ新規の行（`missing` の後ろ）の番号を `grid_option_rows` に渡す（読込・貼り付け・既存の行には出さない・§8.1）
- `_commit_batch` で、新規の keymap のうち `values` の `grid_enabled` が真のものに `keymap["grid"] = new_enabled_grid()` を入れる（`_append_keymap` の前。dirty は既存の `mark_keymap_dirty` で付く）
- 1 つ目の追加（ダイアログなし・`add_keymap` の先頭の分岐）は変えない

### テスト

- `tests/test_screen_grid.py` に `new_enabled_grid` の形（`normalize_grid` を通しても同じ・`monitors` が空・既定の `sub`）
- `tests_ui/test_keymap_switch_batch_dialog.py` に追加: `grid_option_rows` の行にだけチェックが出る / 結果にその行だけ `grid_enabled` が入る / 1 行のときもチェックが出る
- `tests_ui/test_task06_keymap_management_ui.py`（または編集ダイアログ・追加の流れを扱う既存の tests_ui）に追加:
  編集ダイアログの初期値（grid ON / OFF / grid 無し）/ OK で ON → `grid` が作られ未保存になる / ON → OFF で `grid` が残り `enabled` が偽 / 変えずに OK では `grid` に触れない /
  2 つ目以降の追加で「枠を使う」ON → 新しい keymap に既定の `grid` / OFF → `grid` キーが無い / 貼り付け・読込のダイアログにはチェックが出ない
- 既存テストは変えない

### 設計メモ / 制約

- `grid` の作成・切替はダイアログの OK でだけ（キャンセルで捨てる）。形の編集は task_06
- 既存の結果の dict のキー（`key` / `label`）と既存の引数の既定の挙動を変えない

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §2-1・§2-10・§3（`grid` の作成と保存の規則）・§8.1
- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体・編集対象）
- `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py`（全体・編集対象）
- `keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`（全体・編集対象）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:360-440`
- `keyseq/domain/screen_grid/__init__.py`・`models.py`
- テストの手本: `tests_ui/test_keymap_switch_batch_dialog.py` の冒頭 60 行・`tests_ui/test_task06_keymap_management_ui.py` の編集ダイアログを扱うテスト 1 つ（`grep -n "KeymapEditDialog" tests_ui/test_task06_keymap_management_ui.py` で位置を見る）

## 含まない

- 「枠を編集…」ボタンと編集の窓（task_06）
- 枠の表示・操作（task_03・04 で済）
- 正本への反映・`codebase_map.md`（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストのモジュールが pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` と `discover -s tests_ui`（1 本ずつ）が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_06 の後にまとめて実施（チェックで枠が出ること・追加で枠 ON のキーマップを作れること）
