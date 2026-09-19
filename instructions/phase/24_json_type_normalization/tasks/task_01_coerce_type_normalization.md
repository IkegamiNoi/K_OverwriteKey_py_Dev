# task_01_coerce_type_normalization

## 目的

JSON 読込時の型不正の扱いを全経路で統一する（暫定仕様 20 §2 / §3 / §4 / §5 / §6）。
文字列前提の処理へ非文字列が渡って **`AttributeError` になる 6 箇所**を解消し、
`str()` 強制による **repr 文字列の混入**を止める。

レイヤ制約: **domain / application 限定**。presentation 不変・**JSON スキーマ不変**
（読込時の正規化のみ。保存 payload の形は変えない）。

## 対象範囲（domain + application 限定）

### keyseq/domain/config.py

1. **入口関数を 2 本新設**（`normalize_key_name` の直後に置く。暫定仕様 §6）:

   ```python
   def coerce_key_name(value: Any) -> str:   # 非 str は "" / str は normalize_key_name を通す
   def coerce_label(value: Any) -> str:      # 非 str は "" / str は (value or "").strip()
   ```

   - **`normalize_key_name(value: str)` のシグネチャは変えない**（呼び出しが 158 箇所あるため）。
   - `bool` は `str` ではないので `""` になる（`isinstance(value, str)` 判定で足りる）。

2. `normalize_actions`（現 `:136-146`）: `a["label"] = (a.get("label") or "").strip()` を
   `a["label"] = coerce_label(a.get("label"))` へ。

3. `ensure_config_compatibility` の trigger 正規化（現 `:178-179`）:
   - `t["key"] = normalize_key_name(t.get("key", ""))` → `coerce_key_name(t.get("key"))`
   - `t["label"] = (t.get("label") or "").strip()` → `coerce_label(t.get("label"))`

4. 同 keymap 正規化（現 `:248` / `:265`）:
   - `keymap_id = normalize_key_name(item.get("id", ""))` → `coerce_key_name(item.get("id"))`
   - `"label": (item.get("label") or "").strip()` → `coerce_label(item.get("label"))`

5. 同 mappings 正規化（現 `:252-260`）: **target が非文字列なら対ごと除去**する。
   - `source = normalize_key_name(str(raw_source or ""))` は**そのまま**
     （JSON 由来でキーは常に str。暫定仕様 §4 の注記）。
   - `target = normalize_key_name(str(raw_target or ""))` を
     `target = coerce_key_name(raw_target)` へ置き換える。
     非 str は `""` になり、既存の `if not source or not target: continue` で**対ごと落ちる**。

### keyseq/application/config_service/__init__.py

6. `_generate_keymap_id`（現 `:505`）: `normalize_key_name(raw_keymap.get("id", ""))` を
   `coerce_key_name(raw_keymap.get("id"))` へ。import に `coerce_key_name` を追加。
   - 2 行目の `normalize_key_name(os.path.splitext(...)[0])` は stem（必ず str）なので**変えない**。

7. `load_keymap_file`（現 `:130`）: `"label": str(raw_keymap.get("label") or "").strip()` を
   `coerce_label(raw_keymap.get("label"))` へ。

8. `_normalize_sequence_payload`（現 `:456`）: `"label": str(sequence.get("label") or "").strip()` を
   `coerce_label(sequence.get("label"))` へ（**参照先 sequence からの repr 再流入対策**。
   暫定仕様 §5 の注記・`split_loading.py:485-486` の `trigger.update` で参照元へ伝播するため）。

### keyseq/application/config_service/split_loading.py

9. `load_triggers_from_trigger_set`（現 `:468` / `:470` / `:480`）:
   - `"key": normalize_key_name(str(raw_trigger.get("key") or ""))` → `coerce_key_name(raw_trigger.get("key"))`
   - `"label": str(raw_trigger.get("label") or "").strip()` → `coerce_label(raw_trigger.get("label"))`
   - `sequence_path = str(raw_trigger.get("sequence_path") or "").strip()` →
     **非 str なら空**にする（`coerce_label` を流用してよい。暫定仕様 §5 = 空扱い）。
   - `suppress` / `run_to_end` / `run_to_end_delay_ms` は **R3 = 現状のまま触らない**。

### tests/test_domain_config.py / tests/test_config_service.py

10. 下記「確認」1〜8 に対応する単体テストを追加する。

