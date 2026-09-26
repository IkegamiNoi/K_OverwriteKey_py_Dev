# task_02: 旧形式の読込元が無いときは移行しない + 境界値テスト

## 目的

正本 `data_schema.md` §5.13.3-8（task_01 で追記）に実装を合わせ、移行の境界値をテストで固定する。

## 読むファイル

1. `instructions/common/spec_detail/data_schema.md` §5.13.3〜5.13.4（594-655 行付近）
2. `keyseq/application/config_service/split_loading.py:405-485`
3. `keyseq/application/config_service/__init__.py:1129-1135`（`_load_optional_json`）
4. `tests/test_per_keymap_triggers_load.py:120-240`（`load_split` ヘルパと既存の split 移行テスト）

## 実装対象

- `split_loading.py::_migrate_legacy_trigger_set`: 使用済み（`same`）判定の**後**に、
  `service._resolve_config_relative_path(legacy_path, config_root)` の結果に**ファイルが存在しない**
  （`os.path.exists` が偽）なら `return "none", active, False` を追加する。
  「あるが読めない」は従来どおり移行（`attach_trigger_set` の読込失敗扱い）。
- `tests/test_per_keymap_triggers_load.py` の split 系テストクラスへ追加（`load_split` ヘルパを使う）:
  1. 不在 × アクティブが `trigger_set_path` 項目を**持たない** → `_legacy_trigger_set.state == "none"`・
     キーマップ数不変・アクティブの `triggers == []`・`_keymap_dirty` が偽・`_trigger_set_source_path` なし。
  2. 不在 × アクティブが `""` を持つ / 別ファイル（`own.json`）を参照 → キーマップの**自動作成なし**・`auto_created` なし・
     state `"none"`・アクティブの一覧は自分の参照どおり。
  3. 不在のパスを別キーマップが参照している → state `"same"`（判定順の固定）。
  4. **あるが読めない**（壊れた JSON のテキスト / 最上位が list）→ state `"migrated"`・アクティブの `triggers == []`・
     `_trigger_set_source_path` が旧パス・`_keymap_dirty` が真。
  5. keymap_set の `trigger_set_path` が**非文字列**（`1` / `["old.json"]` / `{"path": "old.json"}` / `None` / `True`）→
     `old.json` が実在しても state `"none"`・`path == ""`・移行なし（subTest で列挙）。
- 既存テストの期待値は変えない（変える必要が出たら作業を止めて報告）。

## 対象外

- 正本・`codebase_map.md` の変更 / 他ファイルの production 変更 / 保存側（§5.13.4）の実装変更。
- 単一 JSON のトップレベル `triggers`。
- **テストの実行**（実測は verifier が行う）。

## 完了条件

- 上記の実装とテストが入り、`tests` / `tests_ui` / smoke が pass（verifier 実測）。
- reviewer の別視点レビュー（task_01 の正本追記も対象に含める）を通過。
