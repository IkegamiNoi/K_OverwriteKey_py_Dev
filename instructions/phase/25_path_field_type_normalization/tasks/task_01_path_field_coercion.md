# task_01_path_field_coercion

## 目的

パス系・キー名系のフィールドに残っている `str()` 強制を `coerce_*` へ置き換え、
正本 `data_schema.md` §5.1「型不正の共通規則」へ実装を追従させる。
現在は非文字列を渡すと **Python の repr 文字列がパス / スイッチキーとして runtime に載る**。

レイヤ制約: **domain / application 限定**。presentation 不変・**JSON スキーマ不変**。
**例外（`AttributeError`）になる箇所は無い**ため、本タスクは repr 混入の解消が目的。

## 対象範囲（domain + application・9 箇所の置換）

`coerce_key_name` / `coerce_label` は phase 24 で新設済み（`keyseq/domain/config.py:80` / `:84`）。
**新規関数は作らない**。

### 使い分け（重要）

- **パス** … `coerce_label`（非 str なら `""`、str なら trim）。
  **`coerce_key_name` を使わない**（小文字化でパスが壊れる）。
- **キー名 / id** … `coerce_key_name`（非 str なら `""`、str なら trim + 小文字化）。

### keyseq/domain/config.py

| # | 行 | 現在 | 置換後 |
|---|---|---|---|
| 1 | `:240` | `path = str(item.get("path") or "").strip()` | `path = coerce_label(item.get("path"))` |
| 2 | `:301` | `keymap_id = normalize_key_name(str(raw_keymap_id or ""))` | `keymap_id = coerce_key_name(raw_keymap_id)` |

- #1 は `external_keyboard_layouts` の要素。空になれば直後の `if not path: continue` で
  **要素ごと落ちる**（§5.1「要素が成立しない場合は除去」と整合）。
- #1 の `isinstance(item, str)` 分岐（`:237-238`）は**そのまま**（旧記法の文字列要素）。
- #2 は `keymap_switch_keys` の値。現在は `keymap_ids` の membership check で偶然落ちているだけで、
  **偶然の防御に依存しない形にする**のが目的。
  `switch_key`（`:300`）は JSON のキーで常に str のため**変更しない**。

### keyseq/application/config_service/split_loading.py

| # | 行 | フィールド | 置換後 |
|---|---|---|---|
| 3 | `:312` | `trigger_set_path` | `coerce_label(keymap_set.get("trigger_set_path"))` |
| 4 | `:337` | `active_keymap_path` | `coerce_label(keymap_set.get("active_keymap_path"))` |
| 5 | `:396` | `entry.get("path")` | `coerce_label(entry.get("path"))` |
| 6 | `:397` | `entry.get("switch_key")` | `coerce_key_name(entry.get("switch_key"))` ← **キー名なのでこちら** |
| 7 | `:399` | `entry`（非 dict 形式の旧記法） | `coerce_label(entry)` |
| 8 | `:441` | `path_value`（`load_trigger_set` の引数） | `coerce_label(path_value)` |
| 9 | `:522` / `:524` | 外部レイアウト登録の `item.get("path")` / `item` | `coerce_label(...)` |

- `:308` の `load_trigger_set(service, keymap_set.get("trigger_set_path"), ...)` は
  **引数を生のまま渡している**が、受け側 `:441` を直せば吸収されるため**呼び出し側は変更しない**。
- いずれも空になれば既存の分岐（`if not stored_path: continue` / `return` 等）が処理する。
  **新しい分岐を足さない**。

### tests/test_domain_config.py / tests/test_config_service.py

10. 下記「確認」1〜7 に対応する単体テストを追加する。

### 設計メモ / 制約

- **falsy な非文字列（`0` / `false` / `[]` / `{}` / `None`）の既存挙動を変えないこと**。
  現状も `str(x or "")` / `(x or "")` で空へ倒れている。変わるのは **truthy な非文字列のみ**。
