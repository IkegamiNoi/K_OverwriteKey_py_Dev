# task_09_auto_extend_grid.md

## 配置層

application（主体）+ domain（add_column / add_row ヘルパー）+ presentation（ビューモード Enter 着地連携）

## 目的

保存対象グリッドの端でノード作成を試みた場合、必要な行 / 列を末尾または先頭に **自動追加** してから配置する。
4 方向すべて（上 / 下 / 左 / 右）に対応する。

ユーザーから「クイック作成で右 / 下端に出ると 圏外 エラーになる」事象が発生していた件の本格対応。

仕様正本:
- `instructions/common/spec_detail/features.md` 4.4「端での自動拡張」
- `instructions/common/spec_detail/features.md` 4.6 / 4.7（クイック作成 / カスタム作成）

---

## 実装内容

### A. `src/domain/map_state.py`

行 / 列追加ヘルパーを追加:

- `add_column(state: MapState, column: Column, at_end: bool = True) -> MapState`
  - `at_end=True`: 末尾追加 / `at_end=False`: 先頭追加
  - ID 重複は ValueError
- `add_row(state: MapState, row: Row, at_end: bool = True) -> MapState`
  - 同上
- 既存ノード / エッジ / positions は変更しない（追加された行 / 列に新規 ID を割当）

### B. `src/application/id_generator.py`

行 / 列の ID 生成関数を追加:

- `generate_column_id(state: MapState) -> str`
- `generate_row_id(state: MapState) -> str`
- 既存の column / row ID と衝突しない値を返す（例: `col_<n>` / `row_<n>` 連番）

### C. `src/application/quick_create.py`

- `_step` で圏外検出時、自動拡張する分岐を追加:
  - 行 / 列の追加: settings の `grid_default_row_height` / `_column_width` を使用
  - 4 方向それぞれの拡張ロジック（上: 行先頭、下: 行末尾、左: 列先頭、右: 列末尾）
- 下方向探索（`search_limit`）中の保存範囲外検出も同様に自動拡張
- `QuickCreateResult.OUT_OF_GRID` は実質発生しなくなる（エラーケースは「探索上限超過 + 自動拡張試行回数上限」のみ）

### D. `src/application/custom_create.py`

- 確定位置が保存範囲外の場合、自動拡張してから配置
- カスタム作成カーソルが保存範囲外を指せるよう、`input_controller.py` のカーソルクランプを緩和（仕様 4.7「カーソル移動範囲」）

### E. `src/presentation/input_controller.py`

- ビューモード `VIEW_CREATE_AT_CENTER`（task_04）の自動拡張連携
- 画面中心ワールド座標が保存範囲外の場合、自動拡張してからノード作成

### F. ビュー位置補正

- 先頭追加（左 / 上）時に既存ノードが視覚的にシフトする問題への対応:
  - `view_state` の offset を、追加された列幅 / 行高 分だけシフトして既存ノードを画面上で動かさない
  - presentation 層で対応（domain は無変更）

---

## 要件

- domain ヘルパーは純粋関数。PySide6 非依存
- application 層は domain と settings の橋渡し
- 既存ノードの ID（`row_id` / `column_id`）は変更しない
- JSON フォーマットは変更しない（`columns` / `rows` 配列が伸びるだけ）
- 自動拡張の試行回数上限を設ける（暴走防止、例: 1 操作で最大 16 回）

---

## 完了条件

### 機能面

- クイック作成で 4 方向すべて、保存範囲外でも作成成功
- カスタム作成のカーソルが保存範囲外（無限グリッド範囲内）に移動可能、確定で自動拡張 + 配置
- ビューモードの Enter 着地で画面中心が保存範囲外でも作成成功
- 先頭追加時、既存ノードが画面上でシフトしない（ビュー位置補正）
- 既存の保存ファイル（layout.json）が読み込める後方互換が保たれる
- 拡張後すぐに保存（Ctrl+S）→ 読込（Ctrl+O）でノード位置・グリッド構造が再現される

### 静的確認

- `compileall` クリーン
- domain 層に PySide6 import が増えていない
- application 層に PySide6 import が増えていない
- JSON フォーマットの自動テスト（mvp_fix task_01 で整備済の内容）が通る

### レビュー

- サブエージェントレビュー（仕様適合性 / 依存方向 / 責務分離 / 不要変更の有無 / チェック漏れ）

---

## 注意事項

- task_07（無限描画）と組み合わせて初めて UX が成立する。task_07 完了後に着手すること
- task_04（ビューモード）の `VIEW_CREATE_AT_CENTER` ハンドラと連携する（暫定実装からの切替）
- 自動拡張試行回数上限を超えた場合のエラーメッセージは適切に
- 先頭追加時のビュー位置補正を忘れると「既存ノードが勝手に動いた」と誤解される

---

## スコープ外

- 行 / 列の手動追加 UI
- 行 / 列の削除 UI
- 行 / 列の順序変更（後続フェーズ）
- mvp_fix の task_03（自動拡張先行実装）は本タスクで一括対応するため起票しない
