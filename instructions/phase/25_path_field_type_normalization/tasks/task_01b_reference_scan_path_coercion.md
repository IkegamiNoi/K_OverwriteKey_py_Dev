# task_01b_reference_scan_path_coercion

## 目的

task_01 の完了後レビューで見つかった**参照突合経路の同種箇所**を直す。
`reference_scan.py` は孤児ファイルの棚卸し・参照元の掃除のために**ディスクから生 JSON を直接読む
別実装**で、`ensure_config_compatibility` も `build_runtime_data_from_split` も通らない。
同じ `trigger_set_path` / `active_keymap_path` / `keymaps[].path` /
`external_keyboard_layouts[].path` を task_01 と**違う扱い**にしたままにしない。

レイヤ制約: **application 限定**。domain / presentation 不変・**JSON スキーマ不変**。

## 対象範囲（application 限定・実質 1 行）

### keyseq/application/config_service/reference_scan.py

**変更は `_source_path` の本体 1 行のみ**:

```python
def _source_path(value: Any) -> str:
    return str(value or "").strip()   # :185-186 現在
    return coerce_label(value)        # 置換後
```

- `_entry_path`（`:189-192`）と `_path_value`（`:193-194`）は**どちらも `_source_path` を
  呼ぶだけ**なので変更不要（上記 1 行で全経路が吸収される）。実測で確認済み。
- `coerce_label` を `keyseq.domain.config` から import する
  （現在 `:1-7` は `os` / `typing.Any` / `from . import contracts` のみなので**追加が必要**）。
- **`coerce_key_name` は使わない**（すべてパスであり、小文字化するとパスが壊れる）。
- ヘルパの**シグネチャ・戻り値の型は変えない**（呼び出し側は無変更）。

### tests/test_reference_scan.py

3. 下記「確認」1〜3 に対応する単体テストを追加する。

### 設計メモ / 制約

- 実害は小さい（repr は実在しないパスなので `referenced` 集合に紛れるだけで、実在ファイルが
  誤って掃除されることも、正しいパスの登録が阻害されることもない）。
  **目的は「同じフィールドを 2 経路で違う扱いにしない」こと**。
- **falsy な非文字列（`0` / `false` / `[]` / `{}` / `None`）の既存挙動を変えないこと**
  （現状も `str(x or "")` で空へ倒れている）。
- **正常なパス文字列の結果を 1 文字も変えないこと**（大文字小文字の保持・相対 / 絶対の判定）。

## 読むファイル

- `keyseq/application/config_service/reference_scan.py:60-95`（`_load_source`・生 JSON を読む箇所）/
  `:105-175`（各 `_add_*` の呼び出し）/ `:180-200`（ヘルパ 3 つ）
- `keyseq/domain/config.py:80-86`（`coerce_key_name` / `coerce_label`）
- `tests/test_reference_scan.py`（既存テストの書き方）
- `instructions/phase/25_path_field_type_normalization/tasks/task_01_path_field_coercion.md`（前タスクの方針）

## 含まない

- 正本への明記・記録・`/refactor_check`（**task_02**）
- **`orphan_scan.py` / `quarantine.py` の `str(x or "").strip()`**。これらは
  `normalize_scan_dirs` で正規化済みの値・内部生成の値・startup 設定を受ける引数であり、
  **生 JSON のフィールドを直接読む箇所ではない**（対象外）
- **`startup_io.py:18` の `keymap_set_path`**（config.json の生値を読むが **presentation 層**で、
  phase.md が presentation 不変と宣言しているため対象外。task_02 で残件として記録する）
- 保存側（`split_payloads.py` / `save_path_resolution.py`）
- `coerce_label` の改名 / `normalize_key_name` のシグネチャ変更

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree からは `..\..\..\.venv\Scripts\python.exe`）。

1. `_source_path` / `_path_value` が**非文字列に対して `""` を返す**
   （`{"a":1}` → `""` / `[1]` → `""` / `123` → `""`。**repr にならない**）。
   **修正前は `"{'a': 1}"` / `"[1]"` を返すことを実測済み**なので、このテストは修正前なら落ちる。
2. `_entry_path({"path": {"a": 1}})` が `""` になる（`_source_path` 経由で吸収されること）。
3. **falsy と正常系が不変**: `_path_value(0)` → `""`（現状と同じ）/
   `_source_path("  User/Keymaps/A.json  ")` → `"User/Keymaps/A.json"`（**小文字化されない**）。
4. 参照突合の結果が壊れていないこと（`collect_referenced_paths` 相当の既存テストが全 pass）。
5. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
6. 既存テスト全 pass。**ベースライン: `tests` = 511（skip 7）/ `tests_ui` = 446 / smoke pass**。
   件数が減らないこと。

## 完了条件

- 上記確認 1〜6 が pass・**reviewer 採用**。
- 実機目視: **不要**（参照突合の内部正規化のみで UI 変更なし）。
