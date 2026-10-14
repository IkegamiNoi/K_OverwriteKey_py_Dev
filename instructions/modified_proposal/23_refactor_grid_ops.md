# 提案書 23: phase 57（画面の枠の十字マーク・操作キーの任意化）後のリファクタ

> 状態: **未実施・ユーザー判断待ち**（2026-10-14・phase 57 task_07 の /refactor_check）。

## 判定の要約

範囲 `git diff 4ca8cf1..HEAD -- keyseq/`（14 ファイル・+452 / -97）。メトリクスは verifier の実測、M3・M4・M6 はメインで裏取り（下記の ファイル:行）。

- **M4 該当**: 矢印の 4 操作のタプル `("up", "down", "left", "right")` の直書きと、それから矢印の操作キーの集合を組み立てる形が 0 → **2 か所**で同形（`application/screen_grid_session.py:190`・`:197`）。`:303-304` の `("left", "right")` / `("up", "down")` は向きの判定で対になっており対象外（完了判定前レビューで訂正）。操作の一覧の正は `domain/screen_grid/ops.py:11` の `GRID_OPS`
- **M3 該当**: 編集の窓の「細分化のボタンと操作キーのボタンの選択を両方解除する」2 行の組が **3 か所**（`presentation/dialogs/grid_editor_window.py:78-79`・`:156-157`・`:268-269`）。選択の種類が増えるたびに 3 か所を直す形
- **M6 該当**: パネルのキーのボタンの色 `"#e0e0e0"`（通常）/ `"#d0d0d0"`（押下中）/ `"#ffcc66"`（選択中）が、操作キーのボタンの追加で `presentation/screen_grid/grid_editor_panel.py` 内に 2 組ずつ（`:57`・`:118` と `:140`・`:160`）
- 既知（提案書に含めない）: 枠の窓・編集の窓の線や強調の色の共有（`grid_overlay_window.py:15` `_SELECTED`・`grid_editor_window.py:121` の直値）→ idea_44 / `"esc"` の直書き（`grid_editor_window.py:221`・既存）
- M1（600 行超は `keymap_panel_controller.py` 650 行だが +8）・M2（80 行超の新規関数なし）・M5（0 件）: 非該当

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_screen_grid_session.py`（矢印の集合・移動・優先順位）/ `tests/test_screen_grid_ops.py` / `tests_ui/test_grid_editor_window.py`（選択の排他・Esc の順・操作キーの欄・ボタンの見た目は relief / background を確かめる）
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: 矢印の 4 操作を 1 か所の定義にする（M4）

- 対象: `domain/screen_grid/ops.py`・`application/screen_grid_session.py:190`・`:197`（`:303-304` の向きの判定はそのまま）
- 変更:
  ```python
  # ops.py（GRID_OPS の隣）
  ARROW_OPS = ("up", "down", "left", "right")
  def arrow_keys(ops: Mapping[str, str]) -> frozenset[str]:
      return frozenset(ops[name] for name in ARROW_OPS)
  # screen_grid_session.py
  keys.difference_update({FIXED_BACK_KEY, *arrow_keys(ops)})      # :190
  arrow = arrow_keys(ops)                                          # :197
  ```
- 完了条件: 項目 0 のコマンドが全 pass。`grep -n '"up", "down", "left", "right"' keyseq/application` が 0 件
- リスクと戻し方: 挙動不変（同じ集合を作る）。戻すならタプルを 2 か所に書き戻す
- 依存: なし

## 項目 2: 編集の窓のキーのボタンの選択の解除を 1 つの呼び出しにする（M3）

- 対象: `presentation/screen_grid/grid_editor_panel.py`・`presentation/dialogs/grid_editor_window.py:78-79`・`:156-157`・`:268-269`
- 変更: パネルに `clear_key_button_selections()`（`clear_sub_selection()` + `clear_op_selection()`）を置き、3 か所の 2 行を 1 行に置き換える。Esc の順（`on_escape` の 1 つずつ解除）と単独の呼び出し（`:276`・パネル内の排他）は変えない
- 完了条件: 項目 0 のコマンドが全 pass。`grep -c "clear_sub_selection()" keyseq/presentation/dialogs/grid_editor_window.py` が 1（`on_escape` の分岐だけ）
- リスクと戻し方: 挙動不変（同じ 2 つを同じ順で呼ぶ）。戻すなら 3 か所に 2 行を書き戻す
- 依存: なし

## 項目 3: パネルのキーのボタンの色を定数にする（M6）

- 対象: `presentation/screen_grid/grid_editor_panel.py:57`・`:118`・`:140`・`:160`
- 変更: モジュールの先頭に `_KEY_BUTTON_BG = "#e0e0e0"`・`_KEY_BUTTON_ACTIVE_BG = "#d0d0d0"`・`_KEY_BUTTON_SELECTED_BG = "#ffcc66"` を置き、4 か所の直値を置き換える（Private の定数・モジュール外へは出さない。編集の窓・枠の窓の線の色の共有は idea_44 の範囲）
- 完了条件: 項目 0 のコマンドが全 pass。`grep -c '"#e0e0e0"' keyseq/presentation/screen_grid/grid_editor_panel.py` が 1（定義だけ）
- リスクと戻し方: 挙動不変（同じ値）。戻すなら直値に書き戻す
- 依存: なし

## 実施方法（ユーザー選択）

- (a) phase 57 の末尾に `task_08_refactor` として起票して実施 / (b) 次フェーズ前の独立ミニフェーズ