- **正常なパス文字列の解決結果を 1 文字も変えないこと**。`coerce_label` は trim のみで
  `str(x or "").strip()` と同じ（str 入力時）。相対 / 絶対の判定（§5.7）に影響させない。
- `coerce_label` はパスにも使うため名前が内容と合わないが、**phase 24 の名前を継続する**
  （改名は本タスクのスコープ外）。
- 対象外（意図的に残す）: `orphan_sweep_scan_dirs`（`orphan_scan.py:43` ほか・非 str を除去済）/
  `_normalize_parent_refs`（`config_service/__init__.py:770-780`・非 str を除去済）/
  `hotkey_presets_path`（`domain/config.py:212-214`・`isinstance` ガード済）/
  **保存側の `str(...)`**（`split_payloads.py` / `save_path_resolution.py` は runtime を扱う）。

## 読むファイル

- `keyseq/domain/config.py:76-90`（`coerce_key_name` / `coerce_label`）/ `:232-246`
  （`external_keyboard_layouts`）/ `:293-311`（`keymap_switch_keys`）
- `keyseq/application/config_service/split_loading.py:305-345` / `:390-402` / `:437-448` / `:515-530`
- 正本 `instructions/common/spec_detail/data_schema.md` §5.1「型不正の共通規則」（規定）と §5.7（パス表記）
- `tests/test_domain_config.py`（phase 24 で追加した `coerce_*` テストの書き方）
- `tests/test_config_service.py`（split 読込のテストの書き方）

## 含まない

- 正本 §5.5 / §5.7 への明記・`decisions_archive/25` / `current.md` / backlog の更新・
  `/refactor_check`（**task_02**）
- `orphan_sweep_scan_dirs` / `_parent_refs` / `hotkey_presets_path`（既に規定どおり）
- keymap / trigger_set / sequence の**内容フィールド**（phase 24 で対応済）
- `button` 非文字列（`action_executor.py:119`・実行時の別レイヤ）
- `coerce_label` の改名 / `normalize_key_name` のシグネチャ変更
- パスの実在確認・§5.7 の表記ルールの変更・保存側の変更・UI の変更

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree からは `..\..\..\.venv\Scripts\python.exe`）。

1. `ensure_config_compatibility({"external_keyboard_layouts":[{"path":{"a":1}},{"path":"ok.json"}]})` で
   **repr が残らず** `[{"path": "ok.json"}]` になる。
2. `external_keyboard_layouts` の**旧記法（文字列要素）**が従来どおり通る
   （`["ok.json"]` → `[{"path": "ok.json"}]`）。
3. keymap_set の `keymaps[].switch_key` が dict のとき、**スイッチキーに repr が載らない**
   （有効な `path` と組み合わせても `get_keymap_switch_keys` に `"{'a': 1}"` が現れない）。
   **修正前はこれが載ることを確認済み**なので、このテストは修正前なら落ちる。
4. keymap_set の `trigger_set_path` / `active_keymap_path` / `keymaps[].path` が非文字列でも
   例外が出ず、**未指定と同じ扱い**になる。
5. `keymap_switch_keys` の値が非文字列のとき、`keymap_ids` の membership check に**頼らずに**
   落ちる（同名 id が存在しても採用されない形になっていること）。
6. **falsy と正常系の挙動が不変**: `{"path": 0}` は従来どおり要素ごと落ちる /
   正常なパス文字列（相対・絶対の両方）の解決結果が変わらない /
   **パスが小文字化されていない**（`User/Keymaps/A.json` が `user/keymaps/a.json` にならない）。
7. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
8. 既存テスト全 pass。**ベースライン: `tests` = 505（skip 7）/ `tests_ui` = 446 / smoke pass**。
   件数が減らないこと。

## 完了条件

- 上記確認 1〜8 が pass・**reviewer 採用**。
- 実機目視: **不要**（読込経路の内部正規化のみで UI 変更なし）。
