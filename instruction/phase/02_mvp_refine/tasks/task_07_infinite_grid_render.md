# task_07_infinite_grid_render.md

## 配置層

presentation のみ

## 目的

グリッドを **保存範囲に依存せず、ビューポートに応じて無限に描画** する。
保存範囲を超える領域でも均等間隔のグリッド線が見えるようにする。

仕様正本:
- `instructions/common/spec_detail/viewport.md`「無限グリッド描画」
- `instructions/common/spec_detail/features.md` 4.11「無限グリッド描画」

---

## 実装内容

### A. 「仮想グリッド線位置」の計算

- 保存範囲（`columns` / `rows`）の左端 / 上端の交点座標と、保存範囲外の領域を `default_width` / `default_height`（設定値）刻みで補完する
- 例: 保存範囲が 0〜800px、ビューポートが -400〜1200px なら、
  - 左側: -400, -240, -80（default_width = 160 と仮定）が追加描画対象
  - 右側: 800, 960, 1120 が追加描画対象
- 行も同様

### B. `src/presentation/coordinate_system.py`

- `visible_grid_lines_x(view_state, screen_width, state, default_width) -> list[float]`
- `visible_grid_lines_y(view_state, screen_height, state, default_height) -> list[float]`
- 戻り値はビューポートに表示される全グリッド線（保存範囲内外問わず）の **ワールド座標** リスト

### C. `src/presentation/painters.py` `draw_grid`

- B の関数を使って描画範囲のグリッド線を描く
- 保存範囲との境界線は通常の描画と区別しない（仕様: 保存 / 描画は同じ見た目）
- 交点ドットも保存範囲外に拡張（task_02 / mvp_fix の交点ドットを保存範囲ベースで描いている場合）

### D. 描画パフォーマンス

- ビューポートに収まらないグリッド線は計算 / 描画しない
- 拡大時はグリッド線数が膨大にならないよう、`visible_grid_lines_*` の上限を設ける（例: 1000 本）
- 上限を超える場合は描画をスキップ（task_08 の閾値非表示と相補的に動作）

### E. 設定値

- `default_width` / `default_height` は `settings.json` の `grid_default_column_width` / `grid_default_row_height` を使用

---

## 要件

- domain / application / infrastructure は変更しない
- 既存ノード描画 / エッジ描画 / ヒットテストの挙動は無変更
- 保存範囲内のグリッド線描画は既存と同じ見た目（既存挙動を壊さない）
- カスタム作成カーソルが保存範囲外を指せるようにすること（task_05 後続 / 仕様 4.7）

---

## 完了条件

### 機能面

- パン / ズームでビューポートを動かすと、保存範囲外でもグリッド線が描画される
- 保存範囲内外で見た目に違和感がない（同じ太さ / 色 / 間隔）
- 拡大時でも描画線数が適切に制限される（上限内）
- ノード / エッジの描画は無変更

### 静的確認

- `compileall` クリーン
- 大きく拡大 / 縮小しても描画が破綻しない

### レビュー

- サブエージェントレビュー（仕様適合性 / 不要変更の有無 / パフォーマンス）

---

## 注意事項

- task_06（描画 / 保存分離）が前提
- カスタム作成カーソルの「保存範囲外への移動」を本タスクで対応するかは要判断（task_05 のスコープ次第）
- 保存範囲が空（0 columns / 0 rows）のときの挙動も考慮
- 縮小時の非表示は task_08 で対応するため、本タスクでは縮小時の描画は重くなりうる（B の上限で対応）

---

## スコープ外

- 縮小時のグリッド非表示（task_08）
- 自動グリッド拡張（task_09）
- ノード / エッジ描画の変更