### 設計メモ / 制約

- **falsy な非文字列（`0` / `false` / `[]` / `{}`）は現状でも `x or ""` で空へ倒れている**。
  本タスクで挙動が変わるのは **truthy な非文字列のみ**。既存の falsy 挙動を変えないこと
  （`coerce_key_name(0)` / `coerce_label([])` はいずれも `""`。結果は現状と同じ）。
- **正常な JSON の読込結果は 1 文字も変えない**（後方互換・正本 §5.1）。
- `normalize_actions` は phase 23 で作った関数。要素の非 dict 除去は**そのまま**。
- 保存側（`build_sequence_payload` / `build_keymap_file_payload`）には手を入れない。

## 読むファイル

- `instructions/history/20_individual_json_type_normalization.md`（主入力・§1 / §3〜§6）
- `keyseq/domain/config.py:76-80`（`normalize_key_name`）/ `:110-146`（`safe_deepcopy` / `normalize_actions`）/
  `:160-200`（trigger 正規化）/ `:239-268`（keymap・mappings 正規化）
- `keyseq/application/config_service/__init__.py:7-16`（import）/ `:112-144`（`load_keymap_file`）/
  `:454-466`（`_normalize_sequence_payload`）/ `:499-517`（`_generate_keymap_id`）
- `keyseq/application/config_service/split_loading.py:450-500`（`load_triggers_from_trigger_set`）
- `tests/test_domain_config.py`（`normalize_actions` の既存テストの書き方）
- `tests/test_config_service.py:1718-1745`（`SequenceFileIoTest`）

## 含まない

- 正本 `data_schema.md` への反映・暫定仕様 20 の凍結（**task_02**）
- `decisions_archive/24` / `current.md` の更新・`/refactor_check`（**task_02**）
- `actions[]` の**要素**の型規定の変更（phase 23 で確定済。扱うのは要素内の `label` のみ）
- `hotkey_presets` の読込（既に規定どおり）
- `suppress` / `run_to_end` / `run_to_end_delay_ms` の既定値への倒し方（R3・現状維持）
- `button` 非文字列の `AttributeError`（`action_executor.py:119`・実行時の別レイヤ）
- `normalize_key_name` のシグネチャ変更・既存 158 箇所の呼び出しの書き換え
- UI・ダイアログ・保存 payload の変更

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree からは `..\..\..\.venv\Scripts\python.exe`）。

1. `coerce_key_name` / `coerce_label` の単体テスト: `None` / `""` / `0` / `False` / `[]` / `{}` →
   いずれも `""`。`123` / `["a"]` / `{"a":1}` → いずれも `""`（**repr にならない**）。
   `"  F1  "` → `"f1"`（`coerce_key_name`）/ `"  x  "` → `"x"`（`coerce_label`）。
2. `{"id": 123}` / `{"id": ["a"]}` の keymap JSON を `load_keymap_file` で読んでも**例外が出ず**、
   ファイル名 stem 由来の id になる。
3. `{"mappings": {"a": {"x": 1}, "b": "c"}}` を `load_keymap_file` で読むと `{"b": "c"}` のみが残る。
4. `{"key": {"a": 1}, "label": ["a"]}` を含む trigger_set を `load_trigger_set_file` で読むと
   `key` / `label` がともに `""`。
5. `{"actions": [{"type": "text", "label": 123}]}` を含む sequence / trigger_set の単体読込で
   **例外が出ず**、その action の `label` が `""`。
6. `ensure_config_compatibility({"triggers":[{"key":5}]})` /
   `({"keymaps":[{"id":7,"label":[1]}]})` で**例外が出ない**。
7. 参照先 sequence が `{"label": {"a": 1}}` のとき、参照元 trigger の `label` が
   `"{'a': 1}"` にならない（`""` になる）。
8. **falsy な非文字列の既存挙動が不変**: `{"id": 0}` の keymap はファイル名 stem 由来の id になる
   （現状と同じ）。
9. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
10. 既存テスト全 pass。**ベースライン: `tests` = 486（skip 7）/ `tests_ui` = 446 / smoke pass**。
    **件数が減らないこと**。

## 完了条件

- 上記確認 1〜10 が pass・**reviewer 採用**。
- 実機目視: **不要**（読込経路の内部正規化のみで UI 変更なし）。
