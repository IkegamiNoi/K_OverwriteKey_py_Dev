#### 5.8.2 runtime の内部キー（永続化しない）

* 子ファイルの読込元・保存先（source_path）と未保存フラグ（dirty）は、runtime のデータに
  **内部キー**として保持する:
  * keymap … `INTERNAL_KEYMAP_SOURCE_PATH` / `INTERNAL_KEYMAP_DIRTY`（`keymaps[]` の各要素）
  * sequence … `INTERNAL_SEQUENCE_SOURCE_PATH` / `INTERNAL_SEQUENCE_DIRTY`（各キーマップの `triggers[]` の各要素）
  * trigger_set … **`INTERNAL_TRIGGER_SET_SOURCE_PATH` / `_PARENT_REFS` / `_DIRTY` / `_IMPORTED`（`keymaps[]` の各要素）**
    （phase 34・§5.13.6。共有実体は全メンバーで同値に揃える。runtime データの直下には置かない）
  * 旧形式の移行状態 … `_legacy_trigger_set`（runtime データの直下。状態・旧値・移行先 keymap id。§5.13.3〜4）
* 内部キーは**保存する JSON へ出力しない**（永続化されるのは `_parent_refs` と各ファイル本来のキーのみ）。
  Export（単一 JSON）でも入れ子の内部キーを除く
* trigger_set の未保存状態は**キーマップ要素の内部キーが正**で、未保存状態の管理側は対象の実体を省略したら
  アクティブキーマップの実体を扱う（読み手と書き手が別の場所を見る状態を作らない）
