# task_03_grid_overlay_crosshair

## 目的

枠の窓で、選んでいる枠のクリック点（task_02 の `GridView.click_point`）に十字マークを描き、キーの表示位置が中央の keymap では選んだ枠のキーの文字を十字に置き換える（暫定 41 §7「枠の窓」）。
**presentation 限定**（`keyseq/presentation/screen_grid/`）。domain / application は変えない。スキーマ不変。

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/screen_grid/crosshair.py`

* 定数 `CROSSHAIR_ARM_PX = 12`・`CROSSHAIR_WIDTH = 2`・`CROSSHAIR_TAG = "crosshair"`
* `draw_crosshair(canvas, rect, point, *, fill) -> None`（座標はすべてキャンバス座標で受け取る）
  * 横の線 = `y = point[1]`、`x` は `[max(x1, px - ARM), min(max(x1, x2 - 1), px + ARM)]`
  * 縦の線 = `x = point[0]`、`y` は `[max(y1, py - ARM), min(max(y1, y2 - 1), py + ARM)]`
  * 始点 < 終点の線だけを `canvas.create_line(..., fill=fill, width=CROSSHAIR_WIDTH, tags=CROSSHAIR_TAG)` で描く（0px の向きの腕は描かれない・暫定 41 §6・§7）
  * task_05 の編集の窓でも使う（Feature Shared = `screen_grid/` 直下）

### `keyseq/presentation/screen_grid/grid_overlay_window.py`

* `_draw`: 選んでいる枠（`index == view.selected`）で `view.click_point` が `None` でなければ、
  * 枠の線の後に `draw_crosshair` を呼ぶ（矩形・点はモニタの左上を引いたキャンバス座標・色 = `_SELECTED`）
  * `view.label_position` が `"center"` ならその枠の `draw_cell_label` を呼ばない（左上表示では従来どおり描く）
* 選択なし（`view.selected is None`）・`click_point` が `None` のときは十字を描かない。それ以外の描画は変えない

### テスト（`tests_ui/test_screen_grid_overlay.py` に追加）

* `draw_crosshair`（Mock の canvas）: 通常の枠で横・縦 2 本・腕 12px / 枠の端の近くで腕が枠の中へ切り詰められる / 幅 0px の枠で横の線を描かない（高さ 0px も同様）/ `width=2`・`tags="crosshair"`
* 実キャンバス（既存のテストの組み立てを流用）:
  * 枠を選ぶと `crosshair` タグの線が 2 本・交点がクリック点（キャンバス座標）/ 選択なしでは 0 本
  * 中央表示: 選んだ枠のキーの文字の item が無く、他の枠の文字は残る / 左上表示: 選んだ枠の文字も残る
  * 矢印（`GridKeyAction("right", ...)`）の後に描き直され、十字が移動量だけ動く
  * Enter の後（最上段・選択なし）に十字が消える

## 設計メモ / 制約

* 色・腕・線幅は固定値（設定にしない・暫定 41 §2）。色は既存の `_SELECTED` を使う（新しい色を足さない・配色の見直しは idea_44）
* 描き直しは従来どおり `ScreenGridController` → `GridOverlayWindow.show(view)` の経路（`_changed` → `on_view_changed`）で起きる。controller は変えない
* `cell_label.py` には足さない（十字は文字ではないため別モジュール）

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§6・§7）
* `keyseq/presentation/screen_grid/grid_overlay_window.py`（全体・編集対象）
* `keyseq/presentation/screen_grid/cell_label.py`（全体・手本）
* `keyseq/application/screen_grid_session.py`（:30-41 `GridView` のみ）
* `tests_ui/test_screen_grid_overlay.py`（:1-130 組み立てと既存の描画テスト・:278-300 実キャンバスのテスト）

## 含まない

* 編集の窓のドラッグ中の十字（task_05・`draw_crosshair` を流用する）
* 編集の窓の操作キーの欄（task_04）
* 配色・腕・線幅の設定化（スコープ外・暫定 41 §10）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_screen_grid_overlay` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（既知の実行順依存は current.md「テスト負債」のとおり切り分け）
* `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` OK

## 完了条件

* 上記確認 pass・**reviewer 採用**
* **ユーザーの実機目視（本タスクで実施）**: 暫定 41 §9 の 1〜4（十字の表示と置き換え・矢印 / Shift+矢印 / 端で止まる / リピート・選択なしの矢印はアプリへ届く・Enter / Shift+Enter がずらした点をクリック・選び直し等で中心へ）
