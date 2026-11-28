# task_03b_horizontal_and_deferred_boundary_test

## 目的

完了判定前の Codex 敵対的レビュー 指摘 3（ユーザー採用 2026-11-26）に対応し、横のチェックの配線と、macOS で保存がメニューの待ち行列にある間は実行に使う値が前のままという境界（暫定 62 §4・§5）をテストで押さえる。
**テストのみ・本体（keyseq/）は変えない**。

## 対象範囲（テスト限定）

### `tests_ui/test_scroll_invert_menu.py`（既存の末尾に 1 件追加）

- `test_horizontal_menu_item_saves_after_menu_queue_runs`:
  1. 保存済み（`_startup_settings`）を両方 False・2 つの変数を False・`_scroll_invert` を `ScrollInvert()` にする（元の値は try の前に退避し finally で戻す。task_03a の ③-a と同じ形）。
  2. `write_startup` を `return_value=True` で patch し、「スクロールの向き」のサブメニューの **2 項目目（横を反転）** を `invoke(1)` する。
  3. `is_aqua(self.app)`（`keyseq.presentation` の既存の判定。`views/menu_command_queue.py` が使うものと同じ関数を import する）が真のとき: この時点で `write_startup` は未呼び出し・横の変数は True・`action_executor._get_scroll_invert()` は `ScrollInvert()` のまま（保存前は前の向き）。偽（Windows）のときはこの assert を飛ばす。
  4. `self.app.update()` の後: `write_startup` が `{"scroll_invert": {"vertical": False, "horizontal": True}}` で 1 回呼ばれ、`_get_scroll_invert()` が `ScrollInvert(horizontal=True)`。

### 設計メモ / 制約

- 既存テストは変えない。新しいテストは末尾に足す。
- `is_aqua` の import 元は `keyseq/presentation/views/menu_command_queue.py` の import 行に合わせる（新しい判定を作らない）。

## 読むファイル

- `tests_ui/test_scroll_invert_menu.py`（全体）
- `keyseq/presentation/views/menu_command_queue.py`（全体・`defer` と `is_aqua` の import）

## 含まない

- 本体の変更・他のテストファイル

## 確認

- `../../../.venv/bin/python -m unittest tests_ui.test_scroll_invert_menu -v` が pass（単独・macOS では待ち行列の assert が実際に効く）
- `../../../.venv/bin/python -m compileall -q tests_ui` が clean

## 完了条件

- 上記確認 pass・**reviewer 採用**。
