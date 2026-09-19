# task_03_remaining_key_field_coercion

## 目的

task_01 で取りこぼした**残り 4 箇所**の型不正による `AttributeError` を解消する。
`ensure_config_compatibility` 内で **raw JSON を直接受ける `normalize_key_name` 呼び出し**のうち、
`str()` ガードが無いものが 4 箇所残っていた（task_02 の `deep-reviewer` 指摘 A + メインの全走査で追加 1 件）。

暫定仕様 20 §2 の**案 F（全経路へ一斉適用）**の趣旨は「例外を全経路から消す」ことであり、
残したままではフェーズの受け入れ条件（§8-5）を満たさない。

レイヤ制約: **domain 限定**。application / presentation 不変・**JSON スキーマ不変**。

## 対象範囲（domain 限定・4 箇所の置換）

### keyseq/domain/config.py（`ensure_config_compatibility` 内）

| # | 行 | 現在のコード | 置換後 |
|---|---|---|---|
| 1 | `:163` | `old_key = normalize_key_name(config.get("trigger_key", "f1"))` | `coerce_key_name(config.get("trigger_key", "f1"))` |
| 2 | `:213` | `config[HOOK_STOP_KEY] = normalize_key_name(config.get(HOOK_STOP_KEY, ""))` | `coerce_key_name(config.get(HOOK_STOP_KEY))` |
| 3 | `:214` | `config[HOOK_TOGGLE_KEY] = normalize_key_name(config.get(HOOK_TOGGLE_KEY, ""))` | `coerce_key_name(config.get(HOOK_TOGGLE_KEY))` |
| 4 | `:287` | `active_keymap_id = normalize_key_name(config.get("active_keymap_id", ""))` | `coerce_key_name(config.get("active_keymap_id"))` |

- `coerce_key_name` は task_01 で新設済み（同ファイル `:80`）。**新規関数は作らない**。
- #1 は**旧形式互換**の分岐（`triggers` が無く `trigger_key` がある場合）。
  既定値 `"f1"` は**そのまま残す**（キーが無いときの既定であり、型不正時の挙動とは別）。
- #2〜#4 は `config.get(X, "")` の既定 `""` を落としてよい（`coerce_key_name(None)` が `""` を返すため
  結果は同じ）。**落とさず `config.get(X, "")` のままでも可**。どちらでも挙動は変わらない。

### tests/test_domain_config.py

- 下記「確認」1〜5 に対応する単体テストを追加する。

### 設計メモ / 制約

- **falsy な非文字列の既存挙動を変えないこと**。`0` / `false` / `[]` / `{}` / `None` は
  変更前も `x or ""` で空へ倒れていた。変わるのは **truthy な非文字列のみ**。
- **`resolve_hook_keys_individual`（`:93-107`）は触らない**。`normalize_hook_key_pair` 経由で
  `str()` 済みのため既に安全（`:85-91`）。
- **`split_loading.py:360` の `switch_key` は対象外**。`:397` で `str()` 済みの値を受けており
  例外にならない。パス系・`switch_key` は [idea_25](../../../backlog/idea_25_path_field_type_normalization.md)。
- `format_trigger_list_item`（`:315`）など**表示整形は対象外**（正規化後の runtime を受けるため）。
- 本タスクで **`normalize_key_name` のシグネチャは変えない**（呼び出し多数）。

## 読むファイル

- `keyseq/domain/config.py:76-90`（`normalize_key_name` / `coerce_key_name` / `coerce_label`）/
  `:158-170`（旧形式互換）/ `:205-220`（hook キー）/ `:283-292`（`active_keymap_id`）
- `instructions/history/20_individual_json_type_normalization.md` §2 / §3（確定した方針・凍結済）
- `tests/test_domain_config.py`（task_01 で追加した `coerce_*` テストの書き方）

## 含まない

- 正本 `data_schema.md` の追記（**task_02** で実施済。本タスクで正本の規定は変わらない。
  §5.1 の共通規則は既に「読込経路すべて」と書いてあり、本タスクはその規定へ実装を追従させるもの）
- パス系フィールド・`switch_key`・`keymap_switch_keys`（**idea_25**・未着手のまま）
- `button` 非文字列（`action_executor.py:119`・実行時の別レイヤ）
- `normalize_key_name` のシグネチャ変更・既存呼び出しの書き換え
- application / presentation の変更

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree からは `..\..\..\.venv\Scripts\python.exe`）。

1. `ensure_config_compatibility({"hook_stop_key": 123})` で**例外が出ず**、`hook_stop_key` が `""`。
2. `ensure_config_compatibility({"hook_toggle_key": ["a"]})` で**例外が出ず**、`hook_toggle_key` が `""`。
3. `ensure_config_compatibility({"active_keymap_id": 7})` で**例外が出ず**、`active_keymap_id` が `""`。
4. `ensure_config_compatibility({"trigger_key": 123, "actions": []})`（旧形式互換）で**例外が出ず**、
   生成される trigger の `key` が `""`。
5. **falsy と正常系の挙動が不変**: `{"hook_stop_key": 0}` → `""`（現状と同じ）/
   `{"hook_stop_key": " F12 "}` → `"f12"` / `{"trigger_key": "F1", "actions": []}` の
   旧形式変換が従来どおり成立する。
6. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
7. 既存テスト全 pass。**ベースライン: `tests` = 498（skip 7）/ `tests_ui` = 446 / smoke pass**。
   件数が減らないこと。

## 完了条件

- 上記確認 1〜7 が pass・**reviewer 採用**。
- 実機目視: **不要**（読込経路の内部正規化のみで UI 変更なし）。
- 本タスクの完了をもって、暫定仕様 20 §8-5（全経路で例外が出ない）を満たす。
