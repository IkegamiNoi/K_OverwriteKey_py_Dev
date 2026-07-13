# task_08_grid_hide_at_zoom.md

## 配置層

presentation のみ

## 目的

縮小時に **グリッド線の見かけ間隔が小さくなりすぎる** と画面が線で埋まり視認性が落ちる。
閾値未満の場合はグリッド線を描画しないようにする。

仕様正本:
- `instructions/common/spec_detail/viewport.md`「縮小時のグリッド非表示」
- `instructions/common/spec_detail/features.md` 4.11「縮小時のグリッド非表示」

---

## 実装内容

### A. 閾値定数

- `src/presentation/painters.py` または `coordinate_system.py` に閾値定数を追加
- 例: `GRID_HIDE_APPARENT_INTERVAL_PX = 8.0`（画面上のグリッド間隔がこの値未満で非表示）
- 値は実装時に微調整可。MVP は固定 px 値で開始

### B. 見かけ間隔の算出

- 既定の行高 / 列幅（`settings.grid_default_row_height` / `_column_width`）と現在のズーム倍率から見かけ間隔を計算
- `apparent_interval_x = default_column_width * view_state.scale`
- `apparent_interval_y = default_row_height * view_state.scale`

### C. 描画判定

- `painters.draw_grid` 内で:
  - `apparent_interval_x < GRID_HIDE_APPARENT_INTERVAL_PX` なら縦グリッド線を描かない
  - `apparent_interval_y < GRID_HIDE_APPARENT_INTERVAL_PX` なら横グリッド線を描かない
  - 縦 / 横は独立判定（縦だけ消える、横だけ消える状態もありうる）

### D. 非表示対象の限定

- グリッド線（縦線 / 横線）と交点ドットのみ非表示
- ノード / エッジは描画を維持
- 保存範囲外の補完線も同じ閾値判定で消える（描画範囲全体を均一に扱う）

---

## 要件

- domain / application / infrastructure は変更しない
- ノード / エッジの描画ロジックは無変更
- 拡大時 / 通常倍率では既存挙動と同じ
- 閾値定数は固定値 1 つ。設定化は将来検討

---

## 完了条件

### 機能面

- ズームアウトを進めると、ある倍率からグリッド線が消える
- グリッド線が消えてもノードと接続線は表示されたまま
- ズームを戻すと再びグリッド線が現れる
- 縦 / 横で独立に判定される（テスト可能）

### 静的確認

- `compileall` クリーン

### レビュー

- サブエージェントレビュー（仕様適合性 / 閾値の妥当性 / 不要変更の有無）

---

## 注意事項

- task_06（描画 / 保存分離）が前提
- task_07（無限描画）が完了している必要はないが、両方完了後の見た目を最終確認すること
- 閾値値の決定はユーザビリティテストで微調整可能（MVP は妥当な初期値で OK）

---

## スコープ外

- 自動グリッド拡張（task_09）
- 閾値の設定化
- ノード / エッジの非表示制御
