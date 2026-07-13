# task_05_grid_mode.md

## 配置層

presentation（主体）+ application（軸操作のユースケース連携）+ domain（行高 / 列幅変更ヘルパー）

## 目的

グリッドモードを新規追加する。グリッド（行・列）の操作をマウスなしで完結させる。

仕様正本:
- `instructions/common/spec_detail/key_input.md` §5.8
- `instructions/common/spec_detail/features.md` 4.13

---

## 実装内容

### A. `src/shared/actions.py`

`Action` 列挙体に以下を追加:
- `EXIT_GRID_MODE`
- `GRID_SELECT_AXIS_ROW`
- `GRID_SELECT_AXIS_COLUMN`
- `GRID_TOGGLE_TARGET_SCOPE`
- `GRID_SELECT_LINE_PREV`
- `GRID_SELECT_LINE_NEXT`
- `GRID_INCREASE_SPACING`
- `GRID_DECREASE_SPACING`

### B. `src/shared/actions.py` `Mode`

- `GRID = "grid"` を追加

### C. `src/presentation/key_map.py`

`_GRID_BINDINGS` を新設（推奨キー、実装時に微調整可）:

| キー | アクション |
|---|---|
| R | GRID_SELECT_AXIS_ROW |
| C | GRID_SELECT_AXIS_COLUMN |
| T | GRID_TOGGLE_TARGET_SCOPE |
| ← または ↑ | GRID_SELECT_LINE_PREV |
| → または ↓ | GRID_SELECT_LINE_NEXT |
| ＋ または = | GRID_INCREASE_SPACING |
| - | GRID_DECREASE_SPACING |
| Esc | EXIT_GRID_MODE |

`_BINDINGS_BY_MODE` に `Mode.GRID: _GRID_BINDINGS` を追加。

### D. `src/domain/map_state.py`

行高 / 列幅を変更するヘルパーを追加（純粋関数、PySide6 非依存）:

- `set_row_height(state: MapState, row_id: str, height: float) -> MapState`
- `set_column_width(state: MapState, column_id: str, width: float) -> MapState`
- `scale_all_row_heights(state: MapState, factor: float) -> MapState`
- `scale_all_column_widths(state: MapState, factor: float) -> MapState`

### E. `src/application/grid_service.py`（新規）

グリッドモード用のユースケースを集約:

- `change_global_spacing(state, axis, delta) -> MapState`
- `change_single_line_spacing(state, axis, line_id, delta) -> MapState`
- 軸（row / column）と delta（増減量）から domain ヘルパーを呼ぶ薄い層

### F. `src/presentation/input_controller.py`

- `ENTER_GRID_MODE` ハンドラを本実装に
- 内部状態 `_grid_ctx`（軸 / スコープ / 選択ライン ID）を保持
- 各 GRID_* アクションのハンドラを追加
- EXIT_GRID_MODE: NORMAL 復帰

### G. ビュー描画

- グリッドモード中の選択ライン強調（軽量な見た目変更）
  - 例: 選択中ラインだけ太線 / 色変更
- 描画は `painters.py` に薄く追加

### H. key_guide / help_dialog

- グリッドモード用の表示行を追加

---

## 要件

- domain ヘルパーは純粋関数。PySide6 非依存
- application 層は domain と presentation の橋渡しに徹する
- 間隔変更の delta（px 単位）は定数で（例: ±10.0px）。設定化は将来検討
- グリッドモード中も既存ノードの位置 ID（row_id / column_id）は維持される

---

## 完了条件

### 機能面

- 通常モード中に G キーでグリッドモードへ遷移
- R / C で軸切替（行 / 列）、T でスコープ切替（全体 / 単一ライン）
- 矢印 で単一ライン選択時のライン移動
- ＋ / - で間隔増減（全体 / 単一ライン双方）
- Esc で NORMAL 復帰
- マウスのパン / ズームはグリッドモード中も利用可能
- マウスクリックは当面 no-op

### 静的確認

- `compileall` クリーン
- domain / application 層に PySide6 import が増えていない

### レビュー

- サブエージェントレビュー（仕様適合性 / 依存方向 / 責務分離 / 不要変更の有無）

---

## 注意事項

- 優先実装順序: 全体間隔変更 → 単一ライン選択 → 単一ライン間隔変更 → 複数ライン（後続）
- 行高 / 列幅は float（task_01 で int → float 化済）
- 最小値（0 以下）にしないバリデーションを domain ヘルパーに含める
- グリッドモード中の選択ライン強調は軽量に。複雑なオーバーレイは不要

---

## スコープ外

- ビューモード（task_04）
- 自動グリッド拡張（task_09）
- モード表示 UI（task_10）
- 無限グリッド描画（task_07）
- 複数ライン選択（後続フェーズ）
