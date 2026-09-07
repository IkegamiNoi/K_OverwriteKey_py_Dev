#### 5.8.2 runtime の内部キー（永続化しない）

* 子ファイルの読込元・保存先（source_path）と未保存フラグ（dirty）は、runtime のデータに
  **内部キー**として保持する:
  * keymap … `INTERNAL_KEYMAP_SOURCE_PATH` / `INTERNAL_KEYMAP_DIRTY`（`keymaps[]` の各要素）
  * sequence … `INTERNAL_SEQUENCE_SOURCE_PATH` / `INTERNAL_SEQUENCE_DIRTY`（`triggers[]` の各要素）
  * trigger_set … **`INTERNAL_TRIGGER_SET_SOURCE_PATH`**（runtime データの直下）。
    dirty は runtime データではなく未保存状態の管理側が持つ
* 内部キーは**保存する JSON へ出力しない**（永続化されるのは `_parent_refs` と各ファイル本来のキーのみ）
* trigger_set の source_path は**単一の入口を通して更新し、runtime データ側の
  `INTERNAL_TRIGGER_SET_SOURCE_PATH` と常に一致させる**（読み手と書き手が別の場所を見る状態を作らない）

