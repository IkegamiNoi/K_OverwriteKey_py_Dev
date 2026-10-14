# task_05_grid_editor_drag_crosshair

## 目的

編集の窓で境界をドラッグしている間、その境界に関係する枠すべての中心へ十字マークを描く（暫定 41 §7「編集の窓」）。
**presentation 限定**（`grid_editor_window.py` のみ）。task_03 の `draw_crosshair` を流用する。domain / application は変えない。スキーマ不変。

## 対象範囲（presentation 限定・`keyseq/presentation/dialogs/grid_editor_window.py`）

* **ドラッグ中** = 境界の上でボタンを押してから離すまで（`self._drag` が `None` でない間）
* `_drag_related_cells() -> set[tuple[int, int]]`: `("row", i)` → 段 `i` と段 `i + 1` の全部の枠 / `("cell", r, c)` → `(r, c)` と `(r, c + 1)` / ドラッグなし → 空
* `draw()`: 関係する枠ごとに、
  * 枠の線の後に `draw_crosshair(self.canvas, rect, rect_center(rect), fill=<その枠の線の色>)` を描く（`rect_center` は domain の関数）
  * `self.label_position == "center"` ならその枠の `draw_cell_label` を呼ばない（左上表示では描く）
  * 関係しない枠・ドラッグなしの描画は従来どおり
* `on_press`: 境界を掴んだ（`self._drag` を設定した）ときも `self.draw()` を呼んでから返す（押した時点で十字を出す）
* `on_release`: `self._drag = None` の後に `self.draw()` を呼ぶ（離したら消す）
* 細分化のボタンの並びには十字を出さない（スコープ外）

### テスト（`tests_ui/test_grid_editor_window.py` に追加・既存の組み立てを流用）

* 段の境界を押す → `crosshair` タグの線が「上下 2 段の枠の数 × 2 本」/ 各十字の交点がその枠の中心
* 列の境界を押す → 2 枠分（4 本）
* ドラッグで境界を動かすと、十字が新しい枠の中心へ描き直される
* 離すと `crosshair` タグの線が 0 本
* 中央表示: ドラッグ中は関係する枠のキーの文字が無く、関係しない枠の文字は残る / 離すと戻る。左上表示: ドラッグ中も文字が残る
* 境界でない所の押下（枠の選択）では十字を描かない

## 設計メモ / 制約

* 十字の大きさ・線幅・切り詰めは `presentation/screen_grid/crosshair.py` に従う（新しい定数を足さない）
* 編集の窓の座標はキャンバス座標（`cell_rects()` がモニタ左上を原点にした矩形を返す）なので変換は要らない
* 既存の `on_drag` の処理（境界の移動・8px の制限）は変えない

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§7）
* `keyseq/presentation/dialogs/grid_editor_window.py`（全体・編集対象）
* `keyseq/presentation/screen_grid/crosshair.py`（全体）
* `tests_ui/test_grid_editor_window.py`（:1-80 組み立て・境界のドラッグの既存テスト）

## 含まない

* 細分化のボタンの並びの十字・細分化後の境界のドラッグ（スコープ外・暫定 41 §10）
* 枠の窓（task_03 で済み）・操作キーの欄（task_04 で済み）
* 正本の改訂（task_07）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_grid_editor_window` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（既知の実行順依存は current.md「テスト負債」のとおり切り分け）
* `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` OK

## 完了条件

* 上記確認 pass・**reviewer 採用**
* **ユーザーの実機目視（本タスクで実施）**: 暫定 41 §9 の 8（境界のドラッグ中に関係する枠の中心に十字・離すと消える）
